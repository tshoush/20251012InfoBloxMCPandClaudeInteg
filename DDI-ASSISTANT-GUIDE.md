# DDI Assistant - Enhanced AI Chat Guide

Your DDI Assistant now has **web search** and **enhanced system capabilities**!

## 🎉 What's New

### 🌐 Web Search & Browsing
- **Search the web** - Get current information, news, facts
- **Read web pages** - Fetch and analyze specific URLs
- **Real-time data** - Weather, stock prices, current events

### 📁 Enhanced File System
- **Search files** - Find files by pattern (*.py, *.txt, etc.)
- **Read files** - Examine file contents
- **Recursive search** - Search entire directory trees

### 💻 System Access
- **Execute commands** - Run system commands safely
- **Get system info** - Check uptime, disk usage, processes
- **Date & time** - Always knows the current date/time

## 🚀 Example Uses

### Web Search
```
You: What's the weather in Boston today?
DDI Assistant: [searches web for current Boston weather]

You: What's the latest news about AI?
DDI Assistant: [searches and provides current AI news]

You: Who won the last Super Bowl?
DDI Assistant: [searches for current Super Bowl winner]
```

### Web Page Reading
```
You: Read the Python documentation page at https://docs.python.org/3/tutorial/
DDI Assistant: [fetches and summarizes the page content]

You: What does this article say about quantum computing?
[paste URL]
DDI Assistant: [reads and analyzes the article]
```

### File System
```
You: Find all Python files in my home directory
DDI Assistant: [searches for *.py files]

You: Show me what's in my .bashrc file
DDI Assistant: [reads and displays .bashrc]

You: Search for all config files
DDI Assistant: [finds *.conf, *.cfg, etc.]
```

### System Information
```
You: What's my system uptime?
DDI Assistant: [runs uptime command]

You: Check disk usage
DDI Assistant: [runs df -h]

You: What date is it?
DDI Assistant: [gets current date from system]
```

## 🔧 Technical Details

### Tools Available

1. **web_search** - DuckDuckGo search
   - Free, no API key needed
   - Returns up to 5 results with titles, URLs, snippets
   - Use for current information

2. **fetch_webpage** - Read specific URLs
   - Extracts text content from web pages
   - Removes ads, scripts, styling
   - Truncates long pages

3. **search_files** - Find files by pattern
   - Supports wildcards (*, ?)
   - Recursive directory search
   - Returns up to 50 results

4. **read_file** - Read file contents
   - Works with text files
   - Truncates very long files
   - Good for config files, code, logs

5. **execute_command** - Run shell commands
   - 10 second timeout
   - Captures output
   - Use for safe, simple commands

6. **get_current_datetime** - System clock
   - Current date and time
   - Day of week
   - Formatted output

## 💡 Pro Tips

### For Best Results

1. **Be specific** - "Search for Python 3.10 release notes" is better than "search Python"

2. **Combine tools** - "Search for Red Hat tutorials, then read the first result"

3. **Context matters** - DDI Assistant remembers your conversation

4. **File paths** - Use absolute paths (/home/user/file.txt) or relative (./file.txt)

### What Works Great

✅ **Current events** - "What's happening in tech news today?"
✅ **Documentation** - "Find Python datetime documentation"
✅ **Troubleshooting** - "Search for solution to SSH connection refused"
✅ **Research** - "What's the best way to backup PostgreSQL?"
✅ **Code help** - "Find examples of Flask authentication"

### Limitations

⚠️ **No file writing** - Use `agent` for creating/modifying files
⚠️ **Simple commands** - Complex or long-running commands may timeout
⚠️ **Text only** - Can't process images or videos from web pages
⚠️ **Rate limits** - DuckDuckGo may rate limit excessive searches

## 🆚 Chat vs Agent

### Use `chat` (DDI Assistant) when:
- ✅ You need current information from the web
- ✅ You want to research topics
- ✅ You need to read files
- ✅ You want system information
- ❌ You DON'T need to write/create files

### Use `agent` when:
- ✅ You need to write/create files
- ✅ You want file operations with permission prompts
- ✅ You're building projects
- ✅ You need more control over commands

## 🎯 Common Workflows

### Research & Development
```
You: Search for Python asyncio best practices
DDI Assistant: [finds articles]

You: Read the top result
DDI Assistant: [fetches and summarizes]

You: Now search for asyncio examples
DDI Assistant: [finds code examples]
```

### System Administration
```
You: What's my disk usage?
DDI Assistant: [runs df -h]

You: Find all log files in /var/log
DDI Assistant: [searches for *.log]

You: Read the latest syslog entries
DDI Assistant: [reads file]
```

### Learning & Documentation
```
You: Search for RHEL 7.9 networking guide
DDI Assistant: [finds guides]

You: Explain what's in my network config
DDI Assistant: [reads and explains config files]
```

## 🔒 Privacy & Safety

### What's Sent to the Internet:
- ✅ Web search queries (to DuckDuckGo)
- ✅ URLs you ask to fetch
- ✅ Your questions to Claude (Anthropic API)

### What Stays Local:
- ✅ File contents (unless you ask to search web about them)
- ✅ Command outputs
- ✅ System information

### Best Practices:
- 🔐 Don't paste sensitive data in web searches
- 🔐 Be careful searching for private information
- 🔐 Review file contents before asking about them online

## 🐛 Troubleshooting

### "Web search not available"
**Solution:** Packages not installed
```bash
pip install --user duckduckgo-search requests beautifulsoup4
```

### Search returns no results
**Solution:** Try different search terms or check internet connection
```bash
ping -c 3 google.com
```

### "Permission denied" reading files
**Solution:** Check file permissions
```bash
ls -l filename
chmod +r filename
```

### Command timeout
**Solution:** Use simpler commands or increase timeout in the script

## 📚 Examples by Category

### Current Events
- "What's the latest news about [topic]?"
- "What happened today in [location]?"
- "Search for recent updates on [subject]"

### Technical Help
- "Search for how to [task]"
- "Find documentation for [technology]"
- "Look up error: [error message]"

### System Tasks
- "What files are in [directory]?"
- "Show me the content of [file]"
- "Check my system [resource]"

### Research
- "Compare [A] vs [B]"
- "What are the best practices for [topic]?"
- "Find tutorials about [subject]"

## 🎓 Getting Started

1. **Start the chat:**
   ```bash
   source ~/.bashrc
   chat
   ```

2. **Try a web search:**
   ```
   You: Search for today's date
   ```

3. **Read a file:**
   ```
   You: Show me my .bashrc file
   ```

4. **Get system info:**
   ```
   You: What's my system uptime?
   ```

5. **Fetch a webpage:**
   ```
   You: Read https://www.example.com
   ```

## 🚀 Advanced Usage

### Chain Multiple Tools
```
You: Search for the latest Python version, then read its release notes from the official site
```

### Analyze Local and Web Data
```
You: Find all my Python scripts, then search for best practices for the functions I'm using
```

### Research with Context
```
You: I'm learning Flask. Search for tutorials, explain the concepts, and help me understand my flask_app.py file
```

## 📝 Notes

- All web searches use DuckDuckGo (free, no API key)
- File operations are read-only (use `agent` for writing)
- Commands run with 10-second timeout
- Web pages are truncated to 5000 characters
- File contents truncated to 10,000 characters

## 🎉 You're All Set!

Your DDI Assistant can now:
- 🌐 Search the web for current information
- 📄 Read web pages and analyze content
- 📁 Search and read files on your system
- 💻 Execute commands and get system info
- 🧠 Remember conversation context
- 💬 Maintain natural conversation flow

**Just start chatting and explore the capabilities!**

---

*For file creation/modification, use `agent` instead of `chat`*
