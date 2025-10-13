#!/usr/bin/env python3
"""
Flexible Deployment Script
Deploys Phase 2 security-hardened code with configurable Python version
"""

import argparse
import configparser
import os
import subprocess
import sys
import shutil
from pathlib import Path
from datetime import datetime

class DeploymentManager:
    """Manages deployment to target systems"""

    def __init__(self, config_file="deploy-config.ini"):
        self.config_file = config_file
        self.config = self.load_config()

    def load_config(self):
        """Load configuration from file"""
        config = configparser.ConfigParser()

        # Set defaults
        config['python'] = {
            'version': '3.8.13',
            'executable': '',
            'venv_name': 'venv',
            'auto_install': 'no'
        }
        config['deployment'] = {
            'target_host': '192.168.1.200',
            'target_user': 'tshoush',
            'target_path': '~/REDHAT',
            'method': 'scp'
        }
        config['testing'] = {
            'run_tests': 'yes',
            'test_suite': 'all',
            'coverage': 'yes'
        }
        config['environment'] = {
            'env_file': '.env',
            'copy_env': 'no'
        }

        # Override with file config if exists
        if os.path.exists(self.config_file):
            config.read(self.config_file)
            print(f"✓ Loaded configuration from {self.config_file}")
        else:
            print(f"ℹ Using default configuration (no {self.config_file} found)")

        return config

    def detect_python(self, version_hint=None):
        """Detect available Python executable"""
        # If explicit executable provided
        explicit_exec = self.config.get('python', 'executable')
        if explicit_exec:
            if shutil.which(explicit_exec):
                return explicit_exec
            else:
                print(f"⚠ Warning: Configured Python '{explicit_exec}' not found")

        # If version hint provided (e.g., "3.11" or "3.8.13")
        if version_hint:
            # Try exact version
            candidates = [
                f"python{version_hint}",
                f"python{version_hint.split('.')[0]}.{version_hint.split('.')[1]}",
                f"python{version_hint.split('.')[0]}"
            ]
        else:
            # Try common Python 3 versions in order of preference
            candidates = [
                "python3.11", "python3.10", "python3.9", "python3.8",
                "python3.12", "python3", "python"
            ]

        for candidate in candidates:
            python_path = shutil.which(candidate)
            if python_path:
                # Verify it's Python 3.x
                try:
                    result = subprocess.run(
                        [python_path, "--version"],
                        capture_output=True,
                        text=True
                    )
                    version_str = result.stdout.strip()
                    if "Python 3." in version_str:
                        return python_path
                except:
                    continue

        return None

    def get_python_version(self, python_exec):
        """Get Python version string"""
        try:
            result = subprocess.run(
                [python_exec, "--version"],
                capture_output=True,
                text=True
            )
            return result.stdout.strip()
        except:
            return "Unknown"

    def create_deployment_package(self):
        """Create deployment tarball"""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        package_name = f"phase2-deployment-{timestamp}.tar.gz"

        files_to_deploy = [
            "config.py",
            "validators.py",
            "logging_config.py",
            "infoblox-mcp-server.py",
            "infoblox-rag-builder.py",
            "claude-chat-rag.py",
            "claude-chat-infoblox.py",
            "claude-chat-mcp.py",
            "infoblox-explorer.py",
            "auto-migrate-phase2.py",
            "tests/",
            "pytest.ini",
            "deploy-config.ini",
            "deploy.py"
        ]

        # Add env file if configured
        if self.config.getboolean('environment', 'copy_env'):
            env_file = self.config.get('environment', 'env_file')
            if os.path.exists(env_file):
                files_to_deploy.append(env_file)

        # Create tarball
        cmd = ["tar", "czf", package_name] + files_to_deploy
        try:
            subprocess.run(cmd, check=True, stderr=subprocess.PIPE)
            size = os.path.getsize(package_name) / 1024
            print(f"✓ Created deployment package: {package_name} ({size:.1f} KB)")
            return package_name
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to create package: {e.stderr.decode()}")
            return None

    def deploy_local(self, python_version=None):
        """Deploy locally (create venv and run tests)"""
        print("\n" + "="*80)
        print("LOCAL DEPLOYMENT")
        print("="*80)

        # Detect Python
        version_hint = python_version or self.config.get('python', 'version')
        python_exec = self.detect_python(version_hint)

        if not python_exec:
            print(f"✗ Python 3.x not found!")
            return False

        python_ver = self.get_python_version(python_exec)
        print(f"✓ Using Python: {python_exec}")
        print(f"  Version: {python_ver}")

        # Create virtual environment
        venv_name = self.config.get('python', 'venv_name')
        print(f"\n✓ Creating virtual environment: {venv_name}")

        try:
            subprocess.run(
                [python_exec, "-m", "venv", venv_name],
                check=True
            )
            print(f"✓ Virtual environment created")
        except subprocess.CalledProcessError:
            print(f"✗ Failed to create virtual environment")
            return False

        # Detect venv activation script
        if sys.platform == "win32":
            activate_script = os.path.join(venv_name, "Scripts", "activate")
        else:
            activate_script = os.path.join(venv_name, "bin", "activate")

        # Install dependencies
        pip_exec = os.path.join(venv_name, "bin", "pip") if sys.platform != "win32" else os.path.join(venv_name, "Scripts", "pip.exe")

        print("\n✓ Installing dependencies...")
        deps = ["pytest", "pytest-cov"]
        try:
            subprocess.run(
                [pip_exec, "install", "-q"] + deps,
                check=True
            )
            print(f"✓ Installed {len(deps)} dependencies")
        except subprocess.CalledProcessError:
            print("✗ Failed to install dependencies")
            return False

        # Run tests if configured
        if self.config.getboolean('testing', 'run_tests'):
            print("\n✓ Running tests...")
            return self.run_tests_local(venv_name)

        return True

    def run_tests_local(self, venv_name):
        """Run tests in local venv"""
        pytest_exec = os.path.join(venv_name, "bin", "pytest") if sys.platform != "win32" else os.path.join(venv_name, "Scripts", "pytest.exe")

        test_suite = self.config.get('testing', 'test_suite')
        coverage = self.config.getboolean('testing', 'coverage')

        # Build pytest command
        cmd = [pytest_exec, "-v"]

        if test_suite == "phase1":
            cmd.extend(["tests/test_config.py", "tests/test_validators.py"])
        elif test_suite == "phase2":
            cmd.append("tests/test_integration_phase2.py")
        elif test_suite == "integration":
            cmd.append("tests/test_integration_phase2.py")
        else:  # all
            cmd.append("tests/")

        if coverage:
            cmd.extend(["--cov=.", "--cov-report=term", "--cov-report=html"])

        try:
            result = subprocess.run(cmd, check=False)
            return result.returncode == 0
        except Exception as e:
            print(f"✗ Test execution failed: {e}")
            return False

    def show_python_options(self):
        """Show available Python versions"""
        print("\n" + "="*80)
        print("AVAILABLE PYTHON VERSIONS")
        print("="*80)

        versions_to_check = [
            ("python3", "System Python 3 (default)"),
            ("python3.8", "Python 3.8"),
            ("python3.9", "Python 3.9"),
            ("python3.10", "Python 3.10"),
            ("python3.11", "Python 3.11"),
            ("python3.12", "Python 3.12"),
        ]

        found_versions = []
        for cmd, label in versions_to_check:
            path = shutil.which(cmd)
            if path:
                version = self.get_python_version(path)
                found_versions.append((label, path, version))
                print(f"✓ {label:30s} {path:40s} {version}")
            else:
                print(f"✗ {label:30s} Not found")

        print("\n" + "="*80)
        print(f"Default configured: Python {self.config.get('python', 'version')}")

        if found_versions:
            print(f"\nTo use a specific version:")
            print(f"  ./deploy.py --python-version 3.11")
            print(f"  ./deploy.py --python-exec /usr/bin/python3.11")

        return len(found_versions)


def main():
    parser = argparse.ArgumentParser(
        description="Deploy Phase 2 security-hardened code",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Deploy locally with default Python (3.8.13)
  ./deploy.py --local

  # Deploy locally with Python 3.11
  ./deploy.py --local --python-version 3.11

  # Deploy locally with specific Python executable
  ./deploy.py --local --python-exec /opt/python3.11/bin/python3

  # Show available Python versions
  ./deploy.py --list-python

  # Run specific test suite
  ./deploy.py --local --test-suite phase2

  # Deploy without running tests
  ./deploy.py --local --no-tests
        """
    )

    # Deployment target
    parser.add_argument('--local', action='store_true',
                       help='Deploy locally (default)')
    parser.add_argument('--remote', action='store_true',
                       help='Deploy to remote host')

    # Python version selection
    parser.add_argument('--python-version', metavar='VERSION',
                       help='Python version to use (e.g., 3.11, 3.8.13)')
    parser.add_argument('--python-exec', metavar='PATH',
                       help='Full path to Python executable')
    parser.add_argument('--list-python', action='store_true',
                       help='List available Python versions and exit')

    # Testing options
    parser.add_argument('--test-suite', choices=['all', 'phase1', 'phase2', 'integration'],
                       help='Test suite to run (default: all)')
    parser.add_argument('--no-tests', action='store_true',
                       help='Skip running tests')
    parser.add_argument('--no-coverage', action='store_true',
                       help='Skip coverage report')

    # Config file
    parser.add_argument('--config', default='deploy-config.ini',
                       help='Configuration file (default: deploy-config.ini)')

    # MCP setup
    parser.add_argument('--setup-mcp', action='store_true',
                       help='Configure MCP server in Claude Desktop after deployment')

    args = parser.parse_args()

    # Create deployment manager
    deployer = DeploymentManager(config_file=args.config)

    # List Python versions
    if args.list_python:
        deployer.show_python_options()
        return 0

    # Override config with command-line arguments
    if args.python_version:
        deployer.config.set('python', 'version', args.python_version)

    if args.python_exec:
        deployer.config.set('python', 'executable', args.python_exec)

    if args.test_suite:
        deployer.config.set('testing', 'test_suite', args.test_suite)

    if args.no_tests:
        deployer.config.set('testing', 'run_tests', 'no')

    if args.no_coverage:
        deployer.config.set('testing', 'coverage', 'no')

    # Default to local deployment
    if not args.remote:
        args.local = True

    # Execute deployment
    if args.local:
        success = deployer.deploy_local(args.python_version)

        # Setup MCP if requested and deployment succeeded
        if success and args.setup_mcp:
            print("\n" + "="*80)
            print("CONFIGURING MCP SERVER")
            print("="*80)
            try:
                import subprocess
                result = subprocess.run(
                    [sys.executable, "setup-mcp.py", "--yes"],
                    cwd=str(Path(__file__).parent)
                )
                if result.returncode == 0:
                    print("\n✓ MCP server configured successfully!")
                else:
                    print("\n⚠ MCP setup had issues - you may need to run manually:")
                    print("  ./setup-mcp.py")
            except Exception as e:
                print(f"\n⚠ Could not run MCP setup: {e}")
                print("Run manually: ./setup-mcp.py")

        return 0 if success else 1
    elif args.remote:
        print("Remote deployment not yet implemented")
        print("Use: scp + ssh for now")
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
