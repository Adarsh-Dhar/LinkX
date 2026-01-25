#!/bin/bash
echo "🚀 STARTING ALPHA CONSUMER (FORCE SELL SIMULATION)"
echo "------------------------------------------------"

# 1. Standard Startup
./start_all.sh &

# 2. Start the Agent with the FORCE_ACTION flag
export FORCE_ACTION="SELL"
export PYTHONUNBUFFERED=1
source venv/bin/activate
python3 -m agent.main
