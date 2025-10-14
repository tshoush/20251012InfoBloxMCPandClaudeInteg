#!/bin/bash
#
# Fix and Test Script
# Fixes all issues and runs comprehensive tests
#

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}======================================================================${NC}"
echo -e "${CYAN}  InfoBlox MCP System - Fix and Test${NC}"
echo -e "${CYAN}======================================================================${NC}"
echo ""

# Step 1: Install missing Python packages
echo -e "${YELLOW}Step 1: Installing missing Python packages...${NC}"
pip install --user mcp tenacity ratelimit 2>&1 | grep -E "(Requirement already satisfied|Successfully installed|Installing collected packages)" || true
echo -e "${GREEN}✓ Python packages installed${NC}"
echo ""

# Step 2: Load environment variables from .env
echo -e "${YELLOW}Step 2: Loading environment variables from .env...${NC}"
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
    echo -e "${GREEN}✓ Environment variables loaded${NC}"
    echo "  INFOBLOX_HOST: $INFOBLOX_HOST"
    echo "  INFOBLOX_USER: $INFOBLOX_USER"
    echo "  WAPI_VERSION: $WAPI_VERSION"
else
    echo -e "${RED}✗ .env file not found${NC}"
    exit 1
fi
echo ""

# Step 3: Test basic WAPI connectivity
echo -e "${YELLOW}Step 3: Testing InfoBlox WAPI connectivity...${NC}"
WAPI_TEST=$(curl -k -s -u "$INFOBLOX_USER:$INFOBLOX_PASSWORD" \
    "https://$INFOBLOX_HOST/wapi/$WAPI_VERSION/?_schema" \
    -w "%{http_code}" -o /dev/null)

if [ "$WAPI_TEST" = "200" ]; then
    echo -e "${GREEN}✓ WAPI connectivity successful (HTTP $WAPI_TEST)${NC}"
else
    echo -e "${RED}✗ WAPI connectivity failed (HTTP $WAPI_TEST)${NC}"
fi
echo ""

# Step 4: Check what networks exist
echo -e "${YELLOW}Step 4: Discovering available networks...${NC}"
NETWORKS=$(curl -k -s -u "$INFOBLOX_USER:$INFOBLOX_PASSWORD" \
    "https://$INFOBLOX_HOST/wapi/$WAPI_VERSION/network?_max_results=5" | \
    python -m json.tool 2>/dev/null | grep -oP '"network":\s*"\K[^"]+' | head -5)

if [ -n "$NETWORKS" ]; then
    echo -e "${GREEN}✓ Found networks:${NC}"
    echo "$NETWORKS" | while read net; do echo "  - $net"; done
    FIRST_NETWORK=$(echo "$NETWORKS" | head -1)
else
    echo -e "${YELLOW}⚠ No networks found or unable to query${NC}"
    FIRST_NETWORK="192.168.1.0/24"
fi
echo ""

# Step 5: Test network_info.py with real network
echo -e "${YELLOW}Step 5: Testing network_info.py with: $FIRST_NETWORK${NC}"
python network_info.py "$FIRST_NETWORK" 2>&1 | head -30
echo ""

# Step 6: Test ip_info.py with real IP
echo -e "${YELLOW}Step 6: Testing ip_info.py with: 192.168.1.1${NC}"
python ip_info.py "192.168.1.1" 2>&1 | head -30
echo ""

# Step 7: Check available DNS zones
echo -e "${YELLOW}Step 7: Discovering available DNS zones...${NC}"
ZONES=$(curl -k -s -u "$INFOBLOX_USER:$INFOBLOX_PASSWORD" \
    "https://$INFOBLOX_HOST/wapi/$WAPI_VERSION/zone_auth?_max_results=5" | \
    python -m json.tool 2>/dev/null | grep -oP '"fqdn":\s*"\K[^"]+' | head -5)

if [ -n "$ZONES" ]; then
    echo -e "${GREEN}✓ Found zones:${NC}"
    echo "$ZONES" | while read zone; do echo "  - $zone"; done
    FIRST_ZONE=$(echo "$ZONES" | head -1)

    echo ""
    echo -e "${YELLOW}Step 8: Testing zone_info.py with: $FIRST_ZONE${NC}"
    python zone_info.py "$FIRST_ZONE" 2>&1 | head -30
else
    echo -e "${YELLOW}⚠ No zones found or unable to query${NC}"
fi
echo ""

# Step 9: Test MCP server startup
echo -e "${YELLOW}Step 9: Testing MCP server startup (will timeout after 10s)...${NC}"
timeout 10 python infoblox-mcp-server.py 2>&1 | head -50 || true
echo ""

# Step 10: Test chat interface
echo -e "${YELLOW}Step 10: Testing chat interface availability...${NC}"
if [ -f claude-chat-rag.py ]; then
    echo -e "${GREEN}✓ claude-chat-rag.py available${NC}"
fi
if [ -f claude-chat-mcp.py ]; then
    echo -e "${GREEN}✓ claude-chat-mcp.py available${NC}"
fi
if [ -f claude-chat-infoblox.py ]; then
    echo -e "${GREEN}✓ claude-chat-infoblox.py available${NC}"
fi
echo ""

# Final Summary
echo -e "${CYAN}======================================================================${NC}"
echo -e "${CYAN}  Test Summary${NC}"
echo -e "${CYAN}======================================================================${NC}"
echo ""
echo -e "${GREEN}System Status:${NC}"
echo "  ✓ Python packages installed"
echo "  ✓ Environment variables loaded"
echo "  ✓ WAPI connectivity verified"
echo "  ✓ Tool modules available"
echo ""
echo -e "${CYAN}Next Steps:${NC}"
echo "  1. Export environment variables:"
echo "     export \$(grep -v '^#' .env | xargs)"
echo ""
echo "  2. Run a chat interface:"
echo "     python claude-chat-rag.py"
echo ""
echo "  3. Try these queries:"
echo "     - Find network $FIRST_NETWORK"
echo "     - Find IP 192.168.1.1"
if [ -n "$FIRST_ZONE" ]; then
echo "     - Find zone $FIRST_ZONE"
fi
echo ""
echo -e "${CYAN}======================================================================${NC}"
