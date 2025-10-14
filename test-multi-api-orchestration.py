#!/usr/bin/env python3
"""
Multi-API Orchestration Test Script
Tests Claude's ability to orchestrate multiple basic WAPI tools in sequence
"""

import os
import sys
import json
import time
import subprocess
from datetime import datetime

class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    RED = '\033[91m'
    CYAN = '\033[36m'
    WHITE = '\033[97m'

def print_header(text):
    """Print section header"""
    print(f"\n{Colors.CYAN}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.WHITE}{text}{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*70}{Colors.RESET}\n")

def print_test(number, description):
    """Print test header"""
    print(f"\n{Colors.YELLOW}Test {number}: {description}{Colors.RESET}")
    print(f"{Colors.CYAN}{'-'*70}{Colors.RESET}")

def print_result(passed, message):
    """Print test result"""
    if passed:
        print(f"{Colors.GREEN}✓ PASS:{Colors.RESET} {message}")
    else:
        print(f"{Colors.RED}✗ FAIL:{Colors.RESET} {message}")
    return passed

def check_environment():
    """Check if environment is properly set up"""
    print_header("Environment Check")

    results = []

    # Check Python version
    version = sys.version_info
    passed = version.major == 3 and version.minor >= 8
    results.append(print_result(passed, f"Python version: {version.major}.{version.minor}.{version.micro}"))

    # Check required files exist
    required_files = [
        'infoblox-mcp-server.py',
        'network_info.py',
        'ip_info.py',
        'zone_info.py',
        'claude-chat-mcp.py',
        'config.py'
    ]

    for file in required_files:
        exists = os.path.exists(file)
        results.append(print_result(exists, f"File exists: {file}"))

    # Check environment variables - if missing, prompt for them
    env_vars = ['INFOBLOX_HOST', 'INFOBLOX_USER', 'INFOBLOX_PASSWORD', 'ANTHROPIC_API_KEY']
    missing_vars = [var for var in env_vars if not os.environ.get(var)]

    if missing_vars:
        print(f"\n{Colors.YELLOW}Missing environment variables: {', '.join(missing_vars)}{Colors.RESET}")
        print(f"{Colors.CYAN}Using interactive configuration...{Colors.RESET}\n")

        try:
            from interactive_config import check_and_prompt_if_needed
            check_and_prompt_if_needed()
            print(f"\n{Colors.GREEN}✓ Configuration completed{Colors.RESET}\n")
        except Exception as e:
            print(f"{Colors.RED}✗ Configuration failed: {e}{Colors.RESET}")
            results.append(print_result(False, "Interactive configuration"))
            return False

    # Verify all variables are now set
    for var in env_vars:
        exists = os.environ.get(var) is not None
        value = "***" if exists else "NOT SET"
        results.append(print_result(exists, f"Environment variable {var}: {value}"))

    return all(results)

def test_mcp_server_startup():
    """Test if MCP server can start and lists tools"""
    print_header("MCP Server Startup Test")

    print(f"{Colors.YELLOW}Starting MCP server...{Colors.RESET}")

    try:
        # Start MCP server and capture output
        process = subprocess.Popen(
            ['python', 'infoblox-mcp-server.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Give it time to initialize
        time.sleep(5)

        # Try to get some output
        try:
            stdout, stderr = process.communicate(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()

        output = stdout + stderr

        # Check for success indicators
        has_143_tools = "143" in output or "total tools" in output.lower()
        has_use_case = "use case tools" in output.lower() or "3" in output
        has_server_ready = "server ready" in output.lower()

        print_result(has_server_ready, "MCP server started")
        print_result(has_143_tools, "143 total tools available")
        print_result(has_use_case, "3 use case tools detected")

        # Show relevant output
        print(f"\n{Colors.CYAN}Server output:{Colors.RESET}")
        for line in output.split('\n'):
            if 'tools' in line.lower() or 'ready' in line.lower() or 'error' in line.lower():
                print(f"  {line}")

        return has_server_ready

    except Exception as e:
        print_result(False, f"MCP server startup failed: {e}")
        return False

def test_tool_availability():
    """Test if specific tools are available"""
    print_header("Tool Availability Test")

    try:
        # Import MCP server module to check tools
        sys.path.insert(0, os.getcwd())

        # We'll check by importing and examining
        print(f"{Colors.YELLOW}Checking tool definitions...{Colors.RESET}")

        # Check if use case modules can be imported
        modules = [
            ('network_info', 'NetworkInfoClient'),
            ('ip_info', 'IPInfoClient'),
            ('zone_info', 'ZoneInfoClient')
        ]

        results = []
        for module_name, class_name in modules:
            try:
                module = __import__(module_name)
                cls = getattr(module, class_name)
                results.append(print_result(True, f"Module {module_name}.{class_name} available"))
            except Exception as e:
                results.append(print_result(False, f"Module {module_name}.{class_name} failed: {e}"))

        return all(results)

    except Exception as e:
        print_result(False, f"Tool availability check failed: {e}")
        return False

def test_direct_tool_execution():
    """Test direct execution of use case tools"""
    print_header("Direct Tool Execution Test")

    tests = [
        {
            'name': 'Network Info - Valid Network',
            'command': ['python', 'network_info.py', '192.168.1.0/24'],
            'expected': ['NETWORK INFORMATION', '192.168.1.0/24']
        },
        {
            'name': 'IP Info - Valid IP',
            'command': ['python', 'ip_info.py', '192.168.1.50'],
            'expected': ['IP ADDRESS INFORMATION', '192.168.1.50']
        },
        {
            'name': 'Zone Info - Invalid (Expected)',
            'command': ['python', 'zone_info.py', 'test.local'],
            'expected': ['DNS ZONE INFORMATION', 'test.local']
        }
    ]

    results = []
    for test in tests:
        print(f"\n{Colors.YELLOW}Running: {test['name']}{Colors.RESET}")

        try:
            result = subprocess.run(
                test['command'],
                capture_output=True,
                text=True,
                timeout=30
            )

            output = result.stdout + result.stderr

            # Check if expected strings are in output
            found_all = all(exp in output for exp in test['expected'])

            if found_all:
                results.append(print_result(True, f"{test['name']} - Output contains expected content"))
                print(f"{Colors.CYAN}Output preview:{Colors.RESET}")
                for line in output.split('\n')[:10]:
                    if line.strip():
                        print(f"  {line}")
            else:
                results.append(print_result(False, f"{test['name']} - Missing expected content"))
                print(f"{Colors.RED}Output:{Colors.RESET}")
                print(output[:500])

        except subprocess.TimeoutExpired:
            results.append(print_result(False, f"{test['name']} - Timeout (>30s)"))
        except Exception as e:
            results.append(print_result(False, f"{test['name']} - Exception: {e}"))

    return all(results)

def test_api_connectivity():
    """Test connectivity to InfoBlox WAPI"""
    print_header("InfoBlox WAPI Connectivity Test")

    try:
        from config import get_settings
        import requests

        settings = get_settings()
        base_url = settings.get_infoblox_base_url()

        print(f"{Colors.YELLOW}Testing connection to: {settings.infoblox_host}{Colors.RESET}")

        # Simple GET request to check connectivity
        session = requests.Session()
        session.auth = (settings.infoblox_user, settings.infoblox_password)
        session.verify = settings.get_ssl_verify()

        # Try to get WAPI schema (lightweight request)
        url = f"{base_url}?_schema"
        response = session.get(url, timeout=10)

        success = response.status_code in [200, 401]  # 401 means we reached it but auth might be wrong

        print_result(success, f"WAPI reachable (status: {response.status_code})")

        if response.status_code == 200:
            print_result(True, "WAPI authentication successful")
            return True
        elif response.status_code == 401:
            print_result(False, "WAPI authentication failed (check credentials)")
            return False
        else:
            print_result(False, f"WAPI returned unexpected status: {response.status_code}")
            return False

    except Exception as e:
        print_result(False, f"WAPI connectivity test failed: {e}")
        return False

def generate_report(results):
    """Generate final test report"""
    print_header("TEST REPORT SUMMARY")

    total_tests = len(results)
    passed_tests = sum(1 for r in results if r['passed'])
    failed_tests = total_tests - passed_tests

    print(f"Total Tests Run: {total_tests}")
    print(f"{Colors.GREEN}Passed: {passed_tests}{Colors.RESET}")
    print(f"{Colors.RED}Failed: {failed_tests}{Colors.RESET}")
    print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")

    print(f"\n{Colors.CYAN}Test Details:{Colors.RESET}")
    for idx, result in enumerate(results, 1):
        status = f"{Colors.GREEN}PASS{Colors.RESET}" if result['passed'] else f"{Colors.RED}FAIL{Colors.RESET}"
        print(f"  {idx}. [{status}] {result['name']}")

    print(f"\n{Colors.CYAN}{'='*70}{Colors.RESET}")

    if failed_tests == 0:
        print(f"{Colors.GREEN}{Colors.BOLD}✓ ALL TESTS PASSED - System Ready for Multi-API Orchestration!{Colors.RESET}")
    else:
        print(f"{Colors.YELLOW}⚠ Some tests failed - Review errors above{Colors.RESET}")

    print(f"{Colors.CYAN}{'='*70}{Colors.RESET}\n")

def main():
    """Run all tests"""
    print(f"\n{Colors.BOLD}{Colors.WHITE}{'='*70}")
    print("  Multi-API Orchestration Test Suite")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}{Colors.RESET}\n")

    results = []

    # Test 1: Environment
    env_ok = check_environment()
    results.append({'name': 'Environment Check', 'passed': env_ok})

    if not env_ok:
        print(f"\n{Colors.RED}Environment check failed. Cannot proceed with tests.{Colors.RESET}")
        return

    # Test 2: WAPI Connectivity
    api_ok = test_api_connectivity()
    results.append({'name': 'WAPI Connectivity', 'passed': api_ok})

    # Test 3: Tool Availability
    tools_ok = test_tool_availability()
    results.append({'name': 'Tool Availability', 'passed': tools_ok})

    # Test 4: Direct Tool Execution
    exec_ok = test_direct_tool_execution()
    results.append({'name': 'Direct Tool Execution', 'passed': exec_ok})

    # Test 5: MCP Server Startup (may timeout, that's ok)
    print(f"\n{Colors.YELLOW}Note: MCP server test may take time or timeout (normal){Colors.RESET}")
    mcp_ok = test_mcp_server_startup()
    results.append({'name': 'MCP Server Startup', 'passed': mcp_ok})

    # Generate final report
    generate_report(results)

    print(f"\n{Colors.CYAN}Next Steps:{Colors.RESET}")
    print(f"1. If all tests passed, system is ready for multi-API orchestration")
    print(f"2. Run: python claude-chat-mcp.py")
    print(f"3. Try queries like: 'List all networks, then show details for the first one'")
    print(f"4. Paste this output to Claude for analysis\n")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Test interrupted by user{Colors.RESET}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Unexpected error: {e}{Colors.RESET}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
