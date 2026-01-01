#!/bin/bash

# Test all components of the Alpha-Consumer Agent

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                                                           ║"
echo "║          Alpha-Consumer Agent - System Test              ║"
echo "║                                                           ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Test 1: Check prerequisites
echo "📋 Test 1: Checking prerequisites..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found"
    exit 1
fi
echo "   ✅ Python 3: $(python3 --version)"

if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found"
    exit 1
fi
echo "   ✅ Node.js: $(node --version)"

if ! command -v npm &> /dev/null; then
    echo "❌ npm not found"
    exit 1
fi
echo "   ✅ npm: $(npm --version)"

# Test 2: Check venv
echo ""
echo "🐍 Test 2: Checking Python environment..."
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found"
    exit 1
fi
echo "   ✅ Virtual environment exists"

# Test 3: Check Node modules
echo ""
echo "📦 Test 3: Checking Node.js dependencies..."
if [ ! -d "node_modules" ]; then
    echo "❌ node_modules not found"
    exit 1
fi
echo "   ✅ node_modules exists"

# Test 4: Check configuration
echo ""
echo "⚙️  Test 4: Checking configuration files..."
files=(".env.example" ".env" "requirements.txt" "package.json" "addresses.json")
for file in "${files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Missing: $file"
        exit 1
    fi
    echo "   ✅ $file"
done

# Test 5: Check scripts
echo ""
echo "🔧 Test 5: Checking executable scripts..."
scripts=("start_agent.sh" "start_server.sh" "quickstart.sh")
for script in "${scripts[@]}"; do
    if [ ! -x "$script" ]; then
        echo "❌ Not executable: $script"
        exit 1
    fi
    echo "   ✅ $script"
done

# Test 6: Check Python imports
echo ""
echo "🐍 Test 6: Testing Python imports..."
source venv/bin/activate

# Test crypto-com-agent-client
if ! python -c "from crypto_com_agent_client import Agent" 2>/dev/null; then
    echo "❌ Failed to import crypto_com_agent_client"
    exit 1
fi
echo "   ✅ crypto_com_agent_client"

# Test web3
if ! python -c "from web3 import Web3" 2>/dev/null; then
    echo "❌ Failed to import web3"
    exit 1
fi
echo "   ✅ web3"

# Test eth-account
if ! python -c "from eth_account import Account" 2>/dev/null; then
    echo "❌ Failed to import eth_account"
    exit 1
fi
echo "   ✅ eth_account"

# Test requests
if ! python -c "import requests" 2>/dev/null; then
    echo "❌ Failed to import requests"
    exit 1
fi
echo "   ✅ requests"

# Test dotenv
if ! python -c "from dotenv import load_dotenv" 2>/dev/null; then
    echo "❌ Failed to import dotenv"
    exit 1
fi
echo "   ✅ python-dotenv"

# Test 7: Check Node.js modules
echo ""
echo "📦 Test 7: Testing Node.js dependencies..."
deactivate

if ! npm ls express &>/dev/null; then
    echo "❌ express not installed"
    exit 1
fi
echo "   ✅ express"

if ! npm ls ethers &>/dev/null; then
    echo "❌ ethers not installed"
    exit 1
fi
echo "   ✅ ethers"

if ! npm ls cors &>/dev/null; then
    echo "❌ cors not installed"
    exit 1
fi
echo "   ✅ cors"

if ! npm ls dotenv &>/dev/null; then
    echo "❌ dotenv not installed"
    exit 1
fi
echo "   ✅ dotenv"

# Test 8: File size check
echo ""
echo "📄 Test 8: Checking main files..."
if [ -f "main.py" ]; then
    size=$(wc -c < main.py)
    echo "   ✅ main.py ($((size / 1024))KB)"
else
    echo "❌ main.py not found"
    exit 1
fi

if [ -f "server.js" ]; then
    size=$(wc -c < server.js)
    echo "   ✅ server.js ($((size / 1024))KB)"
else
    echo "❌ server.js not found"
    exit 1
fi

if [ -f "tools.py" ]; then
    size=$(wc -c < tools.py)
    echo "   ✅ tools.py ($((size / 1024))KB)"
else
    echo "❌ tools.py not found"
    exit 1
fi

if [ -f "wallet_manager.py" ]; then
    size=$(wc -c < wallet_manager.py)
    echo "   ✅ wallet_manager.py ($((size / 1024))KB)"
else
    echo "❌ wallet_manager.py not found"
    exit 1
fi

# Test 9: Server syntax check
echo ""
echo "⚙️  Test 9: Checking Node.js server syntax..."
if ! node -c server.js 2>/dev/null; then
    echo "❌ server.js has syntax errors"
    exit 1
fi
echo "   ✅ server.js syntax valid"

# All tests passed
echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                                                           ║"
echo "║          ✅ All Tests Passed!                             ║"
echo "║                                                           ║"
echo "║  The Alpha-Consumer Agent is ready to use!               ║"
echo "║                                                           ║"
echo "║  Next steps:                                              ║"
echo "║  1. Edit .env with your credentials                      ║"
echo "║  2. Run: ./start_server.sh  (Terminal 1)                 ║"
echo "║  3. Run: ./start_agent.sh   (Terminal 2)                 ║"
echo "║                                                           ║"
echo "╚═══════════════════════════════════════════════════════════╝"
