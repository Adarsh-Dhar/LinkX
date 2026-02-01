#!/usr/bin/env python3
"""
Check if USDC/WXTZ pair exists and add initial liquidity if needed.
Run this before starting the trading system.
"""

import os
import sys
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

RPC_URL = os.getenv("RPC_URL", "https://node.shadownet.etherlink.com")
PRIVATE_KEY = os.getenv("WALLET_PRIVATE_KEY")
FACTORY_ADDR = os.getenv("VVS_FACTORY_ADDR")
ROUTER_ADDR = os.getenv("VVS_ROUTER_ADDR")
USDC_ADDR = os.getenv("USDC_CONTRACT")
WXTZ_ADDR = os.getenv("WXTZ_ADDRESS")

FACTORY_ABI = [
    {"type":"function","name":"getPair","inputs":[{"name":"","type":"address"},{"name":"","type":"address"}],"outputs":[{"name":"","type":"address"}],"stateMutability":"view"},
    {"type":"function","name":"createPair","inputs":[{"name":"tokenA","type":"address"},{"name":"tokenB","type":"address"}],"outputs":[{"name":"pair","type":"address"}],"stateMutability":"nonpayable"}
]

ROUTER_ABI = [
    {"inputs":[{"internalType":"address","name":"tokenA","type":"address"},{"internalType":"address","name":"tokenB","type":"address"},{"internalType":"uint256","name":"amountADesired","type":"uint256"},{"internalType":"uint256","name":"amountBDesired","type":"uint256"},{"internalType":"uint256","name":"amountAMin","type":"uint256"},{"internalType":"uint256","name":"amountBMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"addLiquidity","outputs":[{"internalType":"uint256","name":"amountA","type":"uint256"},{"internalType":"uint256","name":"amountB","type":"uint256"},{"internalType":"uint256","name":"liquidity","type":"uint256"}],"stateMutability":"nonpayable","type":"function"}
]

ERC20_ABI = [
    {"constant":False,"inputs":[{"name":"spender","type":"address"},{"name":"value","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"type":"function"},
    {"constant":True,"inputs":[{"name":"account","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"type":"function"},
    {"constant":True,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"}
]

def main():
    print("🔍 Checking USDC/WXTZ Liquidity Pool Status...")
    
    # Connect to blockchain
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not w3.is_connected():
        print("❌ Failed to connect to RPC")
        return 1
    
    account = w3.eth.account.from_key(PRIVATE_KEY)
    print(f"✅ Connected. Wallet: {account.address}")
    
    # Check if pair exists
    factory = w3.eth.contract(address=Web3.to_checksum_address(FACTORY_ADDR), abi=FACTORY_ABI)
    usdc_addr = Web3.to_checksum_address(USDC_ADDR)
    wxtz_addr = Web3.to_checksum_address(WXTZ_ADDR)
    
    pair_address = factory.functions.getPair(usdc_addr, wxtz_addr).call()
    print(f"\n📊 Pair Address: {pair_address}")
    
    if pair_address == "0x0000000000000000000000000000000000000000":
        print("❌ Pair does NOT exist!")
        print("\n💡 You need to:")
        print("   1. Create the pair (factory.createPair)")
        print("   2. Add initial liquidity (router.addLiquidity)")
        
        response = input("\n❓ Would you like to create the pair now? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("Exiting...")
            return 0
        
        # Create pair
        print("\n🏗️  Creating pair...")
        nonce = w3.eth.get_transaction_count(account.address)
        create_tx = factory.functions.createPair(usdc_addr, wxtz_addr).build_transaction({
            'from': account.address,
            'nonce': nonce,
            'gas': 3000000,
            'gasPrice': int(w3.eth.gas_price * 1.2),
            'chainId': w3.eth.chain_id
        })
        
        signed = w3.eth.account.sign_transaction(create_tx, private_key=PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        print(f"⏳ Waiting for confirmation... TX: {tx_hash.hex()}")
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        
        if receipt['status'] == 1:
            print("✅ Pair created!")
            pair_address = factory.functions.getPair(usdc_addr, wxtz_addr).call()
            print(f"   Pair: {pair_address}")
        else:
            print("❌ Failed to create pair")
            return 1
        
        nonce += 1
        
        # Add liquidity
        print("\n💰 Now you need to add liquidity...")
        print("   Checking balances...")
        
        usdc = w3.eth.contract(address=usdc_addr, abi=ERC20_ABI)
        wxtz = w3.eth.contract(address=wxtz_addr, abi=ERC20_ABI)
        
        usdc_balance = usdc.functions.balanceOf(account.address).call()
        wxtz_balance = wxtz.functions.balanceOf(account.address).call()
        usdc_decimals = usdc.functions.decimals().call()
        wxtz_decimals = wxtz.functions.decimals().call()
        
        print(f"   USDC: {usdc_balance / (10 ** usdc_decimals):.2f}")
        print(f"   WXTZ: {wxtz_balance / (10 ** wxtz_decimals):.2f}")
        
        if usdc_balance == 0 or wxtz_balance == 0:
            print("\n❌ Insufficient balance to add liquidity")
            print("   You need both USDC and WXTZ tokens")
            return 1
        
        # Use 10% of balance or minimum amounts
        usdc_amount = min(usdc_balance // 10, 100 * (10 ** usdc_decimals))
        wxtz_amount = min(wxtz_balance // 10, 100 * (10 ** wxtz_decimals))
        
        print(f"\n💧 Adding liquidity:")
        print(f"   {usdc_amount / (10 ** usdc_decimals):.2f} USDC")
        print(f"   {wxtz_amount / (10 ** wxtz_decimals):.2f} WXTZ")
        
        response = input("\n❓ Proceed? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("Exiting...")
            return 0
        
        router_addr = Web3.to_checksum_address(ROUTER_ADDR)
        
        # Approve USDC
        print("\n🔐 Approving USDC...")
        approve_tx = usdc.functions.approve(router_addr, usdc_amount * 2).build_transaction({
            'from': account.address,
            'nonce': nonce,
            'gas': 2000000,
            'gasPrice': int(w3.eth.gas_price * 1.2),
            'chainId': w3.eth.chain_id
        })
        signed = w3.eth.account.sign_transaction(approve_tx, private_key=PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
        print("✅ USDC approved")
        nonce += 1
        
        # Approve WXTZ
        print("🔐 Approving WXTZ...")
        approve_tx = wxtz.functions.approve(router_addr, wxtz_amount * 2).build_transaction({
            'from': account.address,
            'nonce': nonce,
            'gas': 2000000,
            'gasPrice': int(w3.eth.gas_price * 1.2),
            'chainId': w3.eth.chain_id
        })
        signed = w3.eth.account.sign_transaction(approve_tx, private_key=PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
        print("✅ WXTZ approved")
        nonce += 1
        
        # Add liquidity
        print("\n💧 Adding liquidity to pool...")
        router = w3.eth.contract(address=router_addr, abi=ROUTER_ABI)
        import time
        deadline = int(time.time()) + 600
        
        liquidity_tx = router.functions.addLiquidity(
            usdc_addr,
            wxtz_addr,
            usdc_amount,
            wxtz_amount,
            usdc_amount * 95 // 100,  # 5% slippage
            wxtz_amount * 95 // 100,
            account.address,
            deadline
        ).build_transaction({
            'from': account.address,
            'nonce': nonce,
            'gas': 10000000,
            'gasPrice': int(w3.eth.gas_price * 1.2),
            'chainId': w3.eth.chain_id
        })
        
        signed = w3.eth.account.sign_transaction(liquidity_tx, private_key=PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        print(f"⏳ Waiting for confirmation... TX: {tx_hash.hex()}")
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        
        if receipt['status'] == 1:
            print("✅ Liquidity added successfully!")
            print("   You can now start trading")
        else:
            print("❌ Failed to add liquidity")
            return 1
    else:
        print("✅ Pair EXISTS!")
        print("\n💡 The pool is ready. You can now swap tokens.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
