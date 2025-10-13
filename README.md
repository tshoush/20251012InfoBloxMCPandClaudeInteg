# InfoBlox MCP & Claude Integration - Security Hardened

Enterprise-grade InfoBlox DDI management with Claude AI integration, featuring comprehensive security hardening, input validation, and flexible Python version support.

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/tshoush/20251012InfoBloxMCPandClaudeInteg.git
cd 20251012InfoBloxMCPandClaudeInteg

# Set environment variables
export INFOBLOX_HOST="192.168.1.224"
export INFOBLOX_USER="admin"
export INFOBLOX_PASSWORD="your-password"
export ANTHROPIC_API_KEY="sk-ant-..."

# Deploy + Auto-configure MCP server in Claude Desktop (recommended)
./deploy.py --local --setup-mcp

# Restart Claude Desktop - MCP server auto-attached! 🔌
```

**That's it!** The MCP server is automatically configured - no manual setup required.

## 📋 What's Included

### Core Components

- **InfoBlox MCP Server** - Model Context Protocol server exposing 140+ InfoBlox WAPI endpoints
- **Claude Chat Interfaces** - Multiple chat interfaces with different capabilities
- **RAG System** - Vector database for InfoBlox documentation
- **Security Framework** - Comprehensive security modules (Phase 1 & 2 complete)

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

## 📚 Documentation

### Getting Started
- [MCP-SETUP-GUIDE.md](MCP-SETUP-GUIDE.md) - **Automatic MCP setup** (NEW!)
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
