#!/bin/bash
# force_short_situation.sh
# Creates a situation that strongly encourages the agent to go SHORT


# Detect the directory where this script sits
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
OVERRIDE_FILE="$SCRIPT_DIR/agent/override_state.json"

echo "📉 Creating BEARISH situation..."

# Inject human intelligence into the agent's memory via override_state.json


cat <<EOF > "$OVERRIDE_FILE"
{
  "external_context": "CRITICAL: Major security vulnerability reported. Whales are dumping. Sell volume spiking 400%.",
  "priority": "HIGH",
  "forced_bias": "SHORT",
  "bias_override": "SHORT"
}
EOF

echo "✅ Bearish situation injected at $OVERRIDE_FILE. Starting services..."
"$SCRIPT_DIR/start_all.sh"
./start_all.sh