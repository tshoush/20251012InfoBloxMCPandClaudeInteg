# Claude CLI - Command Line Interface for Claude AI

Python-based CLI tools for interacting with Claude AI using the Anthropic API.

## Tools Available

1. **claude-cli.py** - One-shot command line tool (single question/answer)
2. **claude-chat.py** - Interactive chat interface (continuous conversation)

## Installation

The Claude CLI tools are already installed on your Red Hat 7.9 system with all required dependencies:
- ✅ Python 3.8.13
- ✅ Anthropic Python SDK 0.69.0

## Setup

### 1. Get Your Anthropic API Key

1. Visit https://console.anthropic.com/settings/keys
2. Log in to your Anthropic account (or create one)
3. Generate a new API key
4. Copy the API key

### 2. Set the API Key

Add your API key to your environment:

```bash
export ANTHROPIC_API_KEY='your-api-key-here'
```

To make it permanent, add it to your `~/.bashrc`:

```bash
echo 'export ANTHROPIC_API_KEY="your-api-key-here"' >> ~/.bashrc
source ~/.bashrc
```

## Usage

### One-Shot Mode (claude-cli.py)

For single questions/commands:

```bash
python ~/claude-cli.py "your question or prompt here"
```

### Interactive Chat Mode (claude-chat.py) - **RECOMMENDED**

For continuous conversations with context:

```bash
python ~/claude-chat.py
```

**Chat Commands:**
- Type your message and press Enter to chat
- Type `exit`, `quit`, or `bye` to end the chat
- Type `clear` to start a new conversation (clears history)
- Press Ctrl+C or Ctrl+D to exit

**Features:**
- 💬 Maintains conversation history (Claude remembers context)
- 🔄 Continuous chat without restarting
- 🧹 Clear command to reset conversation
- ⌨️ Simple, intuitive interface

### Examples (One-Shot Mode)

**Ask a simple question:**
```bash
./claude-cli.py "What is Python?"
```

**Get coding help:**
```bash
./claude-cli.py "Write a bash script to backup all .conf files to /backup directory"
```

**Explain complex topics:**
```bash
./claude-cli.py "Explain quantum computing in simple terms"
```

**Technical assistance:**
```bash
./claude-cli.py "How do I configure Apache on RHEL 7?"
```

**Code review:**
```bash
./claude-cli.py "Review this Python code: $(cat myscript.py)"
```

### Interactive Chat Example

```bash
$ python ~/claude-chat.py

================================================================================
Claude Sonnet 4.5 - Interactive Chat
================================================================================
Type your messages and press Enter. Type 'exit', 'quit', or 'bye' to end.
Type 'clear' to start a new conversation.
================================================================================

You: What is Python?

Claude: Python is a high-level, interpreted programming language known for its
simplicity and readability...

You: Can you write me a hello world example?

Claude: Certainly! Here's a simple "Hello World" program in Python:

```python
print("Hello, World!")
```

You: exit

Goodbye! 👋
```

## Features

- **Model:** Uses Claude Sonnet 4.5 (claude-sonnet-4-5-20250929) - The latest and most advanced Claude model
- **Max Tokens:** 4096 tokens per response
- **Simple Interface:** Just provide your prompt as a command-line argument
- **Error Handling:** Clear error messages if API key is missing or requests fail

## API Key Security

**Important Security Notes:**

1. **Never commit API keys to version control**
2. **Don't share your API key with others**
3. **Use environment variables instead of hardcoding keys**
4. **Rotate your API keys periodically**
5. **Set usage limits in the Anthropic Console**

## Troubleshooting

### Error: ANTHROPIC_API_KEY environment variable not set

**Solution:** Set your API key:
```bash
export ANTHROPIC_API_KEY='your-api-key-here'
```

### Error: API request failed

**Possible causes:**
- Invalid API key
- No internet connection
- Anthropic API is down
- API rate limit exceeded

**Solution:**
- Check your API key is correct
- Verify internet connectivity: `ping api.anthropic.com`
- Check Anthropic status: https://status.anthropic.com
- Review your usage limits in the Anthropic Console

### Permission denied when running

**Solution:** Make sure the script is executable:
```bash
chmod +x claude-cli.py
```

## Advanced Usage

### Create Aliases (Recommended)

For easier access, create aliases in your `~/.bashrc`:

```bash
# Add both aliases
echo 'alias claude="python ~/claude-cli.py"' >> ~/.bashrc
echo 'alias chat="python ~/claude-chat.py"' >> ~/.bashrc
source ~/.bashrc
```

Now you can use:
```bash
# One-shot mode
claude "your question here"

# Interactive chat mode (recommended)
chat
```

### Move to PATH

To use from anywhere:

```bash
sudo cp ~/claude-cli.py /usr/local/bin/claude
sudo chmod +x /usr/local/bin/claude
```

Then use:
```bash
claude "your question here"
```

### Pipe Input

You can also pipe content to Claude:

```bash
cat myfile.txt | xargs -0 ./claude-cli.py "Summarize this:"
```

## Model Information

**Claude Sonnet 4.5** (claude-sonnet-4-5-20250929):
- Latest and most advanced Claude model (released September 2025)
- Superior performance at coding, analysis, and complex reasoning
- 200K token context window
- Fast response times
- Best-in-class intelligence and capability

## API Costs

Claude API usage is billed by Anthropic. Check current pricing at:
https://www.anthropic.com/pricing

**Pricing for Claude Sonnet 4.5:**
- Check the Anthropic pricing page for the latest rates
- Pricing varies by model and usage volume
- Enterprise pricing available for high-volume usage

**Tip:** Set usage limits in the Anthropic Console to control costs.

## Additional Resources

- **Anthropic Documentation:** https://docs.anthropic.com
- **API Reference:** https://docs.anthropic.com/en/api
- **Python SDK:** https://github.com/anthropics/anthropic-sdk-python
- **Get API Key:** https://console.anthropic.com/settings/keys
- **Check Usage:** https://console.anthropic.com/settings/usage

## Limitations

- Requires internet connection
- Requires valid Anthropic API key
- Subject to Anthropic's rate limits and usage policies
- RHEL 7.9 compatible (uses Python 3.8)

## Files

- `~/claude-cli.py` - One-shot CLI script
- `~/claude-chat.py` - Interactive chat script
- `~/CLAUDE-CLI-README.md` - This documentation

## Support

For issues with:
- **Claude CLI script:** Check this README
- **Anthropic API:** Visit https://support.anthropic.com
- **API Keys:** Visit https://console.anthropic.com
