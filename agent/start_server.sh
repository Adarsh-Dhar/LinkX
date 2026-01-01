#!/bin/bash

# Start the Alpha-Consumer Server

cd "$(dirname "$0")"

echo "🚀 Starting Alpha-Consumer Server..."
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found"
    echo "Please copy .env.example to .env and configure it"
    echo "Run: cp .env.example .env"
    exit 1
fi

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
    echo ""
fi

# Start the server
node server.js