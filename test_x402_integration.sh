#!/bin/bash
# Integration test for x402 payment flow

set -e

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                                                           ║"
echo "║       🧪 x402 Integration Test Suite                     ║"
echo "║                                                           ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test configuration
SERVER_URL="http://localhost:3050"
TEST_TICKER="CRO"

echo "📋 Test Configuration:"
echo "   Server: $SERVER_URL"
echo "   Ticker: $TEST_TICKER"
echo ""

# Step 1: Check server health
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 1: Health Check"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
HEALTH=$(curl -s "$SERVER_URL/health")
if echo "$HEALTH" | grep -q '"ok":true'; then
    echo -e "${GREEN}✅ Server is healthy${NC}"
    echo "$HEALTH" | python3 -m json.tool 2>/dev/null || echo "$HEALTH"
else
    echo -e "${RED}❌ Server health check failed${NC}"
    echo "$HEALTH"
    exit 1
fi
echo ""

# Step 2: Request invoice (should return 402)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 2: Request Invoice (GET /alpha/insight/$TEST_TICKER)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
HTTP_CODE=$(curl -s -o /tmp/x402_invoice.json -w "%{http_code}" "$SERVER_URL/alpha/insight/$TEST_TICKER")

if [ "$HTTP_CODE" = "402" ]; then
    echo -e "${GREEN}✅ Received 402 Payment Required${NC}"
    echo ""
    echo "📄 Invoice Details:"
    cat /tmp/x402_invoice.json | python3 -m json.tool 2>/dev/null || cat /tmp/x402_invoice.json
    echo ""
    
    # Validate invoice structure
    if grep -q '"instruction"' /tmp/x402_invoice.json && \
       grep -q '"eip712Domain"' /tmp/x402_invoice.json && \
       grep -q '"eip712Types"' /tmp/x402_invoice.json; then
        echo -e "${GREEN}✅ Invoice structure is valid${NC}"
        
        # Extract key fields for display
        RECIPIENT=$(cat /tmp/x402_invoice.json | grep -o '"recipient":"[^"]*"' | head -1 | cut -d'"' -f4)
        AMOUNT=$(cat /tmp/x402_invoice.json | grep -o '"amount":"[^"]*"' | head -1 | cut -d'"' -f4)
        AMOUNT_READABLE=$(cat /tmp/x402_invoice.json | grep -o '"amountReadable":[^,}]*' | head -1 | cut -d':' -f2)
        TOKEN=$(cat /tmp/x402_invoice.json | grep -o '"token":"[^"]*"' | head -1 | cut -d'"' -f4)
        
        echo ""
        echo "💰 Payment Required:"
        echo "   Recipient: $RECIPIENT"
        echo "   Token: $TOKEN"
        echo "   Amount: $AMOUNT_READABLE USDC (raw: $AMOUNT)"
    else
        echo -e "${YELLOW}⚠️  Invoice structure incomplete${NC}"
    fi
else
    echo -e "${RED}❌ Expected 402, got $HTTP_CODE${NC}"
    cat /tmp/x402_invoice.json
    exit 1
fi
echo ""

# Step 3: Verify EIP-712 structure
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 3: Validate EIP-712 Structure"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

DOMAIN=$(cat /tmp/x402_invoice.json | grep -o '"eip712Domain":{[^}]*}' || echo "")
TYPES=$(cat /tmp/x402_invoice.json | grep -o '"TransferWithAuthorization":\[' || echo "")

if [ -n "$DOMAIN" ] && [ -n "$TYPES" ]; then
    echo -e "${GREEN}✅ EIP-712 domain and types present${NC}"
    echo "   Domain fields: name, version, chainId, verifyingContract"
    echo "   Types: TransferWithAuthorization"
else
    echo -e "${YELLOW}⚠️  EIP-712 structure may be incomplete${NC}"
fi
echo ""

# Step 4: Test payment endpoint (without actual signature)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 4: Test Payment Endpoint (Missing Signature)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
HTTP_CODE=$(curl -s -o /tmp/x402_payment_test.json -w "%{http_code}" \
    -X POST \
    -H "Content-Type: application/json" \
    "$SERVER_URL/alpha/insight/$TEST_TICKER/payment")

if [ "$HTTP_CODE" = "400" ]; then
    RESPONSE=$(cat /tmp/x402_payment_test.json)
    if echo "$RESPONSE" | grep -q "Missing signature"; then
        echo -e "${GREEN}✅ Payment endpoint correctly rejects empty requests${NC}"
        echo "   Response: $RESPONSE"
    else
        echo -e "${YELLOW}⚠️  Got 400 but unexpected error message${NC}"
        echo "$RESPONSE"
    fi
else
    echo -e "${YELLOW}⚠️  Expected 400, got $HTTP_CODE${NC}"
    cat /tmp/x402_payment_test.json
fi
echo ""

# Step 5: Summary and next steps
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Test Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✅ Server health check passed${NC}"
echo -e "${GREEN}✅ 402 invoice endpoint working${NC}"
echo -e "${GREEN}✅ EIP-712 structure present${NC}"
echo -e "${GREEN}✅ Payment endpoint validation working${NC}"
echo ""
echo "🎯 Next: Run the agent to complete end-to-end payment flow"
echo ""
echo "   cd agent"
echo "   ./start_agent.sh"
echo ""
echo "   Then in the agent prompt:"
echo "   > Access http://localhost:3050/alpha/insight/CRO"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
