#!/bin/bash
##############################################################################
# Deploy REDHAT Project to RedHat System
# This script packages and transfers all necessary files to the RedHat system
##############################################################################

set -e  # Exit on error

# Configuration
REMOTE_USER="tshoush"
REMOTE_HOST="192.168.1.200"
REMOTE_DIR="~/REDHAT"
LOCAL_DIR="/Users/tshoush/REDHAT"

echo "========================================="
echo "REDHAT Project Deployment Script"
echo "========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Step 1: Create deployment package
echo -e "${YELLOW}[1/5] Creating deployment package...${NC}"
cd "$LOCAL_DIR"

# Create temporary deployment directory
DEPLOY_DIR="$(mktemp -d)"
echo "Temporary directory: $DEPLOY_DIR"

# Copy security modules
echo "  - Copying security modules..."
cp config.py "$DEPLOY_DIR/"
cp validators.py "$DEPLOY_DIR/"
cp logging_config.py "$DEPLOY_DIR/"

# Copy test framework
echo "  - Copying test framework..."
mkdir -p "$DEPLOY_DIR/tests"
cp tests/__init__.py "$DEPLOY_DIR/tests/"
cp tests/conftest.py "$DEPLOY_DIR/tests/"
cp tests/test_config.py "$DEPLOY_DIR/tests/"
cp tests/test_validators.py "$DEPLOY_DIR/tests/"

# Copy configuration files
echo "  - Copying configuration files..."
cp pytest.ini "$DEPLOY_DIR/"
cp .env.example "$DEPLOY_DIR/"
cp .gitignore "$DEPLOY_DIR/"

# Copy documentation
echo "  - Copying documentation..."
cp SECURITY-FIXES-MIGRATION-GUIDE.md "$DEPLOY_DIR/" 2>/dev/null || true
cp RECOMMENDATIONS-SUMMARY.md "$DEPLOY_DIR/" 2>/dev/null || true

# Create requirements file
echo "  - Creating requirements.txt..."
cat > "$DEPLOY_DIR/requirements.txt" <<EOF
pytest>=8.3.0
pytest-cov>=6.0.0
anthropic>=0.18.0
requests>=2.31.0
chromadb>=0.4.0
python-dotenv>=1.0.0
EOF

# Create setup script for RedHat
echo "  - Creating setup script for RedHat..."
cat > "$DEPLOY_DIR/setup-redhat.sh" <<'SETUP_EOF'
#!/bin/bash
##############################################################################
# Setup Script for RedHat System
# Run this script on the RedHat system after transferring files
##############################################################################

set -e

echo "========================================="
echo "Setting Up REDHAT Project on RedHat System"
echo "========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check Python version
echo -e "${YELLOW}[1/6] Checking Python version...${NC}"
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $PYTHON_VERSION"

# Check if python 3.9+ is available
if python3 -c "import sys; exit(0 if sys.version_info >= (3, 9) else 1)" 2>/dev/null; then
    echo -e "${GREEN}✓ Python 3.9+ detected${NC}"
else
    echo -e "${RED}✗ Python 3.9+ required${NC}"
    exit 1
fi

# Create virtual environment
echo -e "${YELLOW}[2/6] Creating virtual environment...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment already exists${NC}"
fi

# Activate virtual environment
echo -e "${YELLOW}[3/6] Activating virtual environment...${NC}"
source venv/bin/activate

# Upgrade pip
echo -e "${YELLOW}[4/6] Upgrading pip...${NC}"
pip install --upgrade pip

# Install dependencies
echo -e "${YELLOW}[5/6] Installing dependencies...${NC}"
pip install -r requirements.txt

# Create .env file from template
echo -e "${YELLOW}[6/6] Setting up environment variables...${NC}"
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${YELLOW}⚠ Please edit .env file with your credentials${NC}"
    echo "  nano .env"
else
    echo -e "${GREEN}✓ .env file already exists${NC}"
fi

echo ""
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo "Next steps:"
echo "  1. Edit .env file with your credentials:"
echo "     nano .env"
echo ""
echo "  2. Run tests:"
echo "     source venv/bin/activate"
echo "     pytest tests/ -v"
echo ""
echo "  3. View coverage report:"
echo "     python -m http.server 8000 --directory htmlcov"
echo "     # Then open http://192.168.1.200:8000 in browser"
echo ""
SETUP_EOF

chmod +x "$DEPLOY_DIR/setup-redhat.sh"

# Create run-tests script
echo "  - Creating run-tests script..."
cat > "$DEPLOY_DIR/run-tests.sh" <<'TEST_EOF'
#!/bin/bash
##############################################################################
# Run Tests on RedHat System
##############################################################################

set -e

# Activate virtual environment
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    echo "ERROR: Virtual environment not found. Run ./setup-redhat.sh first"
    exit 1
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "WARNING: .env file not found. Using test environment variables..."
    export INFOBLOX_HOST="test.infoblox.local"
    export INFOBLOX_USER="testuser"
    export INFOBLOX_PASSWORD="testpass"
    export ANTHROPIC_API_KEY="sk-test-key-12345"
    export WAPI_VERSION="v2.13.1"
    export INFOBLOX_VERIFY_SSL="false"
fi

# Run tests with coverage
echo "Running tests..."
pytest tests/ -v

echo ""
echo "========================================="
echo "Test Results Summary"
echo "========================================="
echo "Coverage report generated in: htmlcov/"
echo ""
echo "To view HTML coverage report:"
echo "  python -m http.server 8000 --directory htmlcov"
echo ""
TEST_EOF

chmod +x "$DEPLOY_DIR/run-tests.sh"

echo -e "${GREEN}✓ Package created${NC}"
echo ""

# Step 2: Create tarball
echo -e "${YELLOW}[2/5] Creating tarball...${NC}"
TARBALL="$LOCAL_DIR/redhat-deployment-$(date +%Y%m%d-%H%M%S).tar.gz"
cd "$DEPLOY_DIR"
tar -czf "$TARBALL" .
echo -e "${GREEN}✓ Tarball created: $TARBALL${NC}"
echo ""

# Step 3: Display transfer instructions
echo -e "${YELLOW}[3/5] Transfer Instructions${NC}"
echo ""
echo "Option A: Using SCP (if you have direct access)"
echo "----------------------------------------"
echo "scp $TARBALL $REMOTE_USER@$REMOTE_HOST:~/"
echo ""
echo "Option B: Using USB/Manual Transfer"
echo "----------------------------------------"
echo "1. Copy this file to USB: $TARBALL"
echo "2. Transfer to RedHat system"
echo "3. Extract on RedHat system"
echo ""

# Step 4: Display setup instructions
echo -e "${YELLOW}[4/5] Setup Instructions (Run on RedHat system)${NC}"
echo "----------------------------------------"
cat <<'INSTRUCTIONS'
# On RedHat system, run these commands:

# 1. Create directory and extract
mkdir -p ~/REDHAT
cd ~/REDHAT
tar -xzf ~/redhat-deployment-*.tar.gz

# 2. Run setup script
chmod +x setup-redhat.sh
./setup-redhat.sh

# 3. Configure credentials
nano .env
# Add your InfoBlox and Anthropic credentials

# 4. Run tests
source venv/bin/activate
./run-tests.sh

# 5. View coverage (optional)
python -m http.server 8000 --directory htmlcov
# Open browser to: http://192.168.1.200:8000
INSTRUCTIONS
echo ""

# Step 5: Cleanup
echo -e "${YELLOW}[5/5] Cleanup${NC}"
rm -rf "$DEPLOY_DIR"
echo -e "${GREEN}✓ Temporary files cleaned${NC}"
echo ""

# Summary
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}Deployment Package Ready!${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo "Package location: $TARBALL"
echo "Package size: $(du -h "$TARBALL" | cut -f1)"
echo ""
echo -e "${YELLOW}Quick Start (if SSH works):${NC}"
echo "  scp $TARBALL $REMOTE_USER@$REMOTE_HOST:~/"
echo "  ssh $REMOTE_USER@$REMOTE_HOST"
echo "  cd ~ && tar -xzf redhat-deployment-*.tar.gz -C REDHAT/"
echo "  cd REDHAT && ./setup-redhat.sh"
echo ""
echo -e "${YELLOW}Next: Transfer the tarball to RedHat system and follow setup instructions${NC}"
echo ""
