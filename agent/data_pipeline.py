import requests
import pandas as pd
from agent.data_consumer import fetch_node_data

class DataPipeline:
    def __init__(self, market_manager):
        self.market = market_manager
        self.chart_api_url = "http://localhost:3600/api/dashboard/chart"
        self.nodes_api_url = "http://localhost:3600/api/market/nodes"

    def fetch_candles(self):
        """
        Fetches full OHLCV data for expert analysis.
        Returns a Pandas DataFrame or None.
        """
        try:
            response = requests.get(self.chart_api_url, timeout=2)
            if response.status_code == 200:
                data = response.json()
                if not data or len(data) < 20: 
                    return None
                
                # Convert to DataFrame
                df = pd.DataFrame(data)
                # Ensure numeric types
                cols = ['open', 'high', 'low', 'close', 'volume']
                for c in cols:
                    df[c] = pd.to_numeric(df[c])
                
                return df
        except Exception as e:
            # print(f"   ⚠️ Pipeline Error: {e}")
            pass
        return None

    async def fetch_specific_nodes(self, target_categories):
        """
        Attempts to buy data. Returns dictionary { 'CATEGORY': score }.
        """
        results = {}
        try:
            res = requests.get(self.nodes_api_url, timeout=1)
            if res.status_code != 200: return {}
            
            all_nodes = res.json()
            
            for category in target_categories:
                candidates = [n for n in all_nodes if n.get('category') == category]
                
                if not candidates:
                    # Log immediately if missing
                    print(f"   🚩 [MISSING DATA] I require {category} but no provider is available.")
                    continue

                # Buy from the best one
                node = candidates[0]
                print(f"   🛒 [Purchase] Buying {category} intel from {node['name']}...")
                
                signal = fetch_node_data(
                    node['id'], node['endpointUrl'], node.get('apiKey'), node['category']
                )
                
                if signal:
                    results[category] = signal.value
                    
            return results
        except:
            return {}