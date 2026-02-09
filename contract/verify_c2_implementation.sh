#!/bin/bash

# verify_c2_implementation.sh
# Quick verification that all C2 components are implemented

echo "🔍 Verifying C2 Bridge Implementation"
echo "======================================"
echo ""

ERRORS=0

# Check 1: Agent state awareness
echo "📋 Checking agent/predictive_agent.py..."
if grep -q "def apply_human_interference" agent/predictive_agent.py && \
   grep -q "self.risk_threshold" agent/predictive_agent.py && \
   grep -q "self.forced_bias" agent/predictive_agent.py && \
   grep -q "human_rules" agent/predictive_agent.py; then
  echo "✅ Agent state awareness implemented"
else
  echo "❌ Missing agent state components"
  ERRORS=$((ERRORS + 1))
fi

# Check 2: Strategist override logic
echo "📋 Checking agent/tools.py..."
if grep -q "FUND MANAGER OVERRIDES" agent/tools.py && \
   grep -q "human_rules" agent/tools.py; then
  echo "✅ Strategist override logic implemented"
else
  echo "❌ Missing strategist override components"
  ERRORS=$((ERRORS + 1))
fi

# Check 3: Backend API endpoint
echo "📋 Checking agent/api.py..."
if grep -q "/agent/control/override" agent/api.py && \
   grep -q "apply_human_interference" agent/api.py; then
  echo "✅ Backend control API implemented"
else
  echo "❌ Missing API endpoint components"
  ERRORS=$((ERRORS + 1))
fi

# Check 4: Chat intent extraction
echo "📋 Checking frontend/app/api/chat/route.ts..."
if grep -q "extractIntent" frontend/app/api/chat/route.ts && \
   grep -q "SET_RISK" frontend/app/api/chat/route.ts && \
   grep -q "SET_BIAS" frontend/app/api/chat/route.ts; then
  echo "✅ Chat intent extraction implemented"
else
  echo "❌ Missing chat intent components"
  ERRORS=$((ERRORS + 1))
fi

# Check 5: Documentation
echo "📋 Checking documentation..."
if [ -f "C2_BRIDGE_IMPLEMENTATION.md" ] && \
   [ -f "C2_IMPLEMENTATION_SUMMARY.md" ]; then
  echo "✅ Documentation complete"
else
  echo "❌ Missing documentation files"
  ERRORS=$((ERRORS + 1))
fi

# Check 6: Test scripts
echo "📋 Checking test scripts..."
if [ -f "test_c2_bridge.sh" ] && [ -x "test_c2_bridge.sh" ]; then
  echo "✅ Test script ready"
else
  echo "❌ Missing or non-executable test script"
  ERRORS=$((ERRORS + 1))
fi

echo ""
echo "======================================"
if [ $ERRORS -eq 0 ]; then
  echo "✅ All C2 Bridge Components Verified!"
  echo ""
  echo "Next steps:"
  echo "1. Start agent: cd agent && python -m agent.main"
  echo "2. Run tests: ./test_c2_bridge.sh"
  echo "3. Read guide: cat C2_IMPLEMENTATION_SUMMARY.md"
else
  echo "❌ Found $ERRORS missing components"
  echo "Please review the implementation"
fi
