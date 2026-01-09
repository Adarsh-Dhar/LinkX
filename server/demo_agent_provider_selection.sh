#!/bin/bash

# 🤖 Example: Agent Comparing Multiple Providers
# This shows how your AI agent could evaluate different providers and choose one

echo "
╔════════════════════════════════════════════════════════════╗
║  🤖 Agent Provider Comparison Example                     ║
║  Demonstrates multi-provider decision making              ║
╚════════════════════════════════════════════════════════════╝
"

# Colors
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}Step 1: Agent discovers available providers${NC}\n"

# Query health endpoints from all providers
echo "Querying provider endpoints..."

# Note: These will fail if servers aren't running, but that's okay for demo
providers=(
  "http://localhost:3050 default"
  "http://localhost:3051 premium"
  "http://localhost:3052 scam"
)

declare -A provider_info

for provider in "${providers[@]}"; do
  url=$(echo $provider | cut -d' ' -f1)
  id=$(echo $provider | cut -d' ' -f2)
  
  response=$(curl -s "$url/health" 2>/dev/null || echo "")
  
  if [ ! -z "$response" ]; then
    provider_info[$id]=$response
    echo -e "${GREEN}✓${NC} Found provider: $id"
  else
    echo -e "${RED}✗${NC} Provider $id not responding (make sure server is running on correct port)"
  fi
done

echo ""
echo -e "${BLUE}Step 2: Agent checks pricing from each provider${NC}\n"

# Simulated pricing data from providers.json
declare -A pricing
pricing["default"]="0.1 USDC (Standard, Bullish)"
pricing["premium"]="1.0 USDC (Expensive, Bullish, Most Conservative)"
pricing["scam"]="0.01 USDC (Cheap, Bearish, Most Aggressive)"

declare -A risk_level
risk_level["default"]="Medium"
risk_level["premium"]="Low"
risk_level["scam"]="High"

echo "Provider Pricing Comparison:"
echo ""
printf "%-12s %-35s %-15s\n" "Provider" "Price & Sentiment" "Risk Level"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
for provider in "${!pricing[@]}"; do
  printf "%-12s %-35s %-15s\n" "$provider" "${pricing[$provider]}" "${risk_level[$provider]}"
done
echo ""

echo -e "${BLUE}Step 3: Agent analyzes scenario${NC}\n"

# Simulate different agent decision scenarios
scenario=$(shuf -n 1 -e "aggressive" "balanced" "conservative")

echo "Current Market Scenario: $scenario"
echo ""

case $scenario in
  "aggressive")
    echo -e "${YELLOW}🎯 Agent Decision Logic:${NC}"
    echo "   • Market volatility is HIGH"
    echo "   • Agent risk tolerance: AGGRESSIVE"
    echo "   • Budget available: LOW"
    echo ""
    echo -e "${GREEN}✓ Agent SELECTS: 'scam' provider${NC}"
    echo "   Reason: Cheapest at 0.01 USDC, bearish outlook matches aggressive trading"
    selected_provider="scam"
    selected_port="3052"
    ;;
  "balanced")
    echo -e "${YELLOW}🎯 Agent Decision Logic:${NC}"
    echo "   • Market volatility is MODERATE"
    echo "   • Agent risk tolerance: BALANCED"
    echo "   • Budget available: MEDIUM"
    echo ""
    echo -e "${GREEN}✓ Agent SELECTS: 'default' provider${NC}"
    echo "   Reason: Mid-priced at 0.1 USDC, bullish outlook for stable growth"
    selected_provider="default"
    selected_port="3050"
    ;;
  "conservative")
    echo -e "${YELLOW}🎯 Agent Decision Logic:${NC}"
    echo "   • Market volatility is LOW"
    echo "   • Agent risk tolerance: CONSERVATIVE"
    echo "   • Budget available: HIGH"
    echo ""
    echo -e "${GREEN}✓ Agent SELECTS: 'premium' provider${NC}"
    echo "   Reason: Expensive at 1.0 USDC but most conservative predictions"
    selected_provider="premium"
    selected_port="3051"
    ;;
esac

echo ""
echo -e "${BLUE}Step 4: Agent queries selected provider for alpha${NC}\n"

echo "Requesting alpha insight from '$selected_provider' provider..."
echo "Endpoint: http://localhost:$selected_port/alpha/insight/CRO"
echo ""

# Note: This will show a 402 Payment Required response
# In production, the agent would then verify payment and call /payment endpoint
insight_response=$(curl -s "http://localhost:$selected_port/alpha/insight/CRO" 2>/dev/null || echo "Server not running")

if [ ! -z "$insight_response" ]; then
  echo -e "${YELLOW}Server Response:${NC}"
  echo "$insight_response" | jq . 2>/dev/null || echo "$insight_response"
else
  echo -e "${RED}Note: Make sure to start the server with PROVIDER_ID=$selected_provider${NC}"
  echo "Example: PROVIDER_ID=$selected_provider node index.js"
fi

echo ""
echo -e "${BLUE}Step 5: Agent pays and receives predictions${NC}\n"

echo "In a real scenario:"
echo "  1. Agent verifies payment requirements"
echo "  2. Agent signs transaction with wallet"
echo "  3. Agent submits payment to blockchain"
echo "  4. Agent calls POST /payment endpoint with signature"
echo "  5. Agent receives provider's prediction"
echo ""

echo -e "${GREEN}✨ Multi-provider decision making complete!${NC}"
echo ""
echo "Run this script multiple times to see different agent decisions!"
