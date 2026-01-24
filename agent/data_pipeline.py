import numpy as np
import requests
import random
from .data_consumer import fetch_node_data

class DataPipeline:
    def __init__(self, market_manager):
        self.market = market_manager
        import numpy as np
        import requests
        import random
        import time
        from agent.data_consumer import fetch_node_data

        class DataPipeline:
            def __init__(self, market_manager):
                self.market = market_manager
                # Use localhost for internal communication
                self.chart_api_url = "http://127.0.0.1:3000/api/dashboard/chart"
                self.nodes_api_url = "http://127.0.0.1:3000/api/market/nodes"

            def fetch_chart_history(self):
                """
                Fetches the last 50 candles to analyze trend and volatility.
                """
                try:
                    response = requests.get(self.chart_api_url, timeout=2)
                    if response.status_code == 200:
                        data = response.json()
                        # Extract just the values
                        prices = [float(point.get('value', 0)) for point in data]
                        return prices[-50:] # Return last 50 points
                except Exception as e:
                    print(f"   ⚠️ Chart API Error: {e}")
                return []

            def get_available_nodes(self):
                """Fetches the list of all available data providers from the DB."""
                try:
                    response = requests.get(self.nodes_api_url, timeout=2)
                    if response.status_code == 200:
                        return response.json()
                except:
                    pass
                return []

            async def fetch_specific_nodes(self, target_categories):
                """
                Fetches data ONLY from nodes matching the target categories.
                Auto-pays if necessary.
                """
                all_nodes = self.get_available_nodes()
                features = []
        
                print(f"   🔍 Looking for providers in: {target_categories}")
        
                selected_nodes = [n for n in all_nodes if n.get('category') in target_categories]
        
                if not selected_nodes:
                    print("   ⚠️ No matching providers found.")
                    return [0.5] * 5 # Default neutral signals

                for node in selected_nodes:
                    print(f"   🛒 Buying Data from: {node['name']} ({node['category']})...")
                    signal = fetch_node_data(
                        node['id'],
                        node['endpointUrl'],
                        node.get('apiKey', ''),
                        node['category']
                    )
                    val = signal.value if signal else 0.5
                    features.append(val)
            
                return features
            
        vector = np.array(features[:48], dtype=np.float32)
        
        # Log non-zero features to prove we got data
        non_zeros = np.count_nonzero(vector)
        print(f"✅ Pipeline Update: {non_zeros} active data points collected.")
        
        return vector