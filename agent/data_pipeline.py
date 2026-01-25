
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from agent.data_consumer import fetch_node_data

class DataPipeline:
    def __init__(self, market_manager):
        self.market = market_manager
        self.chart_api_url = "http://localhost:3600/api/dashboard/chart"
        self.nodes_api_url = "http://localhost:3600/api/market/nodes"

        # Defines what category each tool belongs to (for fallback logic)
        self.TOOL_CATEGORIES = {
            "Quantum Scanner": "TECHNICAL", "Flash Arbitrage": "TECHNICAL", "DeFi Pulse": "TECHNICAL",
            "Neural Oracle": "SENTIMENT", "Social Pulse": "SENTIMENT", "Sentiment Surge": "SENTIMENT",
            "On-Chain Watcher": "ON_CHAIN", "Whale Alert": "ON_CHAIN", "Chainlink Sentinel": "ON_CHAIN",
            "Macro News AI": "NEWS"
        }


    def fetch_candles(self):
        try:
            response = requests.get(self.chart_api_url, timeout=2)
            if response.status_code == 200:
                data = response.json()
                if not data or len(data) < 20:
                    print(f"      ⚠️ API returned only {len(data) if data else 0} records.")
                    return None
                df = pd.DataFrame(data)
                cols = ['open', 'high', 'low', 'close', 'volume']
                for c in cols: df[c] = pd.to_numeric(df[c])
                df = df.sort_values('timestamp').reset_index(drop=True)
                df = df.tail(20)
                print(f"      ✅ Tape Synced: Using {len(df)} most recent data points.")
                return df
        except Exception as e:
            print(f"   ⚠️ Fetch Error: {e}")
        return None

    async def fetch_dynamic_tools(self, tool_names):
        """
        Tries to find exact tool -> Falls back to Category -> Returns nothing if empty.
        """
        results = {}
        if not tool_names: return results

        try:
            # 1. Fetch Market Inventory
            res = requests.get(self.nodes_api_url, timeout=2)
            if res.status_code != 200: return {}
            all_nodes = res.json()
            
            print(f"   🕵️ [Intel] Scanning Market for: {tool_names}...")
            
            for name in tool_names:
                # STRATEGY A: EXACT MATCH
                target_node = next((n for n in all_nodes if n['name'].lower() == name.lower()), None)
                
                # STRATEGY B: CATEGORY FALLBACK (The "Closest Match")
                if not target_node:
                    category = self.TOOL_CATEGORIES.get(name)
                    if category:
                        # Find best available node in same category
                        substitutes = [n for n in all_nodes if n['category'] == category]
                        if substitutes:
                            # Pick highest reputation one
                            target_node = sorted(substitutes, key=lambda x: x.get('reputation', 0), reverse=True)[0]
                            print(f"      ⚠️ Exact tool '{name}' missing. Substituting with '{target_node['name']}' (Same Category).")

                if not target_node:
                    print(f"      ❌ {name} unavailable. No substitutes found.")
                    continue
                
                # STRATEGY C: EXECUTE TRANSACTION
                print(f"   🛒 [Purchase] Paying {target_node['price']} USDC for: {target_node['name']}...")
                
                signal = fetch_node_data(
                    target_node['id'],
                    target_node.get('endpointUrl'),
                    target_node.get('apiKey'),
                    target_node['category']
                )
                
                if signal:
                    results[name] = signal.value # Store under original requested name for logic compatibility
                else:
                    print(f"      ❌ Failed to acquire data.")

        except Exception as e:
            print(f"   ⚠️ Pipeline Error: {e}")

        return results