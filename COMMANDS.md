# Commands Executed by setup-python38-centos.sh

This document lists all commands that the `setup-python38-centos.sh` script will execute on your Red Hat 7.9 system.

## Overview
The script automates the installation of Python 3.8 using CentOS Software Collections repositories and Node.js 14 using NVM (Node Version Manager).

---

## Step 1: Create CentOS Base Repositories

**Command:**
```bash
sudo tee /etc/yum.repos.d/CentOS-Base.repo > /dev/null << 'EOF'
[base]
name=CentOS-7 - Base
baseurl=http://vault.centos.org/7.9.2009/os/$basearch/
gpgcheck=0
enabled=1

[updates]
name=CentOS-7 - Updates
baseurl=http://vault.centos.org/7.9.2009/updates/$basearch/
gpgcheck=0
enabled=1

[extras]
name=CentOS-7 - Extras
baseurl=http://vault.centos.org/7.9.2009/extras/$basearch/
gpgcheck=0
enabled=1
EOF
```

**What it does:** Creates repository configuration file for CentOS base, updates, and extras repositories

---

## Step 2: Install EPEL Repository

**Command:**
```bash
sudo yum install -y epel-release
```

**What it does:** Installs Extra Packages for Enterprise Linux (EPEL) repository

---

## Step 3: Install Software Collections Repository

**Command:**
```bash
sudo yum install -y centos-release-scl
```

**What it does:** Installs CentOS Software Collections repository package

---

## Step 4: Fix SCL Repository URLs

**Command 1:**
```bash
sudo tee /etc/yum.repos.d/CentOS-SCLo-scl.repo > /dev/null << 'EOF'
[centos-sclo-sclo]
name=CentOS-7 - SCLo sclo
baseurl=http://vault.centos.org/7.9.2009/sclo/$basearch/sclo/
gpgcheck=0
enabled=1

[centos-sclo-sclo-testing]
name=CentOS-7 - SCLo sclo Testing
baseurl=http://vault.centos.org/7.9.2009/sclo/$basearch/sclo/
gpgcheck=0
enabled=0

[centos-sclo-sclo-source]
name=CentOS-7 - SCLo sclo Sources
baseurl=http://vault.centos.org/7.9.2009/sclo/Source/sclo/
gpgcheck=0
enabled=0

[centos-sclo-sclo-debuginfo]
name=CentOS-7 - SCLo sclo Debuginfo
baseurl=http://vault.centos.org/7.9.2009/sclo/$basearch/sclo/debuginfo/
gpgcheck=0
enabled=0
EOF
```

**Command 2:**
```bash
sudo tee /etc/yum.repos.d/CentOS-SCLo-scl-rh.repo > /dev/null << 'EOF'
[centos-sclo-rh]
name=CentOS-7 - SCLo rh
baseurl=http://vault.centos.org/7.9.2009/sclo/$basearch/rh/
gpgcheck=0
enabled=1

[centos-sclo-rh-testing]
name=CentOS-7 - SCLo rh Testing
baseurl=http://vault.centos.org/7.9.2009/sclo/$basearch/rh/
gpgcheck=0
enabled=0

[centos-sclo-rh-source]
name=CentOS-7 - SCLo rh Sources
baseurl=http://vault.centos.org/7.9.2009/sclo/Source/rh/
gpgcheck=0
enabled=0

[centos-sclo-rh-debuginfo]
name=CentOS-7 - SCLo rh Debuginfo
baseurl=http://vault.centos.org/7.9.2009/sclo/$basearch/rh/debuginfo/
gpgcheck=0
enabled=0
EOF
```

**What it does:** Configures SCL repositories to use vault.centos.org URLs (required for CentOS 7.9)

---

## Step 5: Install Python 3.8 and Related Packages

**Command:**
```bash
sudo yum install -y rh-python38 rh-python38-python-pip rh-python38-python-devel
```

**What it does:** Installs:
- `rh-python38` - Python 3.8 metapackage
- `rh-python38-python-pip` - pip package manager for Python 3.8
- `rh-python38-python-devel` - Development headers and libraries for Python 3.8

---

## Step 5: Install Node.js 14 via NVM

**Commands:**
```bash
# Install NVM if not already present
if [ ! -d "$HOME/.nvm" ]; then
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.0/install.sh | bash
fi

# Load NVM
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# Install Node.js 14
nvm install 14
nvm alias default 14
```

**What it does:**
- Downloads and installs NVM (Node Version Manager) from GitHub
- Loads NVM into the current shell session
- Installs Node.js 14.21.3 (the highest version compatible with RHEL 7.9's glibc 2.17)
- Sets Node.js 14 as the default version
- NVM automatically updates `~/.bashrc` to load Node.js on new shell sessions

**Why Node.js 14?**
RHEL 7.9 has glibc 2.17 and libstdc++ from GCC 4.8. Node.js 16+ requires glibc 2.25-2.28 which is not available in RHEL 7.9. Node.js 14 is the highest version that works with RHEL 7.9's system libraries.

---

## Step 6: Configure User Environment

**Command 1:**
```bash
echo "" >> ~/.bashrc
echo "# Enable Python 3.8 from Software Collections" >> ~/.bashrc
echo "source /opt/rh/rh-python38/enable" >> ~/.bashrc
```

**What it does:** Adds Python 3.8 to your PATH permanently by sourcing the SCL environment file

**Command 2:**
```bash
echo "alias python3=python" >> ~/.bashrc
```

**What it does:** Creates an alias so you can use `python3` command as well as `python`

---

## Step 7: Verify Installation

**Commands:**
```bash
scl enable rh-python38 'python --version'
scl enable rh-python38 'pip --version'
scl enable rh-python38 'which python'
node --version
npm --version
which node
```

**What it does:** Displays:
- Python version (should show 3.8.13)
- pip version (should show 19.3.1)
- Python installation path (should be /opt/rh/rh-python38/root/usr/bin/python)
- Node.js version (should show v14.21.3)
- npm version (should show 6.14.18)
- Node.js installation path (should be ~/.nvm/versions/node/v14.21.3/bin/node)

---

## Final Step: Activate Python 3.8

**Command (manual, after script completes):**
```bash
source ~/.bashrc
```

**What it does:** Reloads your bash configuration to activate Python 3.8 in your current session

---

## Packages and Software Installed

The following will be installed:

**Via YUM:**
- `epel-release` - EPEL repository configuration
- `centos-release-scl` - SCL repository configuration
- `rh-python38` - Python 3.8.13
- `rh-python38-python-pip` - pip 19.3.1
- `rh-python38-python-devel` - Python development files
- `rh-python38-runtime` - Runtime environment for Python 3.8
- `rh-python38-python-libs` - Python 3.8 libraries
- `rh-python38-python-setuptools` - setuptools for Python 3.8
- `scl-utils-build` - SCL build utilities

**Via NVM:**
- NVM (Node Version Manager) v0.40.0
- Node.js 14.21.3
- npm 6.14.18

---

## Repository Files Created/Modified

The script creates or modifies these repository files:
- `/etc/yum.repos.d/CentOS-Base.repo`
- `/etc/yum.repos.d/CentOS-SCLo-scl.repo`
- `/etc/yum.repos.d/CentOS-SCLo-scl-rh.repo`

---

## User Files Modified

The script modifies:
- `~/.bashrc` - Adds Python 3.8 activation and python3 alias

---

## Total Download Size
- **Python packages:** ~13 MB
- **Node.js 14:** ~19 MB (via NVM)
- **NVM:** ~400 KB
- **Total:** ~32-33 MB

## Total Installed Size
- **Python:** ~49 MB
- **Node.js 14:** ~60 MB
- **NVM:** ~1 MB
- **Total:** ~110 MB of disk space will be used
