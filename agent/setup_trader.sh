#!/usr/bin/env bash
# Quick Start Guide for Trader Functionality

echo "================================"
echo "  Alpha-Consumer Trader Setup"
echo "================================"
echo ""

# Check dependencies
echo "📋 Checking dependencies..."

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found"
    exit 1
fi

if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 not found"
    exit 1
fi

echo "✅ Python 3 found"

# Check if we're in the agent directory
if [ ! -f "tools.py" ]; then
    echo "❌ Please run this script from the agent directory"
    exit 1
fi

# Install/update dependencies
echo ""
echo "📦 Installing Python dependencies..."
pip3 install -r requirements.txt -q

if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi

# Check environment
echo ""
echo "🔧 Checking environment configuration..."

if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found"
    echo "   Creating .env from .env.example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "   📝 Please edit .env and add your credentials:"
        echo "      - OPENROUTER_API_KEY"
        echo "      - WALLET_PRIVATE_KEY"
        echo "      - CRYPTO_COM_API_KEY"
    else
        echo "   ❌ .env.example not found"
        exit 1
    fi
else
    echo "✅ .env file found"
fi

# Test imports
echo ""
echo "🧪 Testing Python imports..."
python3 -c "from tools import execute_vvs_swap, get_token_balance, estimate_swap_output; print('✅ All tools imported successfully')" 2>&1

if [ $? -ne 0 ]; then
    echo "❌ Import test failed"
    exit 1
fi

# Summary
echo ""
echo "================================"
echo "  ✅ Setup Complete!"
echo "================================"
echo ""
echo "🚀 Next Steps:"
echo ""
echo "1️⃣  Run the test suite:"
echo "    python3 test_swap.py"
echo ""
echo "2️⃣  Start the agent in interactive mode:"
echo "    python3 main.py"
echo ""
echo "3️⃣  Try these commands:"
echo "    - 'Check my balance'"
echo "    - 'Estimate a 10 USDC to VVS swap'"
echo "    - 'Execute a 5 USDC to VVS swap'"
echo ""
echo "4️⃣  For autonomous mode (runs every 5 minutes):"
echo "    python3 main.py autonomous"
echo ""
echo "📚 Documentation:"
echo "    - See TRADER_IMPLEMENTATION.md for full details"
echo "    - See README.md for agent overview"
echo ""
echo "💡 Tips:"
echo "    - Start with small amounts (1-5 USDC) for testing"
echo "    - Check gas prices before large trades"
echo "    - Monitor transaction hashes on https://cronoscan.com"
echo ""
echo "⚠️  Important: This script executes REAL BLOCKCHAIN TRANSACTIONS"
echo "    Always verify amounts and review gas fees before confirming"
echo ""
