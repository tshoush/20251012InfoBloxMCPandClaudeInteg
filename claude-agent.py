#!/usr/bin/env python
"""Claude AI Agent with file system and command execution capabilities"""

import os
import sys
import json
import subprocess
import anthropic

def ask_permission(action, details):
    """Ask user for permission before taking action"""
    print(f"\n{'='*80}")
    print(f"🔐 PERMISSION REQUIRED: {action}")
    print(f"{'='*80}")
    print(details)
    print(f"{'='*80}")

    while True:
        response = input("Allow this action? (yes/no): ").strip().lower()
        if response in ['yes', 'y']:
            return True
        elif response in ['no', 'n']:
            return False
        else:
            print("Please answer 'yes' or 'no'")

def write_file(file_path, content):
    """Write content to a file with user permission"""
    details = f"File: {file_path}\n"
    details += f"Content length: {len(content)} characters\n"
    details += f"\nContent preview:\n{'-'*80}\n"
    details += content[:500] + ("..." if len(content) > 500 else "")

    if ask_permission("Write File", details):
        try:
            # Create directory if it doesn't exist
            dir_path = os.path.dirname(file_path)
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path)

            with open(file_path, 'w') as f:
                f.write(content)
            print(f"\n✅ Successfully wrote to: {file_path}\n")
            return True
        except Exception as e:
            print(f"\n❌ Error writing file: {e}\n")
            return False
    else:
        print("\n🚫 File write cancelled by user\n")
        return False

def execute_command(command):
    """Execute a shell command with user permission"""
    details = f"Command: {command}\n"
    details += f"\n⚠️  WARNING: This will execute on your system!"

    if ask_permission("Execute Command", details):
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            output = result.stdout + result.stderr
            print(f"\n📋 Command output:\n{'-'*80}\n{output}\n{'-'*80}\n")
            return output
        except Exception as e:
            print(f"\n❌ Error executing command: {e}\n")
            return f"Error: {e}"
    else:
        print("\n🚫 Command execution cancelled by user\n")
        return "Command cancelled by user"

def process_tool_call(tool_name, tool_input):
    """Process tool calls from Claude"""
    if tool_name == "write_file":
        file_path = tool_input.get("file_path")
        content = tool_input.get("content")
        success = write_file(file_path, content)
        return {"success": success, "file_path": file_path}

    elif tool_name == "execute_command":
        command = tool_input.get("command")
        output = execute_command(command)
        return {"output": output}

    elif tool_name == "read_file":
        file_path = tool_input.get("file_path")
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            return {"content": content}
        except Exception as e:
            return {"error": str(e)}

    return {"error": "Unknown tool"}

def main():
    # Get API key from environment variable
    api_key = os.environ.get('ANTHROPIC_API_KEY')

    if not api_key:
        print('Error: ANTHROPIC_API_KEY environment variable not set', file=sys.stderr)
        sys.exit(1)

    # Create Anthropic client
    client = anthropic.Anthropic(api_key=api_key)

    # Define available tools
    tools = [
        {
            "name": "write_file",
            "description": "Write content to a file on the user's system. Always ask user for permission before writing files.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "The path where the file should be written (can be relative or absolute)"
                    },
                    "content": {
                        "type": "string",
                        "description": "The content to write to the file"
                    }
                },
                "required": ["file_path", "content"]
            }
        },
        {
            "name": "read_file",
            "description": "Read content from a file on the user's system",
            "input_schema": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "The path of the file to read"
                    }
                },
                "required": ["file_path"]
            }
        },
        {
            "name": "execute_command",
            "description": "Execute a shell command on the user's system. Always explain what the command does and ask for permission. Use with caution.",
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

    # Welcome message
    print("=" * 80)
    print("🤖 Claude AI Agent - Enhanced with File & Command Capabilities")
    print("=" * 80)
    print("Claude can now:")
    print("  • Write files to your computer (with your permission)")
    print("  • Read files from your computer")
    print("  • Execute shell commands (with your permission)")
    print("")
    print("Type 'exit', 'quit', or 'bye' to end.")
    print("Type 'clear' to start a new conversation.")
    print("=" * 80)
    print()

    while True:
        # Get user input
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nGoodbye! 👋")
            break

        # Check for exit commands
        if user_input.lower() in ['exit', 'quit', 'bye', 'q']:
            print("\nGoodbye! 👋")
            break

        # Check for clear command
        if user_input.lower() == 'clear':
            conversation_history = []
            print("\n✓ Conversation cleared. Starting fresh!\n")
            continue

        # Skip empty input
        if not user_input:
            continue

        # Add user message to conversation history
        conversation_history.append({
            "role": "user",
            "content": user_input
        })

        # Main conversation loop with tool use
        while True:
            try:
                print("\nClaude: ", end='', flush=True)

                # Send message to Claude with tools
                response = client.messages.create(
                    model="claude-sonnet-4-5-20250929",
                    max_tokens=4096,
                    tools=tools,
                    messages=conversation_history
                )

                # Process the response
                assistant_message = {"role": "assistant", "content": []}

                for block in response.content:
                    if block.type == "text":
                        print(block.text, end='', flush=True)
                        assistant_message["content"].append(block)

                    elif block.type == "tool_use":
                        # Add tool use to message
                        assistant_message["content"].append(block)

                        # Process the tool call
                        print(f"\n\n🔧 Using tool: {block.name}")
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

                        # Continue the loop to get Claude's response to the tool result
                        break
                else:
                    # No tool use, end the loop
                    conversation_history.append(assistant_message)
                    print("\n")
                    break

            except Exception as e:
                print(f'\nError: {e}', file=sys.stderr)
                conversation_history.pop()
                break

if __name__ == '__main__':
    main()
