#!/usr/bin/env python3
"""
Deploy updated VVSFactory (with functional VVSPair) and update .env
"""
import os
import json
from web3 import Web3
from dotenv import load_dotenv, set_key

load_dotenv()

RPC_URL = os.getenv("RPC_URL")
PRIVATE_KEY = os.getenv("WALLET_PRIVATE_KEY")

CONTRACT_DIR = "/Users/adarsh/Documents/alpha-consumer/contract"
FACTORY_ARTIFACT = f"{CONTRACT_DIR}/out/VVSFactory.sol/VVSFactory.json"
ENV_PATH = "/Users/adarsh/Documents/alpha-consumer/.env"

def main():
    print("🏗️  Deploying Updated VVSFactory...")
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    account = w3.eth.account.from_key(PRIVATE_KEY)
    print(f"✅ Deployer: {account.address}\n")

    print("🔨 Compiling contracts...")
    os.system(f"cd {CONTRACT_DIR} && forge build --silent")

    with open(FACTORY_ARTIFACT) as f:
        factory_artifact = json.load(f)

    from eth_abi import encode
    constructor_args = encode(['address'], [account.address])

    nonce = w3.eth.get_transaction_count(account.address)
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
    print(f"✅ Factory deployed: {factory_addr}")

    set_key(ENV_PATH, "VVS_FACTORY_ADDR", factory_addr)
    print("📝 Updated .env with new VVS_FACTORY_ADDR")

    print("\nNext: run python add_liquidity_direct.py")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
