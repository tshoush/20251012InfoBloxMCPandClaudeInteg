#!/bin/bash
##############################################################################
# SSH Connection Troubleshooting for RedHat System
##############################################################################

REMOTE_HOST="192.168.1.200"
REMOTE_USER="tshoush"

echo "========================================="
echo "SSH Connection Troubleshooting"
echo "========================================="
echo ""

# Test 1: Network connectivity
echo "[Test 1] Network Connectivity"
echo "-----------------------------"
if ping -c 2 "$REMOTE_HOST" > /dev/null 2>&1; then
    echo "✓ Host $REMOTE_HOST is reachable"
else
    echo "✗ Host $REMOTE_HOST is NOT reachable"
    echo "  Check network connection and firewall"
    exit 1
fi
echo ""

# Test 2: SSH port
echo "[Test 2] SSH Port (22) Open"
echo "-----------------------------"
if nc -z -w 5 "$REMOTE_HOST" 22 2>/dev/null; then
    echo "✓ SSH port 22 is open"
else
    echo "✗ SSH port 22 is closed or filtered"
    echo "  Check if sshd is running on remote host"
fi
echo ""

# Test 3: SSH server identification
echo "[Test 3] SSH Server Identification"
echo "-----------------------------"
ssh-keyscan -t rsa "$REMOTE_HOST" 2>/dev/null | head -1 || echo "Could not retrieve SSH key"
echo ""

# Test 4: Available authentication methods
echo "[Test 4] Authentication Methods"
echo "-----------------------------"
ssh -v -o PreferredAuthentications=none "$REMOTE_USER@$REMOTE_HOST" 2>&1 | grep -i "Authentications that can continue" || echo "Could not determine auth methods"
echo ""

# Test 5: Check for existing SSH keys
echo "[Test 5] Local SSH Keys"
echo "-----------------------------"
if [ -f ~/.ssh/id_rsa ] || [ -f ~/.ssh/id_ed25519 ] || [ -f ~/.ssh/id_ecdsa ]; then
    echo "✓ SSH keys found:"
    ls -1 ~/.ssh/id_* 2>/dev/null | grep -v ".pub" || true
else
    echo "✗ No SSH keys found"
    echo "  Generate with: ssh-keygen -t ed25519"
fi
echo ""

# Test 6: SSH config
echo "[Test 6] SSH Configuration"
echo "-----------------------------"
if [ -f ~/.ssh/config ]; then
    echo "✓ SSH config exists"
    echo "Checking for $REMOTE_HOST entry..."
    grep -A 5 "$REMOTE_HOST" ~/.ssh/config 2>/dev/null || echo "  No specific entry for $REMOTE_HOST"
else
    echo "✗ No SSH config file"
fi
echo ""

# Recommendations
echo "========================================="
echo "Recommendations"
echo "========================================="
echo ""
echo "If SSH password authentication is failing, try:"
echo ""
echo "1. Setup SSH key authentication:"
echo "   ssh-keygen -t ed25519 -f ~/.ssh/redhat_key"
echo "   # Then manually copy ~/.ssh/redhat_key.pub to remote"
echo "   # Add to: ~/.ssh/authorized_keys on RedHat system"
echo ""
echo "2. Or use manual transfer methods:"
echo "   - USB drive"
echo "   - Network share (SMB/NFS)"
echo "   - Web transfer (HTTP upload)"
echo ""
echo "3. Check RedHat system SSH config:"
echo "   sudo grep -E '(PasswordAuthentication|PubkeyAuthentication)' /etc/ssh/sshd_config"
echo ""
echo "4. Verify RedHat system is accessible:"
echo "   # From another terminal, try console login"
echo "   # Or check if you can ping: ping $REMOTE_HOST"
echo ""
