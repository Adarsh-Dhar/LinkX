#!/bin/bash

# --- CLEANUP FUNCTION ---
cleanup() {
    echo ""
    echo "🛑 Shutting down..."
    pkill -f "mock_provider" || true
    pkill -f "node index.js" || true
    pkill -f "uvicorn agent.api:app" || true
    pkill -f "next-server" || true
    pkill -P $$ 
    exit 0
}

trap cleanup SIGINT

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "🚀 STARTING ALPHA CONSUMER (REAL DATABASE MODE)"
echo "------------------------------------------------"

# 1. Cleanup
echo "🧹 Cleaning up..."
pkill -f "python3.*agent"
pkill -f "node.*server/index.js"
pkill -f "next-server"
lsof -ti:8000 | xargs kill -9 2>/dev/null

# 2. Start Real Data Source (Market Analyst Server)
echo "📈 Starting Market Analyst Server..."
cd "$SCRIPT_DIR/server"
if [ ! -d "node_modules" ]; then pnpm install; fi

# Fix: Check for index.js or index.cjs
if [ -f "index.js" ]; then
    node index.js &
elif [ -f "index.cjs" ]; then
    node index.cjs &
else
    echo "❌ Error: Could not find server entry point (index.js or index.cjs)"
    exit 1
fi
SERVER_PID=$!
echo "   ✅ Analyst Server PID: $SERVER_PID"
sleep 5

# 3. Setup Database (Seed with REAL endpoints)
echo "🗄️  Setting up Database..."
cd "$SCRIPT_DIR/frontend"
export DATABASE_URL="file:./agent/agent_state.db"
npx prisma db push --accept-data-loss
echo "🌱 Seeding Database..."
npx prisma db seed

# 4. Start Frontend
echo "🖥️  Starting Frontend..."
pnpm run dev &
FRONTEND_PID=$!
echo "   ✅ Frontend PID: $FRONTEND_PID"
sleep 10

# 5. Start Agent
echo "🤖 Starting Agent..."

# Setup Python venv and install requirements if needed
if [ ! -d "$SCRIPT_DIR/agent/venv" ]; then python3 -m venv "$SCRIPT_DIR/agent/venv"; fi
source "$SCRIPT_DIR/agent/venv/bin/activate"
pip install -r "$SCRIPT_DIR/agent/requirements.txt"
export DATABASE_URL="file:frontend/agent/agent_state.db"
export RPC_URL="https://evm-t3.cronos.org"

# Start the agent API using module mode for correct relative imports
cd "$SCRIPT_DIR"
python -m agent.api &
AGENT_PID=$!

echo "✅ System Online."
trap "kill $SERVER_PID $FRONTEND_PID $AGENT_PID; exit" SIGINT SIGTERM
wait