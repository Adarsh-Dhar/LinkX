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

    def get_strategy(self, market_data, node_signals, memory):
        """Generates a trading strategy using LLM reasoning."""
        human_intel = memory.get('human_intel', "No external human context provided.")
        formatted_signals = json.dumps(node_signals, indent=2)
        
        prompt = f"""
You are a Financial Analysis Engine for LinkX.
Your response MUST be a valid JSON object with ONLY these keys:
    - execution_bias (string, one of "LONG", "SHORT", "NEUTRAL")
    - risk_confidence (float, 0.0 to 1.0)
    - reasoning (string, concise explanation)

You MUST use double quotes for all keys and values. Do NOT use single quotes. 
Do NOT include markdown, code blocks, or any text before or after the JSON.
Return ONLY the JSON object, nothing else.

Example:
{{"execution_bias": "LONG", "risk_confidence": 0.45, "reasoning": "Technical trend is bullish."}}

Context:
QUALITATIVE INTELLIGENCE: {human_intel}
TECHNICAL SIGNALS: {formatted_signals}
MARKET DATA: {market_data}
"""
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
            )
            raw_text = response.choices[0].message.content.strip()
            
            # Robust JSON extraction (removes markdown backticks if AI ignores instruction)
            json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON object found in response.")
            
            json_str = json_match.group().replace("'", '"')
            strategy = json.loads(json_str)

            # Validation
            required_keys = {'execution_bias', 'risk_confidence', 'reasoning'}
            if not required_keys.issubset(strategy.keys()):
                raise ValueError(f"Missing keys. Required: {required_keys}")
            
            bias = strategy['execution_bias']
            confidence = float(strategy['risk_confidence'])
            reasoning = strategy['reasoning']

            print(f"🤖 [BRAIN VERDICT] Bias: {bias} | Confidence: {confidence}")
            print(f"💡 [REASONING] {reasoning}")

            return {
                'execution_bias': bias,
                'risk_confidence': confidence,
                'reasoning': reasoning,
                'utility_score': 100 if human_intel != "No external human context provided." else 0,
                'verdict': 'TRADE' if confidence > 0.05 else 'HOLD'  # Lowered threshold per requirements
            }

        except Exception as e:
            print(f"❌ Error in Strategist Reasoning: {e}")
            return {
                'execution_bias': 'NEUTRAL',
                'risk_confidence': 0.0,
                'reasoning': f"Reasoning failure: {str(e)}",
                'utility_score': 0,
                'verdict': 'HOLD'
            }

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