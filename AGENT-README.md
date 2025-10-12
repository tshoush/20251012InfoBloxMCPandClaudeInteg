# Claude AI Agent - Enhanced CLI with File & Command Capabilities

An advanced AI agent that can interact with your file system and execute commands with your permission.

## 🚀 What's Different?

**claude-agent.py** is an enhanced version of Claude that can:

- ✅ **Write files** to your computer (with permission)
- ✅ **Read files** from your computer
- ✅ **Execute shell commands** (with permission)
- ✅ **Maintain conversation context** like the chat version
- ✅ **Ask for permission** before any action

## 🔐 Security Features

**Safety First!**

1. **Permission System** - Always asks before writing files or running commands
2. **Preview Content** - Shows what will be written before saving
3. **Confirmation Required** - You must explicitly approve each action
4. **No Surprises** - Claude explains what it's doing before doing it
5. **User Control** - You can reject any action at any time

## 📋 Available Tools

Claude Agent has access to these tools:

### 1. Write File
- Creates or overwrites files
- Shows content preview before writing
- Creates directories if needed
- Asks for permission every time

### 2. Read File
- Reads file contents
- Claude can analyze, modify, or work with the content
- Useful for code review, editing, etc.

### 3. Execute Command
- Runs shell commands
- Shows the command before execution
- Displays output after execution
- Asks for permission every time

## 🎯 Usage

### Start the Agent

```bash
source ~/.bashrc
agent
```

Or:
```bash
python ~/claude-agent.py
```

### Example Interactions

#### Example 1: Create a Python Script

```
You: Write me a hello world Python script

Claude: I'll create a hello world script for you. Let me write it to a file.

🔧 Using tool: write_file

================================================================================
🔐 PERMISSION REQUIRED: Write File
================================================================================
File: hello.py
Content length: 45 characters

Content preview:
--------------------------------------------------------------------------------
#!/usr/bin/env python
print("Hello, World!")
================================================================================
Allow this action? (yes/no): yes

✅ Successfully wrote to: hello.py

Claude: I've created the hello.py file with a simple hello world program!
```

#### Example 2: Create and Execute a Bash Script

```
You: Create a bash script to list all Python files in the current directory

Claude: I'll create a script for that and we can run it.

🔧 Using tool: write_file
[Shows permission prompt]

Allow this action? (yes/no): yes

✅ Successfully wrote to: list_python.sh

Claude: Now let me make it executable and run it.

🔧 Using tool: execute_command

================================================================================
🔐 PERMISSION REQUIRED: Execute Command
================================================================================
Command: chmod +x list_python.sh && ./list_python.sh

⚠️  WARNING: This will execute on your system!
================================================================================
Allow this action? (yes/no): yes

📋 Command output:
--------------------------------------------------------------------------------
hello.py
my_script.py
test.py
--------------------------------------------------------------------------------

Claude: The script found 3 Python files in your current directory!
```

#### Example 3: Edit an Existing File

```
You: Read my config.txt file and add a new line "debug=true"

Claude: Let me read the current configuration first.

🔧 Using tool: read_file

Claude: I see your current config. Now I'll add the debug line.

🔧 Using tool: write_file
[Shows permission prompt with full content]

Allow this action? (yes/no): yes

✅ Successfully wrote to: config.txt

Claude: I've updated config.txt with the debug setting!
```

#### Example 4: System Administration

```
You: Check my disk usage and save it to a report

Claude: I'll check the disk usage and create a report for you.

🔧 Using tool: execute_command

================================================================================
🔐 PERMISSION REQUIRED: Execute Command
================================================================================
Command: df -h

⚠️  WARNING: This will execute on your system!
================================================================================
Allow this action? (yes/no): yes

📋 Command output:
--------------------------------------------------------------------------------
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1        50G   20G   28G  42% /
...
--------------------------------------------------------------------------------

Claude: Now I'll save this to a report file.

🔧 Using tool: write_file
[Shows permission prompt]

Allow this action? (yes/no): yes

✅ Successfully wrote to: disk_report.txt

Claude: Disk usage report saved to disk_report.txt!
```

## 🎛️ Commands

- Type your message and press Enter to chat
- Type `exit`, `quit`, or `bye` to end
- Type `clear` to start a new conversation
- Answer `yes` or `no` to permission prompts
- Press Ctrl+C to exit anytime

## ⚙️ Common Use Cases

### Development
- **Generate code files** - "Create a Flask web app"
- **Write tests** - "Write unit tests for my Python script"
- **Create configs** - "Generate a nginx config for my site"
- **Build scripts** - "Create a build script for my project"

### System Administration
- **System monitoring** - "Check system resources and create a report"
- **Log analysis** - "Read my apache logs and find errors"
- **Automation scripts** - "Create a backup script for /home"
- **Configuration management** - "Update my SSH config with new settings"

### Data Processing
- **Transform files** - "Convert this JSON to CSV"
- **Parse logs** - "Extract all errors from this log file"
- **Generate reports** - "Analyze these files and create a summary"

### Documentation
- **Create README files** - "Generate a README for my project"
- **Write docs** - "Document this code in a markdown file"
- **Generate examples** - "Create example configs for users"

## 🔒 Safety Tips

1. **Review before approving** - Always read what Claude wants to do
2. **Check file paths** - Make sure files are going to the right location
3. **Understand commands** - Don't run commands you don't understand
4. **Backup important files** - Before letting Claude modify them
5. **Use in safe directories** - Start in a test directory if unsure

## ⚠️ What NOT to Do

- ❌ Don't run commands you don't understand
- ❌ Don't let it modify system files without review
- ❌ Don't execute commands with sudo without careful consideration
- ❌ Don't approve destructive operations (rm -rf, etc.) without backups
- ❌ Don't grant permission to suspicious commands

## 🆚 Comparison: Which Tool to Use?

### Use `claude` (one-shot CLI):
- Quick questions
- No file operations needed
- Simple answers

### Use `chat` (interactive):
- Long conversations
- No file operations needed
- Back-and-forth discussion

### Use `agent` (enhanced):
- Need to create/edit files
- Need to run commands
- Building projects
- System administration
- Automation tasks

## 📂 Files Created

The agent can create files anywhere on your system (with permission):
- Scripts (`.sh`, `.py`, `.js`, etc.)
- Configuration files
- Documentation (`.md`, `.txt`, etc.)
- Data files (`.json`, `.csv`, `.xml`, etc.)
- Any text-based file

## 🐛 Troubleshooting

### Permission Denied Errors
**Solution:** Make sure you have write permissions in the target directory

### Command Not Found
**Solution:** Ensure the command is installed and in your PATH

### File Already Exists
**Solution:** Claude will overwrite with your permission - backup first if needed

### API Errors
**Solution:** Check your internet connection and API key

## 💡 Pro Tips

1. **Be specific** - "Create a Python script called backup.py that..." is better than "make a backup script"

2. **Review changes** - Always check the content preview before approving

3. **Test in safe directory** - Try it out in ~/test first

4. **Chain operations** - "Create a script, make it executable, and run it"

5. **Use for learning** - Ask Claude to explain what each command does

## 📝 Example Session

```bash
$ agent

================================================================================
🤖 Claude AI Agent - Enhanced with File & Command Capabilities
================================================================================
Claude can now:
  • Write files to your computer (with your permission)
  • Read files from your computer
  • Execute shell commands (with your permission)

Type 'exit', 'quit', or 'bye' to end.
Type 'clear' to start a new conversation.
================================================================================

You: Create a Python script that backs up my home directory

Claude: I'll create a backup script for you...

[Permission prompts and file creation happen here]

You: Now create a cron job to run it daily

Claude: I'll help you set that up...

[More interaction with permission prompts]

You: exit

Goodbye! 👋
```

## 🔗 Related Tools

- **claude-cli.py** (`claude`) - One-shot CLI for quick questions
- **claude-chat.py** (`chat`) - Interactive chat without file access
- **claude-agent.py** (`agent`) - Full-featured agent with file/command access

## ⚡ Quick Reference

```bash
# Start the agent
agent

# Common patterns
You: Create a file called test.py with hello world
You: Read my config.json and show me the database settings
You: Run 'ls -la' and show me what's here
You: Create a bash script to backup /home to /backup
You: Edit my .bashrc and add this alias
```

## 🎓 Learning Resources

- Ask Claude to explain commands before running them
- Have Claude comment code it generates
- Request explanations of what each file does
- Learn by doing - let Claude guide you through tasks

---

**Remember:** With great power comes great responsibility. Always review what the agent wants to do before approving! 🛡️
