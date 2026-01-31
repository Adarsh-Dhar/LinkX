
# --- AlphaStrategist for Cognitive Reasoning/Action ---
import os
import json
from openai import OpenAI

class AlphaStrategist:
    def __init__(self):
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY")
        )
        # Use a high-reasoning model for institutional-grade decision logic
        self.model = "anthropic/claude-3.5-sonnet"

    def rethink_strategy(self, market_snapshot, working_memory):
        """
        Cognitive reasoning step to determine if data acquisition is economically viable.
        """
        prompt = f"""
        ## ROLE: INSTITUTIONAL ALPHA STRATEGIST
        You are an autonomous AI trading desk operator. Your core objective is to maximize 
        Risk-Adjusted Returns while minimizing 'Information Arbitrage' costs (x402 payments).

        ## OPERATIONAL CONTEXT:
        Current Market Snapshot: {json.dumps(market_snapshot)}
        Purchased Intel Memory: {json.dumps(working_memory)}

        ## DECISION PRINCIPLES:
        1. DATA DECAY: Technical signals lose 50% utility every 5 minutes. 
        2. REGIME SENSITIVITY: Only 'PURCHASE_DATA' if the current trend has shifted 
           (e.g., NORMAL -> VOLATILE) or if Memory contains NO relevant category data.
        3. COST PENALTY: Every 402 payment is a drag on our Sharpe Ratio. 
           If the market is 'STABLE', prioritize 'USE_MEMORY' or 'ABORT'.

        ## RESPONSE FORMAT (JSON):
        {{
          "thought": "Deep reasoning regarding market regime vs existing intel age.",
          "verdict": "PURCHASE_DATA | USE_MEMORY | ABORT",
          "target_node_id": "UUID string (if PURCHASE_DATA)",
          "execution_bias": "LONG | SHORT | NEUTRAL",
          "risk_confidence": 0.0-1.0
        }}
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": "You are a professional trader. Respond only in JSON."},
                      {"role": "user", "content": prompt}],
            response_format={ "type": "json_object" }
        )
        return json.loads(response.choices[0].message.content)
                response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": prompt}],
            response_format={ "type": "json_object" }
        )
        return json.loads(response.choices[0].message.content)

    async def route_model(self, phase, prompt, system_prompt=None):
        if phase == "assessment":
            model = "google/gemini-flash-1.5"
        elif phase == "execution":
            model = "anthropic/claude-3.5-sonnet"
        else:
            model = "google/gemini-flash-1.5"
        return await self.get_structured_response(prompt, model=model, system_prompt=system_prompt)

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
VVS_ROUTER_ADDR = os.getenv("VVS_ROUTER_ADDR")
WXTZ_ADDRESS    = os.getenv("WXTZ_ADDRESS")
USDC_CONTRACT   = os.getenv("USDC_CONTRACT")
# ==========================================

RPC_URL = os.getenv("RPC_URL", "https://node.shadownet.etherlink.com")


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
    if token_lower == "wxtz": return Web3.to_checksum_address(WXTZ_ADDRESS)
    # CRITICAL: Treat 'xtz', 'tez', 'native' as NATIVE
    if token_lower in ["xtz", "tez", "native"]: return "xtz"
    if token_lower.startswith("0x"): return Web3.to_checksum_address(token)
    return None

@tool
def execute_vvs_swap(token_in: str, token_out: str, amount_in: float, max_slippage: float = 1.0):
    print(f"\n🔄 EXECUTE SWAP: {amount_in} {token_in} -> {token_out}")
    try:
        w3 = Web3(Web3.HTTPProvider(RPC_URL))
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