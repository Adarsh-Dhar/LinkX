#!/bin/bash

# 🚀 Quick Test Script for Live Chart Implementation

echo "=============================================="
echo "🧪 Testing Live Chart Implementation"
echo "=============================================="

# Step 1: Install server dependencies
echo ""
echo "📦 Step 1: Installing server dependencies..."
cd server
pnpm install
cd ..

# Step 2: Start server in background
echo ""
echo "🚀 Step 2: Starting server..."
cd server
node index.js &
SERVER_PID=$!
cd ..

# Wait for server to start
sleep 3

# Step 3: Test endpoints
echo ""
echo "✅ Step 3: Testing endpoints..."
echo ""

echo "Testing /health endpoint:"
curl -s http://localhost:3050/health | json_pp

echo ""
echo "Testing /market/price/CRO endpoint:"
curl -s http://localhost:3050/market/price/CRO | json_pp

echo ""
echo "Testing /market/price/VVS endpoint:"
curl -s http://localhost:3050/market/price/VVS | json_pp

echo ""
echo "=============================================="
echo "✅ Server is running on http://localhost:3050"
echo "📊 Chart will fetch data from /market/price/:ticker"
echo ""
echo "Now run the frontend:"
echo "  cd frontend && npm run dev"
echo ""
echo "To stop server:"
echo "  kill $SERVER_PID"
echo "=============================================="

# Keep server running
wait $SERVER_PID
