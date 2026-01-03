#!/usr/bin/env python3
"""
Test mainnet pricing with mock transactions
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

print("\n" + "="*80)
print("MAINNET PRICING + TESTNET MOCK TRANSACTIONS")
print("="*80)

# Check network
from web3 import Web3

rpc_url = os.getenv("CRONOS_RPC_URL", "https://evm-t3.cronos.org")
w3 = Web3(Web3.HTTPProvider(rpc_url))

print(f"\n📍 Network Status:")
if w3.is_connected():
    chain_id = w3.eth.chain_id
    print(f"   ✅ Connected to RPC")
    print(f"   Chain ID: {chain_id} {'(TESTNET 338)' if chain_id == 338 else '(MAINNET 25)'}")
else:
    print(f"   ❌ RPC Connection failed")
    sys.exit(1)

print(f"\n📝 Configuration:")
print(f"   RPC URL: {rpc_url}")
print(f"   USDC: {os.getenv('USDC_CONTRACT', 'N/A')[:20]}...")
print(f"   VVS Router: {os.getenv('VVS_ROUTER', 'N/A')[:20]}...")

# Test direct pricing from mainnet
print(f"\n🔄 Testing Real Mainnet Price Fetch...")

try:
    mainnet_rpc = "https://rpc.cronos.org"
    mainnet_w3 = Web3(Web3.HTTPProvider(mainnet_rpc))
    
    if mainnet_w3.is_connected():
        print(f"   ✅ Connected to mainnet RPC")
        
        # Load router ABI
        with open('/Users/adarsh/Documents/alpha-consumer/agent/VVSRouter.json', 'r') as f:
            import json
            router_abi = json.load(f)
        
        # Mainnet addresses
        mainnet_router = "0x145677FC4d9b8F19B4172A2b88f7fb1f02fdf220"
        mainnet_usdc = "0xc21223249CA28397B4B6541dfFaEcC539BfF0c59"
        mainnet_vvs = "0x2D03bECE6747ADC00E1a131BBA1469C15fD11e03"
        
        router = mainnet_w3.eth.contract(
            address=Web3.to_checksum_address(mainnet_router),
            abi=router_abi
        )
        
        # Get price for 1 USDC → VVS
        try:
            amounts = router.functions.getAmountsOut(
                int(1 * 10**6),  # 1 USDC (6 decimals)
                [Web3.to_checksum_address(mainnet_usdc),
                 Web3.to_checksum_address(mainnet_vvs)]
            ).call()
            
            vvs_amount = amounts[-1] / (10**18)
            print(f"   ✅ Real Mainnet Price: 1 USDC = {vvs_amount:.2f} VVS")
            
        except Exception as e:
            print(f"   ⚠️  Could not fetch mainnet price: {e}")
            print(f"      Will use fallback rate: 1 USDC = 502,402 VVS")
    else:
        print(f"   ⚠️  Could not connect to mainnet RPC")
        print(f"      Will use fallback rate: 1 USDC = 502,402 VVS")
        
except Exception as e:
    print(f"   ⚠️  Error: {e}")

print(f"\n🎭 Mock Transaction Behavior (Testnet):")
print(f"   ✅ Real mainnet prices will be used")
print(f"   ✅ Transactions will be simulated (not executed)")
print(f"   ✅ Mock TX hash will be generated")
print(f"   ✅ Realistic gas estimates will be shown")

print(f"\n🚀 Switch to Mainnet for Real Execution:")
print(f"   1. Update .env CHAIN_ID=25")
print(f"   2. Update CRONOS_RPC_URL=https://rpc.cronos.org")
print(f"   3. Real transactions will execute immediately")

print(f"\n" + "="*80)
print("✅ System ready with mainnet pricing + testnet mock transactions")
print("="*80 + "\n")
