#!/bin/bash
# Setup script for installing Python 3.8 and Node.js 14 on Red Hat 7.9 using Red Hat Subscription
# This script requires a valid Red Hat subscription

set -e  # Exit on error

echo "=========================================="
echo "Python 3.8 & Node.js 14 Setup for Red Hat 7.9"
echo "Using Red Hat Subscription"
echo "=========================================="

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    SUDO=""
else
    SUDO="sudo"
fi

# Prompt for Red Hat credentials if not provided as environment variables
if [ -z "$RH_USERNAME" ]; then
    read -p "Enter Red Hat username (email): " RH_USERNAME
fi

if [ -z "$RH_PASSWORD" ]; then
    read -sp "Enter Red Hat password: " RH_PASSWORD
    echo ""
fi

# Step 1: Register with Red Hat Subscription Manager
echo ""
echo "[1/6] Registering with Red Hat Subscription Manager..."
if $SUDO subscription-manager status | grep -q "Overall Status: Current"; then
    echo "✓ System already registered and subscribed"
else
    $SUDO subscription-manager register --username="$RH_USERNAME" --password="$RH_PASSWORD" --auto-attach
    echo "✓ System registered with Red Hat"
fi

# Step 2: Enable required repositories
echo ""
echo "[2/6] Enabling Red Hat repositories..."

# Enable RHEL Server repository
$SUDO subscription-manager repos --enable=rhel-7-server-rpms

# Enable RHEL Server Optional repository
$SUDO subscription-manager repos --enable=rhel-7-server-optional-rpms

# Enable RHEL Server Extras repository
$SUDO subscription-manager repos --enable=rhel-7-server-extras-rpms

# Enable Software Collections repository (for Python 3.8)
$SUDO subscription-manager repos --enable=rhel-server-rhscl-7-rpms

echo "✓ Red Hat repositories enabled"

# Step 3: Update yum cache
echo ""
echo "[3/6] Updating package cache..."
$SUDO yum clean all
$SUDO yum makecache
echo "✓ Package cache updated"

# Step 4: Install Python 3.8
echo ""
echo "[4/6] Installing Python 3.8..."
$SUDO yum install -y rh-python38 rh-python38-python-pip rh-python38-python-devel
echo "✓ Python 3.8 installed"

# Step 5: Install Node.js 14 via NVM
echo ""
echo "[5/6] Installing Node.js 14 via NVM..."
# Install NVM (Node Version Manager)
if [ ! -d "$HOME/.nvm" ]; then
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.0/install.sh | bash
    echo "✓ NVM installed"
else
    echo "✓ NVM already installed"
fi

# Load NVM
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# Install Node.js 14 (highest version compatible with RHEL 7.9)
nvm install 14
nvm alias default 14
echo "✓ Node.js 14 installed"

# Step 6: Install Claude CLI dependencies
echo ""
echo "[6/7] Installing Claude CLI dependencies..."

# Enable Python 3.8 for pip installations
source /opt/rh/rh-python38/enable

# Install Anthropic API SDK
pip install --user anthropic

# Install web search and scraping tools with RHEL 7.9 compatible versions
# Note: urllib3 v2 requires OpenSSL 1.1.1+, but RHEL 7.9 has OpenSSL 1.0.2k
pip install --user 'urllib3<2' 'requests<2.29' duckduckgo-search beautifulsoup4

echo "✓ Claude CLI dependencies installed"

# Step 7: Configure user environment
echo ""
echo "[7/7] Configuring user environment..."

# Add to current user's .bashrc if not already present
if ! grep -q "source /opt/rh/rh-python38/enable" ~/.bashrc; then
    echo "" >> ~/.bashrc
    echo "# Enable Python 3.8 from Red Hat Software Collections" >> ~/.bashrc
    echo "source /opt/rh/rh-python38/enable" >> ~/.bashrc
    echo "✓ Added Python 3.8 to ~/.bashrc"
else
    echo "✓ Python 3.8 already in ~/.bashrc"
fi

# Add python3 alias if not already present
if ! grep -q "alias python3=python" ~/.bashrc; then
    echo "alias python3=python" >> ~/.bashrc
    echo "✓ Added python3 alias to ~/.bashrc"
else
    echo "✓ python3 alias already in ~/.bashrc"
fi

# Verify installation
echo ""
echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo ""
echo "Python version:"
scl enable rh-python38 'python --version'
echo ""
echo "pip version:"
scl enable rh-python38 'pip --version'
echo ""
echo "Python location:"
scl enable rh-python38 'which python'
echo ""
echo "Node.js version:"
node --version
echo ""
echo "npm version:"
npm --version
echo ""
echo "Node.js location:"
which node
echo ""
echo "Anthropic SDK version:"
pip show anthropic | grep Version
echo ""
echo "Subscription status:"
$SUDO subscription-manager status
echo ""
echo "=========================================="
echo "IMPORTANT: Run 'source ~/.bashrc' or start a new shell session"
echo "to use Python 3.8 and Node.js 14 in your current terminal."
echo "=========================================="
echo ""
echo "NOTE: Node.js 14 is the highest version compatible with RHEL 7.9."
echo "For Node.js 18+, please upgrade to RHEL 8 or later."
echo ""
echo "Claude CLI Tools:"
echo "- Set ANTHROPIC_API_KEY environment variable"
echo "- Use 'claude' for one-shot queries"
echo "- Use 'chat' for interactive DDI Assistant with web search"
echo "- Use 'agent' for file operations with permissions"
echo "=========================================="
