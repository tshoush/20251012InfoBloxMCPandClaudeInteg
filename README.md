# InfoBlox MCP & Claude Integration - Security Hardened

Enterprise-grade InfoBlox DDI management with Claude AI integration, featuring comprehensive security hardening, input validation, and flexible Python version support.

## 🚀 Quick Start

### One Command Setup (Recommended) 🌟

```bash
# Clone the repository
git clone https://github.com/tshoush/20251012InfoBloxMCPandClaudeInteg.git
cd 20251012InfoBloxMCPandClaudeInteg

# Run master setup script - does everything!
./setup.py
```

**That's it!** The master setup script will:
- ✅ Guide you through configuration (InfoBlox + Claude credentials)
- ✅ Create Python virtual environment
- ✅ Install all dependencies
- ✅ Configure MCP server in Claude Desktop (macOS only)
- ✅ Build RAG knowledge base (optional)
- ✅ Run tests to verify installation
- ✅ Save configuration to .env file

**Total setup time: 3-5 minutes**

### Quick Options

```bash
# Quick setup (skip optional components)
./setup.py --quick

# Setup without tests
./setup.py --no-tests

# Setup without MCP server (for RHEL/Linux)
./setup.py --no-mcp
```

### Manual Setup (Alternative)

If you prefer manual control:

```bash
# 1. Configure credentials
python claude-chat-rag.py  # Will prompt for configuration

# 2. (Optional) Set up MCP server for Claude Desktop
./setup-mcp.py

# 3. (Optional) Build RAG knowledge base
python infoblox-rag-builder.py
```

## 📋 What's Included

### Core Components

- **InfoBlox MCP Server** - Model Context Protocol server exposing 140+ InfoBlox WAPI endpoints
- **Claude Chat Interfaces** - Multiple chat interfaces with different capabilities
- **Interactive Configuration** - Auto-prompts for missing settings, saves to .env (NEW! 🆕)
- **API Confirmation System** - User-controlled API execution with preview & edit capability (NEW!)
- **RAG System** - Vector database for InfoBlox documentation
- **Security Framework** - Comprehensive security modules (Phase 1 & 2 complete)

### Interactive Configuration (NEW! 🆕)

No environment variables? No problem! Just run any chat interface and it will guide you through setup:

```
══════════════════════════════════════════════════════════════════
               🔧 Configuration Setup
══════════════════════════════════════════════════════════════════

This script requires environment variables to connect to InfoBlox
and Claude AI. Let's set them up!

InfoBlox Configuration
──────────────────────────────────────────────────────────────────

  Hostname or IP address of your InfoBlox server
InfoBlox Host [192.168.1.224]:

  Username for InfoBlox authentication
InfoBlox Username [admin]:

  Password for InfoBlox authentication
InfoBlox Password: ●●●●●●●●

...

Save configuration to .env file? (yes/no) [yes]:
✓ Configuration saved to: /path/to/.env
✓ Environment variables set for current session
✓ Setup complete! You can now use the chat interfaces.
```

**Features:**
- ✅ **Auto-detects missing settings** - Prompts only for what's needed
- ✅ **Secure password entry** - Password masked during input
- ✅ **Smart defaults** - Press Enter to accept suggested values
- ✅ **Saves to .env** - Optionally saves configuration for reuse
- ✅ **File permissions** - Sets .env to 600 (owner read/write only)
- ✅ **Backup existing** - Creates .env.backup before overwriting

### API Confirmation System (NEW!) ✨

Before any InfoBlox API call executes, users see:

```
┌─────────────────────────────────────────────────────────────┐
│ 🔍 API Call Preview                                          │
├─────────────────────────────────────────────────────────────┤
│ List networks from InfoBlox                                  │
│                                                              │
│ Method:     GET                                              │
│ Endpoint:   /wapi/v2.13.1/network                           │
│ Username:   admin                                            │
│ Parameters:                                                  │
│   • _max_results: 100                                       │
│                                                              │
│ Curl Equivalent:                                            │
│ curl -X GET -u admin:$INFOBLOX_PASSWORD \                   │
│   'https://192.168.1.224/wapi/v2.13.1/network?...'          │
└─────────────────────────────────────────────────────────────┘

Execute? (yes/no/edit) [yes]:
```

**Features:**
- ✅ **Full visibility** - See exact API call before execution
- ✅ **Edit capability** - Modify parameters and username
- ✅ **Cancel anytime** - Abort unwanted operations
- ✅ **Curl equivalent** - Copy/paste for manual execution
- ✅ **Security** - Password never displayed (shows $INFOBLOX_PASSWORD)
- ✅ **Best-effort parsing** - Extracts values from natural language prompts

See [API-CONFIRMATION-GUIDE.md](API-CONFIRMATION-GUIDE.md) for complete documentation.

### Security Features (Phase 1 & 2) ✅

- ✅ **Zero hardcoded credentials** - All credentials from environment variables
- ✅ **Input validation** - Command injection, SQL injection, XSS prevention
- ✅ **Configurable SSL** - Support for custom CA bundles
- ✅ **Structured logging** - Application + security audit logs
- ✅ **Rate limiting** - 3 requests/second to InfoBlox API
- ✅ **Retry logic** - Exponential backoff for reliability
- ✅ **Security audit trail** - All sensitive operations logged

## 🐍 Python Version Support

**Default:** Python 3.8.13 (RHEL 7.9 compatible)
**Supported:** Python 3.8 through 3.12

```bash
# List available Python versions
./deploy.py --list-python

# Use Python 3.11
./deploy.py --local --python-version 3.11

# Use specific Python executable
./deploy.py --local --python-exec /opt/python3.11/bin/python3
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment guide.

## 📊 Test Results

| Platform | Python | Tests | Coverage | Status |
|----------|--------|-------|----------|--------|
| **RHEL 7.9** | 3.8.13 | 100/102 | 30% | ✅ Production Ready |
| **macOS** | 3.12.7 | 102/102 | 26% | ✅ Development Ready |

## 🔧 Configuration

All configuration via environment variables (no hardcoded values):

```bash
# InfoBlox Configuration
export INFOBLOX_HOST="192.168.1.224"
export INFOBLOX_USER="admin"
export INFOBLOX_PASSWORD="your-password"
export WAPI_VERSION="v2.13.1"
export INFOBLOX_VERIFY_SSL="false"  # or path to CA bundle

# Claude API
export ANTHROPIC_API_KEY="sk-ant-..."

# Logging
export LOG_LEVEL="INFO"  # DEBUG, INFO, WARNING, ERROR

# Optional
export INFOBLOX_CA_BUNDLE="/path/to/ca-bundle.crt"
export RAG_DB_PATH="~/.infoblox-rag"
```

## 🛠️ Available Tools

### Chat Interfaces

```bash
# RAG-enhanced chat (recommended)
python claude-chat-rag.py

# InfoBlox-focused chat
python claude-chat-infoblox.py

# MCP-based chat (most powerful)
python claude-chat-mcp.py
```

### Utility Scripts

```bash
# Build RAG knowledge base
python infoblox-rag-builder.py

# Explore InfoBlox WAPI
python infoblox-explorer.py

# Run MCP server directly
python infoblox-mcp-server.py
```

## 🔌 MCP Server - Automatic Setup

**Zero manual configuration required!**

```bash
# Automatically configure MCP server in Claude Desktop
./setup-mcp.py

# Or combined with deployment
./deploy.py --local --setup-mcp
```

The script automatically:
- ✅ Detects Claude Desktop installation
- ✅ Configures InfoBlox MCP server
- ✅ Sets up environment variables
- ✅ Tests connection

**Result:** InfoBlox MCP server appears in Claude Desktop's 🔌 menu - no manual config needed!

See [MCP-SETUP-GUIDE.md](MCP-SETUP-GUIDE.md) for details.

## 🏗️ How It All Works Together

```
User: "Show me networks in 192.168.1.0/24"
    ↓
Natural Language → Claude LLM (analyzes intent, extracts parameters)
    ↓
Claude selects tool → infoblox_list_networks
    ↓
API Confirmation System (shows preview with curl equivalent)
    ↓
User confirms → yes
    ↓
InfoBlox WAPI Call → GET /wapi/v2.13.1/network
    ↓
Results returned to user
```

**Complete pipeline:**
1. **Natural Language Input** - User types query in plain English
2. **Claude LLM Processing** - AI extracts intent and parameters
3. **MCP Tool Selection** - Structured tool call generated
4. **API Confirmation** - User sees preview, can edit, cancel, or confirm
5. **WAPI Execution** - Secure REST API call to InfoBlox
6. **Results Display** - Formatted response to user

See [ARCHITECTURE-FLOW.md](ARCHITECTURE-FLOW.md) for complete technical details.

## 📚 Documentation

### Getting Started
- [demo.html](demo.html) - **Interactive presentation** - Open in browser! (NEW! 🌟)
- [ARCHITECTURE-FLOW.md](ARCHITECTURE-FLOW.md) - **How everything works together** (NEW! 🌟)
- [MCP-SETUP-GUIDE.md](MCP-SETUP-GUIDE.md) - **Automatic MCP setup** (NEW!)
- [API-CONFIRMATION-GUIDE.md](API-CONFIRMATION-GUIDE.md) - **API confirmation system** (NEW!)
- [DEPLOYMENT.md](DEPLOYMENT.md) - Deployment guide with Python version options
- [DDI-ASSISTANT-GUIDE.md](DDI-ASSISTANT-GUIDE.md) - Using the DDI Assistant
- [RAG-SYSTEM-GUIDE.md](RAG-SYSTEM-GUIDE.md) - RAG system overview

### Architecture & Design
- [ARCHITECTURE-DOCUMENTATION.md](ARCHITECTURE-DOCUMENTATION.md) - System architecture
- [PRODUCT-REQUIREMENTS-DOCUMENT.md](PRODUCT-REQUIREMENTS-DOCUMENT.md) - Requirements
- [INFOBLOX-MCP-README.md](INFOBLOX-MCP-README.md) - MCP server details

### Security & Testing
- [SECURITY-REVIEW-REPORT.md](SECURITY-REVIEW-REPORT.md) - Security audit results
- [CODE-REVIEW-REPORT.md](CODE-REVIEW-REPORT.md) - Code quality review
- [REDHAT-7.9-TESTING-GUIDE.md](REDHAT-7.9-TESTING-GUIDE.md) - RHEL testing guide

### Project Status
- [PHASE2-COMPLETE.md](PHASE2-COMPLETE.md) - Phase 2 completion summary
- [RECOMMENDATIONS-SUMMARY.md](RECOMMENDATIONS-SUMMARY.md) - Improvement recommendations

## 🏗️ Project Phases

### ✅ Phase 1: Security Foundation (Complete)
- Security configuration management (`config.py`)
- Input validation (`validators.py`)
- Structured logging (`logging_config.py`)
- 83 unit tests passing
- 79% code coverage

### ✅ Phase 2: Integration & Reliability (Complete)
- Migrated all 6 production files to security modules
- Added rate limiting and retry logic
- Command injection prevention
- 102 total tests passing
- Production-ready on RHEL 7.9

### 🔜 Phase 3: Advanced Features (Planned)
- Metrics and monitoring
- Performance optimization
- Advanced caching

### 🔜 Phase 4: Production Hardening (Planned)
- Production deployment guide
- Disaster recovery procedures
- Performance tuning

## 🔒 Security Highlights

### Before Phase 2 (Insecure)
```python
# ❌ INSECURE - Hardcoded credentials
INFOBLOX_HOST = "192.168.1.224"
INFOBLOX_PASSWORD = "infoblox"

# ❌ INSECURE - SSL warnings suppressed
requests.packages.urllib3.disable_warnings()

# ❌ INSECURE - No SSL verification
session.verify = False
```

### After Phase 2 (Secure) ✅
```python
# ✅ SECURE - Credentials from environment
settings = get_settings()
session.auth = (settings.infoblox_user, settings.infoblox_password)

# ✅ SECURE - Configurable SSL with warnings
session.verify = settings.get_ssl_verify()
settings.display_security_warning()

# ✅ SECURE - Input validation
InputValidator.validate_shell_command(command)

# ✅ SECURE - Rate limiting & retry logic
@sleep_and_retry
@limits(calls=3, period=1)
@retry(stop=stop_after_attempt(3))
def api_call(...):
    ...
```

## 🧪 Testing

```bash
# Run all tests
./deploy.py --local

# Run specific test suite
./deploy.py --local --test-suite phase2

# Run tests without coverage
./deploy.py --local --no-coverage

# Deploy without running tests
./deploy.py --local --no-tests
```

## 🤝 Contributing

This is an enterprise security project. Key principles:
- ✅ No hardcoded credentials
- ✅ All inputs validated
- ✅ Comprehensive logging
- ✅ Security-first design
- ✅ 100% test coverage for security modules

## 📝 License

Enterprise internal project.

## 🆘 Support

- GitHub Issues: [Issues Page](https://github.com/tshoush/20251012InfoBloxMCPandClaudeInteg/issues)
- Documentation: See `/docs` folder
- Deployment Help: See [DEPLOYMENT.md](DEPLOYMENT.md)

## 🎯 Key Achievements

✅ **140+ InfoBlox WAPI endpoints** exposed via MCP
✅ **Zero hardcoded credentials** across all files
✅ **100/102 tests passing** on production RHEL 7.9
✅ **Flexible Python support** (3.8 through 3.12)
✅ **Enterprise-grade security** - validated and tested
✅ **Production-ready** - deployed and validated

---

**Last Updated:** October 13, 2025
**Status:** Production Ready ✅
**Phase:** Phase 2 Complete
**Python:** 3.8.13+ (3.8.13 recommended for RHEL 7.9)
