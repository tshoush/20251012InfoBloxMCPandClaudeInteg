#!/usr/bin/env bash
#
# Modern Python Environment Setup for DDI Assistant
# Supports Python 3.9+ with MCP SDK
# Uses pyenv for version management
#

set -e

echo "================================================================================"
echo "Modern Python Environment Setup for DDI Assistant"
echo "================================================================================"
echo ""

# Configuration
DEFAULT_PYTHON_VERSION="3.12.7"  # Latest stable as of Oct 2024
MIN_PYTHON_VERSION="3.9"
VENV_NAME="ddi-assistant"
VENV_PATH="$HOME/.python-envs/${VENV_NAME}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
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

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    SUDO=""
else
    SUDO="sudo"
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Prompt for Python version
echo ""
print_info "Python Version Selection"
echo ""
echo "Recommended versions:"
echo "  • Python 3.12.x - Latest stable (recommended)"
echo "  • Python 3.11.x - Stable, widely tested"
echo "  • Python 3.10.x - Stable, conservative choice"
echo "  • Python 3.9.x  - Minimum for MCP SDK"
echo ""
echo "Note: Python 3.8 reached EOL in October 2024"
echo ""

read -p "Enter Python version to install [${DEFAULT_PYTHON_VERSION}]: " PYTHON_VERSION
PYTHON_VERSION=${PYTHON_VERSION:-$DEFAULT_PYTHON_VERSION}

echo ""
print_info "Selected Python version: ${PYTHON_VERSION}"
echo ""

# Step 1: Install dependencies for building Python
print_step "[1/8] Installing build dependencies..."

DEPS=(
    gcc
    make
    patch
    zlib-devel
    bzip2
    bzip2-devel
    readline-devel
    sqlite
    sqlite-devel
    openssl-devel
    tk-devel
    libffi-devel
    xz-devel
    git
)

echo "  Installing: ${DEPS[*]}"
$SUDO yum install -y "${DEPS[@]}" > /dev/null 2>&1

print_success "Build dependencies installed"
echo ""

# Step 2: Install pyenv
print_step "[2/8] Installing pyenv (Python version manager)..."

if [ -d "$HOME/.pyenv" ]; then
    print_warning "pyenv already installed"
else
    curl -s https://pyenv.run | bash
    print_success "pyenv installed"
fi

# Configure pyenv
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"

echo ""

# Step 3: Install selected Python version
print_step "[3/8] Installing Python ${PYTHON_VERSION}..."
echo "  This may take 5-10 minutes (compiling from source)..."
echo ""

if pyenv versions | grep -q "${PYTHON_VERSION}"; then
    print_warning "Python ${PYTHON_VERSION} already installed"
else
    # Use optimizations for faster Python
    env PYTHON_CONFIGURE_OPTS="--enable-optimizations --with-lto" \
        PYTHON_CFLAGS="-march=native -mtune=native" \
        pyenv install ${PYTHON_VERSION}

    print_success "Python ${PYTHON_VERSION} installed"
fi

echo ""

# Step 4: Set global Python version
print_step "[4/8] Setting global Python version..."

pyenv global ${PYTHON_VERSION}
print_success "Python ${PYTHON_VERSION} set as global"

echo ""
print_info "Python version: $(python --version)"
echo ""

# Step 5: Upgrade pip and install build tools
print_step "[5/8] Upgrading pip and installing build tools..."

python -m pip install --upgrade pip setuptools wheel > /dev/null 2>&1
print_success "pip upgraded to $(pip --version | awk '{print $2}')"

echo ""

# Step 6: Create virtual environment
print_step "[6/8] Creating virtual environment..."

mkdir -p "$HOME/.python-envs"

if [ -d "$VENV_PATH" ]; then
    print_warning "Virtual environment already exists at $VENV_PATH"
    read -p "Recreate it? (yes/no): " RECREATE
    if [ "$RECREATE" = "yes" ]; then
        rm -rf "$VENV_PATH"
        python -m venv "$VENV_PATH"
        print_success "Virtual environment recreated"
    fi
else
    python -m venv "$VENV_PATH"
    print_success "Virtual environment created at $VENV_PATH"
fi

# Activate virtual environment
source "$VENV_PATH/bin/activate"

echo ""
print_info "Virtual environment: $(which python)"
echo ""

# Step 7: Install all required packages
print_step "[7/8] Installing Python packages..."

echo "  Installing core packages..."
pip install --upgrade pip > /dev/null 2>&1

# Core packages
echo "  • anthropic (Claude AI SDK)"
pip install anthropic > /dev/null 2>&1

echo "  • mcp (Model Context Protocol SDK)"
pip install mcp > /dev/null 2>&1

echo "  • requests (HTTP client)"
pip install requests > /dev/null 2>&1

echo "  • beautifulsoup4 (Web scraping)"
pip install beautifulsoup4 > /dev/null 2>&1

echo "  • duckduckgo-search (Web search)"
pip install duckduckgo-search > /dev/null 2>&1

print_success "All packages installed"

echo ""

# Step 8: Configure environment
print_step "[8/8] Configuring environment..."

# Add pyenv configuration to bashrc
BASHRC_CONFIG="
# ============================================================================
# Modern Python Environment for DDI Assistant
# ============================================================================

# pyenv configuration
export PYENV_ROOT=\"\$HOME/.pyenv\"
export PATH=\"\$PYENV_ROOT/bin:\$PATH\"
eval \"\$(pyenv init -)\"

# DDI Assistant virtual environment
export DDI_VENV=\"$VENV_PATH\"

# Aliases for DDI Assistant with modern Python
alias ddi-activate='source \$DDI_VENV/bin/activate'
alias ddi-deactivate='deactivate'
alias ddi-python='\$DDI_VENV/bin/python'
alias ddi-pip='\$DDI_VENV/bin/pip'

# Enhanced DDI Assistant commands (automatically use modern Python)
alias chat-modern='source \$DDI_VENV/bin/activate && python ~/claude-chat.py'
alias chat-infoblox-modern='source \$DDI_VENV/bin/activate && python ~/claude-chat-infoblox.py'
alias chat-mcp='source \$DDI_VENV/bin/activate && python ~/claude-chat-mcp.py'
alias agent-modern='source \$DDI_VENV/bin/activate && python ~/claude-agent.py'
alias infoblox-mcp='source \$DDI_VENV/bin/activate && python ~/infoblox-mcp-server.py'

# Python version info
alias python-version='echo \"System: \$(python --version)\" && echo \"DDI: \$(\$DDI_VENV/bin/python --version)\"'

# Quick help
alias ddi-help='cat << EOF
DDI Assistant - Modern Python Environment

Python Version: ${PYTHON_VERSION}
Virtual Environment: ${VENV_NAME}

Commands:
  ddi-activate           - Activate DDI Python environment
  ddi-deactivate         - Deactivate environment
  python-version         - Show Python versions

  chat-modern            - DDI Assistant with web search
  chat-infoblox-modern   - DDI Assistant with InfoBlox
  chat-mcp               - DDI Assistant with MCP servers
  agent-modern           - Agent with file operations
  infoblox-mcp           - InfoBlox MCP server (standalone)

Legacy (Python 3.8):
  chat                   - Original DDI Assistant
  chat-infoblox          - Original InfoBlox integration
  agent                  - Original agent

Packages Installed:
  • anthropic (Claude SDK)
  • mcp (Model Context Protocol)
  • requests, beautifulsoup4
  • duckduckgo-search

Documentation:
  ~/PROJECT-COMPLETE.md
  ~/INFOBLOX-MCP-README.md
EOF
'
"

# Check if already configured
if grep -q "Modern Python Environment for DDI Assistant" ~/.bashrc; then
    print_warning "bashrc already configured"
    echo "  To reconfigure, remove the 'Modern Python Environment' section from ~/.bashrc"
else
    echo "$BASHRC_CONFIG" >> ~/.bashrc
    print_success "bashrc configured"
fi

echo ""

# Create version info file
cat > "$HOME/.ddi-python-version" << EOF
PYTHON_VERSION=${PYTHON_VERSION}
VENV_PATH=${VENV_PATH}
INSTALLED_DATE=$(date)
INSTALLED_BY=$(whoami)
EOF

print_success "Configuration complete"
echo ""

# Verify installation
print_step "Verifying installation..."
echo ""

# Test Python version
INSTALLED_VERSION=$("$VENV_PATH/bin/python" --version)
echo "  Python version: $INSTALLED_VERSION"

# Test packages
echo "  Testing packages:"
"$VENV_PATH/bin/python" -c "import anthropic; print('    ✓ anthropic')" 2>/dev/null || echo "    ✗ anthropic"
"$VENV_PATH/bin/python" -c "import mcp; print('    ✓ mcp')" 2>/dev/null || echo "    ✗ mcp"
"$VENV_PATH/bin/python" -c "import requests; print('    ✓ requests')" 2>/dev/null || echo "    ✗ requests"
"$VENV_PATH/bin/python" -c "import bs4; print('    ✓ beautifulsoup4')" 2>/dev/null || echo "    ✗ beautifulsoup4"
"$VENV_PATH/bin/python" -c "from duckduckgo_search import DDGS; print('    ✓ duckduckgo-search')" 2>/dev/null || echo "    ✗ duckduckgo-search"

echo ""
print_success "Installation verified"
echo ""

# Print summary
echo "================================================================================"
echo "Installation Complete!"
echo "================================================================================"
echo ""
echo -e "${GREEN}✓ Modern Python Environment Setup Successful${NC}"
echo ""
echo "Details:"
echo "  • Python Version: ${PYTHON_VERSION}"
echo "  • Virtual Environment: ${VENV_NAME}"
echo "  • Location: ${VENV_PATH}"
echo "  • Packages: anthropic, mcp, requests, beautifulsoup4, duckduckgo-search"
echo ""
echo "================================================================================"
echo "Quick Start"
echo "================================================================================"
echo ""
echo "1. Reload your shell:"
echo -e "   ${CYAN}source ~/.bashrc${NC}"
echo ""
echo "2. Check Python version:"
echo -e "   ${CYAN}python-version${NC}"
echo ""
echo "3. Start DDI Assistant with modern Python:"
echo -e "   ${CYAN}chat-modern${NC}           # DDI Assistant with web search"
echo -e "   ${CYAN}chat-infoblox-modern${NC}  # DDI Assistant with InfoBlox"
echo -e "   ${CYAN}chat-mcp${NC}              # DDI Assistant with MCP servers (full)"
echo ""
echo "4. Get help anytime:"
echo -e "   ${CYAN}ddi-help${NC}"
echo ""
echo "================================================================================"
echo "Python Version Management"
echo "================================================================================"
echo ""
echo "Switch Python versions:"
echo -e "   ${CYAN}pyenv install 3.11.9${NC}      # Install another version"
echo -e "   ${CYAN}pyenv global 3.11.9${NC}       # Switch to that version"
echo -e "   ${CYAN}./setup-python-modern.sh${NC}  # Recreate virtual environment"
echo ""
echo "List available versions:"
echo -e "   ${CYAN}pyenv install --list | grep '^  3\.'${NC}"
echo ""
echo "================================================================================"
echo "Legacy Python 3.8"
echo "================================================================================"
echo ""
echo "Your old Python 3.8 environment is still available:"
echo "  • chat              - Original DDI Assistant"
echo "  • chat-infoblox     - Original InfoBlox integration"
echo "  • agent             - Original agent"
echo ""
echo "These will continue to work, but won't have MCP support."
echo ""
echo "================================================================================"
echo ""
echo -e "${YELLOW}Note:${NC} Run ${CYAN}source ~/.bashrc${NC} to activate the new environment!"
echo ""
