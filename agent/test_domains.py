#!/usr/bin/env python3
"""
Test different EIP-712 domain configurations
"""

import os
from dotenv import load_dotenv
from web3 import Web3
from eth_account import Account
from eth_account.messages import encode_typed_data
import json
import time

load_dotenv()

private_key = os.getenv("WALLET_PRIVATE_KEY")
rpc_url = os.getenv("CRONOS_RPC_URL", "https://evm-t3.cronos.org")
usdc_address = os.getenv("USDC_CONTRACT")

account = Account.from_key(private_key)
w3 = Web3(Web3.HTTPProvider(rpc_url))

with open('usdc_abi.json', 'r') as f:
    usdc_abi = json.load(f)

usdc_contract = w3.eth.contract(
    address=w3.to_checksum_address(usdc_address),
    abi=usdc_abi
)

recipient = "0xfe5e03799fe833d93e950d22406f9ad901ff3bb9"
amount = "100000"
nonce = '0x' + os.urandom(32).hex()
now = int(time.time())

eip712_types = {
    "TransferWithAuthorization": [
        {"name": "from", "type": "address"},
        {"name": "to", "type": "address"},
        {"name": "value", "type": "uint256"},
        {"name": "validAfter", "type": "uint256"},
        {"name": "validBefore", "type": "uint256"},
        {"name": "nonce", "type": "bytes32"}
    ]
}

message = {
    "from": account.address,
    "to": recipient,
    "value": amount,
    "validAfter": 0,
    "validBefore": now + 3600,
    "nonce": nonce
}

# Test different domain configurations
test_configs = [
    {"name": "Bridged USDC (Stargate)", "version": "1"},
    {"name": "Bridged USDC (Stargate)", "version": "2"},
    {"name": "Bridged USDC (Stargate)", "version": ""},
    {"name": "devUSDC.e", "version": "1"},
    {"name": "devUSDC.e", "version": "2"},
    {"name": "USD Coin", "version": "2"},  # Original USDC
]

for config in test_configs:
    print(f"\n{'='*60}")
    print(f"Testing: name='{config['name']}', version='{config['version']}'")
    print('='*60)
    
    domain = {
        "name": config["name"],
        "version": config["version"],
        "chainId": 338,
        "verifyingContract": usdc_address
    }
    
    typed_data = {
        "domain": domain,
        "types": eip712_types,
        "primaryType": "TransferWithAuthorization",
        "message": message
    }
    
    # Sign
    encoded = encode_typed_data(full_message=typed_data)
    signed = account.sign_message(encoded)
    signature = signed.signature.hex()
    if not signature.startswith('0x'):
        signature = '0x' + signature
    
    # Parse signature
    sig_bytes = bytes.fromhex(signature[2:])
    r = sig_bytes[:32]
    s = sig_bytes[32:64]
    v = sig_bytes[64]
    
    # Try with standard v values
    for v_val in [27, 28]:
        try:
            nonce_bytes = bytes.fromhex(nonce[2:])
            usdc_contract.functions.transferWithAuthorization(
                w3.to_checksum_address(account.address),
                w3.to_checksum_address(recipient),
                int(amount),
                0,
                now + 3600,
                nonce_bytes,
                v_val,
                r,
                s
            ).call({'from': account.address})
            print(f"✅ SUCCESS with v={v_val}!")
            print(f"   Domain name: '{config['name']}'")
            print(f"   Domain version: '{config['version']}'")
            exit(0)
        except Exception as e:
            if "invalid signature" in str(e).lower():
                continue
            else:
                print(f"   v={v_val}: {str(e)[:80]}")

print("\n" + "="*60)
print("❌ None of the configurations worked")
print("="*60)
