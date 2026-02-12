# ==========================================
# 🧠 LinkX Production-Ready Tools & Brain
# ==========================================
import json
import os
import time
import re
from datetime import datetime
from openai import OpenAI

from web3 import Web3
from dotenv import load_dotenv

# --- VVS ROUTER ABI (imported from abi/vvsrouter.ts) ---
import pathlib

# Load the ABI from the TypeScript file (as a Python list)
VVSROUTER_ABI_PATH = os.path.join(os.path.dirname(__file__), '..', 'abi', 'vvsrouter.ts')
def _load_vvsrouter_abi():
    try:
        with open(VVSROUTER_ABI_PATH, 'r') as f:
            content = f.read()
        # Extract the JSON array from the TypeScript export
        import re, json
        match = re.search(r'VVSRouter_ABI\s*=\s*(\[.*\])', content, re.DOTALL)
        if match:
            abi_json = match.group(1)
            return json.loads(abi_json)
    except Exception as e:
        print(f"[tools.py] Warning: Could not load VVSRouter_ABI: {e}")
    return []

ROUTER_ABI = _load_vvsrouter_abi()


load_dotenv()

# --- 1. ALPHA STRATEGIST (THE BRAIN) ---

class AlphaStrategist:
    def __init__(self, api_key=None):
        self.token = api_key or os.getenv("GITHUB_TOKEN")
        if not self.token:
            raise ValueError("❌ GITHUB_TOKEN not found in environment.")
        
        # Using GitHub Models inference endpoint
        self.client = OpenAI(
            base_url="https://models.inference.ai.azure.com",
            api_key=self.token,
        )
        self.model_name = "gpt-4o-mini"

    async def get_strategy(self, market_data, node_signals, memory):
        """Generates a trading strategy using LLM reasoning."""
        human_intel = memory.get('human_intel', "No external human context provided.")
        formatted_signals = json.dumps(node_signals, indent=2)

        # Optimized prompt to prevent AI from adding extra quotes
        prompt = f"""
Analyze the following market data. Formulate a strategy.
Return ONLY a raw JSON object. Do not use Markdown. Do not use backticks.

REQUIRED JSON FORMAT:
{{
    "execution_bias": "LONG", "SHORT", or "NEUTRAL",
    "risk_confidence": float (0.0 to 1.0),
    "reasoning": "string"
}}

MASTER SIGNAL RULE: QUALITATIVE INTELLIGENCE (Human Intel) always overrides MARKET DATA. If human intel reports an 'exploit' or 'vulnerability', you MUST return a SHORT bias regardless of the technical chart.

MASTER SIGNAL RULE: If `QUALITATIVE INTELLIGENCE` contains the words 'vulnerability', 'exploit', or 'liquidations', you MUST prioritize this over price action and return a SHORT bias immediately.

MASTER RULE: QUALITATIVE INTELLIGENCE (Human Intel) is the primary signal. If human intel reports an 'exploit', 'liquidation', or 'vulnerability', you MUST return an `execution_bias` of SHORT and a `risk_confidence` above 0.8, regardless of what the price chart shows.

CRITICAL RULE: QUALITATIVE INTELLIGENCE always takes precedence over MARKET DATA. If Human Intel reports a crash or vulnerability, you MUST output a SHORT bias regardless of the current price trend or technical signals.

PRIORITY RULE: URGENT: QUALITATIVE INTELLIGENCE (Human Intel) always overrides technical trends. If Human Intel contains words like 'exploit', 'liquidations', or 'short now', you MUST provide a SHORT bias regardless of price movement.

CRITICAL INSTRUCTION: If QUALITATIVE INTELLIGENCE contains a warning (vulnerability, crash, sell volume spike), you MUST prioritize this over technical trends. A 'SHORT' bias is mandatory if the intel is bearish, regardless of the price chart.

IMPORTANT RULES:
QUALITATIVE INTELLIGENCE (Human Intel) ALWAYS overrides TECHNICAL SIGNALS. If human intel reports a vulnerability, exploit, or crash, you MUST move to SHORT regardless of the current price trend or technical signals.

MANDATORY: If `human_intel` contains phrases like 'vulnerability', 'dumping', 'security exploit', 'liquidations', or 'short now', you MUST prioritize this as a SHORT bias regardless of technical indicators.

Context:
INTEL: {human_intel}
SIGNALS: {formatted_signals}
MARKET: {market_data}
"""
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
            )
            raw_text = response.choices[0].message.content.strip()

            # Robust Extraction: Find anything between the first { and last }
            import re
            json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
            if not json_match:
                raise ValueError(f"No JSON found in response: {raw_text}")

            json_str = json_match.group()
            # ONLY replace if the AI uses single quotes instead of doubles
            if "'" in json_str and '"' not in json_str:
                json_str = json_str.replace("'", '"')

            strategy = json.loads(json_str)

            # Map the response to your predictive_agent's expected keys
            return {
                'execution_bias': strategy.get('execution_bias', 'NEUTRAL'),
                'risk_confidence': float(strategy.get('risk_confidence', 0.0)),
                'reasoning': strategy.get('reasoning', 'No reason provided'),
                'verdict': 'TRADE' if float(strategy.get('risk_confidence', 0)) > 0.05 else 'HOLD'
            }

        except Exception as e:
            print(f"❌ Error in Strategist Reasoning: {e}")
            return {'execution_bias': 'NEUTRAL', 'risk_confidence': 0.0, 'reasoning': str(e), 'verdict': 'HOLD'}

# --- 2. TRADE ANALYZER ---

class TradeAnalyzer:
    def analyze_win_rate(self, history):
        if not history:
            return 0.0
        wins = [t for t in history if t.get('profit', 0) > 0]
        return len(wins) / len(history)

# --- 3. UNIVERSAL DECORATOR & TOOLS ---

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

# --- 4. ON-CHAIN EXECUTION TOOLS (ETHERLINK) ---

VVS_ROUTER_ADDR = os.getenv("VVS_ROUTER_ADDR")
WXTZ_ADDRESS    = os.getenv("WXTZ_ADDRESS")
USDC_CONTRACT   = os.getenv("USDC_CONTRACT")
RPC_URL         = os.getenv("RPC_URL", "https://node.shadownet.etherlink.com")

# Export for other modules
__all__ = [
    'VVS_ROUTER_ADDR',
    'WXTZ_ADDRESS',
    'USDC_CONTRACT',
    'RPC_URL',
    'ROUTER_ABI',
    'resolve_address',
    'execute_vvs_swap',
    'get_portfolio_value',
    'estimate_swap_output',
    'get_token_balance',
    'get_trading_signals',
]

def resolve_address(token):
    if not token:
        return None
    token_lower = token.lower()
    if token_lower == "usdc": return Web3.to_checksum_address(USDC_CONTRACT)
    if token_lower == "wxtz": return Web3.to_checksum_address(WXTZ_ADDRESS)
    if token_lower in ["xtz", "tez", "native"]: return "xtz"
    if token_lower.startswith("0x"): return Web3.to_checksum_address(token)
    return None

@tool
def execute_vvs_swap(token_in: str, token_out: str, amount_in: float, max_slippage: float = 1.0):
    """Executes a real swap on Etherlink DEX."""
    print(f"\n🔄 EXECUTE SWAP: {amount_in} {token_in} -> {token_out}")
    try:
        w3 = Web3(Web3.HTTPProvider(RPC_URL))
        private_key = os.getenv("WALLET_PRIVATE_KEY")
        if not private_key: return {"error": "Missing Private Key"}
        
        account = w3.eth.account.from_key(private_key)
        my_addr = account.address
        router_addr = Web3.to_checksum_address(VVS_ROUTER_ADDR)
        
        addr_in = resolve_address(token_in)
        addr_out = resolve_address(token_out)
        
        if not addr_in or not addr_out:
            return {"error": f"Unknown token: {token_in} or {token_out}"}

        is_native_in = (addr_in == "xtz")
        is_native_out = (addr_out == "xtz")
        
        path_in = Web3.to_checksum_address(WXTZ_ADDRESS) if is_native_in else addr_in
        path_out = Web3.to_checksum_address(WXTZ_ADDRESS) if is_native_out else addr_out
        path = [path_in, path_out]
        
        if is_native_in:
            amount_in_wei = w3.to_wei(amount_in, 'ether')
        else:
            erc20 = w3.eth.contract(address=path_in, abi=[
                {"constant":True,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"},
                {"constant":False,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"type":"function"}
            ])
            amount_in_wei = int(amount_in * (10**erc20.functions.decimals().call()))
            
            print(f"   🔐 Checking Approval for {token_in}...")
            tx = erc20.functions.approve(router_addr, amount_in_wei).build_transaction({
                'from': my_addr, 
                'nonce': w3.eth.get_transaction_count(my_addr),
                'gasPrice': int(w3.eth.gas_price * 1.1)
            })
            signed = w3.eth.account.sign_transaction(tx, private_key)
            w3.eth.send_raw_transaction(signed.raw_transaction)
            time.sleep(2)

        router = w3.eth.contract(address=router_addr, abi=[
            {"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"}],"name":"getAmountsOut","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"view","type":"function"},
            {"inputs":[{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactETHForTokens","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"payable","type":"function"},
            {"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactTokensForETH","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"nonpayable","type":"function"},
            {"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactTokensForTokens","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"nonpayable","type":"function"}
        ])

        amounts = router.functions.getAmountsOut(amount_in_wei, path).call()
        min_out = int(amounts[-1] * (1 - max_slippage/100))
        deadline = int(time.time()) + 600
        
        if is_native_in:
            func = router.functions.swapExactETHForTokens(min_out, path, my_addr, deadline)
            tx_params = {'from': my_addr, 'value': amount_in_wei}
        elif is_native_out:
            func = router.functions.swapExactTokensForETH(amount_in_wei, min_out, path, my_addr, deadline)
            tx_params = {'from': my_addr}
        else:
            func = router.functions.swapExactTokensForTokens(amount_in_wei, min_out, path, my_addr, deadline)
            tx_params = {'from': my_addr}

        tx = func.build_transaction({
            **tx_params,
            'nonce': w3.eth.get_transaction_count(my_addr),
            'gas': 300000,
            'gasPrice': int(w3.eth.gas_price * 1.1)
        })
        
        signed = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        return {"status": "success", "tx_hash": tx_hash.hex()}

    except Exception as e:
        return {"error": str(e)}

# --- STUBS FOR IMPORTS ---

@tool
def get_portfolio_value():
    return {"portfolio_value": 0}

@tool
def estimate_swap_output(token_in, token_out, amount_in):
    return {"estimated_output": 0}

@tool
def get_token_balance(token_address):
    return {"balance": "0.0"}

@tool
def get_trading_signals():
    return []