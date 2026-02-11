#!/bin/bash
# force_short_situation.sh
# Creates a situation that strongly encourages the agent to go SHORT


# Always write override_state.json into ./agent/ from project root
echo "📉 Creating BEARISH situation..."

cat <<EOF > "./agent/override_state.json"
{
  "external_context": "CRITICAL: Security exploit detected. Major liquidations starting. SHORT NOW.",
  "priority": "HIGH",
  "forced_bias": "SHORT",
  "bias_override": "SHORT"
}
EOF

echo "✅ Bearish Intelligence Injected into ./agent/override_state.json"
./start_all.sh