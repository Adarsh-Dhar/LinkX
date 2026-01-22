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
    estimate_swap_output,
    get_trading_signals,
    get_portfolio_value
)

load_dotenv()

# Configuration: Pointing to your Next.js Frontend API
# Ensure this matches your Next.js port (usually 3000 or 3600)
MARKET_API_URL = "http://localhost:3600/api/market/nodes" 

class MarketManager:
    """Manages interactions with the Alpha Node Market"""

    def get_market_state(self):
        try:
            response = requests.get(MARKET_API_URL, timeout=5)
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
            return None
        except Exception as e:
            print(f"Market Connection Error: {e}")
            return None

    def buy_node(self, node_id_or_name):
        state = self.get_market_state()
        if not state: return "❌ Error: Could not connect to market API."

        target_node = next((n for n in state['nodes'] if n['id'] == node_id_or_name), None)
        if not target_node:
             node_id_or_name = node_id_or_name.lower()
             target_node = next((n for n in state['nodes'] if node_id_or_name in n['name'].lower()), None)

        if not target_node: return "❌ Node not found."
        
        try:
            print(f"💸 Buying {target_node['name']} via {MARKET_API_URL}...")
            response = requests.post(MARKET_API_URL, json={"nodeId": target_node['id']})
            
            try:
                data = response.json()
            except:
                return f"❌ Invalid JSON response: {response.text}"

            # --- ERROR HANDLING FIX ---
            # 1. Check if backend returned a generic 'response' message (Mock/LLM behavior) instead of tx data
            if "response" in data and "txHash" not in data and "success" not in data:
                return (f"⚠️ **Backend Mismatch Detected**\n"
                        f"The server returned a text message instead of transaction data.\n"
                        f"**Server said:** \"{data['response']}\"\n"
                        f"**Troubleshooting:**\n"
                        f"1. Ensure Next.js is running the latest `route.ts` code.\n"
                        f"2. Restart your Next.js server (`pnpm dev`).")

            # 2. Extract info safely
            tx_hash = data.get('txHash') or data.get('transactionHash') or 'N/A'
            amount = data.get('amountPaid', 'Unknown')
            
            # 3. Handle 'HASH_NOT_FOUND' specific debug case
            if "HASH_NOT_FOUND" in str(tx_hash):
                debug_info = data.get('debug', {})
                debug_str = json.dumps(debug_info, indent=2)
                return (f"⚠️ **Payment Succeeded, but Hash Parsing Failed**\n"
                        f"📦 Node: {target_node['name']}\n"
                        f"Debug Data:\n```json\n{debug_str}\n```")

            # 4. Success Case
            if data.get('success') or (tx_hash != 'N/A'):
                return (f"🚀 **PAYMENT SUCCESSFUL**\n"
                        f"📦 Node: {target_node['name']}\n"
                        f"💰 Paid: {amount}\n" 
                        f"🔗 Tx Hash: `{tx_hash}`\n"
                        f"✅ Data stream active.")

            # 5. Generic Failure Case
            return (f"❌ Payment failed.\n"
                    f"**Raw response:**\n```json\n{json.dumps(data, indent=2)}\n```")

        except Exception as e:
            return f"❌ Network error: {e}"
         
class LightweightAgent:
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
        self.max_tokens = int(os.getenv("OPENROUTER_MAX_TOKENS", "150"))
        # Initialize the Market Manager
        self.market = MarketManager()
        
    def check_and_acquire_data(self):
        """
        AUTONOMOUS LOGIC: Checks coverage. 
        If coverage < 30%, automatically buys the cheapest node.
        """
        state = self.market.get_market_state()
        if not state: return None

        # Logic: If we own less than 30% of the market, buy something!
        if state['percentage'] < 30.0:
            missing_nodes = state['missing']
            if missing_nodes:
                target = sorted(missing_nodes, key=lambda x: float(x.get('price', 0)) if x.get('price') else 9999)[0]
                print(f"💡 Low data coverage ({state['percentage']:.1f}%). Autonomously buying {target['name']}...")
                result = self.market.buy_node(target['id'])
                return f"🔔 **Autonomous Action:** Coverage was low ({state['percentage']:.1f}%), so I purchased **{target['name']}**.\n\n{result}"
        return None
    
    def _call_llm(self, messages):
        """Call OpenRouter LLM"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
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
        
        # --- 0. RUN AUTONOMOUS CHECK ---
        auto_action = self.check_and_acquire_data()
        prefix_msg = f"{auto_action}\n\n---\n\n" if auto_action else ""

        # --- 1. Market Completion & Status ---
        if any(w in user_lower for w in ["completion", "progress", "stats", "market status", "list nodes"]):
            state = self.market.get_market_state()
            if state:
                purchased_names = [n['name'] for n in state['nodes'] if n.get('isPurchased')]
                missing_names = [n['name'] for n in state['missing']]
                
                return prefix_msg + (
                    f"📊 **Alpha Market Coverage: {state['percentage']:.1f}%**\n\n"
                    f"✅ **Acquired ({state['purchased']}):**\n"
                    f"{', '.join(purchased_names) if purchased_names else 'None'}\n\n"
                    f"🔒 **Available to Buy ({len(state['missing'])}):**\n"
                    f"{', '.join(missing_names) if missing_names else 'None'}"
                )
            return prefix_msg + "⚠️ Market offline. Cannot fetch stats."

        # --- 2. Buy Command (Improved Detection) ---
        # Trigger if "buy" is present. We try to find a matching node.
        if "buy" in user_lower or "purchase" in user_lower:
            # Clean up the query
            words = user_input.split()
            buy_index = -1
            if "buy" in words: buy_index = words.index("buy")
            elif "purchase" in words: buy_index = words.index("purchase")
            
            if buy_index != -1:
                query = " ".join(words[buy_index+1:]).replace("node", "").replace("provider", "").strip()
                # Only proceed if we actually found a query string
                if query:
                    # Check if this query actually matches a node before committing to the purchase logic
                    state = self.market.get_market_state()
                    if state:
                        target = next((n for n in state['nodes'] if query.lower() in n['name'].lower()), None)
                        if target:
                            return prefix_msg + self.market.buy_node(target['id'])
                        
            # If no node matched, fall through to LLM (e.g. "buy bitcoin")

        # --- 3. Standard Trading Tools ---
        old_stdout = sys.stdout
        sys.stdout = io.StringIO() 
        
        try:
            if "balance" in user_lower:
                cro = get_token_balance.invoke({"token_address": "cro"})
                usdc = get_token_balance.invoke({"token_address": "usdc"})
                sys.stdout = old_stdout
                return prefix_msg + f"💰 Balance:\nCRO: {cro.get('balance_readable',0):.2f}\nUSDC: {usdc.get('balance_readable',0):.2f}"
            
            elif "swap" in user_lower:
                 sys.stdout = old_stdout
                 return prefix_msg + "⚠️ To execute swaps, please use the specific 'swap X to Y' format or check the full trading engine."

            # --- 4. LLM Fallback ---
            sys.stdout = old_stdout
            messages = [
                {"role": "system", "content": "You are an autonomous trading agent. You can buy data nodes and trade tokens. Keep answers brief."},
                {"role": "user", "content": user_input}
            ]
            return prefix_msg + self._call_llm(messages)
            
        except Exception as e:
            sys.stdout = old_stdout
            return prefix_msg + f"Error: {e}"

def main():
    agent = LightweightAgent()
    print("🤖 Alpha Agent Online. Type 'completion' to see market status.")
    print("   (Ensure your Next.js app is running on localhost:3600)")
    
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