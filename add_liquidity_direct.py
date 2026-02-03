#!/usr/bin/env python3
"""
Add liquidity directly by transferring tokens to pair and calling mint()
This bypasses the router which might have issues.
"""

import os
import sys
import time
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

RPC_URL = os.getenv("RPC_URL")
PRIVATE_KEY = os.getenv("WALLET_PRIVATE_KEY")
USDC_ADDR = Web3.to_checksum_address(os.getenv("USDC_CONTRACT").strip("'\""))
WXTZ_ADDR = Web3.to_checksum_address(
    (os.getenv("WXTZ_ADDRESS") or "0x03a6A5223BF91016175cD95fd8776351843F4998").strip("'\"")
)
FACTORY_ADDR = Web3.to_checksum_address(
    (os.getenv("VVS_FACTORY_ADDR") or "0xe97f55c627eD81b53eDD880A9530f0F5Bc76a2f0").strip("'\"")
)

ERC20_ABI = [
    {"constant":False,"inputs":[{"name":"to","type":"address"},{"name":"value","type":"uint256"}],"name":"transfer","outputs":[{"name":"","type":"bool"}],"type":"function"},
    {"constant":True,"inputs":[{"name":"account","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"type":"function"},
    {"constant":True,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"}
]

FACTORY_ABI = [
    {"type":"function","name":"getPair","inputs":[{"name":"","type":"address"},{"name":"","type":"address"}],"outputs":[{"name":"","type":"address"}],"stateMutability":"view"},
    {"type":"function","name":"createPair","inputs":[{"name":"tokenA","type":"address"},{"name":"tokenB","type":"address"}],"outputs":[{"name":"pair","type":"address"}],"stateMutability":"nonpayable"}
]

PAIR_ABI = [
    {"constant":True,"inputs":[],"name":"token0","outputs":[{"name":"","type":"address"}],"type":"function"},
    {"constant":True,"inputs":[],"name":"token1","outputs":[{"name":"","type":"address"}],"type":"function"},
    {"constant":False,"inputs":[{"name":"to","type":"address"}],"name":"mint","outputs":[{"name":"liquidity","type":"uint256"}],"type":"function"},
    {"constant":True,"inputs":[],"name":"getReserves","outputs":[{"name":"reserve0","type":"uint112"},{"name":"reserve1","type":"uint112"},{"name":"blockTimestampLast","type":"uint32"}],"type":"function"},
    {"constant":False,"inputs":[],"name":"sync","outputs":[],"type":"function"}
]

def wait_for_receipt(w3, tx_hash, label):
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    if receipt["status"] != 1:
        raise RuntimeError(f"{label} failed: {tx_hash.hex()}")
    return receipt

def main():
    print("💧 Adding Liquidity Directly to Pair...")
    
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    account = w3.eth.account.from_key(PRIVATE_KEY)
    print(f"✅ Wallet: {account.address}\n")
    
    usdc = w3.eth.contract(address=USDC_ADDR, abi=ERC20_ABI)
    wxtz = w3.eth.contract(address=WXTZ_ADDR, abi=ERC20_ABI)
    factory = w3.eth.contract(address=FACTORY_ADDR, abi=FACTORY_ABI)
    
    # Get or create pair
    pair_addr = factory.functions.getPair(USDC_ADDR, WXTZ_ADDR).call()
    
    if pair_addr == "0x0000000000000000000000000000000000000000":
        print("Creating pair...")
        nonce = w3.eth.get_transaction_count(account.address)
        tx = factory.functions.createPair(USDC_ADDR, WXTZ_ADDR).build_transaction({
            'from': account.address,
            'nonce': nonce,
            'gas': 5000000,
            'gasPrice': int(w3.eth.gas_price * 1.2),
            'chainId': w3.eth.chain_id
        })
        signed = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        pair_addr = factory.functions.getPair(USDC_ADDR, WXTZ_ADDR).call()
    
    print(f"📊 Pair: {pair_addr}\n")
    
    pair = w3.eth.contract(address=pair_addr, abi=PAIR_ABI)
    token0 = pair.functions.token0().call()
    token1 = pair.functions.token1().call()
    print(f"Token0: {token0}")
    print(f"Token1: {token1}\n")
    
    # Check current reserves
    reserves = pair.functions.getReserves().call()
    print(f"Current reserves: {reserves[0]}, {reserves[1]}")
    
    if reserves[0] > 0 or reserves[1] > 0:
        print("✅ Pool already has liquidity!")
        print("\n💡 Run: ./start_all.sh")
        return 0
    
    # Add liquidity
    usdc_decimals = usdc.functions.decimals().call()
    wxtz_decimals = wxtz.functions.decimals().call()
    
    usdc_amount = 100 * (10 ** usdc_decimals)
    wxtz_amount = 100 * (10 ** wxtz_decimals)
    
    print(f"💧 Adding: 100 USDC + 100 TWXTZ\n")
    
    nonce = w3.eth.get_transaction_count(account.address)
    
    # Transfer USDC to pair
    print("📤 Transferring USDC to pair...")
    tx = usdc.functions.transfer(pair_addr, usdc_amount).build_transaction({
        'from': account.address,
        'nonce': nonce,
        'gas': 2000000,
        'gasPrice': int(w3.eth.gas_price * 1.2),
        'chainId': w3.eth.chain_id
    })
    signed = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    wait_for_receipt(w3, tx_hash, "USDC transfer")
    print("✅ USDC transferred")
    nonce += 1
    
    # Transfer TWXTZ to pair
    print("📤 Transferring TWXTZ to pair...")
    tx = wxtz.functions.transfer(pair_addr, wxtz_amount).build_transaction({
        'from': account.address,
        'nonce': nonce,
        'gas': 2000000,
        'gasPrice': int(w3.eth.gas_price * 1.2),
        'chainId': w3.eth.chain_id
    })
    signed = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    wait_for_receipt(w3, tx_hash, "TWXTZ transfer")
    print("✅ TWXTZ transferred")
    nonce += 1
    
    # Call mint
    print("⚡ Minting LP tokens...")
    tx = pair.functions.mint(account.address).build_transaction({
        'from': account.address,
        'nonce': nonce,
        'gas': 5000000,
        'gasPrice': int(w3.eth.gas_price * 1.2),
        'chainId': w3.eth.chain_id
    })
    signed = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    print(f"   TX: {tx_hash.hex()}")
    wait_for_receipt(w3, tx_hash, "Mint")
    
    print("✅ Liquidity added successfully!\n")

    # Sync reserves to reflect balances
    print("🔄 Syncing reserves...")
    nonce += 1
    sync_tx = pair.functions.sync().build_transaction({
        'from': account.address,
        'nonce': nonce,
        'gas': 2000000,
        'gasPrice': int(w3.eth.gas_price * 1.2),
        'chainId': w3.eth.chain_id
    })
    signed = w3.eth.account.sign_transaction(sync_tx, private_key=PRIVATE_KEY)
    sync_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    wait_for_receipt(w3, sync_hash, "Sync")

    reserves = pair.functions.getReserves().call()
    print(f"Reserves after sync: {reserves[0]}, {reserves[1]}")
    
    # Update .env
    from dotenv import set_key
    env_path = "/Users/adarsh/Documents/alpha-consumer/.env"
    set_key(env_path, "VVS_FACTORY_ADDR", FACTORY_ADDR.lower())
    set_key(env_path, "WXTZ_ADDRESS", WXTZ_ADDR.lower())
    print(f"📝 Updated .env with new addresses")
    
    print("\n💡 Production mode ready! Run: ./start_all.sh")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
