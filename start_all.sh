
#!/bin/bash

# Simple Alpha-Consumer System Startup Script
# Starts: Node Server (Market) -> Python Agent API -> Next.js Frontend

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "Starting Market Analyst Server (Node.js)..."
cd "$SCRIPT_DIR/server"
if [ ! -d "node_modules" ]; then
  pnpm install
fi
pnpm start &
cd "$SCRIPT_DIR"
sleep 2

echo "Starting Agent API (FastAPI)..."
cd "$SCRIPT_DIR/agent"
if [ ! -d "venv" ]; then
  python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt
cd "$SCRIPT_DIR"
uvicorn agent.api:app --host 0.0.0.0 --port 8000 &
sleep 3

echo "Starting Frontend (Next.js)..."
cd "$SCRIPT_DIR/frontend"
if [ ! -d "node_modules" ]; then
  pnpm install
fi
pnpm run dev &
cd "$SCRIPT_DIR"

echo "All services started."
wait
