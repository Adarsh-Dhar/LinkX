#!/usr/bin/env python3
"""
Add liquidity to USDC/TWXTZ pool
"""

import os
import sys
import time
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

RPC_URL = os.getenv("RPC_URL")
PRIVATE_KEY = os.getenv("WALLET_PRIVATE_KEY")
USDC_ADDR = os.getenv("USDC_CONTRACT")
WXTZ_ADDR = os.getenv("WXTZ_ADDRESS") 
ROUTER_ADDR = os.getenv("VVS_ROUTER_ADDR")

ERC20_ABI = [
    {"constant":False,"inputs":[{"name":"spender","type":"address"},{"name":"value","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"type":"function"},
    {"constant":True,"inputs":[{"name":"account","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"type":"function"},
    {"constant":True,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"}
]

ROUTER_ABI = [
    {"inputs":[{"internalType":"address","name":"tokenA","type":"address"},{"internalType":"address","name":"tokenB","type":"address"},{"internalType":"uint256","name":"amountADesired","type":"uint256"},{"internalType":"uint256","name":"amountBDesired","type":"uint256"},{"internalType":"uint256","name":"amountAMin","type":"uint256"},{"internalType":"uint256","name":"amountBMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"addLiquidity","outputs":[{"internalType":"uint256","name":"amountA","type":"uint256"},{"internalType":"uint256","name":"amountB","type":"uint256"},{"internalType":"uint256","name":"liquidity","type":"uint256"}],"stateMutability":"nonpayable","type":"function"}
]

def main():
    print("💧 Adding Liquidity to USDC/TWXTZ Pool...")
    
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    account = w3.eth.account.from_key(PRIVATE_KEY)
    print(f"✅ Wallet: {account.address}")
    
    usdc = w3.eth.contract(address=Web3.to_checksum_address(USDC_ADDR), abi=ERC20_ABI)
    wxtz = w3.eth.contract(address=Web3.to_checksum_address(WXTZ_ADDR), abi=ERC20_ABI)
    router = w3.eth.contract(address=Web3.to_checksum_address(ROUTER_ADDR), abi=ROUTER_ABI)
    
    # Check balances
    usdc_balance = usdc.functions.balanceOf(account.address).call()
    wxtz_balance = wxtz.functions.balanceOf(account.address).call()
    usdc_decimals = usdc.functions.decimals().call()
    wxtz_decimals = wxtz.functions.decimals().call()
    
    print(f"   USDC: {usdc_balance / (10 ** usdc_decimals):.2f}")
    print(f"   TWXTZ: {wxtz_balance / (10 ** wxtz_decimals):.2f}")
    
    # Add 100 USDC + 100 TWXTZ
    usdc_amount = 100 * (10 ** usdc_decimals)
    wxtz_amount = 100 * (10 ** wxtz_decimals)
    
    print(f"\n💧 Adding: 100 USDC + 100 TWXTZ")
    
    nonce = w3.eth.get_transaction_count(account.address)
    
    # Approve USDC
    print("🔐 Approving USDC...")
    tx = usdc.functions.approve(Web3.to_checksum_address(ROUTER_ADDR), usdc_amount * 10).build_transaction({
        'from': account.address,
        'nonce': nonce,
        'gas': 2000000,
        'gasPrice': int(w3.eth.gas_price * 1.2),
        'chainId': w3.eth.chain_id
    })
    signed = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
    print("✅ USDC approved")
    nonce += 1
    
    # Approve TWXTZ
    print("🔐 Approving TWXTZ...")
    tx = wxtz.functions.approve(Web3.to_checksum_address(ROUTER_ADDR), wxtz_amount * 10).build_transaction({
        'from': account.address,
        'nonce': nonce,
        'gas': 2000000,
        'gasPrice': int(w3.eth.gas_price * 1.2),
        'chainId': w3.eth.chain_id
    })
    signed = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
    print("✅ TWXTZ approved")
    nonce += 1
    
    # Add liquidity - router will handle token sorting
    print("💧 Adding liquidity...")
    deadline = int(time.time()) + 600
    
    # Note: Router automatically sorts tokens, so order doesn't matter
    # But WXTZ < USDC alphabetically, so WXTZ is token0
    tx = router.functions.addLiquidity(
        Web3.to_checksum_address(WXTZ_ADDR),  # tokenA (will become token0)
        Web3.to_checksum_address(USDC_ADDR),  # tokenB (will become token1)
        wxtz_amount,
        usdc_amount,
        wxtz_amount * 90 // 100,  # 10% slippage
        usdc_amount * 90 // 100,
        account.address,
        deadline
    ).build_transaction({
        'from': account.address,
        'nonce': nonce,
        'gas': 10000000,
        'gasPrice': int(w3.eth.gas_price * 1.2),
        'chainId': w3.eth.chain_id
    })
    
    signed = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    print(f"⏳ TX: {tx_hash.hex()}")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
    
    if receipt['status'] == 1:
        print("✅ Liquidity added successfully!")
        print("\n💡 You can now start trading!")
        print("   Run: ./start_all.sh")
    else:
        print("❌ Failed to add liquidity")
        print(f"   Transaction reverted. TX: {tx_hash.hex()}")
        print("   Checking transaction on explorer...")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
