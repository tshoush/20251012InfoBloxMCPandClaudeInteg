#!/bin/bash
#
# InfoBlox MCP System - New User Setup Script
# Creates a new user with complete environment setup
#

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Check if running as root/sudo
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Error: This script must be run as root or with sudo${NC}"
    echo "Usage: sudo ./setup-new-user.sh [username]"
    exit 1
fi

# Get username
USERNAME=$1
if [ -z "$USERNAME" ]; then
    echo -e "${YELLOW}Enter username to create:${NC}"
    read -r USERNAME
fi

if [ -z "$USERNAME" ]; then
    echo -e "${RED}Error: Username cannot be empty${NC}"
    exit 1
fi

echo -e "${CYAN}======================================================================${NC}"
echo -e "${BOLD}${CYAN}  InfoBlox MCP System - New User Setup${NC}"
echo -e "${CYAN}======================================================================${NC}"
echo ""
echo -e "Creating user: ${BOLD}${USERNAME}${NC}"
echo ""

# Check if user already exists
if id "$USERNAME" &>/dev/null; then
    echo -e "${YELLOW}⚠ User $USERNAME already exists${NC}"
    echo -e "${YELLOW}Do you want to continue with environment setup? (yes/no)${NC}"
    read -r CONTINUE
    if [ "$CONTINUE" != "yes" ]; then
        echo "Exiting..."
        exit 0
    fi
    USER_EXISTS=true
else
    USER_EXISTS=false
fi

# Step 1: Create user
if [ "$USER_EXISTS" = false ]; then
    echo -e "${YELLOW}Step 1: Creating user $USERNAME...${NC}"
    useradd -m -s /bin/bash "$USERNAME"

    echo -e "${YELLOW}Set password for $USERNAME:${NC}"
    passwd "$USERNAME"

    echo -e "${GREEN}✓ User $USERNAME created${NC}"
else
    echo -e "${GREEN}✓ User $USERNAME exists${NC}"
fi
echo ""

# Get user's home directory
USER_HOME=$(eval echo ~"$USERNAME")

# Step 2: Clone repository
echo -e "${YELLOW}Step 2: Setting up repository...${NC}"
if [ -d "$USER_HOME/REDHAT" ]; then
    echo -e "${YELLOW}⚠ REDHAT directory already exists${NC}"
    echo -e "${YELLOW}Rename existing and clone fresh? (yes/no)${NC}"
    read -r CLONE_FRESH
    if [ "$CLONE_FRESH" = "yes" ]; then
        sudo -u "$USERNAME" mv "$USER_HOME/REDHAT" "$USER_HOME/REDHAT.backup.$(date +%Y%m%d-%H%M%S)"
        echo "Existing directory backed up"
    fi
fi

if [ ! -d "$USER_HOME/REDHAT/.git" ]; then
    echo "Cloning repository..."
    sudo -u "$USERNAME" git clone https://github.com/tshoush/20251012InfoBloxMCPandClaudeInteg.git "$USER_HOME/REDHAT"
    echo -e "${GREEN}✓ Repository cloned to $USER_HOME/REDHAT${NC}"
else
    echo -e "${GREEN}✓ Repository already present${NC}"
fi
echo ""

# Step 3: Create Python virtual environment
echo -e "${YELLOW}Step 3: Creating Python virtual environment...${NC}"
if [ -d "$USER_HOME/REDHAT/venv" ]; then
    echo -e "${YELLOW}⚠ Virtual environment already exists${NC}"
    echo -e "${YELLOW}Recreate? (yes/no)${NC}"
    read -r RECREATE_VENV
    if [ "$RECREATE_VENV" = "yes" ]; then
        sudo -u "$USERNAME" rm -rf "$USER_HOME/REDHAT/venv"
    fi
fi

if [ ! -d "$USER_HOME/REDHAT/venv" ]; then
    sudo -u "$USERNAME" bash << EOF
cd "$USER_HOME/REDHAT"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
EOF
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment exists${NC}"
fi
echo ""

# Step 4: Install Python dependencies
echo -e "${YELLOW}Step 4: Installing Python dependencies...${NC}"
sudo -u "$USERNAME" bash << 'EOF'
cd ~/REDHAT
source venv/bin/activate
pip install --quiet requests anthropic mcp tenacity ratelimit chromadb duckduckgo-search beautifulsoup4 pytest pytest-cov
EOF
echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# Step 5: Create helpful aliases
echo -e "${YELLOW}Step 5: Creating helpful aliases...${NC}"
sudo -u "$USERNAME" bash << 'EOF'
# Add to .bashrc
if ! grep -q "InfoBlox MCP Aliases" ~/.bashrc; then
    cat >> ~/.bashrc << 'ALIASES'

# InfoBlox MCP Aliases
alias infoblox='cd ~/REDHAT && source venv/bin/activate'
alias chat-rag='cd ~/REDHAT && source venv/bin/activate && python claude-chat-rag.py'
alias chat-mcp='cd ~/REDHAT && source venv/bin/activate && python claude-chat-mcp.py'
alias chat-infoblox='cd ~/REDHAT && source venv/bin/activate && python claude-chat-infoblox.py'
alias find-network='cd ~/REDHAT && source venv/bin/activate && python network_info.py'
alias find-ip='cd ~/REDHAT && source venv/bin/activate && python ip_info.py'
alias find-zone='cd ~/REDHAT && source venv/bin/activate && python zone_info.py'
ALIASES
fi
EOF
echo -e "${GREEN}✓ Aliases added to .bashrc${NC}"
echo ""

# Step 6: Set proper permissions
echo -e "${YELLOW}Step 6: Setting permissions...${NC}"
chown -R "$USERNAME:$USERNAME" "$USER_HOME/REDHAT"
chmod +x "$USER_HOME/REDHAT"/*.sh 2>/dev/null || true
echo -e "${GREEN}✓ Permissions set${NC}"
echo ""

# Step 7: Create welcome message
echo -e "${YELLOW}Step 7: Creating welcome message...${NC}"
sudo -u "$USERNAME" bash << 'EOF'
cat > ~/REDHAT/WELCOME.txt << 'WELCOME'
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║          InfoBlox MCP & Claude Integration - Welcome!                ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝

Quick Start:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Activate environment:
   cd ~/REDHAT && source venv/bin/activate

   Or use alias:
   infoblox

2. Run interactive configuration (first time only):
   python claude-chat-rag.py
   (Will prompt for InfoBlox and Claude credentials)

3. Try the chat interfaces:
   chat-rag        # RAG-enhanced with InfoBlox knowledge
   chat-mcp        # MCP server (143 tools)
   chat-infoblox   # Direct InfoBlox integration

4. Or use the tools directly:
   find-network 192.168.1.0/24
   find-ip 192.168.1.50
   find-zone corp.local

Example Queries:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

• "Find network 192.168.1.0/24"
• "Find IP 192.168.1.50"
• "Find zone corp.local"
• "List all networks"
• "Show me DHCP leases for network 192.168.1.0/24"

Documentation:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

• README.md - Main documentation
• USE-CASES.md - Operations use cases
• ARCHITECTURE-FLOW.md - How it all works
• demo.html - Interactive presentation (open in browser)

Need Help?
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Run: ./fix-and-test.sh
This will verify your setup and run diagnostics.

WELCOME
EOF
echo -e "${GREEN}✓ Welcome message created${NC}"
echo ""

# Final Summary
echo -e "${CYAN}======================================================================${NC}"
echo -e "${BOLD}${GREEN}✓ Setup Complete!${NC}"
echo -e "${CYAN}======================================================================${NC}"
echo ""
echo -e "${BOLD}User Information:${NC}"
echo "  Username: $USERNAME"
echo "  Home: $USER_HOME"
echo "  Project: $USER_HOME/REDHAT"
echo ""
echo -e "${BOLD}Installed Components:${NC}"
echo "  ✓ Git repository cloned"
echo "  ✓ Python virtual environment (venv)"
echo "  ✓ All dependencies installed"
echo "  ✓ Helpful aliases configured"
echo ""
echo -e "${BOLD}Available Aliases:${NC}"
echo "  infoblox        - Activate environment"
echo "  chat-rag        - Start RAG-enhanced chat"
echo "  chat-mcp        - Start MCP chat (143 tools)"
echo "  chat-infoblox   - Start InfoBlox chat"
echo "  find-network    - Find network details"
echo "  find-ip         - Find IP details"
echo "  find-zone       - Find DNS zone details"
echo ""
echo -e "${BOLD}Next Steps:${NC}"
echo ""
echo "  1. Switch to the new user:"
echo "     ${CYAN}su - $USERNAME${NC}"
echo ""
echo "  2. View welcome message:"
echo "     ${CYAN}cat ~/REDHAT/WELCOME.txt${NC}"
echo ""
echo "  3. Activate environment:"
echo "     ${CYAN}infoblox${NC}"
echo "     or"
echo "     ${CYAN}cd ~/REDHAT && source venv/bin/activate${NC}"
echo ""
echo "  4. Configure credentials (first time):"
echo "     ${CYAN}chat-rag${NC}"
echo "     (Will prompt for InfoBlox and Claude API credentials)"
echo ""
echo "  5. Start using the system:"
echo "     ${CYAN}Try: 'Find network 192.168.1.0/24'${NC}"
echo ""
echo -e "${CYAN}======================================================================${NC}"
echo ""
echo -e "${GREEN}User $USERNAME is ready to use the InfoBlox MCP system!${NC}"
echo ""
