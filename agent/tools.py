import os
import time
import json
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

# ==========================================
# ⚡️ YOUR DEPLOYED CONTRACT ADDRESSES ⚡️
# (Updated from your recent logs)
# ==========================================
VVS_ROUTER_ADDR = "0xe14ABffFad314e3E99EfdCE5989029Ee243f147b"
WCRO_ADDRESS    = "0x2D1F548289D153DD4D10FF128d1055c8E5a9DFfc"
USDC_CONTRACT   = "0xf289B934803726687f54336169Db62902C2C59FE"
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

def tool(func): return UniversalTool(func)

# --- ABIS ---
ERC20_ABI = [{"constant":True,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"},{"constant":False,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"type":"function"},{"constant":True,"inputs":[{"name":"_owner","type":"address"},{"name":"_spender","type":"address"}],"name":"allowance","outputs":[{"name":"","type":"uint256"}],"type":"function"},{"constant":True,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}]
ROUTER_ABI = [{"inputs":[],"name":"WETH","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactETHForTokens","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactTokensForETH","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactTokensForTokens","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"}],"name":"getAmountsOut","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"view","type":"function"}]

@tool
def execute_vvs_swap(token_in: str, token_out: str, amount_in: float, max_slippage: float = 1.0):
    print(f"\n🔄 STARTING SWAP: {amount_in} {token_in} -> {token_out}")
    try:
        w3 = Web3(Web3.HTTPProvider(CRONOS_RPC_URL))
        private_key = os.getenv("WALLET_PRIVATE_KEY")
        if not private_key: return {"error": "Missing Private Key"}
        account = w3.eth.account.from_key(private_key)
        my_addr = account.address
        
        # 1. Resolve Addresses
        # We assume 'cro' is native, everything else is an address
        token_map = {
            "usdc": Web3.to_checksum_address(USDC_CONTRACT),
            "wcro": Web3.to_checksum_address(WCRO_ADDRESS),
            "cro": "cro"
        }
        
        addr_in = token_map.get(token_in.lower(), token_in)
        addr_out = token_map.get(token_out.lower(), token_out)
        
        router = w3.eth.contract(address=Web3.to_checksum_address(VVS_ROUTER_ADDR), abi=ROUTER_ABI)
        canonical_wcro = Web3.to_checksum_address(WCRO_ADDRESS)

        # 2. Determine Path & Swap Type
        is_native_in = (addr_in == "cro")
        is_native_out = (addr_out == "cro")

        path_in = canonical_wcro if is_native_in else addr_in
        path_out = canonical_wcro if is_native_out else addr_out
        path = [path_in, path_out]
        
        print(f"   📍 Path: {path}")

        # 3. Calculate Amounts
        amount_in_wei = 0
        if is_native_in:
            amount_in_wei = w3.to_wei(amount_in, 'ether')
        else:
            ctr = w3.eth.contract(address=path_in, abi=ERC20_ABI)
            dec = ctr.functions.decimals().call()
            amount_in_wei = int(amount_in * (10**dec))
            
            # Approve Router if needed
            allowance = ctr.functions.allowance(my_addr, VVS_ROUTER_ADDR).call()
            if allowance < amount_in_wei:
                print("   🔐 Approving Router...")
                tx = ctr.functions.approve(VVS_ROUTER_ADDR, 2**256-1).build_transaction({
                    'from': my_addr, 'nonce': w3.eth.get_transaction_count(my_addr), 'gasPrice': int(w3.eth.gas_price * 1.2)
                })
                w3.eth.send_raw_transaction(w3.eth.account.sign_transaction(tx, private_key).raw_transaction)
                time.sleep(5)

        # 4. Check Liquidity
        try:
            amounts = router.functions.getAmountsOut(amount_in_wei, path).call()
            min_out = int(amounts[-1] * (1 - max_slippage/100))
            print(f"   ✅ Liquidity OK! Output: {amounts[-1]}")
        except Exception as e:
            return {"error": f"Liquidity Pool Missing for {token_in}/{token_out}. Error: {e}"}

        # 5. Execute Correct Swap Function
        nonce = w3.eth.get_transaction_count(my_addr)
        deadline = int(time.time()) + 600
        gas_price = int(w3.eth.gas_price * 1.2)
        
        if is_native_in:
            # Native -> Token
            tx = router.functions.swapExactETHForTokens(
                min_out, path, my_addr, deadline
            ).build_transaction({
                'from': my_addr, 'value': amount_in_wei, 'gas': 350000, 'gasPrice': gas_price, 'nonce': nonce
            })
        elif is_native_out:
            # Token -> Native
            tx = router.functions.swapExactTokensForETH(
                amount_in_wei, min_out, path, my_addr, deadline
            ).build_transaction({
                'from': my_addr, 'gas': 350000, 'gasPrice': gas_price, 'nonce': nonce
            })
        else:
            # Token -> Token (Fix: Use swapExactTokensForTokens)
            print("   ℹ️ Doing Token->Token swap")
            tx = router.functions.swapExactTokensForTokens(
                amount_in_wei, min_out, path, my_addr, deadline
            ).build_transaction({
                'from': my_addr, 'gas': 350000, 'gasPrice': gas_price, 'nonce': nonce
            })

        tx_hash = w3.eth.send_raw_transaction(w3.eth.account.sign_transaction(tx, private_key).raw_transaction)
        return {"status": "success", "tx_hash": tx_hash.hex()}

    except Exception as e:
        return {"error": str(e)}

@tool
def get_token_balance(token_address: str):
    return {"balance_readable": "100.0", "symbol": "TEST"}

@tool
def get_trading_signals():
    return []