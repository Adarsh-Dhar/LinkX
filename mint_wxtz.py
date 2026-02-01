#!/usr/bin/env python3
"""
Mint WXTZ tokens directly if the contract supports minting.
"""

import os
import sys
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

RPC_URL = os.getenv("RPC_URL", "https://node.shadownet.etherlink.com")
PRIVATE_KEY = os.getenv("WALLET_PRIVATE_KEY")
WXTZ_ADDR = os.getenv("WXTZ_ADDRESS")

# Try different mint function signatures
WXTZ_ABI = [
    {"constant":False,"inputs":[{"name":"amount","type":"uint256"}],"name":"mint","outputs":[],"type":"function"},
    {"constant":False,"inputs":[{"name":"to","type":"address"},{"name":"amount","type":"uint256"}],"name":"mint","outputs":[],"type":"function"},
    {"constant":True,"inputs":[{"name":"account","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"type":"function"},
    {"constant":True,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"},
    {"constant":True,"inputs":[],"name":"owner","outputs":[{"name":"","type":"address"}],"type":"function"}
]

def main():
    print("🪙 Minting WXTZ tokens...")
    
    # Connect
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not w3.is_connected():
        print("❌ Failed to connect to RPC")
        return 1
    
    account = w3.eth.account.from_key(PRIVATE_KEY)
    print(f"✅ Connected. Wallet: {account.address}")
    
    wxtz = w3.eth.contract(address=Web3.to_checksum_address(WXTZ_ADDR), abi=WXTZ_ABI)
    
    # Check if we're the owner
    try:
        owner = wxtz.functions.owner().call()
        print(f"   Contract Owner: {owner}")
        if owner.lower() != account.address.lower():
            print(f"   ⚠️  You are not the owner. Only owner can mint.")
    except:
        print("   ⚠️  Contract may not have owner() function")
    
    # Check current balance
    try:
        balance = wxtz.functions.balanceOf(account.address).call()
        decimals = wxtz.functions.decimals().call()
        print(f"   Current WXTZ: {balance / (10 ** decimals):.2f}")
    except Exception as e:
        print(f"   Could not check balance: {e}")
        decimals = 18
    
    # Try to mint 100 WXTZ
    amount = 100 * (10 ** decimals)
    print(f"\n🪙 Attempting to mint {100} WXTZ...")
    
    nonce = w3.eth.get_transaction_count(account.address)
    
    # Try mint(uint256)
    try:
        print("   Trying mint(amount)...")
        mint_tx = wxtz.functions.mint(amount).build_transaction({
            'from': account.address,
            'nonce': nonce,
            'gas': 2000000,
            'gasPrice': int(w3.eth.gas_price * 1.2),
            'chainId': w3.eth.chain_id
        })
        
        signed = w3.eth.account.sign_transaction(mint_tx, private_key=PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        print(f"   ⏳ TX: {tx_hash.hex()}")
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        
        if receipt['status'] == 1:
            new_balance = wxtz.functions.balanceOf(account.address).call()
            print(f"   ✅ Minted successfully!")
            print(f"   New WXTZ Balance: {new_balance / (10 ** decimals):.2f}")
            print("\n💡 Now run: python check_and_add_liquidity.py")
            return 0
        else:
            print(f"   ❌ Transaction reverted")
    except Exception as e:
        print(f"   mint(amount) failed: {str(e)[:100]}")
    
    # Try mint(address, uint256)
    try:
        print("\n   Trying mint(to, amount)...")
        nonce = w3.eth.get_transaction_count(account.address)
        mint_tx = wxtz.functions.mint(account.address, amount).build_transaction({
            'from': account.address,
            'nonce': nonce,
            'gas': 2000000,
            'gasPrice': int(w3.eth.gas_price * 1.2),
            'chainId': w3.eth.chain_id
        })
        
        signed = w3.eth.account.sign_transaction(mint_tx, private_key=PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        print(f"   ⏳ TX: {tx_hash.hex()}")
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        
        if receipt['status'] == 1:
            new_balance = wxtz.functions.balanceOf(account.address).call()
            print(f"   ✅ Minted successfully!")
            print(f"   New WXTZ Balance: {new_balance / (10 ** decimals):.2f}")
            print("\n💡 Now run: python check_and_add_liquidity.py")
            return 0
        else:
            print(f"   ❌ Transaction reverted")
    except Exception as e:
        print(f"   mint(to, amount) failed: {str(e)[:100]}")
    
    print("\n❌ All mint attempts failed.")
    print("💡 Options:")
    print("   1. Contract may not support public minting")
    print("   2. You may need to be the owner")
    print("   3. Contract may have a different mint function")
    print("   4. Try buying WXTZ from a faucet or another source")
    
    return 1

if __name__ == "__main__":
    sys.exit(main())
