# Testnet Deployment Guide

## Overview
This guide explains how to deploy the Mock DEX to Cronos Testnet with hardcoded pricing (1 USDC = 55 VVS) and execute a direct swap transaction.

**Important**: This deployment is **TESTNET ONLY** with no liquidity creation. All transactions execute directly with hardcoded values.

## Prerequisites

1. **Foundry Installed**
   ```bash
   curl -L https://foundry.paradigm.xyz | bash
   foundryup
   ```

2. **Environment Variables** (in `../agent/.env`)
   ```
   CHAIN_ID=338
   CRONOS_RPC_URL=https://evm-t3.cronos.org
   WALLET_PRIVATE_KEY=<your_private_key>
   ```

3. **Test CRO in Wallet** (from Cronos Testnet Faucet)
   - Get testnet CRO: https://cronos.org/faucet

## What Gets Deployed

### Contracts
1. **DeployMockDEX** - Main deployment contract
2. **MockERC20 (USDC)** - 1M USDC tokens (6 decimals)
3. **MockERC20 (VVS)** - 55M VVS tokens (18 decimals)
4. **MockERC20 (WCRO)** - 10K WCRO tokens (18 decimals)
5. **MockRouter** - Hardcoded swap router with 1 USDC = 55 VVS rate

### Transactions
- **Contract Deployment**: Deploys all contracts to testnet
- **Swap Transaction**: Executes 1 USDC → 55 VVS swap with hardcoded values

## Deployment Steps

### 1. Navigate to the dex-foundry directory
```bash
cd /Users/adarsh/Documents/alpha-consumer/dex-foundry
```

### 2. Run the deployment script
```bash
chmod +x deploy_mock_dex.sh
./deploy_mock_dex.sh
```

### 3. Monitor the deployment
The script will:
- Build all contracts
- Deploy contracts to Cronos Testnet
- Retrieve token addresses
- Execute hardcoded swap transaction (1 USDC = 55 VVS)
- Save deployment info to `testnet_deployment.json`

### 4. Verify deployment
Check the generated `testnet_deployment.json` file:
```json
{
  "network": "cronos-testnet",
  "chainId": 338,
  "contracts": {
    "deployMockDEX": "0x...",
    "usdc": "0x...",
    "vvs": "0x...",
    "wcro": "0x...",
    "router": "0x..."
  },
  "swap": {
    "transactionHash": "0x...",
    "exchangeRate": "1 USDC = 55 VVS"
  }
}
```

## Exchange Rates (Hardcoded)

| From | To | Rate |
|------|----|----|
| USDC | VVS | 1 USDC = 55 VVS |
| VVS | USDC | 55 VVS = 1 USDC |
| USDC | WCRO | 1 USDC = 10 WCRO |
| WCRO | USDC | 10 WCRO = 1 USDC |

## Contract Interfaces

### DeployMockDEX
```solidity
function getAddresses() external view returns (
    address _usdc,
    address _vvs,
    address _wcro,
    address _router
)
```

### MockRouter
```solidity
// Get swap output amount
function getAmountsOut(uint256 amountIn, address[] memory path) 
    external view returns (uint256[] memory amounts)

// Execute swap with tokens
function swapExactTokensForTokens(
    uint256 amountIn,
    uint256 amountOutMin,
    address[] calldata path,
    address to,
    uint256 deadline
) external returns (uint256[] memory amounts)

// Get hardcoded rates
function getExchangeRate() external pure returns (
    uint256 usdcToVvs, 
    uint256 vvsToUsdc
)
```

## Important Notes

⚠️ **Testnet Only**: This deployment is intended for testing purposes only.

⚠️ **No Liquidity Pools**: This is a mock DEX with no actual liquidity pools. Swaps execute at fixed hardcoded rates.

⚠️ **No Slippage**: Since rates are hardcoded, there is no slippage.

⚠️ **Direct Token Transfers**: The MockRouter directly transfers tokens from sender to recipient without any actual market mechanics.

## Troubleshooting

### Error: "Foundry not found"
Install Foundry: `curl -L https://foundry.paradigm.xyz | bash && foundryup`

### Error: ".env file not found"
Ensure `../agent/.env` exists with required variables:
- CHAIN_ID
- CRONOS_RPC_URL
- WALLET_PRIVATE_KEY

### Error: "Insufficient funds"
Get test CRO from Cronos Testnet Faucet: https://cronos.org/faucet

### Transaction appears to hang
The script has a 1-hour deadline. If transaction takes longer:
1. Check testnet explorer: https://testnet.cronoscan.com
2. Wait a few blocks for confirmation
3. Check gas prices - may need adjustment

## Network Details

- **Network**: Cronos Testnet
- **Chain ID**: 338
- **RPC Endpoint**: https://evm-t3.cronos.org
- **Block Time**: ~6 seconds
- **Explorer**: https://testnet.cronoscan.com
- **Faucet**: https://cronos.org/faucet

## Support

For issues or questions:
1. Check testnet explorer for transaction details
2. Verify .env file configuration
3. Ensure sufficient testnet CRO for gas fees
4. Review contract source code in `src/` directory
