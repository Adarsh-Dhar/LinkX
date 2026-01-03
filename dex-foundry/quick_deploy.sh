#!/bin/bash
# Quick Testnet Deployment Helper
# Executes the Mock DEX deployment with verification steps

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🚀 Mock DEX Testnet Deployment Helper"
echo "======================================"
echo ""

# Check if we're in the right directory
if [ ! -f "$SCRIPT_DIR/foundry.toml" ]; then
    echo "❌ Error: foundry.toml not found in current directory"
    echo "Please run this script from the dex-foundry directory"
    exit 1
fi

# Check if .env exists
if [ ! -f "$SCRIPT_DIR/../agent/.env" ]; then
    echo "❌ Error: .env file not found at ../agent/.env"
    exit 1
fi

# Load environment
export $(cat "$SCRIPT_DIR/../agent/.env" | grep -v '^#' | xargs)

# Verify prerequisites
echo "📋 Checking prerequisites..."
echo ""

if ! command -v forge &> /dev/null; then
    echo "❌ Foundry not installed"
    echo "Install from: https://getfoundry.sh"
    exit 1
fi
echo "✅ Foundry installed: $(forge --version)"

if ! command -v cast &> /dev/null; then
    echo "❌ cast not installed"
    exit 1
fi
echo "✅ cast available"

if [ -z "$WALLET_PRIVATE_KEY" ]; then
    echo "❌ WALLET_PRIVATE_KEY not set in .env"
    exit 1
fi
echo "✅ Wallet configured"

if [ -z "$CRONOS_RPC_URL" ]; then
    echo "❌ CRONOS_RPC_URL not set in .env"
    exit 1
fi
echo "✅ RPC URL configured: $CRONOS_RPC_URL"

echo ""
echo "✅ All prerequisites met!"
echo ""
echo "🔗 Network: Cronos Testnet (Chain ID: 338)"
echo "💾 RPC: $CRONOS_RPC_URL"
echo ""

# Ask for confirmation
echo "Ready to deploy? (y/n)"
read -r confirm

if [ "$confirm" != "y" ]; then
    echo "Deployment cancelled"
    exit 0
fi

echo ""
echo "Starting deployment in 3 seconds..."
sleep 3

# Run deployment
bash "$SCRIPT_DIR/deploy_mock_dex.sh"
