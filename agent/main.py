#!/usr/bin/env python3
"""
Intelligent Trading Agent - Context-Aware Purchasing
"""


import os
import sys
import io
import requests
# Import WalletManager with dynamic import fallback
try:
    from agent.wallet_manager import WalletManager
except ModuleNotFoundError:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from wallet_manager import WalletManager
import json
import re
from dotenv import load_dotenv
from .tools import get_token_balance

load_dotenv()

load_dotenv()

# Configuration
MARKET_API_URL = "http://localhost:3600/api/market/nodes"

# --- KNOWLEDGE BASE: Maps User Intent to Node Requirements ---
# "If user asks for X, I need Node Y"
DATA_REQUIREMENTS = {
    "sentiment": ["Sentiment Radar", "AI News Flash"],
    "news": ["AI News Flash", "Macro Watch"],
    "macro": ["Macro Watch", "AI Macro News"],
    "volume": ["Volume Spike Detector", "Quantum Scanner"],
    "whale": ["Whale Tracker", "On-Chain Analytics"],
    "technical": ["Technical Analyst A", "Quantum Scanner"],
    "predict": ["Predictive Model X", "Alpha Oracle"],
    "trend": ["Trend Spotter", "Sentiment Radar"]
}

class MarketManager:
    """Manages interactions with the Alpha Node Market"""
    
    def get_market_state(self):
        try:
            response = requests.get(MARKET_API_URL, timeout=5)
            if response.status_code == 200:
                nodes = response.json()
                total = len(nodes)
                purchased = len([n for n in nodes if n.get('isPurchased')])
                percentage = (purchased / total) * 100 if total > 0 else 0
                    
                return {
                    "nodes": nodes,
                    "purchased_ids": [n['id'] for n in nodes if n.get('isPurchased')],
                    "purchased_names": [n['name'] for n in nodes if n.get('isPurchased')],
                    "percentage": percentage,
                    "missing": [n for n in nodes if not n.get('isPurchased')]
                }
            return None
        except Exception as e:
            print(f"Market Connection Error: {e}")
            return None

    def buy_node(self, node_name_query):
        """Buys a node by fuzzy name matching, using WalletManager for direct payment"""
        state = self.get_market_state()
        if not state:
            return "❌ Market offline."

        # Find best match
        node_name_query = node_name_query.lower()
        target = next((n for n in state['nodes'] if node_name_query in n['name'].lower()), None)

        if not target:
            return f"❌ Node '{node_name_query}' not found."
        if target.get('isPurchased'):
            return None  # Already owned

        # Buy it using WalletManager
        try:
            print(f"💸 Autonomous Purchase: Buying {target['name']} (${target['price']})...")
            # Extract payment info
            price = float(target.get('price', 0))
            pay_to = target.get('payTo') or target.get('paymentAddress')
            currency = target.get('currency', 'USDC')
            if not pay_to:
                return f"⚠️ No payment address for {target['name']}"

            import os
            private_key = os.getenv("WALLET_PRIVATE_KEY", "")
            rpc_url = os.getenv("RPC_URL") or os.getenv("CRONOS_RPC_URL", "")
            if not rpc_url:
                return "⚠️ No RPC URL found in env (RPC_URL or CRONOS_RPC_URL)"
            wallet = WalletManager(private_key, rpc_url)
            decimals = 6 if currency.upper() == "USDC" else 18
            amount_wei = int(price * (10 ** decimals))
            contract = wallet.w3.eth.contract(address=wallet.w3.to_checksum_address(wallet.usdc_address), abi=wallet.ERC20_ABI)
            nonce = wallet.get_nonce()
            tx = contract.functions.transfer(pay_to, amount_wei).build_transaction({
                'from': wallet.address,
                'nonce': nonce,
                'gas': 100000,
                'gasPrice': wallet.get_gas_price(),
            })
            signed_tx = wallet.w3.eth.account.sign_transaction(tx, private_key)
            tx_hash = wallet.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            print(f"Payment sent, tx hash: {tx_hash.hex()}")
            return (f"🚀 **Auto-Acquired Data:** I needed **{target['name']}** to answer your request.\n"
                    f"💰 Paid: {price} {currency} | 🔗 Tx: `{tx_hash.hex()}`\n\n---\n\n")
        except Exception as e:
            return f"⚠️ Purchase Error: {e}\n\n"

class IntelligentAgent:
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
        self.market = MarketManager()
    
    def analyze_needs_and_act(self, user_input):
        """
        1. Parse user input for keywords.
        2. Check if we own the required data nodes.
        3. If not, buy them automatically.
        """
        user_lower = user_input.lower()
        purchase_logs = ""
        
        # Check our knowledge base
        state = self.market.get_market_state()
        if not state: return "" # Can't buy if offline

        for keyword, required_nodes in DATA_REQUIREMENTS.items():
            if keyword in user_lower:
                # User asked for this topic. Do we have at least one relevant node?
                has_capability = any(req in state['purchased_names'] for req in required_nodes)
                
                if not has_capability:
                    # We lack data! Buy the first available node for this topic
                    # Find which specific node from the list is available in the market
                    for node_name in required_nodes:
                        # Check if this node exists in the "missing" list
                        if any(m['name'] == node_name for m in state['missing']):
                            # Buy it!
                            log = self.market.buy_node(node_name)
                            if log: purchase_logs += log
                            break # Only buy one per topic to save money
        
        return purchase_logs

    def _call_llm(self, messages):
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {"model": self.model, "messages": messages}
        try:
            r = requests.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
            return r.json()["choices"][0]["message"]["content"]
        except: return "LLM Error"

    def interact(self, user_input: str):
        """Main Interaction Loop"""
        
        # 1. INTELLIGENT ACQUISITION
        # Before answering, check if we need to buy tools to answer well
        acquisition_report = self.analyze_needs_and_act(user_input)
        
        # 2. STANDARD TOOLS
        response = ""
        if "balance" in user_input.lower():
            cro = get_token_balance.invoke({"token_address": "cro"})
            usdc = get_token_balance.invoke({"token_address": "usdc"})
            response = f"💰 **Wallet Status:**\nCRO: {cro.get('balance_readable',0):.2f}\nUSDC: {usdc.get('balance_readable',0):.2f}"
        
        elif "completion" in user_input.lower():
            state = self.market.get_market_state()
            response = f"📊 **Data Coverage:** {state['percentage']:.1f}% ({len(state['purchased_ids'])} nodes active)"

        else:
            # LLM Chat
            context = "You are an autonomous AI trading agent. You have access to a real-time data market."
            if acquisition_report:
                context += f"\nSYSTEM UPDATE: You just autonomously purchased new data nodes: {acquisition_report}"
            
            msgs = [{"role": "system", "content": context}, {"role": "user", "content": user_input}]
            response = self._call_llm(msgs)

        # Combine auto-buy logs with the final answer
        return acquisition_report + response

# API Entry Point (Used by api.py)

from .autonomous_loop import start_background_loop
agent = IntelligentAgent()
start_background_loop(agent)

if __name__ == "__main__":
    # Console testing
    while True:
        try:
            i = input("\nYou: ")
            if i in ['q', 'exit']: break
            print(f"Agent: {agent.interact(i)}")
        except: break