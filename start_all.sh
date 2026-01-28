#!/bin/bash
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# --- AGENT CONFIGURATION ---
# Set these to control agent behavior from the shell
export AGENT_MODE="BALANCED"     # Options: ACCURATE, ECONOMY, BALANCED
export AGENT_MIN_ACCURACY=10   # Equivalent to minScore/threshold
export AGENT_MAX_COST=500     # Max USDC to spend per cycle

echo "🚀 STARTING ALPHA CONSUMER (EXPERT MODE)"
echo "------------------------------------------------"


# 1. Cleanup
echo "🧹 Cleaning up..."
pkill -f "python3.*agent"
pkill -f "node.*server"
pkill -f "node.*provider.js"
pkill -f "node.*registry.js"
pkill -f "next-server"
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:3050 | xargs kill -9 2>/dev/null
lsof -ti:3999 | xargs kill -9 2>/dev/null
lsof -ti:4000-4047 | xargs kill -9 2>/dev/null
sleep 2


# 2. Start Registry/Discovery Service
echo "📒 Starting Registry/Discovery Service..."

# 2. Start Demo Provider Microservices (Unified)
echo "📡 Starting Demo Node Providers..."
"$SCRIPT_DIR/start_demo_providers.sh" &
DEMO_PROVIDERS_PID=$!
echo "   ✅ Demo Providers Launched (PID: $DEMO_PROVIDERS_PID)"
sleep 2

# 3. (SKIPPED) Provider Microservices (legacy provider.js) are not used. All providers are now in demo_providers.js
echo "🌐 Provider Microservices are now handled by demo_providers.js."
sleep 2

# 4. Start Real Data Source (Market Analyst Server)
echo "📈 Starting Market Analyst Server..."
if [ -f "index.js" ]; then
        node index.js &
else
        node server/index.cjs &
fi
SERVER_PID=$!
echo "   ✅ Analyst Server PID: $SERVER_PID"
sleep 5

# 5. Setup Database
echo "🗄️  Setting up Database..."
cd "$SCRIPT_DIR/frontend"
DB_PATH="$SCRIPT_DIR/agent/agent_state.db"
export DATABASE_URL="file:$DB_PATH"
npx prisma db push --accept-data-loss
npx prisma db seed


# 6. Start Backend API (agent/api.py)
echo "🔌 Starting Backend API (agent/api.py) if not already running..."
if ! lsof -i:8000 | grep LISTEN; then
        # Ensure venv exists and activate from agent dir
        if [ ! -d "$SCRIPT_DIR/agent/venv" ]; then python3 -m venv "$SCRIPT_DIR/agent/venv"; fi
        source "$SCRIPT_DIR/agent/venv/bin/activate"
        pip install -r "$SCRIPT_DIR/agent/requirements.txt"
        export DATABASE_URL="file:$DB_PATH"
        export RPC_URL="https://evm-t3.cronos.org"
        export PYTHONUNBUFFERED=1
        cd "$SCRIPT_DIR"
        uvicorn agent.api_real:app --host 0.0.0.0 --port 8000 --reload &
        AGENT_PID=$!
        echo "   ✅ Backend API started (PID: $AGENT_PID)"
        sleep 5
else
        echo "   ⚠️  Backend API already running on port 8000. Skipping start."
fi

# 7. Start Frontend
echo "🖥️  Starting Frontend..."
export DATABASE_URL="file:$DB_PATH"
pnpm run dev &
FRONTEND_PID=$!
echo "   ✅ Frontend PID: $FRONTEND_PID"
echo "   ⏳ Waiting 15s for Frontend to boot..."
sleep 15

# 7. Start Agent (WITH UNBUFFERED LOGS)
echo "🤖 Starting Agent..."

# Ensure venv exists and activate from agent dir, but run uvicorn from project root
if [ ! -d "$SCRIPT_DIR/agent/venv" ]; then python3 -m venv "$SCRIPT_DIR/agent/venv"; fi
source "$SCRIPT_DIR/agent/venv/bin/activate"
pip install -r "$SCRIPT_DIR/agent/requirements.txt"
export DATABASE_URL="file:$DB_PATH"
export RPC_URL="https://evm-t3.cronos.org"
export PYTHONUNBUFFERED=1  # <--- CRITICAL FOR LOGS

# Run uvicorn from project root so 'agent' is a package
cd "$SCRIPT_DIR"

# Run agent in the background and capture its PID
uvicorn agent.api_real:app --host 0.0.0.0 --port 8000 --reload &
AGENT_PID=$!

echo "✅ System Online. Watch terminal for '🤖 EXPERT AGENT ANALYSIS'..."
trap "kill $SERVER_PID $FRONTEND_PID $AGENT_PID $REGISTRY_PID; pkill -f provider.js; exit" SIGINT SIGTERM
trap "kill $SERVER_PID $FRONTEND_PID $AGENT_PID $REGISTRY_PID $DEMO_PROVIDERS_PID; pkill -f provider.js; exit" SIGINT SIGTERM
wait