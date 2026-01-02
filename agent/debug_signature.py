#!/usr/bin/env python3
"""
Debug script for EIP-712 signature
"""

import os
from dotenv import load_dotenv
from web3 import Web3
from eth_account import Account
from eth_account.messages import encode_typed_data
import json

load_dotenv()

# Configuration
private_key = os.getenv("WALLET_PRIVATE_KEY")
rpc_url = os.getenv("CRONOS_RPC_URL", "https://evm-t3.cronos.org")
usdc_address = os.getenv("USDC_CONTRACT")

account = Account.from_key(private_key)
w3 = Web3(Web3.HTTPProvider(rpc_url))

print(f"Wallet: {account.address}")
print(f"USDC Contract: {usdc_address}")
print()

# Load USDC ABI
with open('usdc_abi.json', 'r') as f:
    usdc_abi = json.load(f)

usdc_contract = w3.eth.contract(
    address=w3.to_checksum_address(usdc_address),
    abi=usdc_abi
)

# Check contract name and version
try:
    name = usdc_contract.functions.name().call()
    version = usdc_contract.functions.version().call()
    print(f"Contract Name: {name}")
    print(f"Contract Version: {version}")
except Exception as e:
    print(f"Could not read contract name/version: {e}")

print()

# Test EIP-712 domain
chain_id = 338
eip712_domain = {
    "name": "USD Coin",
    "version": "2",
    "chainId": chain_id,
    "verifyingContract": usdc_address
}

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

# Create test message
recipient = "0xfe5e03799fe833d93e950d22406f9ad901ff3bb9"
amount = "100000"
nonce = '0x' + os.urandom(32).hex()

import time
now = int(time.time())

message = {
    "from": account.address,
    "to": recipient,
    "value": amount,
    "validAfter": 0,
    "validBefore": now + 3600,
    "nonce": nonce
}

typed_data = {
    "domain": eip712_domain,
    "types": eip712_types,
    "primaryType": "TransferWithAuthorization",
    "message": message
}

print("Signing EIP-712 message...")
encoded = encode_typed_data(full_message=typed_data)
signed = account.sign_message(encoded)
signature = signed.signature.hex()

if not signature.startswith('0x'):
    signature = '0x' + signature

print(f"Signature: {signature}")
print(f"Signature length: {len(signature)} chars ({len(bytes.fromhex(signature[2:]))} bytes)")

# Parse signature
sig_bytes = bytes.fromhex(signature[2:])
r = sig_bytes[:32]
s = sig_bytes[32:64]
v = sig_bytes[64]

print(f"\nSignature components:")
print(f"  r: 0x{r.hex()}")
print(f"  s: 0x{s.hex()}")
print(f"  v: {v} (raw)")

# Test different v values
for v_test in [v, v + 27, 27, 28]:
    print(f"\nTesting with v={v_test}...")
    try:
        nonce_bytes = bytes.fromhex(nonce[2:])
        result = usdc_contract.functions.transferWithAuthorization(
            w3.to_checksum_address(account.address),
            w3.to_checksum_address(recipient),
            int(amount),
            0,
            now + 3600,
            nonce_bytes,
            v_test,
            r,
            s
        ).call({'from': account.address})
        print(f"  ✓ v={v_test} works!")
        break
    except Exception as e:
        error_msg = str(e)
        if "invalid signature" in error_msg.lower():
            print(f"  ✗ Invalid signature with v={v_test}")
        elif "not yet valid" in error_msg.lower():
            print(f"  ✗ Not yet valid (time issue)")
        elif "expired" in error_msg.lower():
            print(f"  ✗ Expired")
        else:
            print(f"  ✗ Error: {error_msg[:100]}")
