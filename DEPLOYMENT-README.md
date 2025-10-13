# RedHat System Deployment Guide

## Overview

This guide explains how to deploy and test the REDHAT project security modules on your RedHat system (192.168.1.200).

## Package Contents

The deployment package (`redhat-deployment-*.tar.gz`) contains:

- **Security Modules:**
  - `config.py` - Centralized configuration management
  - `validators.py` - Input validation and security checks
  - `logging_config.py` - Structured logging framework

- **Test Framework:**
  - `tests/` directory with 83 unit tests
  - `pytest.ini` - Test configuration
  - `conftest.py` - Test fixtures

- **Setup Scripts:**
  - `setup-redhat.sh` - Automated setup on RedHat
  - `run-tests.sh` - Run test suite with coverage

- **Configuration:**
  - `.env.example` - Environment variable template
  - `requirements.txt` - Python dependencies

## Deployment Methods

### Method 1: Automated SCP Transfer (Recommended if SSH works)

```bash
# From your Mac, run:
scp /Users/tshoush/REDHAT/redhat-deployment-*.tar.gz tshoush@192.168.1.200:~/

# Then SSH to RedHat and extract:
ssh tshoush@192.168.1.200
mkdir -p ~/REDHAT
cd ~/REDHAT
tar -xzf ~/redhat-deployment-*.tar.gz
./setup-redhat.sh
```

### Method 2: Manual Transfer via USB/Network Share

1. Copy the tarball to USB drive or network share:
   ```bash
   cp /Users/tshoush/REDHAT/redhat-deployment-*.tar.gz /path/to/usb/
   ```

2. On RedHat system, extract:
   ```bash
   mkdir -p ~/REDHAT
   cd ~/REDHAT
   tar -xzf /path/to/redhat-deployment-*.tar.gz
   ./setup-redhat.sh
   ```

### Method 3: Using rsync (if available)

```bash
rsync -avz /Users/tshoush/REDHAT/redhat-deployment-*.tar.gz tshoush@192.168.1.200:~/
```

## Setup on RedHat System

Once the files are transferred, run these commands on the RedHat system:

```bash
cd ~/REDHAT

# 1. Run automated setup
chmod +x setup-redhat.sh
./setup-redhat.sh

# This will:
# - Check Python version (requires 3.9+)
# - Create virtual environment
# - Install pytest, pytest-cov, and other dependencies
# - Create .env template
```

## Configuration

### Edit Environment Variables

```bash
nano .env
```

Add your credentials:
```bash
# InfoBlox Configuration
INFOBLOX_HOST=your-infoblox-host.example.com
INFOBLOX_USER=your-username
INFOBLOX_PASSWORD=your-password

# Anthropic API Key
ANTHROPIC_API_KEY=your-anthropic-api-key

# SSL Configuration (RECOMMENDED: true)
INFOBLOX_VERIFY_SSL=true

# Optional: Custom CA bundle
# INFOBLOX_CA_BUNDLE=/path/to/ca-bundle.pem

# WAPI Version
WAPI_VERSION=v2.13.1

# RAG Database Path
RAG_DB_PATH=~/.infoblox-rag

# Logging
LOG_LEVEL=INFO
```

**IMPORTANT SECURITY NOTES:**
- Never commit `.env` file to git
- Keep credentials secure
- Enable SSL verification in production (INFOBLOX_VERIFY_SSL=true)

## Running Tests

### Run Complete Test Suite

```bash
cd ~/REDHAT
source venv/bin/activate
./run-tests.sh
```

This will:
- Run all 83 unit tests
- Generate coverage reports
- Display test results

### Run Specific Test Files

```bash
# Test config module only
pytest tests/test_config.py -v

# Test validators only
pytest tests/test_validators.py -v

# Run security tests only
pytest tests/ -v -m security
```

### Run with Verbose Output

```bash
pytest tests/ -vv --tb=long
```

## Expected Test Results

When tests run successfully, you should see:

```
================================ test session starts =================================
platform linux -- Python 3.x.x, pytest-8.x.x
collected 83 items

tests/test_config.py::TestSettingsInitialization::... PASSED                 [  1%]
tests/test_config.py::TestSettingsDefaults::... PASSED                       [ 12%]
...
tests/test_validators.py::TestSecurityValidation::... PASSED                 [100%]

================================ 83 passed in 0.xx s =================================
```

### Coverage Report

After running tests, view the coverage report:

```bash
# Terminal report
cat coverage.xml

# HTML report (recommended)
python -m http.server 8000 --directory htmlcov
```

Then open in browser: `http://192.168.1.200:8000`

**Expected Coverage:**
- `config.py`: ~87% coverage
- `validators.py`: ~74% coverage
- Test files: ~99% coverage

## Troubleshooting

### Python Version Issues

If Python 3.9+ is not available:

```bash
# Check Python version
python3 --version

# Install Python 3.9+ (if needed on RedHat)
sudo dnf install python39
python3.9 -m venv venv
```

### Permission Issues

```bash
# Make scripts executable
chmod +x setup-redhat.sh run-tests.sh
```

### Missing Dependencies

```bash
# Activate venv and reinstall
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Environment Variable Errors

If tests fail with "ConfigurationError: Missing required environment variables":

```bash
# Option 1: Create .env file
cp .env.example .env
nano .env  # Add your credentials

# Option 2: Export variables manually
export INFOBLOX_HOST="test.infoblox.local"
export INFOBLOX_USER="testuser"
export INFOBLOX_PASSWORD="testpass"
export ANTHROPIC_API_KEY="sk-test-key"
```

## Verification Checklist

After deployment, verify:

- [ ] Python 3.9+ is installed
- [ ] Virtual environment created (`venv/` directory exists)
- [ ] Dependencies installed (`pip list` shows pytest, pytest-cov)
- [ ] .env file configured with credentials
- [ ] All 83 tests pass
- [ ] Coverage reports generated (`htmlcov/` directory)
- [ ] Security validations working (command injection blocked, etc.)

## Next Steps After Testing

Once tests pass on RedHat:

1. **Integrate security modules** into existing code:
   - Follow `SECURITY-FIXES-MIGRATION-GUIDE.md`
   - Update `infoblox-mcp-server.py` to use validators
   - Update all scripts to use config.py

2. **Set up continuous testing:**
   - Add pytest to CI/CD pipeline
   - Run tests before deployment
   - Monitor coverage trends

3. **Production deployment:**
   - Review security recommendations
   - Enable SSL verification
   - Set up log rotation
   - Configure security audit logging

## Support

For issues or questions:
- Check `SECURITY-FIXES-MIGRATION-GUIDE.md` for integration help
- Review `RECOMMENDATIONS-SUMMARY.md` for security best practices
- Check test output for specific error messages

## Package Information

- **Created:** 2025-10-12
- **Package Size:** ~28KB
- **Tests Included:** 83 unit tests
- **Coverage:** 74-87% for security modules
- **Python Required:** 3.9+
- **Dependencies:** pytest, pytest-cov, requests, anthropic, chromadb

## File Manifest

```
REDHAT/
├── config.py                    # Configuration management
├── validators.py                # Input validation
├── logging_config.py            # Logging framework
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # Test fixtures
│   ├── test_config.py          # Config tests (27 tests)
│   └── test_validators.py      # Validator tests (56 tests)
├── pytest.ini                   # Pytest configuration
├── requirements.txt             # Python dependencies
├── .env.example                # Environment template
├── .gitignore                  # Git ignore rules
├── setup-redhat.sh             # Setup script
├── run-tests.sh                # Test runner script
└── *.md                        # Documentation files
```
