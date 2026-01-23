#!/usr/bin/env python3
"""
Lightweight Trading Agent - With x402 Market Integration
Direct API calls to Next.js Market + Autonomous Purchasing
"""

import os
import sys
import io
import requests
import json
from dotenv import load_dotenv
from tools import (
    get_token_balance, 
    execute_vvs_swap,
)

load_dotenv()

# Configuration: Pointing to your Next.js Frontend API
# If running in Docker, use "http://host.docker.internal:3600/api/market/nodes"
MARKET_API_URL = "http://localhost:3600/api/market/nodes" 

class MarketManager:
    """Manages interactions with the Alpha Node Market"""

    def get_market_state(self):
        try:
            response = requests.get(MARKET_API_URL, timeout=2)
            if response.status_code == 200:
                nodes = response.json()
                total = len(nodes)
                purchased = len([n for n in nodes if n.get('isPurchased')])
                percentage = (purchased / total) * 100 if total else 0
                return {
                    "nodes": nodes,
                    "total": total,
                    "purchased": purchased,
                    "percentage": percentage,
                    "missing": [n for n in nodes if not n.get('isPurchased')]
                }
            print(f"⚠️ Market API returned status: {response.status_code}")
            return None
        except Exception as e:
            print(f"❌ Market Connection Error: {e}")
            return None

    def buy_node(self, node_id_or_name):
        state = self.get_market_state()
        if not state: return "❌ Error: Market API is offline. Cannot buy node."

        # Try exact ID match first
        target_node = next((n for n in state['nodes'] if n['id'] == node_id_or_name), None)
        
        # Fuzzy name match
        if not target_node:
             search_term = node_id_or_name.lower().strip()
             target_node = next((n for n in state['nodes'] if search_term in n['name'].lower()), None)

        if not target_node: 
            return f"❌ Error: Node '{node_id_or_name}' not found in the market."
        
        try:
            print(f"💸 Buying {target_node['name']} via {MARKET_API_URL}...")
            response = requests.post(MARKET_API_URL, json={"nodeId": target_node['id']})
            
            try:
                data = response.json()
            except:
                return f"❌ Invalid JSON response from server: {response.text}"

            # --- ROBUST ERROR HANDLING ---
            # 1. Detect Mock/LLM responses from backend
            if "response" in data and "txHash" not in data:
                return (f"⚠️ **Backend Error**\n"
                        f"Server returned text instead of transaction data.\n"
                        f"**Server Message:** \"{data['response']}\"")

            tx_hash = data.get('txHash') or data.get('transactionHash') or 'N/A'
            amount = data.get('amountPaid', 'Unknown')
            
            # 2. Success Case
            if data.get('success') or (tx_hash != 'N/A'):
                return (f"🚀 **PAYMENT SUCCESSFUL**\n"
                        f"📦 Node: {target_node['name']}\n"
                        f"💰 Paid: {amount}\n" 
                        f"🔗 Tx Hash: `{tx_hash}`\n"
                        f"✅ Data stream active.")

            # 3. Failure Case
            return (f"❌ Payment failed.\n"
                    f"**Details:** {json.dumps(data, indent=2)}")

        except Exception as e:
            return f"❌ Network error during purchase: {e}"
         
class LightweightAgent:
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
        self.max_tokens = int(os.getenv("OPENROUTER_MAX_TOKENS", "150"))
        self.market = MarketManager()
        
    def _call_llm(self, messages):
        """Call OpenRouter LLM"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        # Prevent LLM from hallucinating trades
        messages[0]["content"] += " Do NOT confirm trades or purchases. If the user wants to buy something, apologize and say you cannot connect to the market."
        
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": 0.0,
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=10
            )
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            return f"LLM Error: {response.text}"
        except Exception as e:
            return f"Connection Error: {e}"
    
    def interact(self, user_input: str):
        user_lower = user_input.lower()
        
        # --- 1. Market Status ---
        if any(w in user_lower for w in ["completion", "progress", "stats", "market status"]):
            state = self.market.get_market_state()
            if state:
                return f"📊 **Market Coverage: {state['percentage']:.1f}%**"
            return "⚠️ Market offline. Cannot fetch stats."

        # --- 2. Buy Command (STRICT MODE) ---
        if "buy" in user_lower or "purchase" in user_lower:
            words = user_input.split()
            buy_index = -1
            if "buy" in words: buy_index = words.index("buy")
            elif "purchase" in words: buy_index = words.index("purchase")
            
            if buy_index != -1:
                query = " ".join(words[buy_index+1:]).replace("node", "").replace("provider", "").strip()
                if query:
                    # Explicitly attempt buy. Do NOT fall through to LLM if this fails.
                    return self.market.buy_node(query)

        # --- 3. Standard Tools & LLM ---
        if "balance" in user_lower:
            # (Simplified for brevity)
            return "💰 Balance check..."
            
        messages = [
            {"role": "system", "content": "You are a trading agent."},
            {"role": "user", "content": user_input}
        ]
        return self._call_llm(messages)

def main():
    agent = LightweightAgent()
    print("🤖 Alpha Agent Online.")
    while True:
        try:
            i = input("\nYou: ")
            if i.lower() in ['q', 'exit']: break
            print(f"Agent: {agent.interact(i)}")
        except KeyboardInterrupt: break

if __name__ == "__main__":
    main()