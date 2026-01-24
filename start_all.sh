#!/bin/bash
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "🚀 STARTING ALPHA CONSUMER (EXPERT MODE)"
echo "------------------------------------------------"

# 1. Cleanup
echo "🧹 Cleaning up..."
pkill -f "python3.*agent"
pkill -f "node.*server"
pkill -f "next-server"
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:3050 | xargs kill -9 2>/dev/null

# 2. Start Real Data Source (Market Analyst Server)
echo "📈 Starting Market Analyst Server..."
cd "$SCRIPT_DIR/server"
if [ ! -d "node_modules" ]; then pnpm install; fi

# Robust start for index.js or index.cjs
if [ -f "index.js" ]; then
    node index.js &
else
    node index.cjs &
fi
SERVER_PID=$!
echo "   ✅ Analyst Server PID: $SERVER_PID"
sleep 5

# 3. Setup Database
echo "🗄️  Setting up Database..."
cd "$SCRIPT_DIR/frontend"
export DATABASE_URL="file:./agent/agent_state.db"
npx prisma db push --accept-data-loss
npx prisma db seed

# 4. Start Frontend
echo "🖥️  Starting Frontend..."
pnpm run dev &
FRONTEND_PID=$!
echo "   ✅ Frontend PID: $FRONTEND_PID"
echo "   ⏳ Waiting 15s for Frontend to boot..."
sleep 15

# 5. Start Agent (WITH UNBUFFERED LOGS)
echo "🤖 Starting Agent..."
cd "$SCRIPT_DIR/agent"
if [ ! -d "venv" ]; then python3 -m venv venv; fi
source venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL="file:../frontend/agent/agent_state.db"
export RPC_URL="https://evm-t3.cronos.org"
export PYTHONUNBUFFERED=1  # <--- CRITICAL FOR LOGS

uvicorn api:app --host 0.0.0.0 --port 8000 --reload &
AGENT_PID=$!

echo "✅ System Online. Watch terminal for '🤖 EXPERT AGENT ANALYSIS'..."
trap "kill $SERVER_PID $FRONTEND_PID $AGENT_PID; exit" SIGINT SIGTERM
wait