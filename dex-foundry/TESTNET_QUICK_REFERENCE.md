# Testnet Deployment - Quick Reference

## TL;DR - Deploy in 30 seconds

```bash
cd /Users/adarsh/Documents/alpha-consumer/dex-foundry
./quick_deploy.sh
# Answer 'y' when prompted
# Wait for completion
```

## What Happens

1. ✅ Deploys USDC, VVS, WCRO mock tokens to Cronos Testnet
2. ✅ Deploys MockRouter with hardcoded rates (1 USDC = 55 VVS)
3. ✅ Automatically executes swap: 1 USDC → 55 VVS
4. ✅ Saves deployment info to `testnet_deployment.json`
5. ✅ Shows testnet explorer link

## After Deployment

### Option A: Quick Verification
```bash
./verify_testnet.sh
```

### Option B: Detailed Verification
```bash
python3 verify_testnet.py
```

### Option C: Manual Check
1. Get addresses from `testnet_deployment.json`
2. Visit https://testnet.cronoscan.com
3. Paste contract address
4. Verify code is deployed

## Network Details

- **Network**: Cronos Testnet
- **Chain ID**: 338
- **RPC**: https://evm-t3.cronos.org
- **Explorer**: https://testnet.cronoscan.com
- **Faucet**: https://cronos.org/faucet (if you need test CRO)

## Exchange Rates (Fixed)

| Pair | Rate |
|------|------|
| USDC → VVS | 1 USDC = 55 VVS |
| VVS → USDC | 55 VVS = 1 USDC |
| USDC → WCRO | 1 USDC = 10 WCRO |
| WCRO → USDC | 10 WCRO = 1 USDC |

## Deployed Contracts

```json
{
  "DeployMockDEX": "0x...",
  "USDC": "0x...",
  "VVS": "0x...",
  "WCRO": "0x...",
  "Router": "0x..."
}
```

See `testnet_deployment.json` for actual addresses after deployment.

## Files Modified/Created

### Modified
- `deploy_mock_dex.sh` - Now executes hardcoded swap
- `src/MockRouter.sol` - Now transfers tokens during swaps
- `foundry.toml` - Testnet configuration

### Created
- `quick_deploy.sh` - One-command deployment
- `verify_testnet.sh` - Bash verification
- `verify_testnet.py` - Python verification
- `TESTNET_DEPLOYMENT_GUIDE.md` - Full documentation
- `TESTNET_DEPLOYMENT_SUMMARY.md` - Complete summary
- `TESTNET_QUICK_REFERENCE.md` - This file

## Troubleshooting

**Error: Foundry not found**
```bash
curl -L https://foundry.paradigm.xyz | bash && foundryup
```

**Error: .env file not found**
- Check `../agent/.env` exists
- Verify `WALLET_PRIVATE_KEY` is set
- Verify `CRONOS_RPC_URL` is set

**Error: Insufficient funds**
- Get testnet CRO: https://cronos.org/faucet
- Need ~0.1 CRO for deployment gas

**Transaction pending**
- Wait 30-60 seconds for testnet confirmation
- Check explorer: https://testnet.cronoscan.com

## Contract Interaction

### Get Token Info
```bash
# Get token name
cast call 0x... "name()(string)" --rpc-url https://evm-t3.cronos.org

# Get token balance
cast call 0x... "balanceOf(address)(uint256)" <address> --rpc-url https://evm-t3.cronos.org
```

### Execute Swap
```bash
cast send 0x... "swapExactTokensForTokens(...)" \
  <amountIn> <amountOutMin> "[tokenIn,tokenOut]" <to> <deadline> \
  --rpc-url https://evm-t3.cronos.org \
  --private-key <key>
```

## Important Notes

⚠️ **Testnet Only** - Do not use for production
⚠️ **No Slippage** - Fixed exchange rates
⚠️ **No Liquidity** - Mock DEX only
⚠️ **Auto Swap** - Swap happens automatically on deployment

## Success Indicators

You know deployment succeeded when:
1. ✅ Script completes without errors
2. ✅ `testnet_deployment.json` is created
3. ✅ Contract addresses are shown
4. ✅ Swap transaction hash is provided
5. ✅ Explorer link works

## Support Resources

- **Foundry Docs**: https://book.getfoundry.sh
- **Cronos Testnet**: https://testnet.cronoscan.com
- **Web3.py Docs**: https://web3py.readthedocs.io
- **Solidity Docs**: https://docs.soliditylang.org

---

**Ready to Deploy?**
```bash
cd /Users/adarsh/Documents/alpha-consumer/dex-foundry
./quick_deploy.sh
```

**Want Details?**
See [TESTNET_DEPLOYMENT_GUIDE.md](./TESTNET_DEPLOYMENT_GUIDE.md)

**Need Help?**
See [TESTNET_DEPLOYMENT_SUMMARY.md](./TESTNET_DEPLOYMENT_SUMMARY.md)
