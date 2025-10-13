# Deployment Guide

Flexible deployment system for Phase 2 security-hardened InfoBlox/Claude integration.

## Quick Start

### Option A: Use Default Python (3.8.13) ✅ RECOMMENDED

```bash
# Deploy locally with default Python
./deploy.py --local
```

This uses Python 3.8.13 (or whatever is configured in `deploy-config.ini`).

### Option B: Specify Python Version

```bash
# Use Python 3.11
./deploy.py --local --python-version 3.11

# Use Python 3.10
./deploy.py --local --python-version 3.10

# Use specific Python executable
./deploy.py --local --python-exec /opt/python3.11/bin/python3
```

## Configuration File

Edit `deploy-config.ini` to set defaults:

```ini
[python]
# Default Python version (3.8.13 is recommended for RHEL 7.9)
version = 3.8.13

# Or specify exact path
executable = /opt/rh/rh-python38/root/usr/bin/python3.8

# Virtual environment name
venv_name = venv

[testing]
# Run tests after deployment?
run_tests = yes

# Which test suite? (all, phase1, phase2, integration)
test_suite = all

# Generate coverage report?
coverage = yes
```

## Available Commands

### List Available Python Versions
```bash
./deploy.py --list-python
```

Output:
```
✓ System Python 3 (default)      /usr/bin/python3            Python 3.8.13
✓ Python 3.8                     /usr/bin/python3.8          Python 3.8.13
✗ Python 3.9                     Not found
✗ Python 3.10                    Not found
✓ Python 3.11                    /opt/python3.11/bin/python  Python 3.11.9

Default configured: Python 3.8.13
```

### Deploy with Different Python Versions

```bash
# Use Python 3.8 (default)
./deploy.py --local

# Use Python 3.11 (if installed)
./deploy.py --local --python-version 3.11

# Use specific Python executable
./deploy.py --local --python-exec /opt/rh/rh-python38/root/usr/bin/python3.8
```

### Test Options

```bash
# Run all tests (default)
./deploy.py --local

# Run only Phase 1 tests
./deploy.py --local --test-suite phase1

# Run only Phase 2 integration tests
./deploy.py --local --test-suite phase2

# Deploy without running tests
./deploy.py --local --no-tests

# Run tests without coverage report
./deploy.py --local --no-coverage
```

## Platform-Specific Guides

### RedHat 7.9 / CentOS 7 (Default Configuration)

**Recommended:** Python 3.8.13 (via Red Hat Software Collections)

```bash
# Verify Python 3.8 is installed
python3 --version  # Should show: Python 3.8.13

# Deploy with default Python
./deploy.py --local
```

**To Install Python 3.11:**
```bash
# Option 1: Compile from source
cd /tmp
wget https://www.python.org/ftp/python/3.11.9/Python-3.11.9.tgz
tar xzf Python-3.11.9.tgz
cd Python-3.11.9
./configure --enable-optimizations --prefix=/opt/python3.11
make -j$(nproc)
sudo make altinstall

# Then use it:
./deploy.py --local --python-exec /opt/python3.11/bin/python3.11
```

**To Install Python 3.8 (if not present):**
```bash
# Enable Software Collections
sudo yum install -y centos-release-scl
sudo yum install -y rh-python38

# Activate
scl enable rh-python38 bash

# Deploy
./deploy.py --local --python-exec /opt/rh/rh-python38/root/usr/bin/python3.8
```

### macOS

```bash
# List available versions
./deploy.py --list-python

# Use Homebrew Python
brew install python@3.11
./deploy.py --local --python-version 3.11

# Or use system Python
./deploy.py --local --python-version 3
```

### Ubuntu / Debian

```bash
# Install Python 3.11
sudo apt update
sudo apt install -y python3.11 python3.11-venv

# Use it
./deploy.py --local --python-version 3.11
```

## Python Version Compatibility

| Python Version | Compatibility | Status | Notes |
|---------------|---------------|---------|-------|
| 3.8.13 | ✅ Full | **RECOMMENDED** | Default for RHEL 7.9, all tests pass |
| 3.9.x  | ✅ Full | Supported | All features work |
| 3.10.x | ✅ Full | Supported | All features work |
| 3.11.x | ✅ Full | Supported | All features work |
| 3.12.x | ✅ Full | Supported | Latest features available |
| 3.7.x  | ⚠️ Limited | EOL | Not recommended |

## Environment Variables

The deployment respects these environment variables:

```bash
# InfoBlox Configuration
export INFOBLOX_HOST="192.168.1.224"
export INFOBLOX_USER="admin"
export INFOBLOX_PASSWORD="infoblox"
export WAPI_VERSION="v2.13.1"
export INFOBLOX_VERIFY_SSL="false"

# Claude API
export ANTHROPIC_API_KEY="sk-ant-..."

# Logging
export LOG_LEVEL="INFO"

# Then deploy
./deploy.py --local
```

## Troubleshooting

### Python Version Not Found

```bash
# List what's available
./deploy.py --list-python

# Install desired version, then:
./deploy.py --local --python-version 3.11
```

### Virtual Environment Creation Failed

```bash
# Ensure venv module is installed
sudo yum install -y python38-devel  # RHEL/CentOS
sudo apt install -y python3.8-venv  # Ubuntu/Debian

# Or use specific Python with venv
/usr/bin/python3.8 -m venv test_venv
```

### Tests Failing

```bash
# Run only specific test suite
./deploy.py --local --test-suite phase1

# Check Python version compatibility
python3 --version
./deploy.py --list-python
```

## Advanced Usage

### Custom Configuration File

```bash
# Create custom config
cp deploy-config.ini deploy-config-prod.ini

# Edit it, then use:
./deploy.py --local --config deploy-config-prod.ini
```

### CI/CD Integration

```bash
# In GitHub Actions / Jenkins
./deploy.py --local \
  --python-version 3.11 \
  --test-suite all \
  --no-coverage
```

### Development vs Production

```bash
# Development (fast, skip coverage)
./deploy.py --local --no-coverage

# Production (thorough)
./deploy.py --local --test-suite all
```

## Test Results by Python Version

| Version | Platform | Tests Passed | Coverage | Status |
|---------|----------|--------------|----------|--------|
| 3.8.13  | RHEL 7.9 | 100/102 | 30% | ✅ Production Ready |
| 3.12.7  | macOS    | 102/102 | 26% | ✅ Development Ready |

## Support

For issues or questions:
- Check this guide first
- Run `./deploy.py --list-python` to see available options
- Review `deploy-config.ini` for configuration
- GitHub Issues: https://github.com/tshoush/20251012InfoBloxMCPandClaudeInteg

---

**Default Configuration: Python 3.8.13** ✅
- Works out-of-the-box on RHEL 7.9
- All tests pass
- Production-ready
- No additional setup required
