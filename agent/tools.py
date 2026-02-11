# ==========================================
# 🧠 LinkX Production-Ready Tools & Brain
# ==========================================
import json
import os
import time
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
        human_intel = memory.get('human_intel', "No external human context provided.")
        formatted_signals = json.dumps(node_signals, indent=2)
        
        prompt = f"""
        You are a Financial Analysis Engine for LinkX.
        Your goal is to provide a unified market bias by synthesizing technical signals and qualitative intelligence.

        --- 1. QUALITATIVE INTELLIGENCE ---
        CONTEXT: {human_intel}

        --- 2. TECHNICAL QUANTITATIVE SIGNALS ---
        {formatted_signals}

        --- 3. MARKET DATA (market_snapshot) ---
        Current Data: {market_data}

        --- SYNTHESIS PROTOCOL ---
        1. STRATEGIC WEIGHTING: If Qualitative Intelligence is available, assign it a higher weighting (0.8) compared to Technical Signals (0.2) in your final decision.
        2. If short_term_memory is empty or no node_signals are available or the nodes are irrelevant, you MUST perform Technical Analysis (TA) of the market_snapshot.
        3. If no purchased signals are available in short_term_memory, you MUST use the market_snapshot and technical_trend to determine a bias.
        4. Look at price_change_5m, recent_volatility, and technical_trend to determine a trend. If technical_trend is BULLISH, bias LONG. If BEARISH, bias SHORT. If NEUTRAL, bias NEUTRAL.
        5. Assign a confidence between 0.10 and 0.50 based purely on price momentum and volatility.
        6. Your JSON response MUST use these exact keys: 'execution_bias' (must be LONG, SHORT, or NEUTRAL), 'risk_confidence' (float 0-1), and 'reasoning' (string).
        7. FORMAT: Return ONLY valid JSON.

        OUTPUT FORMAT:
        {{
            "execution_bias": "LONG" | "SHORT" | "NEUTRAL",
            "risk_confidence": 0.0 to 1.0,
            "reasoning": "Explain the weighting or technical logic used to reach this bias."
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
            )
            raw_text = response.choices[0].message.content.strip()
            
            # Isolate JSON from any conversational noise
            start = raw_text.find('{')
            end = raw_text.rfind('}')
            strategy = json.loads(raw_text[start:end+1])

            bias = str(strategy.get('bias', 'NEUTRAL')).upper()
            confidence = float(strategy.get('confidence', 0.0))
            reasoning = strategy.get('reasoning', 'No reasoning provided.')

            print(f"🤖 [BRAIN VERDICT] Bias: {bias} | Confidence: {confidence}")
            print(f"💡 [REASONING] {reasoning}")

            # Return DICTIONARY to satisfy decision['thought'] access in predictive_agent.py
            return {
                'bias': bias,
                'confidence': confidence,
                'thought': reasoning,
                'utility_score': 100 if human_intel != "No external human context provided." else 0,
                'verdict': 'TRADE' if confidence > 0.15 else 'HOLD'
            }

        except Exception as e:
            print(f"❌ Error in Strategist Reasoning: {e}")
            return {
                'bias': 'NEUTRAL',
                'confidence': 0.0,
                'thought': f"Reasoning failure: {str(e)}",
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
        
        # Etherlink uses WXTZ as the wrapper
        path_in = Web3.to_checksum_address(WXTZ_ADDRESS) if is_native_in else addr_in
        path_out = Web3.to_checksum_address(WXTZ_ADDRESS) if is_native_out else addr_out
        path = [path_in, path_out]
        
        # Handle Decimals & Approval
        if is_native_in:
            amount_in_wei = w3.to_wei(amount_in, 'ether')
        else:
            # Minimal ERC20 ABI for decimals and balance
            erc20 = w3.eth.contract(address=path_in, abi=[
                {"constant":True,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"},
                {"constant":False,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"type":"function"}
            ])
            amount_in_wei = int(amount_in * (10**erc20.functions.decimals().call()))
            
            # Auto-Approve
            print(f"   🔐 Checking Approval for {token_in}...")
            tx = erc20.functions.approve(router_addr, amount_in_wei).build_transaction({
                'from': my_addr, 'nonce': w3.eth.get_transaction_count(my_addr),
                'gasPrice': int(w3.eth.gas_price * 1.1)
            })
            signed = w3.eth.account.sign_transaction(tx, private_key)
            w3.eth.send_raw_transaction(signed.raw_transaction)
            time.sleep(2)

        # Execute Swap
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