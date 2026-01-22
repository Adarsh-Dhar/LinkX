#!/usr/bin/env python3
"""
Lightweight Trading Agent - With Market Integration
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
    estimate_swap_output,
    get_trading_signals,
    get_portfolio_value
)

load_dotenv()

# Configuration: Pointing to your Next.js Frontend API
MARKET_API_URL = "http://localhost:3600/api/market/nodes"

class MarketManager:
    """Manages interactions with the Alpha Node Market"""
    
    def get_market_state(self):
        """Fetches the entire list and calculates completion percentage"""
        try:
            # Connect to Next.js API
            response = requests.get(MARKET_API_URL, timeout=5)
            
            if response.status_code == 200:
                nodes = response.json()
                total = len(nodes)
                purchased = len([n for n in nodes if n.get('isPurchased')])
                
                if total == 0:
                    percentage = 0
                else:
                    percentage = (purchased / total) * 100
                    
                return {
                    "nodes": nodes,
                    "total": total,
                    "purchased": purchased,
                    "percentage": percentage,
                    "missing": [n for n in nodes if not n.get('isPurchased')]
                }
            return None
        except Exception as e:
            print(f"Market Connection Error: {e}")
            return None

    def buy_node(self, node_id_or_name):
        """Buys a specific node by ID or fuzzy name matching"""
        state = self.get_market_state()
        if not state:
            return "❌ Error: Could not connect to market API (is localhost:3000 running?)."

        target_node = None
        
        # 1. Try exact ID match
        target_node = next((n for n in state['nodes'] if n['id'] == node_id_or_name), None)
        
        # 2. Try fuzzy name match (e.g. "sentiment" finds "Sentiment Analysis A")
        if not target_node:
            node_id_or_name = node_id_or_name.lower()
            target_node = next((n for n in state['nodes'] if node_id_or_name in n['name'].lower()), None)
            
        if not target_node:
            return f"❌ Node '{node_id_or_name}' not found in the market."
            
        if target_node.get('isPurchased'):
            return f"✅ We already own **{target_node['name']}**. Data stream is active."

        # Execute Purchase via API
        try:
            print(f"💸 Paying for {target_node['name']} using x402 protocol...")
            response = requests.post(MARKET_API_URL, json={"nodeId": target_node['id']})
            
            if response.status_code == 200:
                data = response.json()
                tx_hash = data.get('txHash')
                if tx_hash and tx_hash != 'N/A':
                    return (f"🚀 **PAYMENT SUCCESSFUL**\n"
                            f"📦 Node: {target_node['name']}\n"
                            f"🔗 x402 Transaction: `{tx_hash}`\n"
                            f"✅ Data stream is now active.")
                else:
                    return (f"❌ Payment failed: Transaction hash not received.\n"
                            f"Node: {target_node['name']}\n"
                            f"Response: {data}")
            else:
                return f"❌ Payment failed: {response.text}"
        except Exception as e:
            return f"❌ Network error during purchase: {e}"

class LightweightAgent:
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
        self.max_tokens = int(os.getenv("OPENROUTER_MAX_TOKENS", "150"))
        # Initialize the Market Manager
        self.market = MarketManager()
    
    def _call_llm(self, messages, image_url=None):
        """Call OpenRouter LLM with support for text and image input."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            # Optionally set these for rankings:
            # "HTTP-Referer": os.getenv("OPENROUTER_SITE_URL", ""),
            # "X-Title": os.getenv("OPENROUTER_SITE_NAME", ""),
        }

        # If image_url is provided, format the message accordingly
        if image_url:
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": messages if isinstance(messages, str) else messages[0]["content"]},
                            {"type": "image_url", "image_url": {"url": image_url}}
                        ]
                    }
                ],
                "max_tokens": self.max_tokens,
                "temperature": 0.0,
            }
        else:
            # Standard text-only message
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
                data=json.dumps(payload),
                timeout=20
            )
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            return f"LLM Error: {response.text}"
        except Exception as e:
            return f"Connection Error: {e}"
    
    def interact(self, user_input: str):
        """Process user input with Market & Trading Context"""
        user_lower = user_input.lower()
        
        # --- 1. Market Completion & Status ---
        # Detects questions about "completion", "list", "status"
        if any(w in user_lower for w in ["completion", "progress", "stats", "market status", "list nodes"]):
            state = self.market.get_market_state()
            if state:
                # Generate the "Entire List" view for the user
                purchased_names = [n['name'] for n in state['nodes'] if n.get('isPurchased')]
                missing_names = [n['name'] for n in state['missing']]
                
                return (
                    f"📊 **Alpha Market Coverage: {state['percentage']:.1f}%**\n\n"
                    f"✅ **Acquired ({state['purchased']}):**\n"
                    f"{', '.join(purchased_names) if purchased_names else 'None'}\n\n"
                    f"🔒 **Available to Buy ({len(state['missing'])}):**\n"
                    f"{', '.join(missing_names) if missing_names else 'None'}"
                )
            return "⚠️ Market offline. Cannot fetch stats."

        # --- 2. Buy Command ---
        # Detects "buy [node name]"
        if "buy" in user_lower and ("node" in user_lower or "provider" in user_lower):
            # Simple logic to extract the node name
            words = user_input.split()
            try:
                # Finds the text after 'buy' to use as the search query
                buy_index = -1
                if "buy" in words: buy_index = words.index("buy")
                elif "purchase" in words: buy_index = words.index("purchase")
                
                if buy_index != -1:
                    # Join everything after "buy" to form the query
                    query = " ".join(words[buy_index+1:]).replace("node", "").replace("provider", "").strip()
                    if query:
                        return self.market.buy_node(query)
            except Exception as e:
                print(f"Parsing error: {e}")
                
            return "❓ Which node should I buy? (e.g., 'buy sentiment node')"

        # --- 3. Standard Trading Tools (Existing Logic) ---
        old_stdout = sys.stdout
        sys.stdout = io.StringIO() # Capture output to keep console clean
        
        try:
            if "balance" in user_lower:
                cro = get_token_balance.invoke({"token_address": "cro"})
                usdc = get_token_balance.invoke({"token_address": "usdc"})
                sys.stdout = old_stdout
                return f"💰 Balance:\nCRO: {cro.get('balance_readable',0):.2f}\nUSDC: {usdc.get('balance_readable',0):.2f}"
            
            elif "swap" in user_lower:
                 # Minimal swap logic (you can expand this with your previous complex logic if needed)
                 sys.stdout = old_stdout
                 return "⚠️ To execute swaps, please use the specific 'swap X to Y' format or check the full trading engine."

            # --- 4. LLM Fallback ---
            sys.stdout = old_stdout
            messages = [
                {"role": "system", "content": "You are an autonomous trading agent. You can buy data nodes and trade tokens. Keep answers brief."},
                {"role": "user", "content": user_input}
            ]
            return self._call_llm(messages)
            
        except Exception as e:
            sys.stdout = old_stdout
            return f"Error: {e}"

def main():
    agent = LightweightAgent()
    print("🤖 Alpha Agent Online. Type 'completion' to see market status.")
    print("   (Ensure your Next.js app is running on localhost:3000)")
    
    while True:
        try:
            i = input("\nYou: ")
            if i.lower() in ['q', 'exit']: break
            print(f"Agent: {agent.interact(i)}")
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()