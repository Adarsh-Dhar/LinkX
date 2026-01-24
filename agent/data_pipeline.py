import requests
import numpy as np
from agent.data_consumer import fetch_node_data

class DataPipeline:
    def __init__(self, market_manager):
        self.market = market_manager
        # Use 127.0.0.1 to force IPv4 and avoid localhost resolution delays
        self.chart_api_url = "http://127.0.0.1:3600/api/dashboard/chart"
        self.nodes_api_url = "http://127.0.0.1:3600/api/market/nodes"

    def fetch_chart_history(self):
        """
        Fetches real-time candles from the frontend API.
        Returns a list of closing prices.
        """
        try:
            # Short timeout because we want speed
            response = requests.get(self.chart_api_url, timeout=2)
            
            if response.status_code == 200:
                data = response.json()
                if not data: return []

                # Extract 'value' (Close Price)
                prices = [float(p['value']) for p in data]
                
                # Basic validation
                if len(prices) > 0:
                    print(f"   📈 [Pipeline] Chart Data: {len(prices)} points. Current: ${prices[-1]:.4f}")
                    return prices
            
        except Exception as e:
            # print(f"   ⚠️ [Pipeline] Data Fetch Error: {e}")
            pass
            
        return []

    async def fetch_specific_nodes(self, target_categories):
        """Buys data from nodes matching the strategy categories."""
        try:
            res = requests.get(self.nodes_api_url, timeout=2)
            if res.status_code != 200: return []
            
            all_nodes = res.json()
            targets = [n for n in all_nodes if n.get('category') in target_categories]
            
            signals = []
            if targets:
                print(f"   🛒 [Pipeline] Analyzing {len(targets)} providers for {target_categories}...")
                for node in targets:
                    # Triggers Payment & Fetch
                    signal = fetch_node_data(
                        node['id'], node['endpointUrl'], node.get('apiKey'), node['category']
                    )
                    signals.append(signal.value if signal else 0.5)
            
            return signals
        except Exception as e:
            print(f"   ❌ [Pipeline] Node Error: {e}")
            return []

    async def get_market_state(self):
        return np.zeros(10)