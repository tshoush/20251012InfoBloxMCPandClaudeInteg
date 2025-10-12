#!/usr/bin/env python
"""Interactive chat interface for Claude AI with enhanced styling"""

import os
import sys
import anthropic
import textwrap
import json
from datetime import datetime
import subprocess
import glob
try:
    from duckduckgo_search import DDGS
    import requests
    from bs4 import BeautifulSoup
    WEB_SEARCH_AVAILABLE = True
except ImportError:
    WEB_SEARCH_AVAILABLE = False

# ANSI color codes
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'

    # Foreground colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'

    # Bright foreground colors
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'

    # Background colors
    BG_BLACK = '\033[40m'
    BG_BLUE = '\033[44m'
    BG_CYAN = '\033[46m'

def print_header():
    """Print styled header"""
    width = 80
    print()
    print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}{'═' * width}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BRIGHT_WHITE}{'🤖 Claude Sonnet 4.5 - DDI Assistant':^{width}}{Colors.RESET}")
    print(f"{Colors.BRIGHT_BLUE}{'Enhanced AI Chat with Web Search & System Access':^{width}}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}{'═' * width}{Colors.RESET}")
    print()
    print(f"{Colors.BRIGHT_GREEN}  Capabilities:{Colors.RESET}")
    print(f"{Colors.BRIGHT_YELLOW}    🌐{Colors.RESET} Web search and browsing")
    print(f"{Colors.BRIGHT_YELLOW}    📁{Colors.RESET} File system access (read, search)")
    print(f"{Colors.BRIGHT_YELLOW}    💻{Colors.RESET} System commands and information")
    print(f"{Colors.BRIGHT_YELLOW}    📅{Colors.RESET} Current date and time")
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
    if is_user:
        color = Colors.BRIGHT_WHITE
    else:
        color = Colors.BRIGHT_WHITE

    # Wrap text to terminal width
    wrapped = textwrap.fill(text, width=width, break_long_words=False, break_on_hyphens=False)

    # Print with color
    for line in wrapped.split('\n'):
        print(f"{color}{line}{Colors.RESET}")

def print_divider():
    """Print a subtle divider"""
    print(f"{Colors.DIM}{Colors.BRIGHT_BLACK}{'─' * 80}{Colors.RESET}")

def print_status(message, status_type='info'):
    """Print status messages"""
    if status_type == 'success':
        icon = '✓'
        color = Colors.BRIGHT_GREEN
    elif status_type == 'error':
        icon = '✗'
        color = Colors.BRIGHT_RED
    elif status_type == 'info':
        icon = 'ℹ'
        color = Colors.BRIGHT_CYAN
    else:
        icon = '•'
        color = Colors.BRIGHT_YELLOW

    print(f"\n{color}{Colors.BOLD}{icon} {message}{Colors.RESET}\n")

def print_thinking():
    """Print thinking indicator"""
    print(f"{Colors.DIM}{Colors.BRIGHT_BLACK}  (thinking...){Colors.RESET}", end='', flush=True)

def clear_line():
    """Clear the current line"""
    print('\r\033[K', end='', flush=True)

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
        return {"error": "Web search not available. Install duckduckgo-search package."}

    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            return {"results": results, "query": query}
    except Exception as e:
        return {"error": str(e)}

def fetch_webpage(url):
    """Fetch and extract text from a webpage"""
    if not WEB_SEARCH_AVAILABLE:
        return {"error": "Web fetching not available. Install requests and beautifulsoup4 packages."}

    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Get text
        text = soup.get_text()

        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)

        # Limit length
        if len(text) > 5000:
            text = text[:5000] + "...[truncated]"

        return {"url": url, "content": text, "title": soup.title.string if soup.title else "No title"}
    except Exception as e:
        return {"error": str(e), "url": url}

def search_files(pattern, directory="."):
    """Search for files matching a pattern"""
    try:
        files = glob.glob(os.path.join(directory, "**", pattern), recursive=True)
        return {"files": files[:50], "pattern": pattern, "directory": directory}  # Limit to 50 results
    except Exception as e:
        return {"error": str(e)}

def read_file_content(file_path):
    """Read content from a file"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        # Limit length
        if len(content) > 10000:
            content = content[:10000] + "...[truncated]"
        return {"file_path": file_path, "content": content}
    except Exception as e:
        return {"error": str(e), "file_path": file_path}

def process_tool_call(tool_name, tool_input):
    """Process tool calls from Claude"""
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

def main():
    # Get API key from environment variable
    api_key = os.environ.get('ANTHROPIC_API_KEY')

    if not api_key:
        print_status('ANTHROPIC_API_KEY environment variable not set', 'error')
        print(f"{Colors.BRIGHT_YELLOW}Set your API key with:{Colors.RESET}")
        print(f"  {Colors.CYAN}export ANTHROPIC_API_KEY=your-api-key-here{Colors.RESET}")
        sys.exit(1)

    # Create Anthropic client
    client = anthropic.Anthropic(api_key=api_key)

    # Define available tools
    tools = [
        {
            "name": "get_current_datetime",
            "description": "Get the current date and time. Use this when the user asks about the current date, time, day of week, etc.",
            "input_schema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        },
        {
            "name": "web_search",
            "description": "Search the web using DuckDuckGo. Use this to find current information, news, facts, or anything not in your knowledge. Returns search results with titles, URLs, and snippets.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 5)",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        },
        {
            "name": "fetch_webpage",
            "description": "Fetch and read the content of a specific webpage. Use this to get detailed information from a known URL or to read the content of search results.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL of the webpage to fetch"
                    }
                },
                "required": ["url"]
            }
        },
        {
            "name": "search_files",
            "description": "Search for files matching a pattern in a directory. Supports wildcards like *.py, *.txt, etc.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "File pattern to search for (e.g., '*.py', 'config.*')"
                    },
                    "directory": {
                        "type": "string",
                        "description": "Directory to search in (default: current directory)",
                        "default": "."
                    }
                },
                "required": ["pattern"]
            }
        },
        {
            "name": "read_file",
            "description": "Read the content of a file. Use this to examine file contents, read configuration files, or analyze code.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file to read"
                    }
                },
                "required": ["file_path"]
            }
        },
        {
            "name": "execute_command",
            "description": "Execute a shell command to get system information (like uptime, disk usage, etc). Use for simple, safe commands only.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The shell command to execute"
                    }
                },
                "required": ["command"]
            }
        }
    ]

    # Conversation history
    conversation_history = []

    # Print welcome header
    print_header()

    while True:
        # Get user input
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

        # Check for exit commands
        if user_input.lower() in ['exit', 'quit', 'bye', 'q']:
            print()
            print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}{'═' * 80}{Colors.RESET}")
            print(f"{Colors.BRIGHT_CYAN}  Goodbye! 👋 Thanks for chatting!{Colors.RESET}")
            print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}{'═' * 80}{Colors.RESET}")
            print()
            break

        # Check for clear command
        if user_input.lower() == 'clear':
            conversation_history = []
            print()
            print_status("Conversation cleared. Starting fresh!", 'success')
            continue

        # Skip empty input
        if not user_input:
            continue

        # Add user message to conversation history
        conversation_history.append({
            "role": "user",
            "content": user_input
        })

        # Show thinking indicator
        print()
        print_thinking()

        # Main conversation loop with tool use
        while True:
            try:
                # Send message to Claude with tools
                response = client.messages.create(
                    model="claude-sonnet-4-5-20250929",
                    max_tokens=4096,
                    tools=tools,
                    messages=conversation_history
                )

                # Clear thinking indicator
                clear_line()

                # Process the response
                assistant_message = {"role": "assistant", "content": []}
                has_text = False

                for block in response.content:
                    if block.type == "text":
                        if not has_text:
                            # Print assistant prompt only once
                            print_assistant_prompt()
                            has_text = True
                        print_message(block.text, is_user=False)
                        assistant_message["content"].append(block)

                    elif block.type == "tool_use":
                        # Add tool use to message
                        assistant_message["content"].append(block)

                        # Process the tool call silently
                        result = process_tool_call(block.name, block.input)

                        # Add assistant message with tool use
                        conversation_history.append(assistant_message)

                        # Add tool result
                        conversation_history.append({
                            "role": "user",
                            "content": [{
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": json.dumps(result)
                            }]
                        })

                        # Show thinking indicator for next iteration
                        print()
                        print_thinking()

                        # Continue the loop to get Claude's response to the tool result
                        break
                else:
                    # No tool use, end the loop
                    if has_text:
                        print()
                    conversation_history.append(assistant_message)
                    break

            except Exception as e:
                clear_line()
                print_status(f'Error: {e}', 'error')
                conversation_history.pop()
                break

if __name__ == '__main__':
    main()
