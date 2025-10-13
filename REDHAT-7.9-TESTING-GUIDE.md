# Testing on RedHat 7.9 - Step-by-Step Guide

## Prerequisites

- RedHat 7.9 system accessible at 192.168.1.200
- User account: tshoush
- Python 3.9+ (we'll verify/install this)
- Package file: `redhat-deployment-20251012-204302.tar.gz`

---

## Step 1: Transfer the Package to RedHat 7.9

### Option A: Using SCP (Recommended)

From your Mac terminal:

```bash
# Try with password prompt
scp /Users/tshoush/REDHAT/redhat-deployment-20251012-204302.tar.gz tshoush@192.168.1.200:~/

# If prompted, enter password
```

### Option B: Using USB Drive

```bash
# On Mac - Copy to USB
cp /Users/tshoush/REDHAT/redhat-deployment-20251012-204302.tar.gz /Volumes/[USB_NAME]/

# Then on RedHat 7.9 - Mount and copy
sudo mkdir -p /mnt/usb
sudo mount /dev/sdb1 /mnt/usb  # Adjust device name as needed
cp /mnt/usb/redhat-deployment-20251012-204302.tar.gz ~/
sudo umount /mnt/usb
```

### Option C: Using wget/curl (if you have a web server)

```bash
# On RedHat 7.9
cd ~
wget http://[YOUR_MAC_IP]:8000/redhat-deployment-20251012-204302.tar.gz

# Or with curl
curl -O http://[YOUR_MAC_IP]:8000/redhat-deployment-20251012-204302.tar.gz
```

---

## Step 2: SSH to RedHat 7.9 System

From your Mac:

```bash
ssh tshoush@192.168.1.200
```

Or use the console/terminal directly on the RedHat system.

---

## Step 3: Verify Package Transfer

```bash
# Check if file exists
ls -lh ~/redhat-deployment-*.tar.gz

# Should show:
# -rw-r--r-- 1 tshoush tshoush 27K [date] redhat-deployment-20251012-204302.tar.gz
```

---

## Step 4: Extract the Package

```bash
# Create directory
mkdir -p ~/REDHAT
cd ~/REDHAT

# Extract
tar -xzf ~/redhat-deployment-20251012-204302.tar.gz

# Verify extraction
ls -la

# Should see:
# config.py
# validators.py
# logging_config.py
# tests/
# setup-redhat.sh
# run-tests.sh
# requirements.txt
# .env.example
# etc.
```

---

## Step 5: Check Python Version (RedHat 7.9 Specific)

```bash
# Check default Python 3 version
python3 --version

# If Python 3.9+ is not available, install it:
```

### Install Python 3.9 on RedHat 7.9 (if needed)

```bash
# Enable Software Collections (SCL)
sudo yum install -y centos-release-scl

# Install Python 3.9
sudo yum install -y rh-python39

# Enable Python 3.9
scl enable rh-python39 bash

# Verify
python3 --version
# Should show: Python 3.9.x

# Alternative: Install from source or use EPEL
sudo yum install -y epel-release
sudo yum install -y python39
```

### If Python 3.9+ is Already Installed

```bash
# Just verify the version
python3 --version
# Or
python3.9 --version
```

---

## Step 6: Run the Setup Script

```bash
cd ~/REDHAT

# Make setup script executable
chmod +x setup-redhat.sh

# Run setup
./setup-redhat.sh
```

### What This Does:
1. ✅ Checks Python version (requires 3.9+)
2. ✅ Creates virtual environment (venv/)
3. ✅ Activates venv
4. ✅ Upgrades pip
5. ✅ Installs pytest, pytest-cov, and dependencies
6. ✅ Creates .env template

### Expected Output:

```
=========================================
Setting Up REDHAT Project on RedHat System
=========================================

[1/6] Checking Python version...
Python version: 3.9.x
✓ Python 3.9+ detected

[2/6] Creating virtual environment...
✓ Virtual environment created

[3/6] Activating virtual environment...

[4/6] Upgrading pip...

[5/6] Installing dependencies...
Successfully installed pytest-8.x.x pytest-cov-7.x.x ...

[6/6] Setting up environment variables...
⚠ Please edit .env file with your credentials

=========================================
Setup Complete!
=========================================
```

---

## Step 7: Configure Environment Variables

```bash
# Copy example to .env
cp .env.example .env

# Edit with your credentials
nano .env
# Or use vi if nano is not available:
vi .env
```

### Minimal Configuration for Testing:

```bash
# For unit tests (mock data - no real InfoBlox needed)
INFOBLOX_HOST=test.infoblox.local
INFOBLOX_USER=testuser
INFOBLOX_PASSWORD=testpass
ANTHROPIC_API_KEY=sk-test-key-12345
WAPI_VERSION=v2.13.1
INFOBLOX_VERIFY_SSL=false
```

**Save and exit:**
- nano: Ctrl+O, Enter, Ctrl+X
- vi: Press Esc, type `:wq`, Enter

---

## Step 8: Run the Tests

```bash
cd ~/REDHAT

# Activate virtual environment
source venv/bin/activate

# Your prompt should change to show (venv)

# Make run script executable
chmod +x run-tests.sh

# Run tests
./run-tests.sh
```

### Alternative: Run pytest directly

```bash
source venv/bin/activate
pytest tests/ -v
```

---

## Step 9: Verify Test Results

### Expected Output:

```
============================= test session starts ==============================
platform linux -- Python 3.9.x, pytest-8.x.x, pluggy-1.6.0
rootdir: /home/tshoush/REDHAT
configfile: pytest.ini
collected 83 items

tests/test_config.py::TestSettingsInitialization::test_settings_with_all_env_vars PASSED [  1%]
tests/test_config.py::TestSettingsInitialization::test_settings_without_required_vars PASSED [  2%]
...
tests/test_validators.py::TestSecurityValidation::test_command_injection_blocked PASSED [ 97%]
tests/test_validators.py::TestSecurityValidation::test_xss_blocked PASSED [ 98%]
tests/test_validators.py::TestSecurityValidation::test_path_traversal_blocked PASSED [100%]

================================ tests coverage ================================

Name                       Stmts   Miss  Cover   Missing
--------------------------------------------------------
config.py                     68      9    87%   169, 174-181
validators.py                185     48    74%   107, 169, 176, ...
tests/conftest.py             31      2    94%   32, 48
tests/test_config.py         154      1    99%   281
tests/test_validators.py     213      1    99%   408
--------------------------------------------------------
TOTAL                        651     61    91%

Coverage HTML written to dir htmlcov
Coverage XML written to file coverage.xml

============================== 83 passed in 0.xx s ===============================
```

### Success Criteria:
- ✅ **83 tests passed**
- ✅ **0 failed**
- ✅ Coverage: config.py 87%, validators.py 74%
- ✅ HTML coverage report generated

---

## Step 10: View Coverage Report (Optional)

### Option A: HTTP Server (if X11 or browser available)

```bash
cd ~/REDHAT
python3 -m http.server 8000 --directory htmlcov
```

Then from your Mac, open browser to: `http://192.168.1.200:8000`

### Option B: Copy to Mac and View

```bash
# On Mac terminal
scp -r tshoush@192.168.1.200:~/REDHAT/htmlcov /Users/tshoush/REDHAT/redhat-htmlcov
open /Users/tshoush/REDHAT/redhat-htmlcov/index.html
```

---

## Troubleshooting RedHat 7.9 Specific Issues

### Issue 1: Python 3.9 Not Available

```bash
# Install from EPEL
sudo yum install -y epel-release
sudo yum install -y python39 python39-devel

# Or use Software Collections
sudo yum install -y centos-release-scl
sudo yum install -y rh-python39
scl enable rh-python39 bash
```

### Issue 2: Virtual Environment Creation Fails

```bash
# Install venv module
sudo yum install -y python39-virtualenv

# Or use virtualenv
pip3.9 install --user virtualenv
python3.9 -m virtualenv venv
```

### Issue 3: pip Install Fails (Network Issues)

```bash
# Check network connectivity
ping -c 2 pypi.org

# If behind proxy, set:
export http_proxy=http://proxy:port
export https_proxy=http://proxy:port

# Retry setup
./setup-redhat.sh
```

### Issue 4: Permission Denied

```bash
# Make sure you own the directory
sudo chown -R tshoush:tshoush ~/REDHAT

# Make scripts executable
chmod +x ~/REDHAT/*.sh
```

### Issue 5: Missing System Dependencies

```bash
# Install build tools (may be needed for some Python packages)
sudo yum groupinstall -y "Development Tools"
sudo yum install -y python39-devel gcc openssl-devel bzip2-devel libffi-devel
```

---

## Quick Reference Commands

```bash
# Complete workflow on RedHat 7.9:

# 1. Transfer (from Mac)
scp /Users/tshoush/REDHAT/redhat-deployment-*.tar.gz tshoush@192.168.1.200:~/

# 2. SSH to RedHat
ssh tshoush@192.168.1.200

# 3. Extract
mkdir -p ~/REDHAT && cd ~/REDHAT
tar -xzf ~/redhat-deployment-*.tar.gz

# 4. Setup
chmod +x setup-redhat.sh
./setup-redhat.sh

# 5. Configure (use test values for unit tests)
cp .env.example .env
nano .env

# 6. Test
source venv/bin/activate
./run-tests.sh

# 7. Verify results
# Look for: 83 passed
```

---

## Verification Checklist

- [ ] Package transferred to RedHat 7.9
- [ ] Files extracted to ~/REDHAT
- [ ] Python 3.9+ installed and verified
- [ ] Virtual environment created successfully
- [ ] Dependencies installed (pytest, pytest-cov, etc.)
- [ ] .env file configured
- [ ] Tests executed successfully
- [ ] **83 tests passing**
- [ ] Coverage reports generated
- [ ] No security test failures

---

## What the Tests Verify

### Configuration Tests (27 tests)
- Environment variable loading
- Required field validation
- SSL configuration
- Default values
- Credential protection

### Security Validation Tests (56 tests)
- ✅ Command injection blocked
- ✅ SQL injection blocked
- ✅ XSS attacks blocked
- ✅ Path traversal blocked
- ✅ Shell metacharacters blocked
- ✅ Input validation working
- ✅ Network/IP validation
- ✅ URL validation

---

## After Successful Testing

Once all tests pass on RedHat 7.9:

1. **Phase 1 Complete** ✅
   - Security modules validated
   - Test framework working
   - Ready for integration

2. **Next Steps:**
   - Integrate security modules into existing code
   - Follow `SECURITY-FIXES-MIGRATION-GUIDE.md`
   - Test with real InfoBlox connection
   - Deploy to production

---

## Support Files

Located in `/Users/tshoush/REDHAT/`:
- `DEPLOYMENT-README.md` - Detailed deployment guide
- `SECURITY-FIXES-MIGRATION-GUIDE.md` - Integration guide
- `ssh-troubleshooting.sh` - SSH diagnostics

---

## Expected Timeline

- Transfer package: 1-2 minutes
- Extract and setup: 3-5 minutes
- Configure .env: 1-2 minutes
- Run tests: 30 seconds
- **Total: ~10 minutes**

---

## Notes for RedHat 7.9

- Default Python is 2.7 - **must install Python 3.9+**
- Use `yum` package manager (not dnf)
- SELinux may be enabled - usually not an issue for testing
- Firewall may block HTTP server (port 8000) for coverage viewing
- Virtual environment is isolated - won't affect system Python

---

**Ready to test!** Follow the steps above and you should see all 83 tests passing on RedHat 7.9.
