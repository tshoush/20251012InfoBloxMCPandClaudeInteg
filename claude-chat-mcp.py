#!/usr/bin/env python
"""Interactive chat interface for Claude AI with MCP server support"""

import os
import sys
import anthropic
import textwrap
import json
from datetime import datetime
import subprocess
import glob
import asyncio
from typing import List, Dict, Any, Optional

try:
    from duckduckgo_search import DDGS
    import requests
    from bs4 import BeautifulSoup
    WEB_SEARCH_AVAILABLE = True
except ImportError:
    WEB_SEARCH_AVAILABLE = False

# Try to import MCP client
try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("Warning: MCP not available. Install with: pip install mcp")

# ANSI color codes
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

    BG_BLACK = '\033[40m'
    BG_BLUE = '\033[44m'
    BG_CYAN = '\033[46m'


class MCPServerManager:
    """Manages MCP server connections"""

    def __init__(self):
        self.servers = {}
        self.server_tools = {}

    async def connect_server(self, name: str, command: str, args: List[str] = None):
        """Connect to an MCP server"""
        if not MCP_AVAILABLE:
            print(f"{Colors.BRIGHT_RED}MCP not available{Colors.RESET}")
            return False

        try:
            server_params = StdioServerParameters(
                command=command,
                args=args or []
            )

            stdio_transport = await stdio_client(server_params)
            stdio, write = stdio_transport

            async with ClientSession(stdio, write) as session:
                await session.initialize()

                # List available tools
                tools_result = await session.list_tools()
                self.server_tools[name] = tools_result.tools
                self.servers[name] = {
                    'session': session,
                    'transport': stdio_transport
                }

                print(f"{Colors.BRIGHT_GREEN}✓ Connected to {name} MCP server{Colors.RESET}")
                print(f"  {len(tools_result.tools)} tools available")
                return True

        except Exception as e:
            print(f"{Colors.BRIGHT_RED}✗ Error connecting to {name}: {e}{Colors.RESET}")
            return False

    def get_all_tools(self) -> List[Dict]:
        """Get all tools from all connected MCP servers"""
        all_tools = []
        for server_name, tools in self.server_tools.items():
            for tool in tools:
                # Convert MCP tool to Anthropic tool format
                all_tools.append({
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema,
                    "_mcp_server": server_name
                })
        return all_tools

    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict) -> Any:
        """Call a tool on an MCP server"""
        if server_name not in self.servers:
            return {"error": f"Server {server_name} not connected"}

        try:
            session = self.servers[server_name]['session']
            result = await session.call_tool(tool_name, arguments)
            return result
        except Exception as e:
            return {"error": str(e)}


def print_header():
    """Print styled header"""
    width = 80
    print()
    print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}{'═' * width}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BRIGHT_WHITE}{'🤖 Claude Sonnet 4.5 - DDI Assistant with MCP':^{width}}{Colors.RESET}")
    print(f"{Colors.BRIGHT_BLUE}{'Enhanced AI Chat with Web Search, System Access & InfoBlox':^{width}}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}{'═' * width}{Colors.RESET}")
    print()
    print(f"{Colors.BRIGHT_GREEN}  Capabilities:{Colors.RESET}")
    print(f"{Colors.BRIGHT_YELLOW}    🌐{Colors.RESET} Web search and browsing")
    print(f"{Colors.BRIGHT_YELLOW}    📁{Colors.RESET} File system access (read, search)")
    print(f"{Colors.BRIGHT_YELLOW}    💻{Colors.RESET} System commands and information")
    print(f"{Colors.BRIGHT_YELLOW}    📅{Colors.RESET} Current date and time")
    if MCP_AVAILABLE:
        print(f"{Colors.BRIGHT_YELLOW}    🔌{Colors.RESET} MCP servers (InfoBlox and more)")
    print()
    print(f"{Colors.BRIGHT_GREEN}  Commands:{Colors.RESET}")
    print(f"{Colors.BRIGHT_YELLOW}    •{Colors.RESET} Type your message and press {Colors.BOLD}Enter{Colors.RESET}")
    print(f"{Colors.BRIGHT_YELLOW}    •{Colors.RESET} Type {Colors.BOLD}{Colors.CYAN}'exit'{Colors.RESET}, {Colors.BOLD}{Colors.CYAN}'quit'{Colors.RESET}, or {Colors.BOLD}{Colors.CYAN}'bye'{Colors.RESET} to end")
    print(f"{Colors.BRIGHT_YELLOW}    •{Colors.RESET} Type {Colors.BOLD}{Colors.CYAN}'clear'{Colors.RESET} to start a new conversation")
    print()
    print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}{'─' * width}{Colors.RESET}")
    print()


def print_user_prompt():
    """Print styled user prompt"""
    return f"{Colors.BOLD}{Colors.BRIGHT_GREEN}You:{Colors.RESET} "


def print_assistant_prompt():
    """Print styled assistant prompt"""
    print()
    print(f"{Colors.BOLD}{Colors.BRIGHT_MAGENTA}DDI Assistant:{Colors.RESET} ", end='', flush=True)


def print_message(text, is_user=False):
    """Print formatted message with word wrapping"""
    width = 75
    color = Colors.BRIGHT_WHITE

    wrapped = textwrap.fill(text, width=width, break_long_words=False, break_on_hyphens=False)

    for line in wrapped.split('\n'):
        print(f"{color}{line}{Colors.RESET}")


def print_thinking():
    """Print thinking indicator"""
    print(f"{Colors.DIM}{Colors.BRIGHT_BLACK}  (thinking...){Colors.RESET}", end='', flush=True)


def clear_line():
    """Clear the current line"""
    print('\r\033[K', end='', flush=True)


# Built-in tool functions (web search, file system, etc.)
def get_current_datetime():
    """Get current date and time"""
    now = datetime.now()
    return {
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "day_of_week": now.strftime("%A"),
        "formatted": now.strftime("%A, %B %d, %Y at %I:%M %p")
    }


def execute_simple_command(command):
    """Execute a simple shell command"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.stdout + result.stderr
    except Exception as e:
        return f"Error: {e}"


def web_search(query, max_results=5):
    """Search the web using DuckDuckGo"""
    if not WEB_SEARCH_AVAILABLE:
        return {"error": "Web search not available"}

    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            return {"results": results, "query": query}
    except Exception as e:
        return {"error": str(e)}


def fetch_webpage(url):
    """Fetch and extract text from a webpage"""
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
    """Search for files matching a pattern"""
    try:
        files = glob.glob(os.path.join(directory, "**", pattern), recursive=True)
        return {"files": files[:50], "pattern": pattern, "directory": directory}
    except Exception as e:
        return {"error": str(e)}


def read_file_content(file_path):
    """Read content from a file"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        if len(content) > 10000:
            content = content[:10000] + "...[truncated]"
        return {"file_path": file_path, "content": content}
    except Exception as e:
        return {"error": str(e), "file_path": file_path}


def process_tool_call(tool_name, tool_input, mcp_manager=None):
    """Process tool calls - both built-in and MCP tools"""
    # Check if it's an MCP tool
    if mcp_manager and tool_name.startswith('infoblox_'):
        # Find which server has this tool
        for server_name, tools in mcp_manager.server_tools.items():
            if any(t.name == tool_name for t in tools):
                # Call MCP tool asynchronously
                loop = asyncio.get_event_loop()
                result = loop.run_until_complete(
                    mcp_manager.call_tool(server_name, tool_name, tool_input)
                )
                return result
        return {"error": "MCP tool not found"}

    # Built-in tools
    if tool_name == "get_current_datetime":
        return get_current_datetime()
    elif tool_name == "execute_command":
        command = tool_input.get("command")
        output = execute_simple_command(command)
        return {"output": output}
    elif tool_name == "web_search":
        query = tool_input.get("query")
        max_results = tool_input.get("max_results", 5)
        return web_search(query, max_results)
    elif tool_name == "fetch_webpage":
        url = tool_input.get("url")
        return fetch_webpage(url)
    elif tool_name == "search_files":
        pattern = tool_input.get("pattern")
        directory = tool_input.get("directory", ".")
        return search_files(pattern, directory)
    elif tool_name == "read_file":
        file_path = tool_input.get("file_path")
        return read_file_content(file_path)

    return {"error": "Unknown tool"}


def get_builtin_tools():
    """Get built-in tool definitions"""
    return [
        {
            "name": "get_current_datetime",
            "description": "Get the current date and time",
            "input_schema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        },
        {
            "name": "web_search",
            "description": "Search the web using DuckDuckGo",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query"},
                    "max_results": {"type": "integer", "description": "Max results", "default": 5}
                },
                "required": ["query"]
            }
        },
        {
            "name": "fetch_webpage",
            "description": "Fetch and read webpage content",
            "input_schema": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to fetch"}
                },
                "required": ["url"]
            }
        },
        {
            "name": "search_files",
            "description": "Search for files by pattern",
            "input_schema": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "File pattern (*.py)"},
                    "directory": {"type": "string", "description": "Directory to search", "default": "."}
                },
                "required": ["pattern"]
            }
        },
        {
            "name": "read_file",
            "description": "Read file contents",
            "input_schema": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to file"}
                },
                "required": ["file_path"]
            }
        },
        {
            "name": "execute_command",
            "description": "Execute shell command",
            "input_schema": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Command to execute"}
                },
                "required": ["command"]
            }
        }
    ]


async def initialize_mcp_servers():
    """Initialize MCP server connections"""
    mcp_manager = MCPServerManager()

    if not MCP_AVAILABLE:
        return mcp_manager

    print(f"{Colors.BRIGHT_CYAN}Initializing MCP servers...{Colors.RESET}")

    # Connect to InfoBlox MCP server
    infoblox_server = os.path.expanduser("~/REDHAT/infoblox-mcp-server.py")
    if os.path.exists(infoblox_server):
        await mcp_manager.connect_server(
            "infoblox",
            "python",
            [infoblox_server]
        )

    print()
    return mcp_manager


def main():
    """Main function"""
    api_key = os.environ.get('ANTHROPIC_API_KEY')

    if not api_key:
        print(f"{Colors.BRIGHT_RED}ANTHROPIC_API_KEY not set{Colors.RESET}")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    # Initialize MCP servers
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    mcp_manager = loop.run_until_complete(initialize_mcp_servers())

    # Combine built-in and MCP tools
    tools = get_builtin_tools()
    if MCP_AVAILABLE:
        mcp_tools = mcp_manager.get_all_tools()
        tools.extend(mcp_tools)

    conversation_history = []

    print_header()

    while True:
        try:
            user_input = input(print_user_prompt()).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            print()
            print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}{'═' * 80}{Colors.RESET}")
            print(f"{Colors.BRIGHT_CYAN}  Goodbye! 👋 Thanks for chatting!{Colors.RESET}")
            print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}{'═' * 80}{Colors.RESET}")
            print()
            break

        if user_input.lower() in ['exit', 'quit', 'bye', 'q']:
            print()
            print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}{'═' * 80}{Colors.RESET}")
            print(f"{Colors.BRIGHT_CYAN}  Goodbye! 👋 Thanks for chatting!{Colors.RESET}")
            print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}{'═' * 80}{Colors.RESET}")
            print()
            break

        if user_input.lower() == 'clear':
            conversation_history = []
            print()
            print(f"{Colors.BRIGHT_GREEN}✓ Conversation cleared!{Colors.RESET}")
            print()
            continue

        if not user_input:
            continue

        conversation_history.append({
            "role": "user",
            "content": user_input
        })

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
                        print_message(block.text, is_user=False)
                        assistant_message["content"].append(block)

                    elif block.type == "tool_use":
                        assistant_message["content"].append(block)

                        # Process tool call
                        result = process_tool_call(block.name, block.input, mcp_manager)

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
