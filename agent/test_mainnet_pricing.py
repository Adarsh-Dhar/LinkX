#!/usr/bin/env python3
"""
Test the new mainnet pricing with mock transactions on testnet
"""

import os
import sys
from web3 import Web3
from dotenv import load_dotenv

# Load environment
load_dotenv()

print("=" * 80)
print("MAINNET PRICING + TESTNET MOCK TRANSACTIONS TEST")
print("=" * 80)

# Test 1: Estimate swap output
print("\n1️⃣  Testing estimate_swap_output with real mainnet pricing...")

try:
    # Direct import and call
    import subprocess
    result_text = subprocess.run([
        sys.executable, "-c",
        """
import os
from dotenv import load_dotenv
load_dotenv()
from tools import estimate_swap_output
result = estimate_swap_output.invoke({"token_in": "usdc", "token_out": "vvs", "amount_in": 1.0})
import json
print(json.dumps(result))
"""
    ], capture_output=True, text=True, cwd="/Users/adarsh/Documents/alpha-consumer/agent")
    
    import json
    result = json.loads(result_text.stdout.strip())
    
    print(f"\n   Result: {result}")
    
    if "error" not in result:
        print(f"   ✅ Got real mainnet pricing!")
        rate = result.get('exchange_rate', 0)
        if isinstance(rate, (int, float)):
            print(f"      1 USDC = {rate:.2f} VVS")
    else:
        print(f"   ⚠️  {result['error']}")
except Exception as e:
    print(f"   ⚠️  Error: {e}")

# Test 2: Check current network
print("\n2️⃣  Checking current network configuration...")

rpc_url = os.getenv("CRONOS_RPC_URL", "https://evm-t3.cronos.org")
w3 = Web3(Web3.HTTPProvider(rpc_url))

if w3.is_connected():
    chain_id = w3.eth.chain_id
    print(f"   ✅ Connected to network")
    print(f"      Chain ID: {chain_id} {'(Testnet)' if chain_id == 338 else '(Mainnet)'}")
    print(f"      RPC: {rpc_url}")
else:
    print(f"   ❌ Could not connect to RPC")

# Test 3: Verify mock transaction logic
print("\n3️⃣  Testing swap execution with mock transaction...")

result = execute_vvs_swap.invoke({
    "token_in": "usdc",
    "token_out": "vvs",
    "amount_in": 0.1,  # Small amount for testing
})

print(f"\n   Result Summary:")
print(f"      Status: {result.get('status', 'unknown')}")
print(f"      Mode: {result.get('mode', 'unknown')}")
print(f"      Amount In: {result.get('amount_in', 0)} USDC")
print(f"      Expected Out: {result.get('amount_out_expected', 0):.2f} VVS")
print(f"      TX Hash: {result.get('tx_hash', 'N/A')[:30]}...")

if result.get('status') == 'success_mock':
    print(f"   ✅ Mock transaction successful with real mainnet pricing!")
else:
    print(f"   ℹ️  {result.get('error', 'Unknown result')}")

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)
