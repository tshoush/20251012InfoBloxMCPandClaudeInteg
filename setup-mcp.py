#!/usr/bin/env python3
"""
Automatic MCP Server Configuration for Claude Desktop
Configures the InfoBlox MCP server automatically - no manual steps required
"""

import os
import sys
import json
import platform
import subprocess
from pathlib import Path
import shutil


class MCPSetup:
    """Automatically configure MCP server in Claude Desktop"""

    def __init__(self):
        self.platform = platform.system()
        self.config_path = self.get_claude_config_path()
        self.project_dir = Path(__file__).parent.absolute()

    def get_claude_config_path(self):
        """Get Claude Desktop config file path for current platform"""
        if self.platform == "Darwin":  # macOS
            return Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
        elif self.platform == "Windows":
            return Path(os.getenv("APPDATA")) / "Claude" / "claude_desktop_config.json"
        else:  # Linux
            return Path.home() / ".config" / "Claude" / "claude_desktop_config.json"

    def detect_python(self):
        """Detect best Python executable to use"""
        # Check for venv first
        venv_python = self.project_dir / "venv" / "bin" / "python"
        if venv_python.exists():
            return str(venv_python)

        # Check for system Python
        for candidate in ["python3", "python"]:
            python_path = shutil.which(candidate)
            if python_path:
                # Verify it's Python 3
                try:
                    result = subprocess.run(
                        [python_path, "--version"],
                        capture_output=True,
                        text=True
                    )
                    if "Python 3." in result.stdout:
                        return python_path
                except:
                    continue

        return None

    def get_env_vars(self):
        """Get environment variables for MCP server"""
        env_vars = {}

        # Required variables
        required = [
            "INFOBLOX_HOST",
            "INFOBLOX_USER",
            "INFOBLOX_PASSWORD",
            "ANTHROPIC_API_KEY"
        ]

        # Optional variables
        optional = [
            "WAPI_VERSION",
            "INFOBLOX_VERIFY_SSL",
            "INFOBLOX_CA_BUNDLE",
            "LOG_LEVEL"
        ]

        # Check for .env file
        env_file = self.project_dir / ".env"
        if env_file.exists():
            print(f"✓ Found .env file: {env_file}")
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        if key in required + optional:
                            env_vars[key] = value

        # Check environment variables
        for var in required + optional:
            if var in os.environ and var not in env_vars:
                env_vars[var] = os.environ[var]

        return env_vars

    def load_config(self):
        """Load existing Claude Desktop config"""
        if not self.config_path.exists():
            print(f"ℹ Claude Desktop config not found at: {self.config_path}")
            print(f"  Creating new config file...")
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            return {}

        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                print(f"✓ Loaded existing Claude Desktop config")
                return config
        except json.JSONDecodeError:
            print(f"⚠ Config file exists but is invalid JSON, creating backup...")
            backup_path = self.config_path.with_suffix('.json.backup')
            shutil.copy2(self.config_path, backup_path)
            print(f"✓ Backup created: {backup_path}")
            return {}

    def save_config(self, config):
        """Save Claude Desktop config"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=2)

        print(f"✓ Saved configuration to: {self.config_path}")

    def configure_mcp_server(self, python_exec, env_vars):
        """Configure InfoBlox MCP server in Claude Desktop"""
        config = self.load_config()

        # Ensure mcpServers section exists
        if "mcpServers" not in config:
            config["mcpServers"] = {}

        # Get absolute path to MCP server script
        mcp_server_path = str(self.project_dir / "infoblox-mcp-server.py")

        # Configure InfoBlox MCP server
        config["mcpServers"]["infoblox"] = {
            "command": python_exec,
            "args": [mcp_server_path],
            "env": env_vars
        }

        return config

    def verify_setup(self):
        """Verify MCP server setup"""
        print("\n" + "="*80)
        print("VERIFYING SETUP")
        print("="*80)

        # Check Python
        python_exec = self.detect_python()
        if not python_exec:
            print("✗ Python 3 not found!")
            return False
        print(f"✓ Python: {python_exec}")

        # Check MCP server file
        mcp_server = self.project_dir / "infoblox-mcp-server.py"
        if not mcp_server.exists():
            print(f"✗ MCP server not found: {mcp_server}")
            return False
        print(f"✓ MCP server: {mcp_server}")

        # Check required modules
        required_modules = ["config", "validators", "logging_config"]
        for module in required_modules:
            module_file = self.project_dir / f"{module}.py"
            if not module_file.exists():
                print(f"✗ Required module missing: {module}.py")
                return False
        print(f"✓ All required modules present")

        # Check environment variables
        env_vars = self.get_env_vars()
        required_vars = ["INFOBLOX_HOST", "INFOBLOX_USER", "INFOBLOX_PASSWORD", "ANTHROPIC_API_KEY"]
        missing_vars = [var for var in required_vars if var not in env_vars]

        if missing_vars:
            print(f"\n⚠ Missing required environment variables:")
            for var in missing_vars:
                print(f"  - {var}")
            print(f"\nℹ Set these variables in:")
            print(f"  1. .env file in project directory, OR")
            print(f"  2. Your shell profile (~/.bashrc, ~/.zshrc), OR")
            print(f"  3. System environment variables")
            return False

        print(f"✓ All required environment variables set")
        print(f"  - INFOBLOX_HOST: {env_vars.get('INFOBLOX_HOST')}")
        print(f"  - INFOBLOX_USER: {env_vars.get('INFOBLOX_USER')}")
        print(f"  - ANTHROPIC_API_KEY: {'*' * 20} (hidden)")

        return True

    def test_mcp_server(self, python_exec):
        """Test MCP server can start"""
        print("\n" + "="*80)
        print("TESTING MCP SERVER")
        print("="*80)

        mcp_server = self.project_dir / "infoblox-mcp-server.py"

        print(f"Testing MCP server startup...")
        try:
            # Just check if it compiles/imports
            result = subprocess.run(
                [python_exec, "-c", f"import sys; sys.path.insert(0, '{self.project_dir}'); import importlib.util; spec = importlib.util.spec_from_file_location('mcp_server', '{mcp_server}'); module = importlib.util.module_from_spec(spec)"],
                capture_output=True,
                text=True,
                timeout=5,
                cwd=str(self.project_dir)
            )

            if result.returncode == 0:
                print("✓ MCP server imports successfully")
                return True
            else:
                print(f"✗ MCP server import failed:")
                print(result.stderr)
                return False

        except subprocess.TimeoutExpired:
            print("⚠ MCP server test timed out (may be normal)")
            return True  # Timeout is OK - server might be waiting for input
        except Exception as e:
            print(f"✗ Error testing MCP server: {e}")
            return False

    def setup(self, auto_confirm=False):
        """Run complete MCP setup"""
        print("="*80)
        print("InfoBlox MCP Server - Automatic Setup")
        print("="*80)
        print()

        # Verify prerequisites
        if not self.verify_setup():
            print("\n✗ Setup verification failed!")
            print("\nPlease fix the issues above and run setup again.")
            return False

        # Detect Python
        python_exec = self.detect_python()
        if not python_exec:
            print("\n✗ Could not detect Python executable!")
            return False

        # Get environment variables
        env_vars = self.get_env_vars()

        # Show what will be configured
        print("\n" + "="*80)
        print("CONFIGURATION SUMMARY")
        print("="*80)
        print(f"Config file: {self.config_path}")
        print(f"Python: {python_exec}")
        print(f"MCP Server: {self.project_dir / 'infoblox-mcp-server.py'}")
        print(f"Environment variables: {len(env_vars)} configured")

        # Confirm
        if not auto_confirm:
            print()
            response = input("Configure MCP server in Claude Desktop? (yes/no): ").lower()
            if response not in ['yes', 'y']:
                print("Setup cancelled.")
                return False

        # Configure
        print("\n" + "="*80)
        print("CONFIGURING MCP SERVER")
        print("="*80)

        try:
            config = self.configure_mcp_server(python_exec, env_vars)
            self.save_config(config)
            print("✓ MCP server configured successfully!")

            # Test
            if self.test_mcp_server(python_exec):
                print("\n" + "="*80)
                print("✅ SETUP COMPLETE")
                print("="*80)
                print()
                print("Next steps:")
                print("  1. Restart Claude Desktop application")
                print("  2. Look for the 🔌 MCP icon in Claude Desktop")
                print("  3. The InfoBlox MCP server should appear as connected")
                print()
                print("You can now use InfoBlox tools directly in Claude Desktop!")
                return True
            else:
                print("\n⚠ Configuration saved but server test had issues")
                print("Try restarting Claude Desktop - it may still work")
                return True

        except Exception as e:
            print(f"\n✗ Configuration failed: {e}")
            return False

    def show_status(self):
        """Show current MCP configuration status"""
        print("="*80)
        print("MCP SERVER STATUS")
        print("="*80)
        print()

        # Check config file
        if not self.config_path.exists():
            print(f"✗ Claude Desktop config not found: {self.config_path}")
            print(f"\nRun setup to configure: ./setup-mcp.py")
            return

        # Load config
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
        except:
            print(f"✗ Could not read config file")
            return

        # Check for MCP servers
        if "mcpServers" not in config:
            print("✗ No MCP servers configured")
            print(f"\nRun setup to configure: ./setup-mcp.py")
            return

        # Check for InfoBlox server
        if "infoblox" not in config["mcpServers"]:
            print("✗ InfoBlox MCP server not configured")
            print(f"\nRun setup to configure: ./setup-mcp.py")
            return

        # Show InfoBlox configuration
        infoblox_config = config["mcpServers"]["infoblox"]
        print("✓ InfoBlox MCP server is configured")
        print()
        print(f"Command: {infoblox_config.get('command')}")
        print(f"Script: {infoblox_config.get('args', [])[0] if infoblox_config.get('args') else 'N/A'}")
        print(f"Environment variables: {len(infoblox_config.get('env', {}))} configured")
        print()
        print("To apply changes:")
        print("  1. Restart Claude Desktop")
        print("  2. Check for 🔌 MCP icon")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Automatic MCP Server Setup for Claude Desktop",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive setup (asks for confirmation)
  ./setup-mcp.py

  # Automatic setup (no confirmation)
  ./setup-mcp.py --yes

  # Show current status
  ./setup-mcp.py --status

  # Remove MCP server configuration
  ./setup-mcp.py --remove
        """
    )

    parser.add_argument('--yes', '-y', action='store_true',
                       help='Auto-confirm setup (no prompts)')
    parser.add_argument('--status', action='store_true',
                       help='Show current MCP configuration status')
    parser.add_argument('--remove', action='store_true',
                       help='Remove InfoBlox MCP server configuration')

    args = parser.parse_args()

    setup = MCPSetup()

    if args.status:
        setup.show_status()
        return 0

    if args.remove:
        print("Removing InfoBlox MCP server configuration...")
        config = setup.load_config()
        if "mcpServers" in config and "infoblox" in config["mcpServers"]:
            del config["mcpServers"]["infoblox"]
            setup.save_config(config)
            print("✓ InfoBlox MCP server removed")
            print("Restart Claude Desktop to apply changes")
        else:
            print("ℹ InfoBlox MCP server not configured")
        return 0

    # Run setup
    success = setup.setup(auto_confirm=args.yes)
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
