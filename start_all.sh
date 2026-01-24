#!/bin/bash

# Simple Alpha-Consumer System Startup Script
# Fixed Order: Node Server -> Frontend (Wait) -> Python Agent

# --- CLEANUP FUNCTION ---
cleanup() {
    echo ""
    echo "🛑 Shutting down..."
    pkill -f "mock_provider" || true
    pkill -f "node index.js" || true
    pkill -f "uvicorn agent.api:app" || true
    pkill -f "next-server" || true
    # Kill the background pnpm processes
    pkill -P $$ 
    exit 0
}

trap cleanup SIGINT
set -e

# --- STEP 0: PRE-FLIGHT CLEANUP ---
echo "🧹 Cleaning up old processes..."
pkill -f "mock_provider" || true
pkill -f "uvicorn agent.api:app" || true
pkill -f "node index.js" || true
sleep 2



SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# --- STEP 2: START MARKET SERVER (BACKEND) ---
echo "📈 Starting Market Analyst Server (Node.js)..."
cd "$SCRIPT_DIR/server"
if [ ! -d "node_modules" ]; then
  pnpm install
fi
pnpm start &
cd "$SCRIPT_DIR"
sleep 3


# --- STEP 3: START FRONTEND (NEXT.JS) ---
echo "🖥️  Starting Frontend (Next.js)..."
cd "$SCRIPT_DIR/frontend"
if [ ! -d "node_modules" ]; then
  pnpm install
fi

# 1. Export the DB URL explicitly for local SQLite
export DATABASE_URL="file:./agent/agent_state.db"

# 2. Ensure DB schema is up to date (creates file if missing)
echo "🗄️  Syncing Database Schema..."
npx prisma db push --accept-data-loss

# 3. (Optional) Seed data if needed
# npx prisma db seed

# 4. Start Next.js and wait for it to compile
pnpm run dev &
echo "⏳ Waiting 10s for Frontend to boot..."
sleep 10

# --- STEP 4: START AGENT API (PYTHON) ---
echo "🤖 Starting Agent API (FastAPI)..."
cd "$SCRIPT_DIR/agent"
if [ ! -d "venv" ]; then
  python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt > /dev/null 2>&1
cd "$SCRIPT_DIR"
uvicorn agent.api:app --host 0.0.0.0 --port 8000 &
sleep 2

echo ""
echo "✅ All services started in correct order!"
echo "------------------------------------------------"
echo "🌐 Frontend: http://localhost:3600"
echo "📡 Agent API: http://localhost:8000"
echo "------------------------------------------------"
echo "Press Ctrl+C to stop all services cleanly."

wait