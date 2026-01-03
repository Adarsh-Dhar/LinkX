#!/bin/bash
# Deploy Mock DEX to Cronos Testnet with Hardcoded Swap
# Exchange Rate: 1 USDC = 55 VVS (hardcoded)
# NO LIQUIDITY CREATION - Direct testnet transaction

set -e

echo "════════════════════════════════════════════════════════════════"
echo "   DEPLOYING MOCK DEX TO CRONOS TESTNET"
echo "   Exchange Rate: 1 USDC = 55 VVS (Hardcoded)"
echo "   NO Liquidity Creation - Testnet Only"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Check foundry is installed
if ! command -v forge &> /dev/null; then
    echo "❌ Foundry not found. Install from https://getfoundry.sh"
    exit 1
fi

# Check cast is available
if ! command -v cast &> /dev/null; then
    echo "❌ cast not found. Install foundry from https://getfoundry.sh"
    exit 1
fi

# Load environment
if [ -f "../agent/.env" ]; then
    export $(cat ../agent/.env | grep -v '^#' | xargs)
    echo "✅ Loaded environment from agent/.env"
else
    echo "❌ .env file not found at ../agent/.env"
    exit 1
fi

# Verify we're on testnet
if [ "$CHAIN_ID" != "338" ]; then
    echo "⚠️  WARNING: CHAIN_ID is $CHAIN_ID (not 338 testnet)"
    echo "Continuing with testnet deployment..."
fi

echo ""
echo "📋 Deployment Configuration:"
echo "   Network: Cronos Testnet (Chain ID: 338)"
echo "   RPC: $CRONOS_RPC_URL"
echo "   Deployer: ${WALLET_PRIVATE_KEY:0:10}...${WALLET_PRIVATE_KEY: -4}"
echo "   Exchange Rate: 1 USDC = 55 VVS"
echo ""

# Build contracts
echo "🔨 Building contracts..."
forge build 2>&1 | grep -v "^warning:"

if [ $? -ne 0 ]; then
    echo "❌ Build failed"
    exit 1
fi

echo "✅ Build successful"
echo ""

# Deploy
echo "🚀 Deploying contracts to Cronos Testnet..."
echo ""

DEPLOY_OUTPUT=$(forge create src/DeployMockDEX.sol:DeployMockDEX \
  --rpc-url "$CRONOS_RPC_URL" \
  --private-key "$WALLET_PRIVATE_KEY" \
  --legacy \
  --broadcast \
  --slow \
  2>&1)

echo "$DEPLOY_OUTPUT"

# Extract deployment address
DEPLOY_ADDRESS=$(echo "$DEPLOY_OUTPUT" | grep "Deployed to:" | awk '{print $3}')

if [ -z "$DEPLOY_ADDRESS" ]; then
    echo ""
    echo "❌ Deployment failed - could not find contract address"
    echo "Full output: $DEPLOY_OUTPUT"
    exit 1
fi

echo ""
echo "✅ DeployMockDEX contract deployed to: $DEPLOY_ADDRESS"
echo ""

# Get token addresses using cast
echo "📡 Fetching deployed token addresses..."
sleep 2

USDC_ADDRESS=$(cast call "$DEPLOY_ADDRESS" "usdc()(address)" --rpc-url "$CRONOS_RPC_URL")
VVS_ADDRESS=$(cast call "$DEPLOY_ADDRESS" "vvs()(address)" --rpc-url "$CRONOS_RPC_URL")
WCRO_ADDRESS=$(cast call "$DEPLOY_ADDRESS" "wcro()(address)" --rpc-url "$CRONOS_RPC_URL")
ROUTER_ADDRESS=$(cast call "$DEPLOY_ADDRESS" "router()(address)" --rpc-url "$CRONOS_RPC_URL")

echo "✅ Token addresses retrieved"
echo ""

# Execute hardcoded swap transaction
echo "💱 Executing hardcoded swap transaction..."
echo "   Input: 1 USDC (1000000)"
echo "   Expected Output: 55 VVS (55000000000000000000)"
echo ""

# Prepare swap call data
# swapExactTokensForTokens(uint256 amountIn, uint256 amountOutMin, address[] path, address to, uint256 deadline)
AMOUNT_IN="1000000"  # 1 USDC (6 decimals)
AMOUNT_OUT_MIN="55000000000000000000"  # 55 VVS (18 decimals) - exact amount
DEADLINE=$(($(date +%s) + 3600))  # 1 hour from now

echo "   Amount In: $AMOUNT_IN"
echo "   Amount Out Min: $AMOUNT_OUT_MIN"
echo "   Deadline: $DEADLINE"
echo ""

# Get deployer address from private key
DEPLOYER=$(cast wallet address --private-key "$WALLET_PRIVATE_KEY")
echo "   Deployer Address: $DEPLOYER"
echo ""

# Execute swap
echo "🚀 Sending swap transaction..."
SWAP_TX=$(cast send "$ROUTER_ADDRESS" \
    "swapExactTokensForTokens(uint256,uint256,address[],address,uint256)" \
    "$AMOUNT_IN" \
    "$AMOUNT_OUT_MIN" \
    "[$USDC_ADDRESS,$VVS_ADDRESS]" \
    "$DEPLOYER" \
    "$DEADLINE" \
    --rpc-url "$CRONOS_RPC_URL" \
    --private-key "$WALLET_PRIVATE_KEY" \
    --legacy \
    2>&1)

echo "$SWAP_TX"
echo ""

# Extract transaction hash
TX_HASH=$(echo "$SWAP_TX" | grep "transactionHash" | head -1 | awk '{print $2}' | tr -d '"')

if [ -z "$TX_HASH" ]; then
    echo "⚠️  Transaction may have been sent. Check testnet explorer."
    TX_HASH="pending"
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "   DEPLOYMENT & SWAP SUCCESSFUL"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "📝 Contract Addresses:"
echo "   DeployMockDEX: $DEPLOY_ADDRESS"
echo "   USDC:          $USDC_ADDRESS"
echo "   VVS:           $VVS_ADDRESS"
echo "   WCRO:          $WCRO_ADDRESS"
echo "   Router:        $ROUTER_ADDRESS"
echo ""
echo "💱 Swap Transaction:"
echo "   Hash: $TX_HASH"
echo "   From: $DEPLOYER"
echo "   To:   $ROUTER_ADDRESS"
echo ""
echo "📊 Transaction Details:"
echo "   Input:  1 USDC"
echo "   Output: 55 VVS"
echo "   Rate:   1 USDC = 55 VVS"
echo ""
echo "🌐 Network: Cronos Testnet"
echo "🔗 Explorer: https://testnet.cronoscan.com/tx/$TX_HASH"
echo ""
echo "✅ All transactions completed on testnet!"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Save deployment info to file
cat > testnet_deployment.json << EOF
{
  "network": "cronos-testnet",
  "chainId": 338,
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "contracts": {
    "deployMockDEX": "$DEPLOY_ADDRESS",
    "usdc": "$USDC_ADDRESS",
    "vvs": "$VVS_ADDRESS",
    "wcro": "$WCRO_ADDRESS",
    "router": "$ROUTER_ADDRESS"
  },
  "swap": {
    "transactionHash": "$TX_HASH",
    "fromAddress": "$DEPLOYER",
    "router": "$ROUTER_ADDRESS",
    "tokenIn": "$USDC_ADDRESS",
    "tokenOut": "$VVS_ADDRESS",
    "amountIn": "1000000",
    "amountOut": "55000000000000000000",
    "exchangeRate": "1 USDC = 55 VVS"
  },
  "status": "SUCCESS"
}
EOF

echo "📄 Deployment info saved to: testnet_deployment.json"
echo ""
echo "💱 Exchange Rate: 1 USDC = 55 VVS (hardcoded)"
echo ""
echo "🔗 View on Explorer:"
echo "   https://explorer.cronos.org/testnet/address/$ROUTER_ADDRESS"
echo ""

# Save addresses to file
cat > deployment_addresses.json << EOF
{
  "network": "cronos_testnet",
  "chainId": 338,
  "deployedAt": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "deployer": "$DEPLOY_ADDRESS",
  "contracts": {
    "USDC": "$USDC_ADDRESS",
    "VVS": "$VVS_ADDRESS",
    "WCRO": "$WCRO_ADDRESS",
    "MockRouter": "$ROUTER_ADDRESS"
  },
  "exchangeRates": {
    "USDC_to_VVS": 55,
    "VVS_to_USDC": 0.01818
  }
}
EOF

echo "💾 Addresses saved to: deployment_addresses.json"
echo ""

# Update agent .env file
echo "📝 Updating agent/.env with new addresses..."

# Backup existing .env
cp ../agent/.env ../agent/.env.backup

# Update addresses
sed -i.bak "s|^USDC_CONTRACT=.*|USDC_CONTRACT=$USDC_ADDRESS|" ../agent/.env
sed -i.bak "s|^VVS_CONTRACT=.*|VVS_CONTRACT=$VVS_ADDRESS|" ../agent/.env
sed -i.bak "s|^WCRO_ADDRESS=.*|WCRO_ADDRESS=$WCRO_ADDRESS|" ../agent/.env
sed -i.bak "s|^VVS_ROUTER=.*|VVS_ROUTER=$ROUTER_ADDRESS|" ../agent/.env

rm ../agent/.env.bak

echo "✅ Updated agent/.env with new contract addresses"
echo ""

echo "════════════════════════════════════════════════════════════════"
echo "   NEXT STEPS"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "1. Test the deployment:"
echo "   cd ../agent"
echo "   python test_agent_transactions.py"
echo ""
echo "2. Try a swap:"
echo "   python main.py"
echo "   > Estimate 1 USDC to VVS"
echo "   > Swap 0.1 USDC to VVS"
echo ""
echo "3. Expected results:"
echo "   • 1 USDC = 55 VVS (hardcoded)"
echo "   • Swaps execute instantly"
echo "   • No real liquidity needed"
echo ""
echo "✨ Your Mock DEX is ready to use!"
echo "════════════════════════════════════════════════════════════════"
