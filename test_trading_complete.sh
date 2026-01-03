#!/bin/bash

# Complete Trading System Test Suite
# Tests all trading endpoints and agent tools

set -e

echo ""
echo "======================================================================"
echo "🧪 COMPLETE TRADING SYSTEM TEST SUITE"
echo "======================================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

SERVER_URL="http://localhost:3050"
PASSED=0
FAILED=0

# Test function
test_endpoint() {
    local name="$1"
    local method="$2"
    local endpoint="$3"
    local expected_status="$4"
    local data="$5"
    
    echo -e "${BLUE}Testing:${NC} $name"
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "$SERVER_URL$endpoint")
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" \
            -H "Content-Type: application/json" \
            -d "$data" \
            "$SERVER_URL$endpoint")
    fi
    
    status_code=$(echo "$response" | tail -n 1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$status_code" = "$expected_status" ]; then
        echo -e "${GREEN}✅ PASSED${NC} - Status: $status_code"
        echo "$body" | jq '.' 2>/dev/null || echo "$body"
        ((PASSED++))
    else
        echo -e "${RED}❌ FAILED${NC} - Expected: $expected_status, Got: $status_code"
        echo "$body"
        ((FAILED++))
    fi
    echo ""
}

echo "======================================================================"
echo "📡 TESTING SERVER ENDPOINTS"
echo "======================================================================"
echo ""

# Check if server is running
if ! curl -s "$SERVER_URL/health" > /dev/null 2>&1; then
    echo -e "${RED}❌ Server is not running!${NC}"
    echo "Please start the server first:"
    echo "  cd server && npm start"
    exit 1
fi

echo -e "${GREEN}✅ Server is running${NC}"
echo ""

# Test Health Endpoint
test_endpoint "Health Check" "GET" "/health" "200"

# Test Trading Signals
test_endpoint "Get All Trading Signals" "GET" "/trading/signals" "200"

# Test Specific Recommendation
test_endpoint "Get VVS Recommendation" "GET" "/trading/recommendation/VVS" "200"
test_endpoint "Get CRO Recommendation" "GET" "/trading/recommendation/CRO" "200"

# Test BUY Alpha Endpoint
test_endpoint "Get Free BUY Signals" "GET" "/buy-alpha" "200"

# Test Portfolio Value
test_endpoint "Get Portfolio Value" "GET" "/portfolio/value?address=0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb" "200"

# Test Record Trade
trade_data='{
  "ticker": "VVS",
  "action": "BUY",
  "amount": 5,
  "tx_hash": "0xtest123456789",
  "status": "success"
}'
test_endpoint "Record Trade" "POST" "/portfolio/trade" "200" "$trade_data"

# Test Get Trade History
test_endpoint "Get Trade History" "GET" "/portfolio/trades?limit=5" "200"

# Test Premium Endpoints (x402)
test_endpoint "Get Premium Insight (402)" "GET" "/alpha/insight/VVS" "402"

# Test Invalid Ticker
test_endpoint "Invalid Ticker (404)" "GET" "/trading/recommendation/INVALID" "404"

echo "======================================================================"
echo "📊 TEST RESULTS"
echo "======================================================================"
echo ""
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL TESTS PASSED!${NC}"
    echo ""
    echo "======================================================================"
    echo "🚀 TRADING SYSTEM STATUS: COMPLETE ✅"
    echo "======================================================================"
    echo ""
    echo "Available Trading Features:"
    echo "  ✅ Trading signal generation"
    echo "  ✅ BUY/SELL recommendations"
    echo "  ✅ Portfolio value tracking"
    echo "  ✅ Trade history recording"
    echo "  ✅ x402 payment protocol"
    echo ""
    echo "Next Steps:"
    echo "  1. Test agent tools: cd agent && python test_swap.py"
    echo "  2. Run interactive agent: cd agent && python main.py"
    echo "  3. Check BUY signals: curl $SERVER_URL/buy-alpha"
    echo "  4. Execute trades through agent"
    echo ""
    exit 0
else
    echo -e "${RED}❌ SOME TESTS FAILED${NC}"
    echo ""
    echo "Please check the server logs and try again."
    exit 1
fi
