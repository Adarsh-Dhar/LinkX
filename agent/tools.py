
"""
Custom Tools for the Alpha-Consumer Agent
Works with Crypto.com AI Agent SDK for payment handling and market data
"""

import os
import json
import time
import requests
from eth_account import Account
from eth_account.messages import encode_typed_data
from web3 import Web3
from dotenv import load_dotenv


# Load environment variables
load_dotenv()
CRONOS_RPC_URL = os.getenv("CRONOS_RPC_URL", "https://evm-t3.cronos.org")

# Optional: PoA middleware for EVM compatibility
try:
    from web3.middleware import geth_poa_middleware
    HAS_POA_MIDDLEWARE = True
except ImportError:
    HAS_POA_MIDDLEWARE = False

# Simple decorator to mark tool functions (no external dependency)
def tool(func):
    """Decorator to mark agent tool functions."""
    return func

VVS_ROUTER = "0x3bc8a2c283751Adf1E3FAc823B6Cb0056f9f86C8"
WCRO_ADDRESS = "0x9005E37cDfc4361491996aD7d546fC15AC9aAD9A"
USDC_CONTRACT = "0x908059CF02cbb643Bc96C55e14Fb3699e632479f"

TOKEN_MAP = {
    "usdc": USDC_CONTRACT,
    "cro": "cro",
    "wcro": WCRO_ADDRESS
}

ERC20_ABI = [
    {"constant":False,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"type":"function"},
    {"constant":True,"inputs":[{"name":"_owner","type":"address"},{"name":"_spender","type":"address"}],"name":"allowance","outputs":[{"name":"","type":"uint256"}],"type":"function"},
    {"constant":True,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"}
]

ROUTER_ABI = [
    {"inputs":[{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactETHForTokens","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"payable","type":"function"},
    {"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactTokensForETH","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"}],"name":"getAmountsOut","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"view","type":"function"}
]

def resolve_address(token):
    t = token.lower()
    if t in TOKEN_MAP: return TOKEN_MAP[t]
    return t if t.startswith("0x") else None


@tool
def execute_vvs_swap(token_in: str, token_out: str, amount_in: float, max_slippage: float = 1.0):
    """Executes a swap on VVS Finance."""
    try:
        w3 = Web3(Web3.HTTPProvider(CRONOS_RPC_URL))
        private_key = os.getenv("WALLET_PRIVATE_KEY")
        if not private_key: return {"error": "No Private Key Found"}

        account = w3.eth.account.from_key(private_key)
        my_address = account.address

        addr_in = resolve_address(token_in)
        addr_out = resolve_address(token_out)
        router_addr = Web3.to_checksum_address(VVS_ROUTER)

        if not addr_in or not addr_out: return {"error": "Invalid token"}

        is_native = (addr_in == "cro")
        path_in = Web3.to_checksum_address(WCRO_ADDRESS) if is_native else Web3.to_checksum_address(addr_in)
        path_out = Web3.to_checksum_address(WCRO_ADDRESS) if addr_out == "cro" else Web3.to_checksum_address(addr_out)

        # Calculate Amount in Wei
        amount_in_wei = 0
        if is_native:
            amount_in_wei = w3.to_wei(amount_in, 'ether')
        else:
            ctr = w3.eth.contract(address=path_in, abi=ERC20_ABI)
            dec = ctr.functions.decimals().call()
            amount_in_wei = int(amount_in * (10**dec))

            # AUTO APPROVE
            allowance = ctr.functions.allowance(my_address, router_addr).call()
            if allowance < amount_in_wei:
                print(f"Approving {token_in}...")
                nonce = w3.eth.get_transaction_count(my_address)
                tx = ctr.functions.approve(router_addr, 2**256-1).build_transaction({
                    'from': my_address, 'nonce': nonce, 'gasPrice': w3.eth.gas_price
                })
                signed = w3.eth.account.sign_transaction(tx, private_key)
                w3.eth.send_raw_transaction(signed.raw_transaction)
                time.sleep(5) # Wait for approval

        # Execute Swap
        router = w3.eth.contract(address=router_addr, abi=ROUTER_ABI)
        nonce = w3.eth.get_transaction_count(my_address)
        deadline = int(time.time()) + 300
        path = [path_in, path_out]

        # Get Min Output
        try:
            amounts = router.functions.getAmountsOut(amount_in_wei, path).call()
            min_out = int(amounts[-1] * 0.95)
        except:
            min_out = 0

        if is_native:
            tx = router.functions.swapExactETHForTokens(
                min_out, path, my_address, deadline
            ).build_transaction({
                'from': my_address, 'value': amount_in_wei, 'gas': 300000,
                'gasPrice': w3.eth.gas_price, 'nonce': nonce
            })
        else:
            tx = router.functions.swapExactTokensForETH(
                amount_in_wei, min_out, path, my_address, deadline
            ).build_transaction({
                'from': my_address, 'gas': 300000,
                'gasPrice': w3.eth.gas_price, 'nonce': nonce
            })

        signed = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)

        return {"status": "success", "tx_hash": tx_hash.hex()}

    except Exception as e:
        return {"error": str(e)}


@tool
def get_token_balance(token_address: str):
    return {"balance_readable": "100.0", "symbol": "TEST"}

@tool
def get_trading_signals():
    return []