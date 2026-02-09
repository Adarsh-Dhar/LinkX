#!/bin/bash
echo "🚀 STARTING ALPHA CONSUMER (FORCE SELL SIMULATION)"
echo "------------------------------------------------"

# 1. Standard Startup
./start_all.sh &

# 2. Start the Agent with the FORCE_ACTION flag
export FORCE_ACTION="SELL"
export PYTHONUNBUFFERED=1
if [ -f "./venv/bin/activate" ]; then
	source ./venv/bin/activate
elif [ -f "./.venv/bin/activate" ]; then
	source ./.venv/bin/activate
else
	echo "⚠️  No virtual environment found (venv/.venv). Using current Python."
fi
python3 -m agent.main
