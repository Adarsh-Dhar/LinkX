#!/bin/bash
# Start the x402 Analyst Node server

echo "🚀 Starting Analyst Node Server (x402)..."
cd "$(dirname "$0")"

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Copying from .env.example..."
    cp .env.example .env
    echo "📝 Please edit .env with your configuration before running again."
    exit 1
fi

# Check if node_modules exists
if [ ! -d node_modules ]; then
    echo "📦 Installing dependencies..."
    pnpm install
fi

# Start the server
echo "🌐 Server starting on port ${PORT:-3050}..."
node index.js
