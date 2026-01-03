#!/bin/bash
# Quick Test Script - Run this to test your trading agent
# Usage: ./quick_test.sh

echo "════════════════════════════════════════════════════════════════"
echo "   AI TRADING AGENT - QUICK TEST SUITE"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Change to agent directory
cd "$(dirname "$0")"

echo "📍 Working directory: $(pwd)"
echo ""

# Test 1: Environment Check
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 1: Environment Configuration"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -f ".env" ]; then
    echo -e "${GREEN}✅ .env file found${NC}"
else
    echo -e "${RED}❌ .env file not found${NC}"
    exit 1
fi

# Test 2: Dependencies Check
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 2: Python Dependencies"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

python3 -c "import web3; import dotenv; print('✅ Core dependencies installed')" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Missing dependencies${NC}"
    echo "Run: pip install -r requirements.txt"
    exit 1
fi

# Test 3: Run Manual Tests
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 3: Transaction Tests (Detailed)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

python test_agent_transactions.py

# Test 4: Run Pytest (Optional - comment out if too slow)
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 4: Automated Tests (PyTest)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Run only fast tests, skip integration
pytest tests/test_transactions.py -v -m "not integration" --tb=line 2>&1 | grep -E "(PASSED|FAILED|ERROR|test_|passed|failed)"

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "   TESTING COMPLETE"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "📖 For detailed testing instructions, see: TESTING_GUIDE.md"
echo "📊 To test with the agent interface, run: python main.py"
echo ""
