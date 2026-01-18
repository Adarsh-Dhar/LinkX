#!/bin/bash

# Alpha-Consumer Complete System Startup Script
# Starts all three tiers: Node Server (Market) -> Python Agent API -> Next.js Frontend

echo "🚀 Starting Alpha-Consumer System..."
echo "=================================================="

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# PID file locations
SERVER_PID_FILE="$SCRIPT_DIR/server/.server.pid"
AGENT_PID_FILE="$SCRIPT_DIR/agent/.agent.pid"
FRONTEND_PID_FILE="$SCRIPT_DIR/frontend/.frontend.pid"

# Cleanup function
cleanup() {
    echo ""
    echo "🛑 Shutting down all services..."
    
    # Kill frontend
    if [ -f "$FRONTEND_PID_FILE" ]; then
        FRONTEND_PID=$(cat "$FRONTEND_PID_FILE")
        echo "Stopping Frontend (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID 2>/dev/null || true
        rm "$FRONTEND_PID_FILE"
    fi
    
    # Kill agent
    if [ -f "$AGENT_PID_FILE" ]; then
        AGENT_PID=$(cat "$AGENT_PID_FILE")
        echo "Stopping Agent API (PID: $AGENT_PID)..."
        kill $AGENT_PID 2>/dev/null || true
        rm "$AGENT_PID_FILE"
    fi
    
    # Kill server
    if [ -f "$SERVER_PID_FILE" ]; then
        SERVER_PID=$(cat "$SERVER_PID_FILE")
        echo "Stopping Market Server (PID: $SERVER_PID)..."
        kill $SERVER_PID 2>/dev/null || true
        rm "$SERVER_PID_FILE"
    fi
    
    echo "✅ All services stopped"
    exit 0
}

# Trap CTRL+C and cleanup
trap cleanup SIGINT SIGTERM

# Check if services are already running
check_running_services() {
    if [ -f "$SERVER_PID_FILE" ] || [ -f "$AGENT_PID_FILE" ] || [ -f "$FRONTEND_PID_FILE" ]; then
        echo -e "${YELLOW}⚠️  Some services may already be running${NC}"
        echo "Run './stop_all.sh' to stop existing services first"
        read -p "Continue anyway? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

check_running_services

# 1. Start Node.js Market Server (Port 3050)
echo ""
echo "📊 [1/3] Starting Market Analyst Server (Node.js)..."
cd "$SCRIPT_DIR/server"

if [ ! -d "node_modules" ]; then
    echo "Installing Node.js dependencies..."
    npm install
fi

node index.js > .server.log 2>&1 &
SERVER_PID=$!
echo $SERVER_PID > "$SERVER_PID_FILE"
echo -e "${GREEN}✓ Market Server started (PID: $SERVER_PID)${NC}"
echo "  • Running on http://localhost:3050"
echo "  • Logs: server/.server.log"

# Wait for server to be ready
sleep 2


# 2. Start Python Agent API (Port 8000)
echo ""
echo "🤖 [2/3] Starting Agent API (FastAPI)..."
cd "$SCRIPT_DIR/agent"

# Check if port 8000 is already in use
if lsof -i :8000 | grep LISTEN > /dev/null; then
    echo -e "${RED}❌ Port 8000 is already in use!${NC}"
    echo "  The Agent API (FastAPI) cannot start because something else is using port 8000."
    echo "  Please stop the process using port 8000 and try again."
    lsof -i :8000 | grep LISTEN
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies if needed
if ! python -c "import fastapi" 2>/dev/null; then
    echo "Installing Python dependencies..."
    pip install -r requirements.txt
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  Warning: .env file not found in agent/${NC}"
    echo "  Please configure your environment variables"
    if [ -f ".env.example" ]; then
        echo "  Copy .env.example to .env and configure it"
    fi
fi

uvicorn api:app --host 0.0.0.0 --port 8000 > .agent.log 2>&1 &
AGENT_PID=$!
echo $AGENT_PID > "$AGENT_PID_FILE"
echo -e "${GREEN}✓ Agent API started (PID: $AGENT_PID)${NC}"
echo "  • Running on http://localhost:8000"
echo "  • Logs: agent/.agent.log"
echo "  • API Docs: http://localhost:8000/docs"

# Wait for agent to be ready
sleep 3

# 3. Start Next.js Frontend (Port 3600)
echo ""
echo "🎨 [3/3] Starting Frontend (Next.js)..."
cd "$SCRIPT_DIR/frontend"

if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    pnpm install
fi

pnpm dev > .frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > "$FRONTEND_PID_FILE"
echo -e "${GREEN}✓ Frontend started (PID: $FRONTEND_PID)${NC}"
echo "  • Running on http://localhost:3600"
echo "  • Logs: frontend/.frontend.log"

echo ""
echo "=================================================="
echo -e "${GREEN}🎉 All services started successfully!${NC}"
echo "=================================================="
echo ""
echo "📱 Access Points:"
echo "  • Frontend UI:    http://localhost:3600"
echo "  • Agent API:      http://localhost:8000"
echo "  • Agent Docs:     http://localhost:8000/docs"
echo "  • Market Server:  http://localhost:3050"
echo ""
echo "📋 Service Status:"
echo "  • Market Server: PID $SERVER_PID (Port 3050)"
echo "  • Agent API:     PID $AGENT_PID (Port 8000)"
echo "  • Frontend:      PID $FRONTEND_PID (Port 3600)"
echo ""
echo "🔧 Commands:"
echo "  • View logs:     tail -f server/.server.log"
echo "  •                tail -f agent/.agent.log"
echo "  •                tail -f frontend/.frontend.log"
echo "  • Stop all:      Press CTRL+C or run ./stop_all.sh"
echo ""
echo "💡 Next Steps:"
echo "  1. Open http://localhost:3600 in your browser"
echo "  2. Connect your MetaMask wallet"
echo "  3. Chat with the agent or browse the Alpha Marketplace"
echo ""
echo "⏳ Services are running. Press CTRL+C to stop all..."
echo ""

# Wait for services (this keeps the script running)
wait
