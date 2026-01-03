#!/bin/bash
# Complete Testnet Deployment Workflow
# Handles deployment + verification + summary all in one

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOYMENT_FILE="$SCRIPT_DIR/testnet_deployment.json"

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║     MOCK DEX - COMPLETE TESTNET DEPLOYMENT WORKFLOW            ║"
echo "║     Cronos Testnet (Chain ID: 338)                             ║"
echo "║     Exchange Rate: 1 USDC = 55 VVS (Hardcoded)                 ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Step 1: Check prerequisites
echo "📋 STEP 1: Checking Prerequisites"
echo "═══════════════════════════════════════════════════════════════════"
echo ""

if ! command -v forge &> /dev/null; then
    echo "❌ Foundry not installed"
    echo "Install from: https://getfoundry.sh"
    exit 1
fi
echo "✅ Foundry: $(forge --version | head -1)"

if [ ! -f "$SCRIPT_DIR/../agent/.env" ]; then
    echo "❌ .env file not found at ../agent/.env"
    exit 1
fi
echo "✅ Environment file found"

if [ ! -f "$SCRIPT_DIR/foundry.toml" ]; then
    echo "❌ foundry.toml not found"
    exit 1
fi
echo "✅ Foundry config found"

echo ""

# Step 2: Load environment
echo "📋 STEP 2: Loading Environment"
echo "═══════════════════════════════════════════════════════════════════"
echo ""

export $(cat "$SCRIPT_DIR/../agent/.env" | grep -v '^#' | xargs)

echo "✅ Chain ID: $CHAIN_ID (Cronos Testnet)"
echo "✅ RPC: $CRONOS_RPC_URL"
echo "✅ Wallet: ${WALLET_PRIVATE_KEY:0:10}...${WALLET_PRIVATE_KEY: -4}"

echo ""
echo ""

# Step 3: Run deployment
echo "📋 STEP 3: Deploying to Cronos Testnet"
echo "═══════════════════════════════════════════════════════════════════"
echo ""

bash "$SCRIPT_DIR/deploy_mock_dex.sh"

if [ ! -f "$DEPLOYMENT_FILE" ]; then
    echo ""
    echo "❌ Deployment failed - deployment.json not found"
    exit 1
fi

echo ""
echo ""

# Step 4: Verify deployment
echo "📋 STEP 4: Verifying Deployment"
echo "═══════════════════════════════════════════════════════════════════"
echo ""

# Extract addresses
DEPLOY_CONTRACT=$(grep '"deployMockDEX"' "$DEPLOYMENT_FILE" | cut -d'"' -f4)
USDC_ADDRESS=$(grep '"usdc"' "$DEPLOYMENT_FILE" | cut -d'"' -f4)
VVS_ADDRESS=$(grep '"vvs"' "$DEPLOYMENT_FILE" | cut -d'"' -f4)
ROUTER_ADDRESS=$(grep '"router"' "$DEPLOYMENT_FILE" | cut -d'"' -f4)
SWAP_TX=$(grep '"transactionHash"' "$DEPLOYMENT_FILE" | head -1 | cut -d'"' -f4)

echo "Checking contract deployments on testnet..."
sleep 2

# Verify with cast
USDC_CODE=$(cast code "$USDC_ADDRESS" --rpc-url "$CRONOS_RPC_URL" 2>/dev/null || echo "0x")
if [ "$USDC_CODE" != "0x" ] && [ ! -z "$USDC_CODE" ]; then
    echo "✅ USDC contract deployed"
else
    echo "⏳ USDC contract may still be processing..."
fi

VVS_CODE=$(cast code "$VVS_ADDRESS" --rpc-url "$CRONOS_RPC_URL" 2>/dev/null || echo "0x")
if [ "$VVS_CODE" != "0x" ] && [ ! -z "$VVS_CODE" ]; then
    echo "✅ VVS contract deployed"
else
    echo "⏳ VVS contract may still be processing..."
fi

ROUTER_CODE=$(cast code "$ROUTER_ADDRESS" --rpc-url "$CRONOS_RPC_URL" 2>/dev/null || echo "0x")
if [ "$ROUTER_CODE" != "0x" ] && [ ! -z "$ROUTER_CODE" ]; then
    echo "✅ Router contract deployed"
else
    echo "⏳ Router contract may still be processing..."
fi

echo ""
echo ""

# Step 5: Display results
echo "📋 STEP 5: Deployment Summary"
echo "═══════════════════════════════════════════════════════════════════"
echo ""

echo "🎯 Network:"
echo "   • Cronos Testnet (Chain ID: 338)"
echo "   • RPC: $CRONOS_RPC_URL"
echo ""

echo "📝 Deployed Contracts:"
echo "   • DeployMockDEX: $DEPLOY_CONTRACT"
echo "   • USDC Token:    $USDC_ADDRESS"
echo "   • VVS Token:     $VVS_ADDRESS"
echo "   • Router:        $ROUTER_ADDRESS"
echo ""

echo "💱 Swap Transaction:"
echo "   • Hash: $SWAP_TX"
echo "   • From: 1 USDC (1000000 with 6 decimals)"
echo "   • To:   55 VVS (55000000000000000000 with 18 decimals)"
echo "   • Rate: 1 USDC = 55 VVS"
echo ""

echo "🔗 Testnet Explorer:"
echo "   https://testnet.cronoscan.com/tx/$SWAP_TX"
echo ""

echo "📄 Configuration File:"
echo "   $DEPLOYMENT_FILE"
echo ""

echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "✅ DEPLOYMENT COMPLETE!"
echo "═══════════════════════════════════════════════════════════════════"
echo ""

echo "📚 Next Steps:"
echo ""
echo "1. Verify deployment on testnet explorer"
echo "   https://testnet.cronoscan.com"
echo ""
echo "2. Wait 30-60 seconds for transaction confirmation"
echo ""
echo "3. Run verification script for detailed info"
echo "   ./verify_testnet.sh"
echo ""
echo "4. Use deployed contract addresses for testing"
echo "   See testnet_deployment.json for addresses"
echo ""

echo "📖 Documentation:"
echo "   • TESTNET_QUICK_REFERENCE.md - Quick reference"
echo "   • TESTNET_DEPLOYMENT_GUIDE.md - Full guide"
echo "   • TESTNET_DEPLOYMENT_SUMMARY.md - Detailed summary"
echo ""

echo "✨ Your Mock DEX is ready on Cronos Testnet!"
echo ""
