import requests
import numpy as np
import time
from agent.data_consumer import fetch_node_data

class DataPipeline:
    def __init__(self, market_manager):
        self.market = market_manager
        # Use localhost to hit the Next.js API
        self.chart_api_url = "http://localhost:3600/api/dashboard/chart"
        self.nodes_api_url = "http://localhost:3600/api/market/nodes"

    def fetch_chart_history(self):
        try:
            # Short timeout, we want real-time data or fail fast
            response = requests.get(self.chart_api_url, timeout=1.5)
            if response.status_code == 200:
                data = response.json()
                if not data: return []
                # Return list of prices
                return [float(p['value']) for p in data]
        except:
            pass
        return []

    async def fetch_specific_nodes(self, target_categories):
        """
        Finds the BEST provider for the requested category and pays for it.
        """
        try:
            # 1. Fetch Registry
            res = requests.get(self.nodes_api_url, timeout=1)
            if res.status_code != 200: return []
            all_nodes = res.json()
            
            signals = []
            
            # 2. Iterate through requirements
            for category in target_categories:
                # Find the 'best' node for this category (highest reputation)
                candidates = [n for n in all_nodes if n.get('category') == category]
                if not candidates:
                    print(f"   ⚠️ [Intel] No provider found for {category}")
                    continue
                
                # Pick top rep node
                best_node = sorted(candidates, key=lambda x: x.get('reputation', 0), reverse=True)[0]
                
                print(f"   💸 [Payment] Buying report from: {best_node['name']} ({best_node['price']} USDC)")
                
                # Execute Data Purchase (Wallet Transaction)
                signal = fetch_node_data(
                    best_node['id'], 
                    best_node['endpointUrl'], 
                    best_node.get('apiKey'), 
                    best_node['category']
                )
                
                if signal:
                    val = signal.value
                    sentiment = "Bullish" if val > 0.6 else "Bearish" if val < 0.4 else "Neutral"
                    print(f"      📄 Report Received: {category} is {sentiment} ({val:.2f})")
                    signals.append(val)
                else:
                    print(f"      ❌ Failed to get report from {best_node['name']}")
                    
            return signals

        except Exception as e:
            print(f"   ❌ Pipeline Error: {e}")
            return []