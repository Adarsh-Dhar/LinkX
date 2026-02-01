#!/usr/bin/env python3
"""
Deploy complete DEX stack: Factory, Router, TestWXTZ, create pair, and add liquidity
"""

import os
import sys
import json
import time
from web3 import Web3
from dotenv import load_dotenv, set_key

load_dotenv()

RPC_URL = os.getenv("RPC_URL")
PRIVATE_KEY = os.getenv("WALLET_PRIVATE_KEY")
USDC_ADDR = os.getenv("USDC_CONTRACT")

def main():
    print("🏗️  Deploying Complete DEX Stack...")
    
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    account = w3.eth.account.from_key(PRIVATE_KEY)
    print(f"✅ Deployer: {account.address}\n")
    
    # Compile contracts
    print("🔨 Compiling contracts...")
    os.system("cd /Users/adarsh/Documents/alpha-consumer/contract && forge build --silent")
    
    nonce = w3.eth.get_transaction_count(account.address)
    
    # 1. Deploy Factory
    print("\n📝 Deploying Factory...")
    with open("/Users/adarsh/Documents/alpha-consumer/contract/out/VVSFactory.sol/VVSFactory.json") as f:
        factory_artifact = json.load(f)
    
    # Constructor: address _feeToSetter
    from eth_abi import encode
    constructor_args = encode(['address'], [account.address])
    
    tx = {
        'from': account.address,
        'data': factory_artifact['bytecode']['object'] + constructor_args.hex(),
        'nonce': nonce,
        'gas': 20000000,
        'gasPrice': int(w3.eth.gas_price * 1.2),
        'chainId': w3.eth.chain_id
    }
    
    signed = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    print(f"   TX: {tx_hash.hex()}")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
    
    if receipt['status'] != 1:
        print("❌ Factory deployment failed")
        return 1
    
    factory_addr = receipt['contractAddress']
    print(f"✅ Factory: {factory_addr}")
    nonce += 1
    
    # 2. Deploy TestWXTZ
    print("\n📝 Deploying TestWXTZ...")
    with open("/Users/adarsh/Documents/alpha-consumer/contract/out/TestWXTZ.sol/TestWXTZ.json") as f:
        wxtz_artifact = json.load(f)
    
    tx = {
        'from': account.address,
        'data': wxtz_artifact['bytecode']['object'],
        'nonce': nonce,
        'gas': 20000000,
        'gasPrice': int(w3.eth.gas_price * 1.2),
        'chainId': w3.eth.chain_id
    }
    
    signed = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
    
    if receipt['status'] != 1:
        print("❌ TestWXTZ deployment failed")
        return 1
    
    wxtz_addr = receipt['contractAddress']
    print(f"✅ TestWXTZ: {wxtz_addr}")
    nonce += 1
    
    # 3. Deploy Router
    print("\n📝 Deploying Router...")
    with open("/Users/adarsh/Documents/alpha-consumer/contract/out/VVSRouter.sol/EtherlinkVVSRouter.json") as f:
        router_artifact = json.load(f)
    
    # Constructor: address factory__, address WXTZ__
    constructor_args = encode(['address', 'address'], [factory_addr, wxtz_addr])
    
    tx = {
        'from': account.address,
        'data': router_artifact['bytecode']['object'] + constructor_args.hex(),
        'nonce': nonce,
        'gas': 20000000,
        'gasPrice': int(w3.eth.gas_price * 1.2),
        'chainId': w3.eth.chain_id
    }
    
    signed = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
    
    if receipt['status'] != 1:
        print("❌ Router deployment failed")
        return 1
    
    router_addr = receipt['contractAddress']
    print(f"✅ Router: {router_addr}")
    nonce += 1
    
    # 4. Create pair
    print(f"\n📝 Creating USDC/TWXTZ pair...")
    factory_abi = factory_artifact['abi']
    factory = w3.eth.contract(address=factory_addr, abi=factory_abi)
    
    tx = factory.functions.createPair(
        Web3.to_checksum_address(USDC_ADDR),
        Web3.to_checksum_address(wxtz_addr)
    ).build_transaction({
        'from': account.address,
        'nonce': nonce,
        'gas': 20000000,
        'gasPrice': int(w3.eth.gas_price * 1.2),
        'chainId': w3.eth.chain_id
    })
    
    signed = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
    
    if receipt['status'] != 1:
        print("❌ Pair creation failed")
        return 1
    
    pair_addr = factory.functions.getPair(USDC_ADDR, wxtz_addr).call()
    print(f"✅ Pair: {pair_addr}")
    nonce += 1
    
    # 5. Add liquidity
    print(f"\n💧 Adding initial liquidity (100 USDC + 100 TWXTZ)...")
    
    erc20_abi = [
        {"constant":False,"inputs":[{"name":"spender","type":"address"},{"name":"value","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"type":"function"},
        {"constant":True,"inputs":[{"name":"account","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"type":"function"},
        {"constant":True,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"}
    ]
    
    usdc = w3.eth.contract(address=Web3.to_checksum_address(USDC_ADDR), abi=erc20_abi)
    wxtz = w3.eth.contract(address=wxtz_addr, abi=erc20_abi)
    
    usdc_decimals = usdc.functions.decimals().call()
    wxtz_decimals = wxtz.functions.decimals().call()
    
    usdc_amount = 100 * (10 ** usdc_decimals)
    wxtz_amount = 100 * (10 ** wxtz_decimals)
    
    # Approve USDC
    print("   🔐 Approving USDC...")
    tx = usdc.functions.approve(router_addr, usdc_amount * 1000).build_transaction({
        'from': account.address,
        'nonce': nonce,
        'gas': 2000000,
        'gasPrice': int(w3.eth.gas_price * 1.2),
        'chainId': w3.eth.chain_id
    })
    signed = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
    nonce += 1
    
    # Approve TWXTZ
    print("   🔐 Approving TWXTZ...")
    tx = wxtz.functions.approve(router_addr, wxtz_amount * 1000).build_transaction({
        'from': account.address,
        'nonce': nonce,
        'gas': 2000000,
        'gasPrice': int(w3.eth.gas_price * 1.2),
        'chainId': w3.eth.chain_id
    })
    signed = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
    nonce += 1
    
    # Add liquidity
    print("   💧 Adding to pool...")
    router_abi = router_artifact['abi']
    router = w3.eth.contract(address=router_addr, abi=router_abi)
    
    deadline = int(time.time()) + 600
    
    tx = router.functions.addLiquidity(
        Web3.to_checksum_address(USDC_ADDR),
        wxtz_addr,
        usdc_amount,
        wxtz_amount,
        usdc_amount * 90 // 100,
        wxtz_amount * 90 // 100,
        account.address,
        deadline
    ).build_transaction({
        'from': account.address,
        'nonce': nonce,
        'gas': 20000000,
        'gasPrice': int(w3.eth.gas_price * 1.2),
        'chainId': w3.eth.chain_id
    })
    
    signed = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    print(f"   TX: {tx_hash.hex()}")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
    
    if receipt['status'] != 1:
        print("❌ Add liquidity failed")
        return 1
    
    print("✅ Liquidity added!")
    
    # Update .env
    print(f"\n📝 Updating .env file...")
    env_path = "/Users/adarsh/Documents/alpha-consumer/.env"
    set_key(env_path, "VVS_FACTORY_ADDR", factory_addr.lower())
    set_key(env_path, "VVS_ROUTER_ADDR", router_addr.lower())
    set_key(env_path, "WXTZ_ADDRESS", wxtz_addr.lower())
    
    print(f"\n✅ DEX Stack Deployed!")
    print(f"\n📋 Addresses:")
    print(f"   Factory: {factory_addr}")
    print(f"   Router:  {router_addr}")
    print(f"   TWXTZ:   {wxtz_addr}")
    print(f"   Pair:    {pair_addr}")
    
    print(f"\n💡 Production mode ready! Run: ./start_all.sh")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
