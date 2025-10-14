#!/usr/bin/env python3
"""
Master Setup Script - One Command to Set Up Everything
Orchestrates complete system setup including configuration, MCP, RAG, and testing
"""

import os
import sys
import subprocess
import platform
from pathlib import Path
import argparse

class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    CYAN = '\033[36m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_WHITE = '\033[97m'
    BRIGHT_RED = '\033[91m'


def print_banner():
    """Print setup banner"""
    print()
    print(f"{Colors.BRIGHT_CYAN}{'═' * 70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BRIGHT_WHITE}    InfoBlox MCP & Claude Integration - Master Setup    {Colors.RESET}")
    print(f"{Colors.BRIGHT_CYAN}{'═' * 70}{Colors.RESET}")
    print()


def print_step(number, title, description=""):
    """Print setup step"""
    print()
    print(f"{Colors.BRIGHT_CYAN}{'─' * 70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BRIGHT_WHITE}Step {number}: {title}{Colors.RESET}")
    if description:
        print(f"{Colors.CYAN}{description}{Colors.RESET}")
    print(f"{Colors.BRIGHT_CYAN}{'─' * 70}{Colors.RESET}")
    print()


def run_command(cmd, description, check=True):
    """Run a shell command and display output"""
    print(f"{Colors.YELLOW}▶ {description}...{Colors.RESET}")
    try:
        result = subprocess.run(
            cmd,
            shell=isinstance(cmd, str),
            check=check,
            capture_output=True,
            text=True
        )
        if result.stdout:
            print(result.stdout)
        if check and result.returncode == 0:
            print(f"{Colors.BRIGHT_GREEN}✓ {description} completed{Colors.RESET}")
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"{Colors.BRIGHT_RED}✗ {description} failed{Colors.RESET}")
        if e.stderr:
            print(e.stderr)
        return False
    except Exception as e:
        print(f"{Colors.BRIGHT_RED}✗ Error: {e}{Colors.RESET}")
        return False


def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"{Colors.BRIGHT_RED}✗ Python 3.8+ required (found {version.major}.{version.minor}){Colors.RESET}")
        return False
    print(f"{Colors.BRIGHT_GREEN}✓ Python {version.major}.{version.minor}.{version.micro}{Colors.RESET}")
    return True


def interactive_configuration():
    """Run interactive configuration"""
    print_step(1, "Configuration", "Set up InfoBlox and Claude AI credentials")

    # Check if already configured
    required_vars = ['INFOBLOX_HOST', 'INFOBLOX_USER', 'INFOBLOX_PASSWORD', 'ANTHROPIC_API_KEY']
    missing = [var for var in required_vars if not os.environ.get(var)]

    if not missing:
        print(f"{Colors.BRIGHT_GREEN}✓ Configuration already present{Colors.RESET}")
        response = input(f"{Colors.YELLOW}Reconfigure? (yes/no) [{Colors.BRIGHT_WHITE}no{Colors.RESET}]: ").strip().lower()
        if response not in ['yes', 'y']:
            return True

    # Run interactive config
    try:
        from interactive_config import prompt_and_configure
        config = prompt_and_configure()
        return True
    except Exception as e:
        print(f"{Colors.BRIGHT_RED}✗ Configuration failed: {e}{Colors.RESET}")
        return False


def setup_python_venv():
    """Create Python virtual environment"""
    print_step(2, "Virtual Environment", "Create isolated Python environment")

    venv_path = Path("venv")

    if venv_path.exists():
        print(f"{Colors.BRIGHT_GREEN}✓ Virtual environment already exists{Colors.RESET}")
        return True

    return run_command(
        [sys.executable, "-m", "venv", "venv"],
        "Creating virtual environment"
    )


def install_dependencies():
    """Install Python dependencies"""
    print_step(3, "Dependencies", "Install required Python packages")

    # Determine pip path
    if platform.system() == "Windows":
        pip_path = Path("venv") / "Scripts" / "pip.exe"
    else:
        pip_path = Path("venv") / "bin" / "pip"

    if not pip_path.exists():
        pip_path = "pip3"  # Fallback to system pip

    # Install pytest and pytest-cov (always needed)
    success = run_command(
        [str(pip_path), "install", "-q", "pytest", "pytest-cov"],
        "Installing test dependencies"
    )

    if not success:
        return False

    # Install optional dependencies
    print()
    print(f"{Colors.YELLOW}Optional dependencies:{Colors.RESET}")
    print(f"  • chromadb - For RAG system (recommended)")
    print(f"  • duckduckgo-search - For web search capability")
    print(f"  • beautifulsoup4 - For web page fetching")
    print(f"  • mcp - For MCP server (macOS only)")
    print()

    response = input(f"{Colors.YELLOW}Install optional dependencies? (yes/no) [{Colors.BRIGHT_WHITE}yes{Colors.RESET}]: ").strip().lower()

    if not response or response in ['yes', 'y']:
        optional_deps = ["chromadb", "duckduckgo-search", "beautifulsoup4"]
        for dep in optional_deps:
            run_command(
                [str(pip_path), "install", "-q", dep],
                f"Installing {dep}",
                check=False  # Don't fail if optional dep fails
            )

    return True


def setup_mcp_server():
    """Setup MCP server in Claude Desktop"""
    print_step(4, "MCP Server", "Configure InfoBlox MCP server in Claude Desktop")

    # Check if macOS
    if platform.system() != "Darwin":
        print(f"{Colors.YELLOW}⚠ MCP server setup only available on macOS{Colors.RESET}")
        print(f"{Colors.CYAN}  RHEL 7.9 users: Use claude-chat-rag.py or claude-chat-infoblox.py instead{Colors.RESET}")
        return True

    # Check if Claude Desktop is installed
    claude_config = Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    if not claude_config.parent.exists():
        print(f"{Colors.YELLOW}⚠ Claude Desktop not installed{Colors.RESET}")
        print(f"{Colors.CYAN}  Download from: https://claude.ai/download{Colors.RESET}")
        return True

    response = input(f"{Colors.YELLOW}Configure MCP server in Claude Desktop? (yes/no) [{Colors.BRIGHT_WHITE}yes{Colors.RESET}]: ").strip().lower()

    if not response or response in ['yes', 'y']:
        return run_command(
            [sys.executable, "setup-mcp.py", "--yes"],
            "Configuring MCP server",
            check=False
        )

    return True


def build_rag_database():
    """Build RAG knowledge base"""
    print_step(5, "RAG Knowledge Base", "Build vector database from InfoBlox WAPI schemas")

    rag_path = Path.home() / ".infoblox-rag"

    if rag_path.exists():
        print(f"{Colors.BRIGHT_GREEN}✓ RAG database already exists{Colors.RESET}")
        response = input(f"{Colors.YELLOW}Rebuild? (yes/no) [{Colors.BRIGHT_WHITE}no{Colors.RESET}]: ").strip().lower()
        if response not in ['yes', 'y']:
            return True

    response = input(f"{Colors.YELLOW}Build RAG knowledge base? (yes/no) [{Colors.BRIGHT_WHITE}yes{Colors.RESET}]: ").strip().lower()

    if not response or response in ['yes', 'y']:
        print(f"{Colors.CYAN}This will take 2-5 minutes...{Colors.RESET}")
        return run_command(
            [sys.executable, "infoblox-rag-builder.py"],
            "Building RAG database",
            check=False
        )

    return True


def run_tests():
    """Run test suite"""
    print_step(6, "Testing", "Verify installation with test suite")

    response = input(f"{Colors.YELLOW}Run tests? (yes/no) [{Colors.BRIGHT_WHITE}yes{Colors.RESET}]: ").strip().lower()

    if not response or response in ['yes', 'y']:
        # Determine pytest path
        if platform.system() == "Windows":
            pytest_path = Path("venv") / "Scripts" / "pytest.exe"
        else:
            pytest_path = Path("venv") / "bin" / "pytest"

        if not pytest_path.exists():
            pytest_path = "pytest"  # Fallback to system pytest

        return run_command(
            [str(pytest_path), "-v", "tests/"],
            "Running test suite",
            check=False
        )

    return True


def print_summary():
    """Print setup summary and next steps"""
    print()
    print(f"{Colors.BRIGHT_CYAN}{'═' * 70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BRIGHT_GREEN}✓ Setup Complete!{Colors.RESET}")
    print(f"{Colors.BRIGHT_CYAN}{'═' * 70}{Colors.RESET}")
    print()
    print(f"{Colors.BRIGHT_WHITE}Next Steps:{Colors.RESET}")
    print()

    # Platform-specific instructions
    if platform.system() == "Darwin":
        print(f"{Colors.BRIGHT_CYAN}macOS Users:{Colors.RESET}")
        print(f"  1. {Colors.GREEN}Restart Claude Desktop{Colors.RESET} (if MCP server was configured)")
        print(f"     Look for the 🔌 icon - InfoBlox should be connected")
        print()
        print(f"  2. {Colors.GREEN}Try a chat interface:{Colors.RESET}")
        print(f"     {Colors.CYAN}python claude-chat-rag.py{Colors.RESET}      # RAG-enhanced (recommended)")
        print(f"     {Colors.CYAN}python claude-chat-mcp.py{Colors.RESET}      # MCP server integration")
        print(f"     {Colors.CYAN}python claude-chat-infoblox.py{Colors.RESET} # Direct InfoBlox")
        print()
    else:
        print(f"{Colors.BRIGHT_CYAN}RHEL 7.9 / Linux Users:{Colors.RESET}")
        print(f"  1. {Colors.GREEN}Try a chat interface:{Colors.RESET}")
        print(f"     {Colors.CYAN}python claude-chat-rag.py{Colors.RESET}      # RAG-enhanced (recommended)")
        print(f"     {Colors.CYAN}python claude-chat-infoblox.py{Colors.RESET} # Direct InfoBlox")
        print()

    print(f"  3. {Colors.GREEN}Test an API call:{Colors.RESET}")
    print(f"     {Colors.CYAN}> List all networks{Colors.RESET}")
    print(f"     You'll see the API preview before execution!")
    print()

    print(f"{Colors.BRIGHT_WHITE}Documentation:{Colors.RESET}")
    print(f"  • {Colors.CYAN}README.md{Colors.RESET} - Main documentation")
    print(f"  • {Colors.CYAN}ARCHITECTURE-FLOW.md{Colors.RESET} - How everything works together")
    print(f"  • {Colors.CYAN}API-CONFIRMATION-GUIDE.md{Colors.RESET} - API confirmation system")
    print(f"  • {Colors.CYAN}DDI-ASSISTANT-GUIDE.md{Colors.RESET} - Using the DDI Assistant")
    print()

    print(f"{Colors.BRIGHT_CYAN}{'═' * 70}{Colors.RESET}")
    print()


def main():
    """Main setup function"""
    parser = argparse.ArgumentParser(
        description="Master setup script for InfoBlox MCP & Claude Integration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full interactive setup (recommended)
  ./setup.py

  # Quick setup (skip optional steps)
  ./setup.py --quick

  # Setup without tests
  ./setup.py --no-tests

  # Setup without MCP server
  ./setup.py --no-mcp

  # Non-interactive (use defaults)
  ./setup.py --auto
        """
    )

    parser.add_argument('--quick', action='store_true',
                       help='Quick setup (skip optional components)')
    parser.add_argument('--no-tests', action='store_true',
                       help='Skip running tests')
    parser.add_argument('--no-mcp', action='store_true',
                       help='Skip MCP server setup')
    parser.add_argument('--no-rag', action='store_true',
                       help='Skip RAG database build')
    parser.add_argument('--auto', action='store_true',
                       help='Non-interactive mode (use defaults)')

    args = parser.parse_args()

    print_banner()

    # Step 0: Check Python version
    if not check_python_version():
        sys.exit(1)

    # Step 1: Interactive configuration
    if not interactive_configuration():
        print(f"\n{Colors.BRIGHT_RED}✗ Setup failed at configuration step{Colors.RESET}\n")
        sys.exit(1)

    # Step 2: Create virtual environment
    if not setup_python_venv():
        print(f"\n{Colors.BRIGHT_RED}✗ Setup failed at virtual environment step{Colors.RESET}\n")
        sys.exit(1)

    # Step 3: Install dependencies
    if not install_dependencies():
        print(f"\n{Colors.BRIGHT_RED}✗ Setup failed at dependencies step{Colors.RESET}\n")
        sys.exit(1)

    # Step 4: Setup MCP server (optional, macOS only)
    if not args.no_mcp and not args.quick:
        setup_mcp_server()

    # Step 5: Build RAG database (optional)
    if not args.no_rag and not args.quick:
        build_rag_database()

    # Step 6: Run tests (optional)
    if not args.no_tests:
        run_tests()

    # Print summary
    print_summary()

    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Setup cancelled by user{Colors.RESET}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.BRIGHT_RED}✗ Unexpected error: {e}{Colors.RESET}\n")
        sys.exit(1)
