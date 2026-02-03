#!/usr/bin/env python3
"""
Deploy TestWXTZ using web3.py directly with proper gas limit.
"""

import os
import sys
import json
from web3 import Web3
from dotenv import load_dotenv, set_key

load_dotenv()

RPC_URL = os.getenv("RPC_URL", "https://node.shadownet.etherlink.com")
PRIVATE_KEY = os.getenv("WALLET_PRIVATE_KEY")

# Compile the contract first
print("🔨 Compiling TestWXTZ contract...")
os.system("cd /Users/adarsh/Documents/alpha-consumer/contract && forge build --silent")

# Read the compiled bytecode and ABI
artifact_path = "/Users/adarsh/Documents/alpha-consumer/contract/out/TestWXTZ.sol/TestWXTZ.json"
with open(artifact_path, 'r') as f:
    artifact = json.load(f)

bytecode = artifact['bytecode']['object']
abi = artifact['abi']

def main():
    print("🚀 Deploying TestWXTZ Token...")
    
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not w3.is_connected():
        print("❌ Failed to connect to RPC")
        return 1
    
    account = w3.eth.account.from_key(PRIVATE_KEY)
    print(f"✅ Deployer: {account.address}")
    
    # Deploy contract
    nonce = w3.eth.get_transaction_count(account.address)
    
    deploy_tx = {
        'from': account.address,
        'data': bytecode,
        'nonce': nonce,
        'gas': 20000000,  # 20M gas
        'gasPrice': int(w3.eth.gas_price * 1.2),
        'chainId': w3.eth.chain_id
    }
    
    print(f"📝 Signing and sending transaction...")
    signed = w3.eth.account.sign_transaction(deploy_tx, private_key=PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    print(f"⏳ TX: {tx_hash.hex()}")
    print(f"   Waiting for confirmation...")
    
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
    
    if receipt['status'] != 1:
        print("❌ Deployment failed")
        return 1
    
    token_address = receipt['contractAddress']
    print(f"\n✅ TestWXTZ deployed at: {token_address}")
    
    # Verify initial balance
    token = w3.eth.contract(address=token_address, abi=abi)
    balance = token.functions.balanceOf(account.address).call()
    print(f"   Initial supply: {w3.from_wei(balance, 'ether')} TWXTZ")
    print(f"   Owner: {account.address}")
    
    # Update .env
    print(f"\n📝 Updating .env file...")
    env_path = "/Users/adarsh/Documents/alpha-consumer/.env"
    set_key(env_path, "WXTZ_ADDRESS", token_address)
    print(f"   WXTZ_ADDRESS={token_address}")
    
    print("\n✅ Setup complete!")
    print("\n💡 Next steps:")
    print("   1. Run: python check_and_add_liquidity.py")
    print("   2. Then: ./start_all.sh")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
