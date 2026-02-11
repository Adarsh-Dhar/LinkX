#!/bin/bash
# force_long_situation.sh
# Creates a situation that strongly encourages the agent to go LONG

OVERRIDE_FILE="./agent/override_state.json"

echo "🚀 Creating BULLISH situation for the agent..."

# Inject human intelligence into the agent's memory via override_state.json
cat <<EOF > "$OVERRIDE_FILE"
{
  "external_context": "URGENT: Major institutional partner just announced a \$500M buy-wall on Etherlink. Whales are accumulating rapidly at this level. Market sentiment is 95% bullish.",
  "priority": "HIGH",
  "forced_bias": "LONG"
}
EOF

echo "✅ intelligence injected. Starting all services..."
./start_all.sh