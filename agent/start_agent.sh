#!/bin/bash

# Start the Alpha-Consumer Agent

cd "$(dirname "$0")"

echo "🤖 Starting Alpha-Consumer Agent..."
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found"
    echo "Please copy .env.example to .env and configure it"
    echo "Run: cp .env.example .env"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Check if dependencies are installed
if ! python -c "import cryptocom_agent_client" 2>/dev/null; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
    echo ""
fi

# Start the agent
python main.py "$@"