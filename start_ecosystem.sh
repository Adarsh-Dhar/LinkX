#!/bin/bash

# 🚀 Start the 48-Node Ecosystem + Agent
# Usage: ./start_ecosystem.sh

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║   🚀 48-Node Autonomous Ecosystem Launcher                     ║"
echo "║   Decentralized Data Economy v1.0                             ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${YELLOW}⚠️  Node.js not found. Please install Node.js 16+${NC}"
    exit 1
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}⚠️  Python3 not found. Please install Python3${NC}"
    exit 1
fi

# Kill any existing processes on the ports
echo -e "${BLUE}🔄 Cleaning up existing processes...${NC}"
pkill -f "node ecosystem.js" 2>/dev/null || true
sleep 1

echo ""
echo -e "${BLUE}📦 Step 1: Installing server dependencies...${NC}"
cd server
if [ ! -d "node_modules" ]; then
    npm install 2>&1 | grep -v "^$" || echo "✅ Dependencies ready"
fi

echo ""
echo -e "${GREEN}✅ Server ready${NC}"

echo ""
echo -e "${BLUE}🚀 Step 2: Starting 48-Node Ecosystem...${NC}"
echo "   📊 24 Data Categories × 2 Competitors = 48 Nodes"
echo "   🔗 Registry on Port 3999"
echo "   💾 Logging to: ecosystem.log"
echo ""

# Start ecosystem in background
nohup node ecosystem.js > ecosystem.log 2>&1 &
ECOSYSTEM_PID=$!
echo -e "${GREEN}✅ Ecosystem started (PID: $ECOSYSTEM_PID)${NC}"

# Wait for it to start
sleep 3

# Check if it's running
if ! kill -0 $ECOSYSTEM_PID 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Ecosystem failed to start. Checking logs...${NC}"
    tail -20 ecosystem.log
    exit 1
fi

# Verify registry is responding
echo ""
echo -e "${BLUE}🔍 Verifying registry...${NC}"
RETRY_COUNT=0
MAX_RETRIES=10
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:3999/directory > /dev/null 2>&1; then
        NODES=$(curl -s http://localhost:3999/directory | python3 -c 'import sys, json; print(len(json.load(sys.stdin)))' 2>/dev/null || echo "0")
        echo -e "${GREEN}✅ Registry running with $NODES nodes${NC}"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    sleep 1
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo -e "${YELLOW}⚠️  Registry not responding${NC}"
    echo "Check ecosystem.log for errors"
    exit 1
fi

echo ""
echo -e "${GREEN}═════════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${GREEN}✨ ECOSYSTEM READY! ✨${NC}"
echo ""
echo -e "${BLUE}📡 System Status:${NC}"
echo "   • Nodes: 48 (Ports 4000-4047)"
echo "   • Registry: http://localhost:3999"
echo "   • Categories: 24"
echo "   • Competitors per Category: 2 (Premium/Budget)"
echo ""
echo -e "${BLUE}🚀 Next Steps:${NC}"
echo "   1. Open a new terminal"
echo "   2. Run: cd agent && python3 lightweight_agent.py"
echo "   3. Try: 'check whale transactions'"
echo ""
echo -e "${BLUE}📚 Documentation:${NC}"
echo "   • View: ECOSYSTEM_GUIDE.md"
echo "   • Test: bash test_ecosystem.sh"
echo ""
echo -e "${GREEN}═════════════════════════════════════════════════════════════════${NC}"

# Keep the script running
echo ""
echo -e "${BLUE}Press Ctrl+C to stop the ecosystem${NC}"
trap "echo ''; echo 'Stopping ecosystem...'; kill $ECOSYSTEM_PID 2>/dev/null || true; exit 0" SIGINT

wait $ECOSYSTEM_PID 2>/dev/null || true
