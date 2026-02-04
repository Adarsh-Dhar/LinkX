#!/bin/bash

# demo_c2_commands.sh
# Demonstrates various C2 commands for the agent

echo "🎮 C2 Bridge Command Demonstrations"
echo "===================================="
echo ""
echo "This script shows example commands you can issue to the agent."
echo "Each command will be executed with a 2-second pause between them."
echo ""
read -p "Press Enter to start demonstration..."
echo ""

# Command 1: Aggressive mode
echo "📡 Command 1: Setting AGGRESSIVE mode (risk=0.1)"
curl -X POST http://localhost:8000/agent/control/override \
  -H "Content-Type: application/json" \
  -d '{"risk": 0.1}' 2>/dev/null | jq '.'
echo ""
sleep 2

# Command 2: Force SHORT bias
echo "📡 Command 2: Forcing SHORT bias"
curl -X POST http://localhost:8000/agent/control/override \
  -H "Content-Type: application/json" \
  -d '{"bias": "SHORT"}' 2>/dev/null | jq '.'
echo ""
sleep 2

# Command 3: Check status
echo "📡 Command 3: Checking current configuration"
curl -X POST http://localhost:8000/agent/control/override \
  -H "Content-Type: application/json" \
  -d '{}' 2>/dev/null | jq '.current_config'
echo ""
sleep 2

# Command 4: Conservative LONG
echo "📡 Command 4: Setting CONSERVATIVE + LONG (risk=0.85, bias=LONG)"
curl -X POST http://localhost:8000/agent/control/override \
  -H "Content-Type: application/json" \
  -d '{"risk": 0.85, "bias": "LONG"}' 2>/dev/null | jq '.'
echo ""
sleep 2

# Command 5: Neutral stance
echo "📡 Command 5: Setting NEUTRAL stance (blocks all trades)"
curl -X POST http://localhost:8000/agent/control/override \
  -H "Content-Type: application/json" \
  -d '{"bias": "NEUTRAL"}' 2>/dev/null | jq '.'
echo ""
sleep 2

# Command 6: Reset to defaults
echo "📡 Command 6: Resetting to institutional defaults (risk=0.15, no bias)"
curl -X POST http://localhost:8000/agent/control/override \
  -H "Content-Type: application/json" \
  -d '{"risk": 0.15, "bias": "NONE"}' 2>/dev/null | jq '.'
echo ""

echo "===================================="
echo "✅ Demonstration complete!"
echo ""
echo "Try these natural language commands in the chat interface:"
echo "  • 'be extremely aggressive'"
echo "  • 'go short only'"
echo "  • 'let AI decide'"
echo "  • 'be conservative'"
echo "  • 'neutral stance'"
