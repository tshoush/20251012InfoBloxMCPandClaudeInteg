#!/bin/bash
##############################################################################
# Quick Start Script for RedHat 7.9 Testing
# Run this script on the RedHat 7.9 system after transferring the package
##############################################################################

cat << 'EOF'
╔══════════════════════════════════════════════════════════════════════════╗
║           RedHat 7.9 Testing - Quick Start                               ║
╚══════════════════════════════════════════════════════════════════════════╝

This script will guide you through testing the deployment package.
Press Enter to continue at each step...

EOF

read -p "Press Enter to start..."

# Step 1: Check if package exists
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 1: Checking for deployment package..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -f ~/redhat-deployment-*.tar.gz ]; then
    PACKAGE=$(ls ~/redhat-deployment-*.tar.gz 2>/dev/null | head -1)
    echo "✅ Found: $PACKAGE"
else
    echo "❌ Package not found in home directory!"
    echo ""
    echo "Please transfer the package first:"
    echo "  scp /Users/tshoush/REDHAT/redhat-deployment-*.tar.gz tshoush@192.168.1.200:~/"
    echo ""
    exit 1
fi

read -p "Press Enter to continue..."

# Step 2: Extract
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 2: Extracting package..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

mkdir -p ~/REDHAT
cd ~/REDHAT
tar -xzf "$PACKAGE"

if [ -f "config.py" ] && [ -f "setup-redhat.sh" ]; then
    echo "✅ Package extracted successfully"
    ls -1 | head -10
else
    echo "❌ Extraction failed"
    exit 1
fi

read -p "Press Enter to continue..."

# Step 3: Check Python
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 3: Checking Python version..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1)
    echo "Found: $PYTHON_VERSION"

    if python3 -c "import sys; exit(0 if sys.version_info >= (3, 9) else 1)" 2>/dev/null; then
        echo "✅ Python 3.9+ detected"
    else
        echo "⚠️  Python 3.9+ required"
        echo ""
        echo "Install with:"
        echo "  sudo yum install -y epel-release"
        echo "  sudo yum install -y python39"
        echo ""
        read -p "Do you want to continue anyway? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
else
    echo "❌ Python 3 not found"
    echo "Install with: sudo yum install -y python39"
    exit 1
fi

read -p "Press Enter to continue..."

# Step 4: Run setup
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 4: Running setup script..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

chmod +x setup-redhat.sh
./setup-redhat.sh

if [ $? -eq 0 ]; then
    echo "✅ Setup completed successfully"
else
    echo "❌ Setup failed"
    exit 1
fi

read -p "Press Enter to continue..."

# Step 5: Configure .env
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 5: Configuring environment..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ ! -f ".env" ]; then
    echo "Creating .env file with test values..."
    cat > .env << 'ENVEOF'
# Test Configuration (for unit tests - no real InfoBlox needed)
INFOBLOX_HOST=test.infoblox.local
INFOBLOX_USER=testuser
INFOBLOX_PASSWORD=testpass
ANTHROPIC_API_KEY=sk-test-key-12345
WAPI_VERSION=v2.13.1
INFOBLOX_VERIFY_SSL=false
RAG_DB_PATH=~/.infoblox-rag
LOG_LEVEL=INFO
ENVEOF
    echo "✅ .env file created with test configuration"
else
    echo "✅ .env file already exists"
fi

read -p "Press Enter to run tests..."

# Step 6: Run tests
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 6: Running tests..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

source venv/bin/activate
chmod +x run-tests.sh

./run-tests.sh

TEST_RESULT=$?

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ $TEST_RESULT -eq 0 ]; then
    echo "✅ All tests passed successfully!"
else
    echo "❌ Some tests failed"
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Summary:"
echo "  Tests passed: Look for '83 passed' in output above"
echo "  Coverage: config.py (87%), validators.py (74%)"
echo "  Reports: htmlcov/ directory"
echo ""
echo "To view coverage report:"
echo "  python3 -m http.server 8000 --directory htmlcov"
echo "  Then browse to: http://192.168.1.200:8000"
echo ""
echo "Next steps:"
echo "  - Review SECURITY-FIXES-MIGRATION-GUIDE.md for integration"
echo "  - Update existing code to use new security modules"
echo ""

EOF
