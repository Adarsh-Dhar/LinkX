
# --- UNIVERSAL DECORATOR ---
class UniversalTool:
    def __init__(self, func):
        self.func = func
        self.name = func.__name__
    def invoke(self, args):
        return self.func(**args) if isinstance(args, dict) else self.func(args)
    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

def tool(func):
    return UniversalTool(func)

# Add missing get_portfolio_value stub to fix ImportError
@tool
def get_portfolio_value():
    """Stub: Returns a dummy portfolio value. Implement real logic as needed."""
    return {"portfolio_value": 0, "note": "Stub function. Implement logic."}

import os
import time
import json

# --- UNIVERSAL DECORATOR ---
class UniversalTool:
    def __init__(self, func):
        self.func = func
        self.name = func.__name__
    def invoke(self, args):
        return self.func(**args) if isinstance(args, dict) else self.func(args)
    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

def tool(func):
    return UniversalTool(func)

from web3 import Web3
from dotenv import load_dotenv

@tool
def estimate_swap_output(token_in: str, token_out: str, amount_in: float):
    """Stub: Estimate the output amount for a swap. Implement logic as needed."""
    return {"estimated_output": 0, "note": "Stub function. Implement logic."}

load_dotenv()

# ==========================================
# ⚡️ YOUR DEPLOYED CONTRACTS ⚡️
# ==========================================
VVS_ROUTER_ADDR = "0x87AE95401447ef92c32f047a79F51Ed4879D516f"
WCRO_ADDRESS    = "0x8F65e9482DB43F403400C6Cb7B20E7dc132d21D2"
USDC_CONTRACT   = "0xE373E44E5e64496BD092A5ad097881C0fa31D326"
# ==========================================

CRONOS_RPC_URL = os.getenv("CRONOS_RPC_URL", "https://evm-t3.cronos.org")


# --- UNIVERSAL DECORATOR ---
class UniversalTool:
    def __init__(self, func):
        self.func = func
        self.name = func.__name__
    def invoke(self, args):
        return self.func(**args) if isinstance(args, dict) else self.func(args)
    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

def tool(func):
    return UniversalTool(func)

# --- ABIS ---
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [
            {"name": "_spender", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [
            {"name": "_owner", "type": "address"},
            {"name": "_spender", "type": "address"}
        ],
        "name": "allowance",
        "outputs": [{"name": "remaining", "type": "uint256"}],
        "type": "function"
    }
]
# Minimal Router ABI required for swaps
ROUTER_ABI = [{"inputs":[{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactETHForTokens","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactTokensForETH","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactTokensForTokens","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"}],"name":"getAmountsOut","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"view","type":"function"}]

def resolve_address(token):
    token_lower = token.lower()
    if token_lower == "usdc": return Web3.to_checksum_address(USDC_CONTRACT)
    if token_lower == "wcro": return Web3.to_checksum_address(WCRO_ADDRESS)
    
    # CRITICAL: Treat 'cro', 'tcro' as NATIVE
    if token_lower in ["cro", "tcro", "native"]: return "cro"
    
    if token_lower.startswith("0x"): return Web3.to_checksum_address(token)
    return None

@tool
def execute_vvs_swap(token_in: str, token_out: str, amount_in: float, max_slippage: float = 1.0):
    print(f"\n🔄 EXECUTE SWAP: {amount_in} {token_in} -> {token_out}")
    try:
        w3 = Web3(Web3.HTTPProvider(CRONOS_RPC_URL))
        private_key = os.getenv("WALLET_PRIVATE_KEY")
        if not private_key: return {"error": "Missing Private Key"}
        
        account = w3.eth.account.from_key(private_key)
        my_addr = account.address
        router_addr = Web3.to_checksum_address(VVS_ROUTER_ADDR)
        
        # 1. Resolve Addresses
        addr_in = resolve_address(token_in)
        addr_out = resolve_address(token_out)
        
        if not addr_in or not addr_out:
            return {"error": f"Unknown token: {token_in} or {token_out}"}

        # DETECT NATIVE SWAP
        is_native_in = (addr_in == "cro")
        is_native_out = (addr_out == "cro")
        
        canonical_wcro = Web3.to_checksum_address(WCRO_ADDRESS)
        
        # Path logic: Native CRO always uses WCRO as the first/last hop
        path_in = canonical_wcro if is_native_in else addr_in
        path_out = canonical_wcro if is_native_out else addr_out
        path = [path_in, path_out]
        
        # 2. Calculate Amounts & Check Balance
        amount_in_wei = 0
        if is_native_in:
            amount_in_wei = w3.to_wei(amount_in, 'ether')
            balance = w3.eth.get_balance(my_addr)
            if balance < amount_in_wei:
                 return {"error": f"Insufficient Native CRO. Have: {balance/10**18:.4f}, Need: {amount_in}"}
        else:
            ctr = w3.eth.contract(address=path_in, abi=ERC20_ABI)
            dec = ctr.functions.decimals().call()
            amount_in_wei = int(amount_in * (10**dec))
            
            # Check Token Balance
            balance = ctr.functions.balanceOf(my_addr).call()
            if balance < amount_in_wei:
                 return {"error": f"Insufficient {token_in}. Have: {balance/10**dec:.4f}"}

            # Auto-Approve if selling tokens
            allowance = ctr.functions.allowance(my_addr, router_addr).call()
            if allowance < amount_in_wei:
                print(f"   🔐 Approving Router for {token_in}...")
                nonce = w3.eth.get_transaction_count(my_addr)
                tx = ctr.functions.approve(router_addr, 2**256-1).build_transaction({
                    'from': my_addr, 'nonce': nonce, 'gasPrice': int(w3.eth.gas_price * 1.2)
                })
                signed = w3.eth.account.sign_transaction(tx, private_key)
                w3.eth.send_raw_transaction(signed.raw_transaction)
                time.sleep(5) 

        # 3. Check Liquidity
        router = w3.eth.contract(address=router_addr, abi=ROUTER_ABI)
        try:
            amounts = router.functions.getAmountsOut(amount_in_wei, path).call()
            min_out = int(amounts[-1] * (1 - max_slippage/100))
            print(f"   ✅ Liquidity OK. Est Output: {amounts[-1]}")
        except Exception as e:
            return {"error": f"Liquidity Check Failed for {token_in}->{token_out}. Error: {e}"}

        # 4. Execute Transaction
        nonce = w3.eth.get_transaction_count(my_addr)
        deadline = int(time.time()) + 600
        gas_price = int(w3.eth.gas_price * 1.2)
        
        tx_data = None
        
        # === SCENARIO A: NATIVE CRO -> TOKEN (This is what you want) ===
        if is_native_in:
            print("   🚀 Executing swapExactETHForTokens...")
            tx_data = router.functions.swapExactETHForTokens(
                min_out, path, my_addr, deadline
            ).build_transaction({
                'from': my_addr, 
                'value': amount_in_wei, # Send CRO with the tx
                'gas': 350000, 
                'gasPrice': gas_price, 
                'nonce': nonce
            })
            
        # === SCENARIO B: TOKEN -> NATIVE CRO ===
        elif is_native_out:
            print("   🚀 Executing swapExactTokensForETH...")
            tx_data = router.functions.swapExactTokensForETH(
                amount_in_wei, min_out, path, my_addr, deadline
            ).build_transaction({
                'from': my_addr, 'gas': 350000, 'gasPrice': gas_price, 'nonce': nonce
            })
            
        # === SCENARIO C: TOKEN -> TOKEN ===
        else:
            print("   🚀 Executing swapExactTokensForTokens...")
            tx_data = router.functions.swapExactTokensForTokens(
                amount_in_wei, min_out, path, my_addr, deadline
            ).build_transaction({
                'from': my_addr, 'gas': 350000, 'gasPrice': gas_price, 'nonce': nonce
            })

        signed = w3.eth.account.sign_transaction(tx_data, private_key)
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