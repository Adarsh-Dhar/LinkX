#!/usr/bin/env python3
"""
Manual Transaction Test Script for Trading Agent
Run this to test all agent transaction capabilities
"""

import os
import sys
from web3 import Web3
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Import tools
from tools import (
    get_token_balance,
    estimate_swap_output,
    execute_vvs_swap,
    get_trade_history
)

print("=" * 80)
print("TRADING AGENT - TRANSACTION TEST SCRIPT")
print("=" * 80)

def test_section(title):
    """Print test section header"""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}")

def test_result(name, passed, details=""):
    """Print test result"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} - {name}")
    if details:
        print(f"        {details}")

# ============================================================================
# TEST 1: Environment Setup
# ============================================================================
test_section("TEST 1: Environment Configuration")

wallet_key = os.getenv("WALLET_PRIVATE_KEY")
rpc_url = os.getenv("CRONOS_RPC_URL")
chain_id = os.getenv("CHAIN_ID")

test_result("Wallet Private Key", wallet_key is not None, f"Length: {len(wallet_key) if wallet_key else 0}")
test_result("RPC URL", rpc_url is not None, rpc_url)
test_result("Chain ID", chain_id is not None, chain_id)

# ============================================================================
# TEST 2: Web3 Connection
# ============================================================================
test_section("TEST 2: Blockchain Connection")

try:
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    connected = w3.is_connected()
    test_result("RPC Connection", connected)
    
    if connected:
        block_number = w3.eth.block_number
        test_result("Latest Block", True, f"Block #{block_number}")
        
        actual_chain_id = w3.eth.chain_id
        test_result("Chain ID Match", actual_chain_id == int(chain_id), 
                   f"Expected {chain_id}, Got {actual_chain_id}")
except Exception as e:
    test_result("Web3 Connection", False, str(e))

# ============================================================================
# TEST 3: Balance Checks
# ============================================================================
test_section("TEST 3: Token Balance Queries")

# Test CRO balance
try:
    result = get_token_balance.invoke({"token_address": "cro"})
    if "balance_readable" in result:
        test_result("CRO Balance", True, f"{result['balance_readable']:.4f} CRO")
    else:
        test_result("CRO Balance", False, result.get("error", "Unknown error"))
except Exception as e:
    test_result("CRO Balance", False, str(e))

# Test USDC balance
try:
    usdc_address = os.getenv("USDC_CONTRACT")
    result = get_token_balance.invoke({"token_address": usdc_address})
    if "balance_readable" in result:
        test_result("USDC Balance", True, f"{result['balance_readable']:.4f} USDC")
    else:
        test_result("USDC Balance", False, result.get("error", "Unknown error"))
except Exception as e:
    test_result("USDC Balance", False, str(e))

# Test WTCRO balance
try:
    wcro_address = os.getenv("WCRO_ADDRESS")
    result = get_token_balance.invoke({"token_address": wcro_address})
    if "balance_readable" in result:
        test_result("WTCRO Balance", True, f"{result['balance_readable']:.4f} WTCRO")
    else:
        test_result("WTCRO Balance", False, result.get("error", "Unknown error"))
except Exception as e:
    test_result("WTCRO Balance", False, str(e))

# ============================================================================
# TEST 4: Swap Estimation
# ============================================================================
test_section("TEST 4: Swap Price Estimation")

# Test 1 USDC -> VVS estimation
try:
    result = estimate_swap_output.invoke({
        "token_in": "usdc",
        "token_out": "vvs",
        "amount_in": 1.0
    })
    
    if "amount_out" in result:
        test_result("Estimate 1 USDC -> VVS", True, 
                   f"~{result['amount_out']:.2f} VVS (Rate: {result.get('exchange_rate', 0):.2f})")
    else:
        test_result("Estimate 1 USDC -> VVS", False, result.get("error", "No output"))
except Exception as e:
    test_result("Estimate 1 USDC -> VVS", False, str(e))

# Test 10 USDC -> VVS estimation
try:
    result = estimate_swap_output.invoke({
        "token_in": "usdc",
        "token_out": "vvs",
        "amount_in": 10.0
    })
    
    if "amount_out" in result:
        test_result("Estimate 10 USDC -> VVS", True, 
                   f"~{result['amount_out']:.2f} VVS")
    else:
        test_result("Estimate 10 USDC -> VVS", False, result.get("error", "No output"))
except Exception as e:
    test_result("Estimate 10 USDC -> VVS", False, str(e))

# ============================================================================
# TEST 5: Mock Swap Execution
# ============================================================================
test_section("TEST 5: Mock Swap Execution (No Real Transaction)")

try:
    result = execute_vvs_swap.invoke({
        "token_in": "usdc",
        "token_out": "vvs",
        "amount_in": 0.1
    })
    
    status = result.get("status", "unknown")
    if status == "success_mock":
        test_result("Mock Swap 0.1 USDC -> VVS", True, 
                   f"Mock successful - {result.get('amount_out_expected', 0):.4f} VVS expected")
    elif "error" in result:
        test_result("Mock Swap 0.1 USDC -> VVS", False, result["error"])
    else:
        test_result("Mock Swap 0.1 USDC -> VVS", True, f"Status: {status}")
except Exception as e:
    test_result("Mock Swap 0.1 USDC -> VVS", False, str(e))

# ============================================================================
# TEST 6: Transaction History
# ============================================================================
test_section("TEST 6: Trading History")

try:
    result = get_trade_history.invoke({})
    
    if "trades" in result:
        trade_count = len(result["trades"])
        test_result("Get Trading History", True, f"{trade_count} trades recorded")
        
        if trade_count > 0:
            latest = result["trades"][-1]
            print(f"        Latest: {latest.get('action', 'unknown')} @ {latest.get('timestamp', 'unknown')}")
    else:
        test_result("Get Trading History", False, result.get("error", "Unknown error"))
except Exception as e:
    test_result("Get Trading History", False, str(e))

# ============================================================================
# TEST 7: Contract Verification
# ============================================================================
test_section("TEST 7: Smart Contract Verification")

contracts = {
    "USDC": os.getenv("USDC_CONTRACT"),
    "VVS Router": os.getenv("VVS_ROUTER"),
    "WCRO": os.getenv("WCRO_ADDRESS")
}

if connected:
    for name, address in contracts.items():
        if address:
            try:
                code = w3.eth.get_code(Web3.to_checksum_address(address))
                has_code = code != b'' and code != b'\x00'
                test_result(f"{name} Contract", has_code, 
                           f"{address[:10]}...{address[-8:]}")
            except Exception as e:
                test_result(f"{name} Contract", False, str(e))

# ============================================================================
# TEST 8: Gas Price Check
# ============================================================================
test_section("TEST 8: Gas Price Information")

if connected:
    try:
        gas_price = w3.eth.gas_price
        gas_price_gwei = w3.from_wei(gas_price, 'gwei')
        test_result("Current Gas Price", True, f"{gas_price_gwei:.2f} Gwei")
        
        # Estimate costs for typical transactions
        costs = {
            "Token Transfer": 65000,
            "Token Approval": 50000,
            "DEX Swap": 200000
        }
        
        print("\n        Estimated Transaction Costs:")
        for tx_type, gas_limit in costs.items():
            cost_wei = gas_price * gas_limit
            cost_cro = w3.from_wei(cost_wei, 'ether')
            print(f"        • {tx_type}: ~{cost_cro:.6f} CRO")
    except Exception as e:
        test_result("Gas Price", False, str(e))

# ============================================================================
# Summary and Next Steps
# ============================================================================
print("\n" + "=" * 80)
print("TEST SUMMARY")
print("=" * 80)
print("""
✅ If all tests passed:
   • Your agent is ready to trade!
   • Try: python main.py
   • Ask: "What are my token balances?"
   • Ask: "Estimate 1 USDC to VVS"
   • Ask: "Swap 0.1 USDC to VVS" (will execute mock swap)

⚠️  If some tests failed:
   • Check your .env file configuration
   • Ensure you have CRO for gas fees
   • Verify RPC URL is accessible
   • Check wallet has sufficient balances

📝 To test REAL transactions on testnet:
   1. Ensure you have testnet CRO (>1 CRO)
   2. Ensure you have testnet USDC (>1 USDC)
   3. Run: python main.py
   4. Ask: "Approve USDC to router"
   5. Ask: "Swap 0.1 USDC to VVS"
   
   Note: Real swaps may fail due to liquidity on testnet.
   For production trading, deploy to mainnet (see FINAL_REPORT.txt)

🔗 Useful Links:
   • Testnet Explorer: https://explorer.cronos.org/testnet
   • Your Wallet: https://explorer.cronos.org/testnet/address/{os.getenv('WALLET_ADDRESS', 'N/A')}
   • Get Testnet CRO: https://cronos.org/faucet
""")
print("=" * 80)
