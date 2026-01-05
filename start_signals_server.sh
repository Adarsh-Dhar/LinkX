#!/bin/bash
# Start the trading signals server if not already running

SERVER_DIR="/Users/adarsh/Documents/alpha-consumer/server"
PORT=3050

# Check if server is already running
if lsof -i :$PORT 2>/dev/null | grep -q LISTEN; then
    echo "✅ Server already running on port $PORT"
    exit 0
fi

echo "🚀 Starting trading signals server on port $PORT..."
cd "$SERVER_DIR"

# Start server in background
pnpm start > server.log 2>&1 &
SERVER_PID=$!
echo $SERVER_PID > server.pid

# Wait and verify
sleep 3
if lsof -i :$PORT 2>/dev/null | grep -q LISTEN; then
    echo "✅ Server started successfully (PID: $SERVER_PID)"
    echo "📊 Access trading signals at: http://localhost:$PORT/trading/signals"
else
    echo "❌ Server failed to start. Check $SERVER_DIR/server.log for details"
    exit 1
fi
