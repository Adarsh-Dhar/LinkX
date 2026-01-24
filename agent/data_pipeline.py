import requests
import numpy as np
from agent.data_consumer import fetch_node_data

class DataPipeline:
    def __init__(self, market_manager):
        self.market = market_manager
        # Point to the host's Next.js API
        self.chart_api_url = "http://localhost:3600/api/dashboard/chart"
        self.nodes_api_url = "http://localhost:3600/api/market/nodes"

    def fetch_chart_history(self):
        """Fetches the last 50 price points for analysis."""
        try:
            # print(f"   📉 Fetching Chart: {self.chart_api_url}")
            response = requests.get(self.chart_api_url, timeout=3)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    # Support various chart formats (value, price, uv)
                    prices = [float(p.get('value', p.get('price', 0))) for p in data]
                    return prices[-50:] # Return last 50 candles
        except Exception as e:
            print(f"   ⚠️ Chart API Unreachable: {e}")
        return []

    async def fetch_specific_nodes(self, target_categories):
        """Buys data from nodes matching the strategy categories."""
        try:
            # 1. Get All Nodes
            res = requests.get(self.nodes_api_url, timeout=2)
            if res.status_code != 200: return []
            
            all_nodes = res.json()
            
            # 2. Filter by Category
            targets = [n for n in all_nodes if n.get('category') in target_categories]
            
            signals = []
            if targets:
                print(f"   🛒 Acquiring Data from {len(targets)} providers in {target_categories}...")
                for node in targets:
                    # This triggers the Payment + Data Fetch
                    signal = fetch_node_data(
                        node['id'], node['endpointUrl'], node.get('apiKey'), node['category']
                    )
                    signals.append(signal.value if signal else 0.5)
            else:
                print(f"   ⚠️ No providers found for {target_categories}")
                
            return signals
        except Exception as e:
            print(f"   ❌ Node Fetch Error: {e}")
            return []

    # Legacy support
    async def get_market_state(self):
        return np.zeros(10)