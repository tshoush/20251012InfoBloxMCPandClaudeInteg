#!/usr/bin/env bash
#
# Python Version Manager for DDI Assistant
# Easy switching between Python environments
#

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo ""
    echo -e "${CYAN}================================================================================${NC}"
    echo -e "${CYAN}    DDI Assistant - Python Version Manager${NC}"
    echo -e "${CYAN}================================================================================${NC}"
    echo ""
}

print_current_environment() {
    echo -e "${BLUE}Current Environment:${NC}"
    echo ""

    if [ -n "$VIRTUAL_ENV" ]; then
        echo -e "  ${GREEN}✓ Virtual Environment Active${NC}"
        echo "    Path: $VIRTUAL_ENV"
        echo "    Python: $(python --version)"
    else
        echo -e "  ${YELLOW}○ No Virtual Environment Active${NC}"
        echo "    System Python: $(python --version 2>/dev/null || echo 'Not found')"
    fi

    echo ""

    if command -v pyenv >/dev/null 2>&1; then
        echo -e "${BLUE}Pyenv Status:${NC}"
        echo "    Installed: Yes"
        echo "    Global: $(pyenv global 2>/dev/null || echo 'Not set')"
        echo "    Available versions:"
        pyenv versions 2>/dev/null | sed 's/^/      /'
    else
        echo -e "${BLUE}Pyenv Status:${NC} Not installed"
    fi

    echo ""
}

list_environments() {
    echo -e "${BLUE}Available Environments:${NC}"
    echo ""

    # Python 3.8 (Software Collections)
    if [ -f "/opt/rh/rh-python38/enable" ]; then
        echo -e "  ${GREEN}1.${NC} Python 3.8 (Software Collections)"
        echo "     Location: /opt/rh/rh-python38/"
        echo "     Status: Legacy, EOL October 2024"
        echo "     Features: Basic DDI Assistant, InfoBlox (no MCP)"
        echo ""
    fi

    # Modern Python environments
    if [ -d "$HOME/.python-envs/ddi-assistant" ]; then
        local version=$("$HOME/.python-envs/ddi-assistant/bin/python" --version 2>/dev/null)
        echo -e "  ${GREEN}2.${NC} Modern Python ($version)"
        echo "     Location: ~/.python-envs/ddi-assistant/"
        echo "     Status: Active, Recommended"
        echo "     Features: Full MCP support, Latest packages"
        echo ""
    fi

    # Check for other virtual environments
    if [ -d "$HOME/.python-envs" ]; then
        local count=$(find "$HOME/.python-envs" -maxdepth 1 -type d ! -name "ddi-assistant" ! -name ".python-envs" | wc -l)
        if [ "$count" -gt 0 ]; then
            echo -e "  ${BLUE}Additional Environments:${NC}"
            find "$HOME/.python-envs" -maxdepth 1 -type d ! -name "ddi-assistant" ! -name ".python-envs" -exec basename {} \; | while read env; do
                echo "     • $env"
            done
            echo ""
        fi
    fi
}

switch_environment() {
    local choice=$1

    case $choice in
        1|legacy|3.8)
            echo -e "${CYAN}Switching to Python 3.8 (Software Collections)...${NC}"
            if [ -f "/opt/rh/rh-python38/enable" ]; then
                source /opt/rh/rh-python38/enable
                echo -e "${GREEN}✓ Switched to Python 3.8${NC}"
                echo "  Use: chat, chat-infoblox, agent"
            else
                echo -e "${RED}✗ Python 3.8 not installed${NC}"
                return 1
            fi
            ;;
        2|modern|mcp)
            echo -e "${CYAN}Switching to Modern Python...${NC}"
            if [ -d "$HOME/.python-envs/ddi-assistant" ]; then
                source "$HOME/.python-envs/ddi-assistant/bin/activate"
                echo -e "${GREEN}✓ Switched to Modern Python${NC}"
                echo "  Python: $(python --version)"
                echo "  Use: chat-modern, chat-infoblox-modern, chat-mcp"
            else
                echo -e "${RED}✗ Modern Python environment not found${NC}"
                echo "  Run: ./setup-python-modern.sh"
                return 1
            fi
            ;;
        *)
            echo -e "${RED}Invalid choice${NC}"
            return 1
            ;;
    esac
}

install_new_version() {
    echo ""
    echo -e "${CYAN}Install New Python Version${NC}"
    echo ""

    if ! command -v pyenv >/dev/null 2>&1; then
        echo -e "${RED}✗ pyenv not installed${NC}"
        echo "  Run: ./setup-python-modern.sh"
        return 1
    fi

    echo "Available Python versions:"
    echo ""
    pyenv install --list | grep "^  3\." | tail -20
    echo ""

    read -p "Enter version to install (e.g., 3.12.7): " version

    if [ -z "$version" ]; then
        echo -e "${RED}No version specified${NC}"
        return 1
    fi

    echo ""
    echo -e "${CYAN}Installing Python ${version}...${NC}"
    echo "This may take 5-10 minutes..."
    echo ""

    env PYTHON_CONFIGURE_OPTS="--enable-optimizations --with-lto" \
        PYTHON_CFLAGS="-march=native -mtune=native" \
        pyenv install ${version}

    if [ $? -eq 0 ]; then
        echo ""
        echo -e "${GREEN}✓ Python ${version} installed${NC}"
        echo ""
        read -p "Set as global version? (yes/no): " setglobal

        if [ "$setglobal" = "yes" ]; then
            pyenv global ${version}
            echo -e "${GREEN}✓ Set as global version${NC}"
        fi

        echo ""
        read -p "Recreate DDI Assistant virtual environment with this version? (yes/no): " recreate

        if [ "$recreate" = "yes" ]; then
            echo ""
            echo -e "${CYAN}Recreating virtual environment...${NC}"
            rm -rf "$HOME/.python-envs/ddi-assistant"
            "$HOME/.pyenv/versions/${version}/bin/python" -m venv "$HOME/.python-envs/ddi-assistant"

            source "$HOME/.python-envs/ddi-assistant/bin/activate"

            echo "Installing packages..."
            pip install --upgrade pip > /dev/null 2>&1
            pip install anthropic mcp requests beautifulsoup4 duckduckgo-search > /dev/null 2>&1

            echo -e "${GREEN}✓ Virtual environment recreated${NC}"
            echo "  Python: $(python --version)"
        fi
    else
        echo -e "${RED}✗ Installation failed${NC}"
        return 1
    fi
}

show_help() {
    echo ""
    echo -e "${CYAN}Python Version Manager - Help${NC}"
    echo ""
    echo "Commands:"
    echo "  status       - Show current environment"
    echo "  list         - List available environments"
    echo "  switch N     - Switch to environment N (1=legacy, 2=modern)"
    echo "  install      - Install new Python version"
    echo "  help         - Show this help"
    echo ""
    echo "Quick switches:"
    echo "  switch legacy    - Use Python 3.8"
    echo "  switch modern    - Use Modern Python with MCP"
    echo ""
    echo "Examples:"
    echo "  python-manager switch 2       # Switch to modern Python"
    echo "  python-manager install        # Install new version"
    echo "  python-manager status         # Check current setup"
    echo ""
}

# Main menu
main() {
    local command=$1
    local arg=$2

    print_header

    case $command in
        status|"")
            print_current_environment
            ;;
        list)
            list_environments
            ;;
        switch)
            if [ -z "$arg" ]; then
                list_environments
                echo -e "${CYAN}Select environment:${NC}"
                read -p "Enter choice (1-2): " arg
            fi
            switch_environment "$arg"
            ;;
        install)
            install_new_version
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            echo -e "${RED}Unknown command: $command${NC}"
            show_help
            return 1
            ;;
    esac

    echo ""
}

# Run main function
main "$@"
