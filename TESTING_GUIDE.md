# Testing Guide for AI Trading Agent

## Overview
This guide explains how to test all transaction capabilities of your AI trading agent.

## Test Files Created

1. **`test_agent_transactions.py`** - Manual test script with detailed output
2. **`tests/test_transactions.py`** - Pytest test suite for automated testing

---

## Quick Start: Run All Tests

### Option 1: Manual Test Script (Recommended for first-time)
```bash
cd /Users/adarsh/Documents/alpha-consumer/agent
python test_agent_transactions.py
```

**What it tests:**
- ✅ Environment configuration (.env file)
- ✅ Web3 RPC connection to Cronos testnet
- ✅ Wallet balances (CRO, USDC, WTCRO)
- ✅ Token swap estimation
- ✅ Mock swap execution
- ✅ Trading history
- ✅ Smart contract verification
- ✅ Gas price estimation

**Expected output:** Detailed pass/fail for each test with explanations.

---

### Option 2: Pytest Suite (Automated Testing)
```bash
cd /Users/adarsh/Documents/alpha-consumer/agent
pytest tests/test_transactions.py -v
```

**Run specific test groups:**
```bash
# Test only Web3 connection
pytest tests/test_transactions.py::TestWeb3Connection -v

# Test only balance queries
pytest tests/test_transactions.py::TestWalletBalance -v

# Test only swap functionality
pytest tests/test_transactions.py::TestSwapEstimation -v

# Run integration tests
pytest tests/test_transactions.py::TestIntegration -v -m integration
```

---

## Testing Real Transactions from the Agent

### Method 1: Using the Agent Interface (Interactive)

**Start the agent:**
```bash
cd /Users/adarsh/Documents/alpha-consumer/agent
python main.py
```

**Test commands to try:**

1. **Check Balances**
   ```
   > What are my token balances?
   ```
   
2. **Estimate Swap**
   ```
   > Estimate 1 USDC to VVS
   > How much VVS can I get for 10 USDC?
   ```

3. **Execute Mock Swap**
   ```
   > Swap 0.1 USDC to VVS
   ```
   Note: On testnet, this will likely be a mock swap due to lack of liquidity.

4. **Check Transaction History**
   ```
   > Show my trading history
   > What trades have I made?
   ```

---

### Method 2: Direct Tool Testing (Python REPL)

**Test individual tools:**
```python
cd /Users/adarsh/Documents/alpha-consumer/agent
python

# In Python REPL:
from tools import get_token_balance, estimate_swap_output, execute_vvs_swap

# Test 1: Check CRO balance
result = get_token_balance.invoke({"token_address": "cro"})
print(result)
# Expected: {'token': 'CRO', 'balance_readable': 46.88, ...}

# Test 2: Check USDC balance
import os
from dotenv import load_dotenv
load_dotenv()
usdc = os.getenv("USDC_CONTRACT")
result = get_token_balance.invoke({"token_address": usdc})
print(result)
# Expected: {'token': '0xc01e...', 'balance_readable': 9.3, ...}

# Test 3: Estimate swap
result = estimate_swap_output.invoke({
    "token_in": usdc,
    "token_out": os.getenv("VVS_CONTRACT"),
    "amount_in": 1.0
})
print(result)
# Expected: {'amount_out': 502402.85, 'exchange_rate': ...}

# Test 4: Execute mock swap
result = execute_vvs_swap.invoke({
    "token_in": usdc,
    "token_out": os.getenv("VVS_CONTRACT"),
    "amount_in": 0.1
})
print(result)
# Expected: {'status': 'success_mock', ...} or error due to liquidity
```

---

### Method 3: Test Actual On-Chain Transactions

⚠️ **WARNING:** This will submit real transactions to the blockchain!

**Prerequisites:**
- Wallet has sufficient CRO for gas (>1 CRO recommended)
- Wallet has tokens to swap (e.g., >1 USDC)
- Using testnet (CHAIN_ID=338) for testing

**Step 1: Check current balances**
```bash
python test_agent_transactions.py | grep "Balance"
```

**Step 2: Verify you have gas**
- Need at least 0.1 CRO for each transaction
- Typical costs: 0.02-0.08 CRO per transaction

**Step 3: Test a small swap**
```bash
python main.py
> Swap 0.1 USDC to VVS
```

**Step 4: Verify transaction**
After execution, you'll get a transaction hash. Check it on:
- Testnet: https://explorer.cronos.org/testnet/tx/{TX_HASH}
- Mainnet: https://explorer.cronos.org/tx/{TX_HASH}

---

## Understanding Test Results

### ✅ PASS Results
Tests that pass indicate:
- Configuration is correct
- Network connection is working
- Contracts are deployed and accessible
- Wallet has balances
- Agent can interact with blockchain

### ❌ FAIL Results

**Common failures and solutions:**

1. **"Could not connect to RPC"**
   - Check internet connection
   - Verify CRONOS_RPC_URL in .env
   - Try alternative RPC: https://evm-cronos.org

2. **"No output" on swap estimation**
   - This is NORMAL on testnet (limited liquidity)
   - Agent uses mock pricing instead
   - Works fine on mainnet with real liquidity

3. **"Execution reverted" on swaps**
   - Testnet doesn't have USDC/VVS liquidity
   - Expected behavior on testnet
   - Use mainnet for real swaps

4. **"Insufficient balance"**
   - Need CRO for gas fees
   - Get testnet CRO: https://cronos.org/faucet
   - Need actual token balance to swap

---

## Verifying Transactions On-Chain

### Check Transaction Status
```python
from web3 import Web3
w3 = Web3(Web3.HTTPProvider("https://evm-t3.cronos.org"))

tx_hash = "0x..." # Your transaction hash
receipt = w3.eth.get_transaction_receipt(tx_hash)

print(f"Status: {'✅ SUCCESS' if receipt.status == 1 else '❌ FAILED'}")
print(f"Block: {receipt.blockNumber}")
print(f"Gas Used: {receipt.gasUsed}")
print(f"From: {receipt['from']}")
print(f"To: {receipt['to']}")
```

### View on Block Explorer
**Testnet:**
- Transaction: `https://explorer.cronos.org/testnet/tx/{TX_HASH}`
- Your wallet: `https://explorer.cronos.org/testnet/address/{WALLET_ADDRESS}`

**Mainnet:**
- Transaction: `https://explorer.cronos.org/tx/{TX_HASH}`
- Your wallet: `https://explorer.cronos.org/address/{WALLET_ADDRESS}`

---

## Testing Checklist

Before deploying to mainnet, ensure:

- [ ] All environment variables configured
- [ ] Web3 connection working
- [ ] Can check wallet balances
- [ ] Can estimate swap outputs
- [ ] Contracts verified on explorer
- [ ] Gas estimation working
- [ ] Mock swaps execute without errors
- [ ] Agent responds to queries
- [ ] Trading history tracking works

---

## Mainnet Testing (Real Money!)

⚠️ **EXTREMELY IMPORTANT:** Use small amounts first!

### Pre-deployment Checklist
1. [ ] Update .env to mainnet values:
   ```
   CHAIN_ID=25
   CRONOS_RPC_URL=https://rpc.cronos.org
   VVS_ROUTER=0x145677FC4d9b8F19B4172A2b88f7fb1f02fdf220
   ```

2. [ ] Fund wallet with:
   - Minimum: $10-20 CRO for gas
   - Minimum: $50-100 USDC for trading

3. [ ] Test with small amounts:
   ```
   > Swap 1 USDC to VVS
   ```

4. [ ] Verify transaction succeeds:
   - Check balance changed
   - Verify on explorer
   - Ensure expected output received

### Mainnet Test Script
```bash
# 1. Update to mainnet config
cp .env .env.testnet.backup
# Edit .env with mainnet values

# 2. Run connection tests
python test_agent_transactions.py

# 3. Test with small amount via agent
python main.py
> Check my balances
> Estimate 1 USDC to VVS
> Swap 0.5 USDC to VVS  # Start small!

# 4. Verify on mainnet explorer
# Visit: https://explorer.cronos.org/address/{YOUR_WALLET}
```

---

## Continuous Testing (CI/CD)

**Run tests before every deployment:**
```bash
#!/bin/bash
# test_before_deploy.sh

echo "🧪 Running pre-deployment tests..."

# Run pytest
pytest tests/test_transactions.py -v
if [ $? -ne 0 ]; then
    echo "❌ Tests failed! Do not deploy."
    exit 1
fi

# Run manual tests
python test_agent_transactions.py > test_output.txt
if grep -q "❌ FAIL" test_output.txt; then
    echo "⚠️  Some tests failed. Review test_output.txt"
    exit 1
fi

echo "✅ All tests passed! Safe to deploy."
```

---

## Troubleshooting

### Agent won't start
```bash
# Check Python version
python --version  # Should be 3.12+

# Check dependencies
pip install -r requirements.txt

# Check .env file exists
ls -la .env

# Test environment loading
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('WALLET_PRIVATE_KEY')[:10])"
```

### Tests hang or timeout
- Check RPC URL is accessible
- Try alternative RPC endpoint
- Check internet connection
- Increase timeout in code

### Balance shows 0 but wallet has funds
- Verify correct CHAIN_ID
- Check WALLET_ADDRESS matches WALLET_PRIVATE_KEY
- Ensure using correct network (testnet vs mainnet)
- Check contract address is correct

---

## Support & Resources

**Documentation:**
- [FINAL_REPORT.txt](FINAL_REPORT.txt) - Complete deployment guide
- [agent/tools.py](agent/tools.py) - Tool implementations
- [agent/main.py](agent/main.py) - Agent entry point

**Blockchain Explorers:**
- Testnet: https://explorer.cronos.org/testnet
- Mainnet: https://explorer.cronos.org

**Get Test Tokens:**
- Testnet CRO: https://cronos.org/faucet

**For Help:**
- Check test output for specific error messages
- Review .env configuration
- Verify wallet has funds and gas
- Check RPC connectivity

---

## Example: Full Testing Session

```bash
# 1. Initial setup check
cd /Users/adarsh/Documents/alpha-consumer/agent
python test_agent_transactions.py

# 2. Run automated tests
pytest tests/test_transactions.py -v

# 3. Test agent interactively
python main.py

# In agent:
> What are my balances?
> Estimate 5 USDC to VVS
> Show me current gas prices
> What's my trading history?

# 4. Test direct swap (mock)
> Swap 0.1 USDC to VVS

# 5. Check results
> What are my balances now?
> Show my trading history

# 6. Exit and verify
# Check logs in console output
# Verify any transactions on explorer
```

---

## Success Criteria

Your agent is ready for production when:
- ✅ All tests pass
- ✅ Balances show correctly
- ✅ Estimations return reasonable values
- ✅ Mock swaps execute without errors
- ✅ Agent responds to natural language queries
- ✅ Gas estimation is reasonable (<0.1 CRO per tx)
- ✅ Contracts verified on explorer
- ✅ Trading history tracks properly

**Next Steps:** Follow [FINAL_REPORT.txt](FINAL_REPORT.txt) for mainnet deployment! 🚀
