#!/bin/bash

# Alpha-Consumer Agent - Quick Start Script
# This script helps you quickly set up and test the agent

set -e  # Exit on error

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                                                           ║"
echo "║      🚀 Alpha-Consumer Agent Quick Start                  ║"
echo "║                                                           ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command_exists python3; then
    echo "❌ Python 3 not found. Please install Python 3.9 or higher."
    exit 1
fi
echo "✅ Python 3 found: $(python3 --version)"

if ! command_exists node; then
    echo "❌ Node.js not found. Please install Node.js 18 or higher."
    exit 1
fi
echo "✅ Node.js found: $(node --version)"

if ! command_exists npm; then
    echo "❌ npm not found. Please install npm."
    exit 1
fi
echo "✅ npm found: $(npm --version)"

echo ""
echo "📦 Installing dependencies..."

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Install Python dependencies
echo "Installing Python packages..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

source venv/bin/activate
pip install -r requirements.txt
deactivate
echo "✅ Python dependencies installed"

# Install Node dependencies
echo "Installing Node.js packages..."
npm install --silent
echo "✅ Node.js dependencies installed"

echo ""
echo "🔧 Configuration check..."

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found"
    echo "📝 Copying .env.example to .env"
    cp .env.example .env
    echo "⚠️  Please edit .env and add your credentials!"
    NEEDS_CONFIG=true
fi

if [ "$NEEDS_CONFIG" = true ]; then
    echo ""
    echo "╔═══════════════════════════════════════════════════════════╗"
    echo "║                                                           ║"
    echo "║  ⚠️  CONFIGURATION REQUIRED                                ║"
    echo "║                                                           ║"
    echo "║  Please edit .env file with:                              ║"
    echo "║  1. GEMINI_API_KEY (from Google AI Studio)               ║"
    echo "║  2. WALLET_PRIVATE_KEY (generate with wallet_manager.py) ║"
    echo "║  3. SELLER_WALLET (address to receive payments)          ║"
    echo "║  4. USDC_CONTRACT (testnet USDC address)                 ║"
    echo "║                                                           ║"
    echo "║  Get testnet funds:                                       ║"
    echo "║  https://cronos.org/faucet                                ║"
    echo "║                                                           ║"
    echo "║  Then run this script again.                              ║"
    echo "║                                                           ║"
    echo "╚═══════════════════════════════════════════════════════════╝"
    exit 0
fi

echo "✅ Configuration files found"

echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                                                           ║"
echo "║  ✅ Setup Complete!                                        ║"
echo "║                                                           ║"
echo "║  To start the system:                                     ║"
echo "║                                                           ║"
echo "║  Terminal 1 (Server):                                     ║"
echo "║  $ ./start_server.sh                                      ║"
echo "║                                                           ║"
echo "║  Terminal 2 (Agent):                                      ║"
echo "║  $ ./start_agent.sh                                       ║"
echo "║                                                           ║"
echo "║  Or test individual components:                           ║"
echo "║  $ node server.js              (start server)             ║"
echo "║  $ source venv/bin/activate    (activate Python env)     ║"
echo "║  $ python main.py              (start agent)              ║"
echo "║                                                           ║"
echo "║  Generate a wallet:                                       ║"
echo "║  $ python wallet_manager.py                               ║"
echo "║                                                           ║"
echo "╚═══════════════════════════════════════════════════════════╝"