#!/usr/bin/env python3
"""Debug script to test swap execution with full error output"""

import os
import sys
import time
from web3 import Web3
from eth_account import Account

# Setup environment
os.environ["CRONOS_RPC_URL"] = "https://evm-t3.cronos.org"
os.environ["USDC_CONTRACT"] = "0x908059CF02cbb643Bc96C55e14Fb3699e632479f"
os.environ["VVS_CONTRACT"] = "0xea59AC2CcEfe907e7F77B502e2C87aC929832bfF"
os.environ["VVS_ROUTER"] = "0x3bc8a2c283751Adf1E3FAc823B6Cb0056f9f86C8"
os.environ["WCRO_ADDRESS"] = "0x9005E37cDfc4361491996aD7d546fC15AC9aAD9A"
os.environ["WALLET_PRIVATE_KEY"] = "276c1780d486387b7f4cad347a60c2e3c41fe757688c4e2c2cbc50d315dbb9fe"

from tools import ROUTER_ABI, ERC20_ABI

# Setup Web3
rpc_url = "https://evm-t3.cronos.org"
w3 = Web3(Web3.HTTPProvider(rpc_url))

print(f"Connected to RPC: {w3.is_connected()}")
print(f"Chain ID: {w3.eth.chain_id}")

# Setup addresses
usdc = Web3.to_checksum_address("0x908059CF02cbb643Bc96C55e14Fb3699e632479f")
vvs = Web3.to_checksum_address("0xea59AC2CcEfe907e7F77B502e2C87aC929832bfF")
router_addr = Web3.to_checksum_address("0x3bc8a2c283751Adf1E3FAc823B6Cb0056f9f86C8")

# Setup wallet
private_key = os.getenv("WALLET_PRIVATE_KEY")
account = w3.eth.account.from_key(private_key)
my_address = account.address

print(f"\n👤 Wallet: {my_address}")

# Get balances
usdc_contract = w3.eth.contract(address=usdc, abi=ERC20_ABI)
vvs_contract = w3.eth.contract(address=vvs, abi=ERC20_ABI)

usdc_balance = usdc_contract.functions.balanceOf(my_address).call() / (10**6)
vvs_balance = vvs_contract.functions.balanceOf(my_address).call() / (10**18)

print(f"💰 USDC Balance: {usdc_balance}")
print(f"💰 VVS Balance: {vvs_balance}")

# Check allowance
allowance = usdc_contract.functions.allowance(my_address, router_addr).call() / (10**6)
print(f"✓ Allowance to Router: {allowance}")

# Setup swap
amount_in = 1.0
amount_in_wei = int(amount_in * (10**6))
amount_out_min_wei = int(54.45 * (10**18))
deadline = int(time.time()) + 900
path = [usdc, vvs]

print(f"\n📊 Swap Details:")
print(f"  Input: {amount_in} USDC ({amount_in_wei} wei)")
print(f"  Output min: 54.45 VVS ({amount_out_min_wei} wei)")
print(f"  Deadline: {deadline}")
print(f"  Path: {path}")

# Build transaction
print(f"\n🔨 Building transaction...")
router = w3.eth.contract(address=router_addr, abi=ROUTER_ABI)

try:
    gas_price = w3.eth.gas_price
    print(f"  Gas price: {w3.from_wei(gas_price, 'gwei')} gwei")
except Exception as e:
    gas_price = w3.to_wei(5, 'gwei')
    print(f"  Gas price (fallback): {w3.from_wei(gas_price, 'gwei')} gwei")

try:
    nonce = w3.eth.get_transaction_count(my_address)
    print(f"  Nonce: {nonce}")
except Exception as e:
    nonce = 0
    print(f"  Nonce (fallback): {nonce}")

print(f"\n📝 Transaction parameters:")
tx_params = {
    'from': my_address,
    'gas': 300000,
    'gasPrice': gas_price,
    'nonce': nonce
}
for k, v in tx_params.items():
    print(f"  {k}: {v} ({type(v).__name__})")

try:
    print(f"\n🏗️  Building swap transaction...")
    swap_tx = router.functions.swapExactTokensForTokens(
        amount_in_wei,
        amount_out_min_wei,
        path,
        my_address,
        deadline
    ).build_transaction(tx_params)
    print(f"✅ Transaction built!")
    print(f"   Gas: {swap_tx.get('gas')}")
    print(f"   GasPrice: {swap_tx.get('gasPrice')}")
    print(f"   Nonce: {swap_tx.get('nonce')}")
except Exception as e:
    print(f"❌ Build error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Sign transaction
print(f"\n🔐 Signing transaction...")
try:
    signed_tx = w3.eth.account.sign_transaction(swap_tx, private_key)
    print(f"✅ Transaction signed!")
except Exception as e:
    print(f"❌ Signing error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Send transaction
print(f"\n📤 Sending transaction...")
try:
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    print(f"✅ Transaction sent!")
    print(f"   Hash: {tx_hash.hex()}")
    
    # Wait for receipt
    print(f"\n⏳ Waiting for confirmation...")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
    print(f"✅ Transaction confirmed!")
    print(f"   Block: {receipt['blockNumber']}")
    print(f"   Status: {receipt['status']}")
    print(f"   Gas used: {receipt['gasUsed']}")
    print(f"   Explorer: https://testnet.cronoscan.com/tx/{tx_hash.hex()}")
    
except Exception as e:
    print(f"❌ Send/Confirm error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print(f"\n✅ Swap completed successfully!")
