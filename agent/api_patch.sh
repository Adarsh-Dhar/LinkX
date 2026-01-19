#!/bin/bash
# Patch agent/api.py to use get_market_state instead of get_normalized_vector

API_FILE="$(dirname "$0")/api.py"

# Use sed to replace the old code with the correct async call
sed -i '' \
  '/if hasattr(agent, .data_pipeline.):/!b;n;c\
            # Fetch normalized data from all 48 nodes (async)\
            try:\
                vector = await agent.data_pipeline.get_market_state()\
                market_data = {f"feature_{i}": float(v) for i, v in enumerate(vector)}\
                nodes_used = getattr(agent.data_pipeline, "last_fetch_keys", [])\
            except Exception as e:\
                print(f"Could not fetch market state: {e}")\
                market_data = {{}}\
                nodes_used = []' \
  "$API_FILE"

echo "✅ Patched agent/api.py for async data pipeline."
