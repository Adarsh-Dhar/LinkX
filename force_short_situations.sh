#!/bin/bash
# force_short_situation.sh
# Creates a situation that strongly encourages the agent to go SHORT

OVERRIDE_FILE="./agent/override_state.json"

echo "📉 Creating BEARISH situation for the agent..."

# Inject human intelligence into the agent's memory via override_state.json

cat <<EOF > "$OVERRIDE_FILE"
{
  "external_context": "URGENT: Critical security vulnerability reported in major Tezos-bridge. Massive liquidation event expected in the next 10 minutes. Sell volume is spiking.",
  "priority": "HIGH",
  "bias_override": "SHORT"
}
EOF

echo "✅ intelligence injected. Starting all services..."
./start_all.sh