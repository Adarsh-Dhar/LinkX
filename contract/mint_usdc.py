#!/usr/bin/env python3
"""
Mint USDC tokens to the specified wallet using the bridge (owner) account.
"""
import os
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

RPC_URL = os.getenv("RPC_URL")
PRIVATE_KEY = os.getenv("WALLET_PRIVATE_KEY")
USDC_ADDR = os.getenv("USDC_CONTRACT")

USDC_ABI = [
    {"constant":False,"inputs":[{"name":"_to","type":"address"},{"name":"_amount","type":"uint256"}],"name":"mint","outputs":[],"type":"function"},
    {"constant":True,"inputs":[{"name":"account","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"type":"function"},
    {"constant":True,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"}
]

def main():
    print("🪙 Minting USDC tokens...")
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not w3.is_connected():
        print("❌ Failed to connect to RPC")
        return 1
    account = w3.eth.account.from_key(PRIVATE_KEY)
    print(f"✅ Connected. Wallet: {account.address}")
    usdc = w3.eth.contract(address=Web3.to_checksum_address(USDC_ADDR), abi=USDC_ABI)
    try:
        decimals = usdc.functions.decimals().call()
    except Exception as e:
        print(f"Could not get decimals: {e}")
        decimals = 6
    amount = 1000 * (10 ** decimals)
    print(f"Minting {1000} USDC to {account.address}...")
    nonce = w3.eth.get_transaction_count(account.address)
    try:
        mint_tx = usdc.functions.mint(account.address, amount).build_transaction({
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
            new_balance = usdc.functions.balanceOf(account.address).call()
            print(f"   ✅ Minted successfully!")
            print(f"   New USDC Balance: {new_balance / (10 ** decimals):.2f}")
            return 0
        else:
            print(f"   ❌ Transaction reverted")
    except Exception as e:
        print(f"Mint failed: {str(e)[:200]}")
    return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
