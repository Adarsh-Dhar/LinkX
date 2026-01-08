#!/bin/bash

# 🚀 FINAL SYSTEM TEST - All Components
# This script helps you test all three parts of the Alpha-Consumer system

echo "=============================================="
echo "🎯 ALPHA-CONSUMER FINAL SYSTEM TEST"
echo "=============================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}This script will help you launch all 3 components:${NC}"
echo "  1️⃣  Data Server (Backend - Port 3050)"
echo "  2️⃣  AI Agent (Port 8000)"
echo "  3️⃣  Frontend UI (Port 3000)"
echo ""
echo "=============================================="

# Check if already running
check_port() {
    lsof -i :$1 >/dev/null 2>&1
}

# Step 1: Server
echo ""
echo "📡 STEP 1: Data Server"
echo "=============================================="
if check_port 3050; then
    echo -e "${GREEN}✓ Server already running on port 3050${NC}"
else
    echo -e "${YELLOW}Starting server...${NC}"
    cd server
    pnpm install >/dev/null 2>&1
    echo "Run in a separate terminal:"
    echo -e "${GREEN}  cd server && node index.js${NC}"
    cd ..
fi

# Step 2: Agent
echo ""
echo "🤖 STEP 2: AI Agent"
echo "=============================================="
if check_port 8000; then
    echo -e "${GREEN}✓ Agent already running on port 8000${NC}"
else
    echo "Run in a separate terminal:"
    echo -e "${GREEN}  cd agent && ./start_agent.sh${NC}"
fi

# Step 3: Frontend
echo ""
echo "🎨 STEP 3: Frontend UI"
echo "=============================================="
if check_port 3000; then
    echo -e "${GREEN}✓ Frontend already running on port 3000${NC}"
else
    echo "Run in a separate terminal:"
    echo -e "${GREEN}  cd frontend && npm run dev${NC}"
fi

# Final Instructions
echo ""
echo "=============================================="
echo "✅ TESTING CHECKLIST"
echo "=============================================="
echo ""
echo "1️⃣  Test Server:"
echo "   curl http://localhost:3050/market/price/CRO"
echo "   Expected: Real CRO price from CoinGecko"
echo ""
echo "2️⃣  Test Frontend:"
echo "   Open: http://localhost:3000"
echo "   Expected: Dashboard with live chart updating every 5 seconds"
echo ""
echo "3️⃣  Test the 'Alpha' Feature:"
echo "   • Navigate to Chat page"
echo "   • Type: 'Buy alpha data'"
echo "   • Watch: Chart switches to PREDICTION MODE 🔮"
echo ""
echo "=============================================="
echo "🎬 DEMO SCRIPT"
echo "=============================================="
echo ""
echo "Opening Line:"
echo '  "Here is the Live Market with REAL data from CoinGecko..."'
echo ""
echo "The Action:"
echo '  "I want to find an entry..." [Type: "Buy alpha data"]'
echo ""
echo "The Payoff:"
echo '  "The Agent negotiates the paywall, executes the trade,'
echo '   and the system projects the outcome." [Point to purple prediction line]'
echo ""
echo "=============================================="
echo "🏆 Ready to Win!"
echo "=============================================="
