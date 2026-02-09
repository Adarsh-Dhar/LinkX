#!/bin/bash
echo "🚀 STARTING ALPHA CONSUMER (FORCE BUY SIMULATION)"
echo "------------------------------------------------"

# 1. Standard Cleanup and Startup (Same as start_all.sh)
./start_all.sh &

# 2. Start the Agent with the FORCE_ACTION flag
cd agent
source .venv/bin/activate
export FORCE_ACTION="BUY"
export PYTHONUNBUFFERED=1
python3 main.py
