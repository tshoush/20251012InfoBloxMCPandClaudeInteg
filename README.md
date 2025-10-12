# Python 3.8 & Node.js 14 Setup Scripts for Red Hat 7.9

This directory contains two versions of the setup script for installing Python 3.8 and Node.js 14 on Red Hat Enterprise Linux 7.9.

## Scripts

### 1. setup-python38-centos.sh (Recommended)
**No subscription required** - Uses CentOS 7 repositories

- Uses CentOS vault repositories (binary-compatible with RHEL 7.9)
- No Red Hat subscription needed
- Works immediately on any RHEL 7.9 system
- Same packages and versions as RHEL
- Perfect for testing, development, or when subscription is unavailable

**Usage:**
```bash
./setup-python38-centos.sh
```

### 2. setup-python38-redhat.sh
**Requires Red Hat subscription** - Uses official Red Hat repositories

- Registers system with Red Hat Subscription Manager
- Uses official Red Hat Software Collections (RHSCL)
- Requires valid Red Hat subscription (paid or free Developer subscription)
- Prompts for Red Hat credentials during installation

**Usage:**
```bash
# Interactive (prompts for credentials):
./setup-python38-redhat.sh

# Or provide credentials as environment variables:
RH_USERNAME="your-email@domain.com" RH_PASSWORD="your-password" ./setup-python38-redhat.sh
```

## Which Script Should You Use?

### Use **setup-python38-centos.sh** if:
- You don't have a Red Hat subscription
- You want a quick, hassle-free installation
- You're setting up development/test systems
- CentOS repos are acceptable in your environment

### Use **setup-python38-redhat.sh** if:
- You have a valid Red Hat subscription
- Corporate policy requires official Red Hat packages
- You need Red Hat support
- You're setting up production systems

## What Gets Installed

Both scripts install:
- **Python 3.8.13**
- **pip 19.3.1**
- **Python development headers and tools**
- **Node.js 14.21.3** (highest version compatible with RHEL 7.9)
- **npm 6.14.18**
- **NVM (Node Version Manager)**
- Automatic PATH configuration
- `python3` alias

**Important Note:** RHEL 7.9 cannot run Node.js 18+ due to glibc 2.17 limitations. Node.js 14 is the maximum supported version. For newer Node.js versions, upgrade to RHEL 8 or later.

## Installation Locations

- **Python 3.8:** `/opt/rh/rh-python38/root/usr/bin/python`
- **Node.js 14:** `~/.nvm/versions/node/v14.21.3/bin/node`

## After Installation

Run the following to activate Python 3.8 and Node.js 14 in your current session:
```bash
source ~/.bashrc
```

Or for Python 3.8 only:
```bash
scl enable rh-python38 bash
```

## Red Hat Subscription

If you don't have a Red Hat subscription, you can get a free Developer subscription:
1. Visit https://developers.redhat.com/
2. Register for a free account
3. Download RHEL and get access to all repositories

## Notes

- Both scripts are functionally equivalent
- CentOS 7 is a 1:1 binary-compatible rebuild of RHEL 7
- The Python 3.8 packages are identical in both repositories
