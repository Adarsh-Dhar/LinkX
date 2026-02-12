#!/bin/bash
# force_short_situation.sh
# Creates a situation that strongly encourages the agent to go SHORT


OVERRIDE_FILE="./agent/override_state.json"

# We include both keys and a very aggressive text context
cat <<EOF > "$OVERRIDE_FILE"
{
  "external_context": "CRITICAL: Major exploit detected. Security breach in progress. SHORT IMMEDIATELY.",
  "priority": "HIGH",
  "forced_bias": "SHORT",
  "bias_override": "SHORT"
}
EOF

echo "✅ Bearish Situation Injected at $OVERRIDE_FILE"
./start_all.sh