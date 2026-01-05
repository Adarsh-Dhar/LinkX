#!/bin/bash

# Alpha-Consumer System Shutdown Script
# Stops all running services

echo "🛑 Stopping Alpha-Consumer System..."

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# PID file locations
SERVER_PID_FILE="$SCRIPT_DIR/server/.server.pid"
AGENT_PID_FILE="$SCRIPT_DIR/agent/.agent.pid"
FRONTEND_PID_FILE="$SCRIPT_DIR/frontend/.frontend.pid"

# Stop frontend
if [ -f "$FRONTEND_PID_FILE" ]; then
    FRONTEND_PID=$(cat "$FRONTEND_PID_FILE")
    echo "Stopping Frontend (PID: $FRONTEND_PID)..."
    kill $FRONTEND_PID 2>/dev/null && echo "✓ Frontend stopped" || echo "⚠️  Frontend not running"
    rm "$FRONTEND_PID_FILE"
fi

# Stop agent
if [ -f "$AGENT_PID_FILE" ]; then
    AGENT_PID=$(cat "$AGENT_PID_FILE")
    echo "Stopping Agent API (PID: $AGENT_PID)..."
    kill $AGENT_PID 2>/dev/null && echo "✓ Agent API stopped" || echo "⚠️  Agent not running"
    rm "$AGENT_PID_FILE"
fi

# Stop server
if [ -f "$SERVER_PID_FILE" ]; then
    SERVER_PID=$(cat "$SERVER_PID_FILE")
    echo "Stopping Market Server (PID: $SERVER_PID)..."
    kill $SERVER_PID 2>/dev/null && echo "✓ Market Server stopped" || echo "⚠️  Server not running"
    rm "$SERVER_PID_FILE"
fi

echo ""
echo "✅ All services stopped"
