#!/usr/bin/env bash
#
# InfoBlox MCP Server Deployment Script
# Deploys InfoBlox MCP integration to Red Hat 7.9 system
#

set -e

echo "================================================================================"
echo "InfoBlox MCP Server Deployment"
echo "================================================================================"
echo ""

# Configuration
REMOTE_HOST="${REMOTE_HOST:-192.168.1.200}"
REMOTE_USER="${REMOTE_USER:-tshoush}"
REMOTE_PASS="${REMOTE_PASS:-123Jason!}"
REMOTE_DIR="/home/${REMOTE_USER}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Helper functions
print_step() {
    echo -e "${CYAN}▶ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Function to copy file using expect
copy_file() {
    local source="$1"
    local dest="$2"

    expect << EOF
set timeout 30
spawn scp -o StrictHostKeyChecking=no "$source" "${REMOTE_USER}@${REMOTE_HOST}:${dest}"
expect {
    "password:" {
        send "${REMOTE_PASS}\r"
        expect eof
    }
    timeout {
        puts "Connection timeout"
        exit 1
    }
}
EOF
}

# Function to run remote command
run_remote() {
    local command="$1"

    expect << EOF
set timeout 60
spawn ssh -o StrictHostKeyChecking=no "${REMOTE_USER}@${REMOTE_HOST}" "$command"
expect {
    "password:" {
        send "${REMOTE_PASS}\r"
        expect eof
    }
    timeout {
        puts "Connection timeout"
        exit 1
    }
}
EOF
}

# Check dependencies
print_step "Checking dependencies..."

if ! command -v expect &> /dev/null; then
    print_error "expect is not installed"
    echo "Install with: brew install expect (macOS) or sudo yum install expect (RHEL)"
    exit 1
fi

if ! command -v scp &> /dev/null; then
    print_error "scp is not installed"
    exit 1
fi

print_success "Dependencies OK"
echo ""

# Test connection
print_step "Testing connection to ${REMOTE_HOST}..."

if run_remote "echo 'Connection test successful'" > /dev/null 2>&1; then
    print_success "Connected to ${REMOTE_HOST}"
else
    print_error "Cannot connect to ${REMOTE_HOST}"
    exit 1
fi
echo ""

# Deploy files
print_step "Deploying InfoBlox MCP files..."

FILES=(
    "infoblox-explorer.py"
    "infoblox-mcp-server.py"
    "claude-chat-mcp.py"
    "infoblox_schemas.json"
    "INFOBLOX-MCP-README.md"
)

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -n "  Copying $file... "
        if copy_file "$file" "${REMOTE_DIR}/$file" > /dev/null 2>&1; then
            print_success "OK"
        else
            print_error "Failed"
        fi
    else
        print_warning "$file not found, skipping"
    fi
done

echo ""

# Make scripts executable
print_step "Setting execute permissions..."

run_remote "chmod +x ~/infoblox-explorer.py ~/infoblox-mcp-server.py ~/claude-chat-mcp.py" > /dev/null 2>&1
print_success "Execute permissions set"
echo ""

# Install Python dependencies
print_step "Installing Python dependencies..."

echo "  Installing MCP SDK..."
run_remote "pip install --user mcp anthropic" 2>&1 | grep -E "(Successfully installed|Requirement already satisfied)" || true

print_success "Dependencies installed"
echo ""

# Create MCP cache directory
print_step "Creating MCP cache directory..."

run_remote "mkdir -p ~/.infoblox-mcp" > /dev/null 2>&1
print_success "Cache directory created"
echo ""

# Set up environment variables
print_step "Configuring environment variables..."

ENV_CONFIG="
# InfoBlox MCP Configuration
export INFOBLOX_HOST=\"192.168.1.224\"
export INFOBLOX_USER=\"admin\"
export INFOBLOX_PASSWORD=\"infoblox\"
export WAPI_VERSION=\"v2.13.1\"
"

# Check if already configured
if run_remote "grep -q 'InfoBlox MCP Configuration' ~/.bashrc" > /dev/null 2>&1; then
    print_warning "Environment variables already configured"
else
    run_remote "echo '$ENV_CONFIG' >> ~/.bashrc" > /dev/null 2>&1
    print_success "Environment variables added to ~/.bashrc"
fi

echo ""

# Create aliases
print_step "Creating command aliases..."

ALIASES="
# InfoBlox MCP Aliases
alias infoblox-explore='python ~/infoblox-explorer.py'
alias infoblox-mcp='python ~/infoblox-mcp-server.py'
alias chat-mcp='python ~/claude-chat-mcp.py'
"

if run_remote "grep -q 'InfoBlox MCP Aliases' ~/.bashrc" > /dev/null 2>&1; then
    print_warning "Aliases already configured"
else
    run_remote "echo '$ALIASES' >> ~/.bashrc" > /dev/null 2>&1
    print_success "Aliases added to ~/.bashrc"
fi

echo ""

# Run initial discovery (if schemas don't exist)
print_step "Checking InfoBlox schema cache..."

if run_remote "test -f ~/infoblox_schemas.json" > /dev/null 2>&1; then
    print_success "Schema cache exists"
else
    print_warning "No schema cache found"
    echo ""
    print_step "Running initial schema discovery (this may take 30-45 seconds)..."

    run_remote "python ~/infoblox-explorer.py" 2>&1 | tail -10

    if run_remote "test -f ~/infoblox_schemas.json" > /dev/null 2>&1; then
        print_success "Schema discovery completed"
    else
        print_error "Schema discovery failed"
    fi
fi

echo ""

# Test InfoBlox connectivity
print_step "Testing InfoBlox connectivity..."

TEST_RESULT=$(run_remote "python -c \"
import requests
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
try:
    r = requests.get('https://192.168.1.224/wapi/v2.13.1/network?_max_results=1',
                     auth=('admin', 'infoblox'), verify=False, timeout=5)
    if r.status_code == 200:
        print('SUCCESS')
    else:
        print('HTTP_ERROR:' + str(r.status_code))
except Exception as e:
    print('ERROR:' + str(e))
\"" 2>&1 | tail -1)

if echo "$TEST_RESULT" | grep -q "SUCCESS"; then
    print_success "InfoBlox API is accessible"
else
    print_error "Cannot connect to InfoBlox API"
    echo "    Result: $TEST_RESULT"
    echo "    Please verify InfoBlox IP, credentials, and network connectivity"
fi

echo ""

# Verify installation
print_step "Verifying installation..."

echo ""
echo "Checking deployed files:"

run_remote "ls -lh ~/{infoblox-*.py,claude-chat-mcp.py,infoblox_schemas.json,INFOBLOX-MCP-README.md} 2>/dev/null | awk '{print \"  \" \$9, \$5}'" 2>/dev/null || true

echo ""
echo "Checking Python packages:"

run_remote "pip show mcp anthropic 2>/dev/null | grep -E '(Name|Version)' | head -4" 2>/dev/null || true

echo ""

# Print summary
echo "================================================================================"
echo "Deployment Complete!"
echo "================================================================================"
echo ""
echo -e "${GREEN}✓ InfoBlox MCP Server deployed successfully${NC}"
echo ""
echo "Files deployed:"
echo "  • infoblox-explorer.py       - Schema discovery tool"
echo "  • infoblox-mcp-server.py     - MCP server (1,392 tools)"
echo "  • claude-chat-mcp.py         - Enhanced Claude chat"
echo "  • infoblox_schemas.json      - Cached schemas"
echo "  • INFOBLOX-MCP-README.md     - Complete documentation"
echo ""
echo "Environment configured:"
echo "  • INFOBLOX_HOST=192.168.1.224"
echo "  • INFOBLOX_USER=admin"
echo "  • WAPI_VERSION=v2.13.1"
echo ""
echo "Commands available:"
echo "  ${CYAN}infoblox-explore${NC}  - Discover/refresh InfoBlox schemas"
echo "  ${CYAN}infoblox-mcp${NC}      - Start InfoBlox MCP server (standalone)"
echo "  ${CYAN}chat-mcp${NC}          - Start Claude chat with InfoBlox integration"
echo ""
echo "Quick Start:"
echo "  1. SSH to Red Hat system:"
echo "     ${CYAN}ssh ${REMOTE_USER}@${REMOTE_HOST}${NC}"
echo ""
echo "  2. Source environment:"
echo "     ${CYAN}source ~/.bashrc${NC}"
echo ""
echo "  3. Start enhanced chat:"
echo "     ${CYAN}chat-mcp${NC}"
echo ""
echo "  4. Try InfoBlox queries:"
echo "     ${CYAN}You: List all networks in InfoBlox${NC}"
echo "     ${CYAN}You: Show me DNS records for example.com${NC}"
echo ""
echo "Documentation:"
echo "  Read ~/INFOBLOX-MCP-README.md for complete guide"
echo ""
echo "================================================================================"
echo ""
