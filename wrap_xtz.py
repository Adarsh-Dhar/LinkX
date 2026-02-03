#!/usr/bin/env python3
"""
Wrap some native XTZ to WXTZ tokens.
"""

import os
import sys
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

RPC_URL = os.getenv("RPC_URL", "https://node.shadownet.etherlink.com")
PRIVATE_KEY = os.getenv("WALLET_PRIVATE_KEY")
WXTZ_ADDR = os.getenv("WXTZ_ADDRESS")

WXTZ_ABI = [
    {"constant":False,"inputs":[],"name":"deposit","outputs":[],"payable":True,"stateMutability":"payable","type":"function"},
    {"constant":True,"inputs":[{"name":"account","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"type":"function"},
    {"constant":True,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"}
]

def main():
    print("🌊 Wrapping XTZ to WXTZ...")
    
    # Connect
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not w3.is_connected():
        print("❌ Failed to connect to RPC")
        return 1
    
    account = w3.eth.account.from_key(PRIVATE_KEY)
    print(f"✅ Connected. Wallet: {account.address}")
    
    # Check native balance
    native_balance = w3.eth.get_balance(account.address)
    print(f"   Native XTZ: {w3.from_wei(native_balance, 'ether'):.4f}")
    
    if native_balance == 0:
        print("❌ No XTZ to wrap!")
        return 1
    
    # Wrap 100 XTZ (or less if balance is low)
    amount_to_wrap = min(native_balance // 2, w3.to_wei(100, 'ether'))
    print(f"\n💧 Wrapping {w3.from_wei(amount_to_wrap, 'ether'):.2f} XTZ to WXTZ...")
    
    wxtz = w3.eth.contract(address=Web3.to_checksum_address(WXTZ_ADDR), abi=WXTZ_ABI)
    
    nonce = w3.eth.get_transaction_count(account.address)
    deposit_tx = wxtz.functions.deposit().build_transaction({
        'from': account.address,
        'value': amount_to_wrap,
        'nonce': nonce,
        'gas': 1000000,
        'gasPrice': int(w3.eth.gas_price * 1.2),
        'chainId': w3.eth.chain_id
    })
    
    signed = w3.eth.account.sign_transaction(deposit_tx, private_key=PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    print(f"⏳ Waiting for confirmation... TX: {tx_hash.hex()}")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    
    if receipt['status'] == 1:
        balance = wxtz.functions.balanceOf(account.address).call()
        decimals = wxtz.functions.decimals().call()
        print(f"✅ Wrapped successfully!")
        print(f"   WXTZ Balance: {balance / (10 ** decimals):.2f}")
        print("\n💡 Now run: python check_and_add_liquidity.py")
    else:
        print("❌ Failed to wrap XTZ")
        print(f"   Transaction reverted. Check: {tx_hash.hex()}")
        print(f"   This might mean WXTZ contract doesn't have deposit() function")
        print(f"   Try minting WXTZ directly if it has a mint function")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
