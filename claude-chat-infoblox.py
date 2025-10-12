#!/usr/bin/env python
"""Interactive chat interface for Claude AI with InfoBlox WAPI integration"""

import os
import sys
import anthropic
import textwrap
import json
from datetime import datetime
import subprocess
import glob
import requests
from urllib3.exceptions import InsecureRequestWarning

# Suppress SSL warnings
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

try:
    from duckduckgo_search import DDGS
    from bs4 import BeautifulSoup
    WEB_SEARCH_AVAILABLE = True
except ImportError:
    WEB_SEARCH_AVAILABLE = False

# InfoBlox Configuration
INFOBLOX_HOST = os.getenv("INFOBLOX_HOST", "192.168.1.224")
INFOBLOX_USER = os.getenv("INFOBLOX_USER", "admin")
INFOBLOX_PASSWORD = os.getenv("INFOBLOX_PASSWORD", "infoblox")
WAPI_VERSION = os.getenv("WAPI_VERSION", "v2.13.1")
BASE_URL = f"https://{INFOBLOX_HOST}/wapi/{WAPI_VERSION}"

# ANSI color codes (same as before)
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'


class InfoBloxClient:
    """Client for InfoBlox WAPI"""

    def __init__(self):
        self.session = requests.Session()
        self.session.auth = (INFOBLOX_USER, INFOBLOX_PASSWORD)
        self.session.verify = False
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })

    def wapi_request(self, method: str, path: str, **kwargs):
        """Make WAPI request"""
        url = f"{BASE_URL}/{path.lstrip('/')}"
        try:
            response = self.session.request(method, url, timeout=30, **kwargs)
            if response.status_code >= 400:
                return {"error": f"HTTP {response.status_code}", "details": response.text}

            if not response.text or response.text.strip() == "":
                return {"success": True, "message": "Operation completed successfully"}

            return response.json()
        except Exception as e:
            return {"error": str(e)}


# Global InfoBlox client
infoblox_client = InfoBloxClient()


def print_header():
    """Print styled header"""
    width = 80
    print()
    print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}{'═' * width}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BRIGHT_WHITE}{'🤖 Claude Sonnet 4.5 - DDI Assistant with InfoBlox':^{width}}{Colors.RESET}")
    print(f"{Colors.BRIGHT_BLUE}{'AI Chat with Web Search, System Access & InfoBlox WAPI':^{width}}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}{'═' * width}{Colors.RESET}")
    print()
    print(f"{Colors.BRIGHT_GREEN}  Capabilities:{Colors.RESET}")
    print(f"{Colors.BRIGHT_YELLOW}    🌐{Colors.RESET} Web search and browsing")
    print(f"{Colors.BRIGHT_YELLOW}    📁{Colors.RESET} File system access")
    print(f"{Colors.BRIGHT_YELLOW}    💻{Colors.RESET} System commands")
    print(f"{Colors.BRIGHT_YELLOW}    📅{Colors.RESET} Current date and time")
    print(f"{Colors.BRIGHT_YELLOW}    🔷{Colors.RESET} InfoBlox network management")
    print()
    print(f"{Colors.BRIGHT_GREEN}  Commands:{Colors.RESET}")
    print(f"{Colors.BRIGHT_YELLOW}    •{Colors.RESET} Type your message and press {Colors.BOLD}Enter{Colors.RESET}")
    print(f"{Colors.BRIGHT_YELLOW}    •{Colors.RESET} Type {Colors.BOLD}{Colors.CYAN}'exit'{Colors.RESET} to end")
    print(f"{Colors.BRIGHT_YELLOW}    •{Colors.RESET} Type {Colors.BOLD}{Colors.CYAN}'clear'{Colors.RESET} to reset conversation")
    print()
    print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}{'─' * width}{Colors.RESET}")
    print()


def print_user_prompt():
    return f"{Colors.BOLD}{Colors.BRIGHT_GREEN}You:{Colors.RESET} "


def print_assistant_prompt():
    print()
    print(f"{Colors.BOLD}{Colors.BRIGHT_MAGENTA}DDI Assistant:{Colors.RESET} ", end='', flush=True)


def print_message(text, is_user=False):
    width = 75
    color = Colors.BRIGHT_WHITE
    wrapped = textwrap.fill(text, width=width, break_long_words=False, break_on_hyphens=False)
    for line in wrapped.split('\n'):
        print(f"{color}{line}{Colors.RESET}")


def print_thinking():
    print(f"{Colors.DIM}{Colors.BRIGHT_BLACK}  (thinking...){Colors.RESET}", end='', flush=True)


def clear_line():
    print('\r\033[K', end='', flush=True)


# Built-in tool functions
def get_current_datetime():
    now = datetime.now()
    return {
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "day_of_week": now.strftime("%A"),
        "formatted": now.strftime("%A, %B %d, %Y at %I:%M %p")
    }


def execute_simple_command(command):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10)
        return result.stdout + result.stderr
    except Exception as e:
        return f"Error: {e}"


def web_search(query, max_results=5):
    if not WEB_SEARCH_AVAILABLE:
        return {"error": "Web search not available"}
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            return {"results": results, "query": query}
    except Exception as e:
        return {"error": str(e)}


def fetch_webpage(url):
    if not WEB_SEARCH_AVAILABLE:
        return {"error": "Web fetching not available"}
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        if len(text) > 5000:
            text = text[:5000] + "...[truncated]"
        return {"url": url, "content": text, "title": soup.title.string if soup.title else "No title"}
    except Exception as e:
        return {"error": str(e), "url": url}


def search_files(pattern, directory="."):
    try:
        files = glob.glob(os.path.join(directory, "**", pattern), recursive=True)
        return {"files": files[:50], "pattern": pattern, "directory": directory}
    except Exception as e:
        return {"error": str(e)}


def read_file_content(file_path):
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        if len(content) > 10000:
            content = content[:10000] + "...[truncated]"
        return {"file_path": file_path, "content": content}
    except Exception as e:
        return {"error": str(e), "file_path": file_path}


# InfoBlox WAPI tools
def infoblox_list_networks(max_results=100, return_fields=""):
    """List networks from InfoBlox"""
    params = {"_max_results": max_results}
    if return_fields:
        params["_return_fields"] = return_fields
    return infoblox_client.wapi_request("GET", "network", params=params)


def infoblox_get_network(ref, return_fields=""):
    """Get specific network by reference"""
    params = {}
    if return_fields:
        params["_return_fields"] = return_fields
    return infoblox_client.wapi_request("GET", ref, params=params)


def infoblox_create_network(network, comment="", **kwargs):
    """Create a new network"""
    data = {"network": network}
    if comment:
        data["comment"] = comment
    data.update(kwargs)
    return infoblox_client.wapi_request("POST", "network", json=data)


def infoblox_search_records(record_type, name="", value="", max_results=100):
    """Search DNS records"""
    params = {"_max_results": max_results}
    if name:
        params["name"] = name
    if value:
        params["ipv4addr"] = value if record_type == "a" else value
    return infoblox_client.wapi_request("GET", f"record:{record_type}", params=params)


def infoblox_list_dhcp_leases(network="", mac="", max_results=100):
    """List DHCP leases"""
    params = {"_max_results": max_results}
    if network:
        params["network"] = network
    if mac:
        params["hardware"] = mac
    return infoblox_client.wapi_request("GET", "lease", params=params)


def infoblox_generic_query(object_type, filters=None, max_results=100):
    """Generic InfoBlox query"""
    params = {"_max_results": max_results}
    if filters:
        params.update(filters)
    return infoblox_client.wapi_request("GET", object_type, params=params)


def process_tool_call(tool_name, tool_input):
    """Process tool calls"""
    # InfoBlox tools
    if tool_name == "infoblox_list_networks":
        return infoblox_list_networks(
            tool_input.get("max_results", 100),
            tool_input.get("return_fields", "")
        )
    elif tool_name == "infoblox_get_network":
        return infoblox_get_network(
            tool_input.get("ref"),
            tool_input.get("return_fields", "")
        )
    elif tool_name == "infoblox_create_network":
        return infoblox_create_network(**tool_input)
    elif tool_name == "infoblox_search_records":
        return infoblox_search_records(**tool_input)
    elif tool_name == "infoblox_list_dhcp_leases":
        return infoblox_list_dhcp_leases(**tool_input)
    elif tool_name == "infoblox_query":
        return infoblox_generic_query(**tool_input)

    # Built-in tools
    elif tool_name == "get_current_datetime":
        return get_current_datetime()
    elif tool_name == "execute_command":
        return {"output": execute_simple_command(tool_input.get("command"))}
    elif tool_name == "web_search":
        return web_search(tool_input.get("query"), tool_input.get("max_results", 5))
    elif tool_name == "fetch_webpage":
        return fetch_webpage(tool_input.get("url"))
    elif tool_name == "search_files":
        return search_files(tool_input.get("pattern"), tool_input.get("directory", "."))
    elif tool_name == "read_file":
        return read_file_content(tool_input.get("file_path"))

    return {"error": "Unknown tool"}


def get_all_tools():
    """Get all tool definitions"""
    return [
        # Built-in tools
        {
            "name": "get_current_datetime",
            "description": "Get the current date and time",
            "input_schema": {"type": "object", "properties": {}, "required": []}
        },
        {
            "name": "web_search",
            "description": "Search the web using DuckDuckGo",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "max_results": {"type": "integer", "default": 5}
                },
                "required": ["query"]
            }
        },
        {
            "name": "fetch_webpage",
            "description": "Fetch and read webpage content",
            "input_schema": {
                "type": "object",
                "properties": {"url": {"type": "string"}},
                "required": ["url"]
            }
        },
        {
            "name": "search_files",
            "description": "Search for files by pattern",
            "input_schema": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string"},
                    "directory": {"type": "string", "default": "."}
                },
                "required": ["pattern"]
            }
        },
        {
            "name": "read_file",
            "description": "Read file contents",
            "input_schema": {
                "type": "object",
                "properties": {"file_path": {"type": "string"}},
                "required": ["file_path"]
            }
        },
        {
            "name": "execute_command",
            "description": "Execute shell command",
            "input_schema": {
                "type": "object",
                "properties": {"command": {"type": "string"}},
                "required": ["command"]
            }
        },
        # InfoBlox tools
        {
            "name": "infoblox_list_networks",
            "description": "List networks from InfoBlox WAPI. Returns network objects with their IP ranges, comments, and configuration.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "max_results": {"type": "integer", "description": "Max results (default: 100)", "default": 100},
                    "return_fields": {"type": "string", "description": "Comma-separated fields to return"}
                }
            }
        },
        {
            "name": "infoblox_get_network",
            "description": "Get a specific network object by its reference (_ref). Use this after listing to get detailed information.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "ref": {"type": "string", "description": "Network object reference (_ref)"},
                    "return_fields": {"type": "string", "description": "Fields to return"}
                },
                "required": ["ref"]
            }
        },
        {
            "name": "infoblox_create_network",
            "description": "Create a new network in InfoBlox. Requires network in CIDR format (e.g., 10.0.0.0/24).",
            "input_schema": {
                "type": "object",
                "properties": {
                    "network": {"type": "string", "description": "Network in CIDR format"},
                    "comment": {"type": "string", "description": "Network comment/description"}
                },
                "required": ["network"]
            }
        },
        {
            "name": "infoblox_search_records",
            "description": "Search DNS records by type and filters. Supports A, AAAA, PTR, CNAME, MX, TXT, SRV records.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "record_type": {"type": "string", "description": "Record type (a, aaaa, ptr, cname, mx, txt, srv)"},
                    "name": {"type": "string", "description": "DNS name to search for"},
                    "value": {"type": "string", "description": "IP address or value to search for"},
                    "max_results": {"type": "integer", "default": 100}
                },
                "required": ["record_type"]
            }
        },
        {
            "name": "infoblox_list_dhcp_leases",
            "description": "List DHCP leases from InfoBlox. Can filter by network or MAC address.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "network": {"type": "string", "description": "Filter by network (e.g., 10.0.0.0/24)"},
                    "mac": {"type": "string", "description": "Filter by MAC address"},
                    "max_results": {"type": "integer", "default": 100}
                }
            }
        },
        {
            "name": "infoblox_query",
            "description": "Generic InfoBlox WAPI query for any object type. Use for advanced queries of any InfoBlox object (zone_auth, fixedaddress, range, etc.).",
            "input_schema": {
                "type": "object",
                "properties": {
                    "object_type": {"type": "string", "description": "InfoBlox object type (e.g., zone_auth, fixedaddress, range)"},
                    "filters": {"type": "object", "description": "Filter criteria as key-value pairs"},
                    "max_results": {"type": "integer", "default": 100}
                },
                "required": ["object_type"]
            }
        }
    ]


def main():
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print(f"{Colors.BRIGHT_RED}ANTHROPIC_API_KEY not set{Colors.RESET}")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)
    tools = get_all_tools()
    conversation_history = []

    print_header()

    # Test InfoBlox connectivity
    print(f"{Colors.BRIGHT_CYAN}Testing InfoBlox connection...{Colors.RESET}")
    test_result = infoblox_client.wapi_request("GET", "network?_max_results=1")
    if "error" in test_result:
        print(f"{Colors.BRIGHT_RED}✗ InfoBlox not accessible: {test_result.get('error')}{Colors.RESET}")
        print(f"{Colors.BRIGHT_YELLOW}  InfoBlox tools will not work{Colors.RESET}")
    else:
        print(f"{Colors.BRIGHT_GREEN}✓ InfoBlox WAPI is accessible{Colors.RESET}")
    print()

    while True:
        try:
            user_input = input(print_user_prompt()).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            print(f"{Colors.BRIGHT_CYAN}Goodbye! 👋{Colors.RESET}")
            break

        if user_input.lower() in ['exit', 'quit', 'bye', 'q']:
            print()
            print(f"{Colors.BRIGHT_CYAN}Goodbye! 👋{Colors.RESET}")
            break

        if user_input.lower() == 'clear':
            conversation_history = []
            print(f"{Colors.BRIGHT_GREEN}✓ Conversation cleared!{Colors.RESET}")
            continue

        if not user_input:
            continue

        conversation_history.append({"role": "user", "content": user_input})

        print()
        print_thinking()

        while True:
            try:
                response = client.messages.create(
                    model="claude-sonnet-4-5-20250929",
                    max_tokens=4096,
                    tools=tools,
                    messages=conversation_history
                )

                clear_line()
                assistant_message = {"role": "assistant", "content": []}
                has_text = False

                for block in response.content:
                    if block.type == "text":
                        if not has_text:
                            print_assistant_prompt()
                            has_text = True
                        print_message(block.text)
                        assistant_message["content"].append(block)

                    elif block.type == "tool_use":
                        assistant_message["content"].append(block)
                        result = process_tool_call(block.name, block.input)

                        conversation_history.append(assistant_message)
                        conversation_history.append({
                            "role": "user",
                            "content": [{
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": json.dumps(result)
                            }]
                        })

                        print()
                        print_thinking()
                        break
                else:
                    if has_text:
                        print()
                    conversation_history.append(assistant_message)
                    break

            except Exception as e:
                clear_line()
                print(f"{Colors.BRIGHT_RED}Error: {e}{Colors.RESET}")
                conversation_history.pop()
                break


if __name__ == '__main__':
    main()
