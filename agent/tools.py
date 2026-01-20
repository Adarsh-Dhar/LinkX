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

# Optional: PoA middleware for EVM compatibility

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

# Example: Direct API integration with Crypto.com using requests
def get_crypto_com_market_data(symbol: str) -> dict:
    """Fetch market data from Crypto.com public API (template)."""
    url = f"https://api.crypto.com/v2/public/get-ticker?instrument_name={symbol}_USDT"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}


# Configuration from environment variables
CRONOS_RPC_URL = os.getenv("CRONOS_RPC_URL", "https://evm-t3.cronos.org")
USDC_CONTRACT = os.getenv("USDC_CONTRACT", "0x908059CF02cbb643Bc96C55e14Fb3699e632479f")
VVS_CONTRACT = os.getenv("VVS_CONTRACT", "0xea59AC2CcEfe907e7F77B502e2C87aC929832bfF")
VVS_ROUTER = os.getenv("VVS_ROUTER", "0x3bc8a2c283751Adf1E3FAc823B6Cb0056f9f86C8")
WCRO_ADDRESS = os.getenv("WCRO_ADDRESS", "0x9005E37cDfc4361491996aD7d546fC15AC9aAD9A")

# Token symbol to address mapping
TOKEN_MAP = {
    "usdc": USDC_CONTRACT,
    "vvs": VVS_CONTRACT,
    "cro": "cro",
    "wcro": WCRO_ADDRESS
}

def resolve_token_address(token: str):
    """Convert token symbol or address to checksum address"""
    token_lower = token.lower().strip()
    if token_lower in TOKEN_MAP:
        addr = TOKEN_MAP[token_lower]
        if addr == "cro": return "cro"
        return Web3.to_checksum_address(addr)
    if token_lower.startswith("0x") and len(token_lower) == 42:
        try:
            return Web3.to_checksum_address(token_lower)
        except:
            return None
    return None

# --- ABI DEFINITIONS ---
ROUTER_ABI = [
    {"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"}],"name":"getAmountsOut","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactTokensForTokens","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactETHForTokens","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"payable","type":"function"},
    {"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactTokensForETH","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"nonpayable","type":"function"}
]

ERC20_ABI = [
    {"constant":False,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"type":"function"},
    {"constant":True,"inputs":[{"name":"_owner","type":"address"},{"name":"_spender","type":"address"}],"name":"allowance","outputs":[{"name":"","type":"uint256"}],"type":"function"},
    {"constant":True,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"},
    {"constant":True,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"}
]

@tool
def execute_vvs_swap(token_in: str, token_out: str, amount_in: float, max_slippage: float = 1.0, chain: str = "cronos_testnet"):
    """Execute token swap on VVS Finance with auto-approval and native token handling."""
    print(f"\n🔄 Initiating VVS Swap: {amount_in} {token_in} → {token_out}")
    
    try:
        # 1. Resolve Addresses
        token_in_addr = resolve_token_address(token_in)
        token_out_addr = resolve_token_address(token_out)
        
        if not token_in_addr or not token_out_addr:
            return {"error": f"Cannot resolve addresses: {token_in} or {token_out}"}
        
        WCRO_ACTUAL = Web3.to_checksum_address(WCRO_ADDRESS)
        ROUTER_ADDRESS = Web3.to_checksum_address(VVS_ROUTER)
        
        # 2. Setup Web3
        w3 = Web3(Web3.HTTPProvider(CRONOS_RPC_URL))
        if not w3.is_connected():
            return {"error": "Could not connect to RPC"}
        
        private_key = os.getenv("WALLET_PRIVATE_KEY")
        if not private_key:
            return {"error": "WALLET_PRIVATE_KEY not set"}
        
        account = w3.eth.account.from_key(private_key)
        my_address = account.address
        print(f"   👤 Wallet: {my_address}")

        # 3. Handle Allowance (Auto-Approve for ERC20s)
        is_native_in = (token_in_addr == "cro")
        token_in_contract = None
        decimals_in = 18
        
        if not is_native_in:
            token_in_contract = w3.eth.contract(address=token_in_addr, abi=ERC20_ABI)
            decimals_in = token_in_contract.functions.decimals().call()
            amount_in_wei = int(amount_in * (10 ** decimals_in))
            
            allowance = token_in_contract.functions.allowance(my_address, ROUTER_ADDRESS).call()
            print(f"   🔐 Allowance check: {allowance} >= {amount_in_wei}")
            
            if allowance < amount_in_wei:
                print(f"   ⚠️  Insufficient allowance. Approving now...")
                try:
                    gas_price = w3.eth.gas_price
                    nonce = w3.eth.get_transaction_count(my_address)
                    
                    approve_tx = token_in_contract.functions.approve(
                        ROUTER_ADDRESS, 
                        2**256 - 1
                    ).build_transaction({
                        'from': my_address,
                        'gas': 100000,
                        'gasPrice': gas_price,
                        'nonce': nonce
                    })
                    
                    signed_approve = w3.eth.account.sign_transaction(approve_tx, private_key)
                    approve_hash = w3.eth.send_raw_transaction(signed_approve.raw_transaction)
                    print(f"   ⏳ Approval sent: {approve_hash.hex()} - Waiting for confirmation...")
                    w3.eth.wait_for_transaction_receipt(approve_hash, timeout=60)
                    print(f"   ✅ Approved!")
                    # Refresh nonce after approval
                    nonce = w3.eth.get_transaction_count(my_address)
                except Exception as e:
                    return {"error": f"Approval failed: {str(e)}"}
        else:
            amount_in_wei = w3.to_wei(amount_in, 'ether')

        # 4. Prepare Swap Path
        path_in = WCRO_ACTUAL if is_native_in else token_in_addr
        path_out = WCRO_ACTUAL if token_out_addr == "cro" else token_out_addr
        path = [path_in, path_out]
        
        # 5. Calculate Outputs
        router = w3.eth.contract(address=ROUTER_ADDRESS, abi=ROUTER_ABI)
        deadline = int(time.time()) + 900
        
        try:
            amounts = router.functions.getAmountsOut(amount_in_wei, path).call()
            amount_out_min = int(amounts[-1] * (1 - max_slippage/100))
            print(f"   💹 Expected output: {amounts[-1]}")
        except Exception as e:
            return {"error": f"Liquidity lookup failed: {str(e)}"}

        # 6. Build Transaction
        gas_price = w3.eth.gas_price
        # Nonce is managed above (incremented if approval happened)
        if 'nonce' not in locals():
             nonce = w3.eth.get_transaction_count(my_address)
        
        if is_native_in:
            # Native CRO -> Token
            print("   ℹ️  Swapping Native CRO (swapExactETHForTokens)")
            swap_tx = router.functions.swapExactETHForTokens(
                amount_out_min,
                path,
                my_address,
                deadline
            ).build_transaction({
                'from': my_address,
                'value': amount_in_wei,
                'gas': 300000,
                'gasPrice': gas_price,
                'nonce': nonce
            })
        elif token_out_addr == "cro":
            # Token -> Native CRO
            print("   ℹ️  Swapping for Native CRO (swapExactTokensForETH)")
            swap_tx = router.functions.swapExactTokensForETH(
                amount_in_wei,
                amount_out_min,
                path,
                my_address,
                deadline
            ).build_transaction({
                'from': my_address,
                'gas': 300000,
                'gasPrice': gas_price,
                'nonce': nonce
            })
        else:
            # Token -> Token
            print("   ℹ️  Swapping Token for Token (swapExactTokensForTokens)")
            swap_tx = router.functions.swapExactTokensForTokens(
                amount_in_wei,
                amount_out_min,
                path,
                my_address,
                deadline
            ).build_transaction({
                'from': my_address,
                'gas': 300000,
                'gasPrice': gas_price,
                'nonce': nonce
            })

        # 7. Execute
        print(f"   🚀 Sending swap transaction...")
        signed_swap = w3.eth.account.sign_transaction(swap_tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_swap.raw_transaction)
        tx_hash_hex = tx_hash.hex()
        
        print(f"   ✅ Swap submitted: {tx_hash_hex}")
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
        
        if receipt['status'] == 1:
            return {
                "status": "success",
                "tx_hash": tx_hash_hex,
                "block_number": receipt['blockNumber'],
                "amount_in": amount_in,
                "path": [token_in, token_out]
            }
        else:
            return {"error": "Swap transaction reverted on-chain", "tx_hash": tx_hash_hex}
            
    except Exception as e:
        print(f"   ❌ Execution Error: {str(e)}")
        return {"error": str(e)}

# Stub for compatibility if needed
@tool
def get_token_balance(token_address: str, chain: str = "cronos_mainnet"):
    return {"balance_readable": 0, "symbol": "TEST"}

@tool
def get_trading_signals(server_url: str = None):
    return {"signals": []}