# MCP Server Automatic Setup Guide

## TL;DR - One Command Setup

```bash
# Automatically configure MCP server in Claude Desktop
./setup-mcp.py
```

That's it! The MCP server will be automatically attached to Claude Desktop. No manual configuration needed.

## What This Does

The `setup-mcp.py` script automatically:

1. ✅ Detects your Claude Desktop installation
2. ✅ Finds the configuration file for your OS
3. ✅ Configures the InfoBlox MCP server
4. ✅ Sets up environment variables
5. ✅ Tests the server connection
6. ✅ No manual editing required!

## Quick Start

### Option 1: Standalone MCP Setup

```bash
# Interactive setup (asks for confirmation)
./setup-mcp.py

# Automatic setup (no prompts)
./setup-mcp.py --yes
```

### Option 2: Deploy + MCP Setup (Recommended)

```bash
# Deploy and configure MCP in one step
./deploy.py --local --setup-mcp
```

### Option 3: Check Status

```bash
# See if MCP server is configured
./setup-mcp.py --status
```

## Prerequisites

### 1. Environment Variables Required

Set these in `.env` file or your shell:

```bash
# Required
export INFOBLOX_HOST="192.168.1.224"
export INFOBLOX_USER="admin"
export INFOBLOX_PASSWORD="your-password"
export ANTHROPIC_API_KEY="sk-ant-..."

# Optional
export WAPI_VERSION="v2.13.1"
export INFOBLOX_VERIFY_SSL="false"
export LOG_LEVEL="INFO"
```

**Using .env file (Recommended):**

```bash
# Create .env file in project directory
cat > .env << 'EOF'
INFOBLOX_HOST=192.168.1.224
INFOBLOX_USER=admin
INFOBLOX_PASSWORD=your-password
ANTHROPIC_API_KEY=sk-ant-...
WAPI_VERSION=v2.13.1
INFOBLOX_VERIFY_SSL=false
LOG_LEVEL=INFO
EOF
```

### 2. Claude Desktop Installed

- Download from: https://claude.ai/download
- Installed and running (doesn't need to be open during setup)

### 3. Python Virtual Environment (Optional but Recommended)

```bash
# Create and activate venv
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install pytest pytest-cov
```

## Configuration Locations

The script automatically finds and configures:

| Platform | Config File Location |
|----------|---------------------|
| **macOS** | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| **Windows** | `%APPDATA%/Claude/claude_desktop_config.json` |
| **Linux** | `~/.config/Claude/claude_desktop_config.json` |

## What Gets Configured

The script adds this to your Claude Desktop config:

```json
{
  "mcpServers": {
    "infoblox": {
      "command": "/path/to/python",
      "args": ["/path/to/infoblox-mcp-server.py"],
      "env": {
        "INFOBLOX_HOST": "192.168.1.224",
        "INFOBLOX_USER": "admin",
        "INFOBLOX_PASSWORD": "your-password",
        "ANTHROPIC_API_KEY": "sk-ant-...",
        "WAPI_VERSION": "v2.13.1",
        "INFOBLOX_VERIFY_SSL": "false",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

**Note:** Your existing config is preserved - this only adds/updates the InfoBlox server.

## Complete Workflow

### For New Users (First Time)

```bash
# 1. Clone the repository
git clone https://github.com/tshoush/20251012InfoBloxMCPandClaudeInteg.git
cd 20251012InfoBloxMCPandClaudeInteg

# 2. Set environment variables
export INFOBLOX_HOST="192.168.1.224"
export INFOBLOX_USER="admin"
export INFOBLOX_PASSWORD="your-password"
export ANTHROPIC_API_KEY="sk-ant-..."

# 3. Deploy + configure MCP (all in one)
./deploy.py --local --setup-mcp

# 4. Restart Claude Desktop
# Look for 🔌 icon - InfoBlox should be connected!
```

### For Existing Users (Update MCP Config)

```bash
# Just reconfigure MCP server
./setup-mcp.py

# Or remove and reconfigure
./setup-mcp.py --remove
./setup-mcp.py
```

## Verification

### 1. Check Configuration Status

```bash
./setup-mcp.py --status
```

**Expected output:**
```
================================================================================
MCP SERVER STATUS
================================================================================

✓ InfoBlox MCP server is configured

Command: /path/to/python
Script: /path/to/infoblox-mcp-server.py
Environment variables: 7 configured

To apply changes:
  1. Restart Claude Desktop
  2. Check for 🔌 MCP icon
```

### 2. Check Claude Desktop

1. **Restart Claude Desktop** (important!)
2. Look for **🔌 icon** in the bottom-right or toolbar
3. Click it to see connected MCP servers
4. **"infoblox"** should appear as connected
5. Status should be **green/active**

### 3. Test with Claude

In Claude Desktop, try:

```
Can you list all InfoBlox networks?
```

or

```
What InfoBlox tools are available?
```

Claude should now have access to 140+ InfoBlox WAPI endpoints!

## Troubleshooting

### MCP Server Not Appearing

**Problem:** 🔌 icon not showing or InfoBlox not listed

**Solution:**
```bash
# 1. Verify configuration
./setup-mcp.py --status

# 2. Check environment variables
cat .env

# 3. Restart Claude Desktop completely
# (Quit and reopen, not just minimize)

# 4. Check Claude Desktop logs (if available)
# macOS: ~/Library/Logs/Claude/
```

### Missing Environment Variables

**Problem:** `⚠ Missing required environment variables`

**Solution:**
```bash
# Option A: Create .env file
cat > .env << 'EOF'
INFOBLOX_HOST=192.168.1.224
INFOBLOX_USER=admin
INFOBLOX_PASSWORD=your-password
ANTHROPIC_API_KEY=sk-ant-...
EOF

# Option B: Add to shell profile
echo 'export INFOBLOX_HOST="192.168.1.224"' >> ~/.bashrc
echo 'export INFOBLOX_USER="admin"' >> ~/.bashrc
echo 'export INFOBLOX_PASSWORD="your-password"' >> ~/.bashrc
echo 'export ANTHROPIC_API_KEY="sk-ant-..."' >> ~/.bashrc
source ~/.bashrc

# Then run setup again
./setup-mcp.py
```

### Python Not Found

**Problem:** `✗ Python 3 not found!`

**Solution:**
```bash
# Create virtual environment first
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install pytest pytest-cov

# Then run setup
./setup-mcp.py
```

### Config File Permissions

**Problem:** Permission denied writing config

**Solution:**
```bash
# Check permissions
ls -la ~/Library/Application\ Support/Claude/  # macOS
ls -la ~/.config/Claude/  # Linux

# Fix if needed
chmod 755 ~/Library/Application\ Support/Claude/  # macOS
chmod 644 ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

### Server Won't Start

**Problem:** MCP server configured but won't start

**Solution:**
```bash
# Test server manually
cd /path/to/project
source venv/bin/activate
python infoblox-mcp-server.py

# Check for errors in output
# Common issues:
# - Missing dependencies: pip install -r requirements.txt
# - Wrong Python version: use Python 3.8+
# - Missing environment variables
```

## Advanced Usage

### Multiple MCP Servers

You can have multiple MCP servers. The setup script only configures InfoBlox:

```json
{
  "mcpServers": {
    "infoblox": {
      "command": "/path/to/python",
      "args": ["/path/to/infoblox-mcp-server.py"],
      "env": {...}
    },
    "other-server": {
      "command": "...",
      "args": [...],
      "env": {...}
    }
  }
}
```

### Custom Python Path

The script auto-detects Python, but you can manually edit:

```bash
# Edit config file directly
code ~/Library/Application\ Support/Claude/claude_desktop_config.json

# Change "command" to your preferred Python:
"command": "/opt/python3.11/bin/python"
```

### Environment-Specific Configs

```bash
# Development
./setup-mcp.py  # Uses .env file

# Production (different host)
INFOBLOX_HOST=prod.infoblox.com ./setup-mcp.py
```

### Uninstall/Remove

```bash
# Remove InfoBlox MCP server
./setup-mcp.py --remove

# Restart Claude Desktop
# InfoBlox server will no longer appear
```

## Security Notes

### Environment Variables in Config

The setup script stores environment variables directly in Claude Desktop's config file. This means:

⚠️ **Passwords are stored in plaintext** in `claude_desktop_config.json`

**Recommendations:**
1. Use least-privilege InfoBlox accounts
2. Rotate passwords regularly
3. Keep config file permissions restricted (600)
4. Don't commit `claude_desktop_config.json` to git

**Future improvement:** Use keychain/credential manager

### SSL Verification

By default, the setup uses `INFOBLOX_VERIFY_SSL=false` for dev environments.

**For production:**
```bash
# Use SSL with CA bundle
export INFOBLOX_VERIFY_SSL=true
export INFOBLOX_CA_BUNDLE=/path/to/ca-bundle.crt

./setup-mcp.py
```

## Integration with Other Tools

### With deploy.py

```bash
# One-step deploy + MCP setup
./deploy.py --local --setup-mcp

# Deploy with specific Python version + MCP
./deploy.py --local --python-version 3.11 --setup-mcp
```

### CI/CD Pipeline

```bash
#!/bin/bash
# deploy.sh

# Set secrets from CI/CD environment
export INFOBLOX_HOST="$INFOBLOX_HOST_SECRET"
export INFOBLOX_USER="$INFOBLOX_USER_SECRET"
export INFOBLOX_PASSWORD="$INFOBLOX_PASSWORD_SECRET"
export ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY_SECRET"

# Deploy
./deploy.py --local --no-tests

# Configure MCP (optional - for dev machines only)
if [ "$SETUP_MCP" = "true" ]; then
    ./setup-mcp.py --yes
fi
```

## FAQ

**Q: Do I need to run setup every time?**
A: No, only once or when config changes.

**Q: Can I have multiple InfoBlox servers?**
A: Yes, manually edit config and use different server names.

**Q: Does this work with Claude Web?**
A: No, only Claude Desktop supports MCP servers.

**Q: What if Claude Desktop updates?**
A: Config is preserved across updates. May need to re-setup if format changes.

**Q: Can I automate this in a script?**
A: Yes! Use `./setup-mcp.py --yes` for non-interactive setup.

**Q: How do I update environment variables?**
A: Edit `.env` file and run `./setup-mcp.py` again.

## Summary

**Automatic MCP Setup = Zero Manual Configuration**

```bash
# One command does everything:
./setup-mcp.py

# Or combined with deployment:
./deploy.py --local --setup-mcp
```

No need to:
- ❌ Manually edit config files
- ❌ Find config file locations
- ❌ Copy/paste JSON
- ❌ Set up Python paths
- ❌ Configure environment variables manually

The script handles everything automatically! 🎉

---

**For more information:**
- Main README: [README.md](README.md)
- Deployment Guide: [DEPLOYMENT.md](DEPLOYMENT.md)
- MCP Server Details: [INFOBLOX-MCP-README.md](INFOBLOX-MCP-README.md)
