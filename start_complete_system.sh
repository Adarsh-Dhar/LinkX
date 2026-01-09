#!/bin/bash

# 🚀 START COMPLETE SYSTEM - One Command
# Starts: 48 Servers + Tests Integration + Shows Status

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Header
echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║           🚀 COMPLETE SYSTEM STARTUP v2.0                     ║"
echo "║     48-Server Ecosystem + AI Agent Integration                 ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Step 1: Kill existing processes
log_info "Step 1: Cleaning up existing processes..."
pkill -f "node ecosystem.js" 2>/dev/null || true
sleep 1
log_success "Cleaned up"

# Step 2: Start ecosystem
log_info "Step 2: Starting 48-node ecosystem..."
cd server

if [ ! -d "node_modules" ]; then
    log_info "Installing dependencies..."
    npm install --silent 2>&1 | grep -v "^$" || true
fi

nohup node ecosystem.js > ../ecosystem.log 2>&1 &
ECOSYSTEM_PID=$!
log_success "Ecosystem started (PID: $ECOSYSTEM_PID)"

sleep 3

# Step 3: Verify ecosystem
log_info "Step 3: Verifying ecosystem..."
RETRY_COUNT=0
MAX_RETRIES=10

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:3999/directory > /dev/null 2>&1; then
        NODES=$(curl -s http://localhost:3999/directory | python3 -c 'import sys, json; print(len(json.load(sys.stdin)))' 2>/dev/null || echo "?")
        log_success "Registry running with $NODES nodes"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    sleep 1
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    log_error "Registry not responding!"
    echo "Checking logs:"
    tail -10 ../ecosystem.log
    exit 1
fi

cd ..

# Step 4: Run integration test
log_info "Step 4: Running integration test..."
sleep 2

if python3 test_48server_integration.py; then
    log_success "Integration test passed!"
else
    log_error "Integration test failed"
    exit 1
fi

# Step 5: Show summary
echo ""
echo -e "${GREEN}"
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║              ✨ SYSTEM FULLY OPERATIONAL ✨                    ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo ""
echo -e "${BLUE}📊 System Status:${NC}"
echo "   • 48 Nodes: RUNNING (Ports 4000-4047)"
echo "   • Registry: RUNNING (Port 3999)"
echo "   • Data Pipeline: CONNECTED"
echo "   • Neural Network: LOADED"
echo "   • Integration: VERIFIED ✅"

echo ""
echo -e "${BLUE}🚀 Next Steps:${NC}"
echo "   1. Open a new terminal"
echo "   2. cd agent && python3 lightweight_agent.py"
echo "   3. Try: 'neural predict' or 'swap 10 usdc to cro'"

echo ""
echo -e "${BLUE}📚 Documentation:${NC}"
echo "   • Status: INTEGRATION_STATUS.md"
echo "   • Config: agent/.env"
echo "   • Logs: ecosystem.log"

echo ""
echo -e "${BLUE}🔍 Monitoring:${NC}"
echo "   • Registry: curl http://localhost:3999/directory"
echo "   • Logs: tail -f ecosystem.log"
echo "   • Test: python3 test_48server_integration.py"

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Ready for trading! Press Ctrl+C to stop servers.${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"

# Keep running
trap "echo ''; log_info 'Stopping ecosystem...'; kill $ECOSYSTEM_PID 2>/dev/null || true; exit 0" SIGINT

wait $ECOSYSTEM_PID 2>/dev/null || true
