#!/bin/bash

# test_c2_bridge.sh
# Integration test for the Command-and-Control bridge

echo "🧪 Testing C2 Bridge Implementation"
echo "===================================="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Check agent is running
echo "📡 Test 1: Agent API Health Check"
response=$(curl -s http://localhost:8000/health 2>/dev/null)
if [ $? -eq 0 ]; then
  echo -e "${GREEN}✅ Agent API is responding${NC}"
else
  echo -e "${RED}❌ Agent API not responding on localhost:8000${NC}"
  echo "   Start with: cd agent && python -m agent.main"
  exit 1
fi
echo ""

# Test 2: Set aggressive risk
echo "📡 Test 2: Apply Aggressive Override (risk=0.1)"
response=$(curl -s -X POST http://localhost:8000/agent/control/override \
  -H "Content-Type: application/json" \
  -d '{"risk": 0.1}' 2>/dev/null)

if echo "$response" | jq -e '.status == "Override Applied Successfully"' > /dev/null 2>&1; then
  echo -e "${GREEN}✅ Override applied successfully${NC}"
  echo "$response" | jq '.current_config'
else
  echo -e "${RED}❌ Failed to apply override${NC}"
  echo "$response" | jq '.'
  exit 1
fi
echo ""

# Test 3: Set SHORT bias
echo "📡 Test 3: Apply SHORT Bias"
response=$(curl -s -X POST http://localhost:8000/agent/control/override \
  -H "Content-Type: application/json" \
  -d '{"bias": "SHORT"}' 2>/dev/null)

if echo "$response" | jq -e '.current_config.forced_bias == "SHORT"' > /dev/null 2>&1; then
  echo -e "${GREEN}✅ SHORT bias applied${NC}"
  echo "$response" | jq '.current_config'
else
  echo -e "${RED}❌ Failed to apply SHORT bias${NC}"
  echo "$response" | jq '.'
  exit 1
fi
echo ""

# Test 4: Check current status
echo "📡 Test 4: Verify Current Configuration"
response=$(curl -s -X POST http://localhost:8000/agent/control/override \
  -H "Content-Type: application/json" \
  -d '{}' 2>/dev/null)

risk=$(echo "$response" | jq -r '.current_config.risk_threshold')
bias=$(echo "$response" | jq -r '.current_config.forced_bias')

if [ "$risk" == "0.1" ] && [ "$bias" == "SHORT" ]; then
  echo -e "${GREEN}✅ Configuration matches expected state${NC}"
  echo "   Risk Threshold: $risk"
  echo "   Forced Bias: $bias"
else
  echo -e "${YELLOW}⚠️  Configuration doesn't match expected${NC}"
  echo "   Expected: risk=0.1, bias=SHORT"
  echo "   Got: risk=$risk, bias=$bias"
fi
echo ""

# Test 5: Reset to AI discretion
echo "📡 Test 5: Reset to AI Discretion"
response=$(curl -s -X POST http://localhost:8000/agent/control/override \
  -H "Content-Type: application/json" \
  -d '{"risk": 0.15, "bias": "NONE"}' 2>/dev/null)

if echo "$response" | jq -e '.current_config.forced_bias == "AI Discretion"' > /dev/null 2>&1; then
  echo -e "${GREEN}✅ Reset to AI discretion successful${NC}"
  echo "$response" | jq '.current_config'
else
  echo -e "${RED}❌ Failed to reset${NC}"
  echo "$response" | jq '.'
  exit 1
fi
echo ""

# Test 6: Check frontend (if running)
echo "📡 Test 6: Frontend API Health Check"
response=$(curl -s http://localhost:3600/api/health 2>/dev/null)
if [ $? -eq 0 ]; then
  echo -e "${GREEN}✅ Frontend API is responding${NC}"
else
  echo -e "${YELLOW}⚠️  Frontend not running on localhost:3600${NC}"
  echo "   Start with: cd frontend && npm run dev"
fi
echo ""

echo "===================================="
echo -e "${GREEN}🎉 C2 Bridge Tests Complete!${NC}"
echo ""
echo "Next Steps:"
echo "1. Open chat at http://localhost:3600"
echo "2. Say: 'be extremely aggressive'"
echo "3. Run: ./check_override_status.sh"
echo "4. Verify agent executes trades with lowered threshold"
