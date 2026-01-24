import requests
import pandas as pd
from agent.data_consumer import fetch_node_data

class DataPipeline:
    def __init__(self, market_manager):
        self.market = market_manager
        # Internal Docker networking or localhost
        self.chart_api_url = "http://localhost:3600/api/dashboard/chart"
        self.nodes_api_url = "http://localhost:3600/api/market/nodes"

    def fetch_candles(self):
        try:
            response = requests.get(self.chart_api_url, timeout=2)
            if response.status_code == 200:
                data = response.json()
                if not data or len(data) < 20: return None
                df = pd.DataFrame(data)
                cols = ['open', 'high', 'low', 'close', 'volume']
                for c in cols: df[c] = pd.to_numeric(df[c])
                return df
        except: pass
        return None

    async def fetch_dynamic_tools(self, tool_names):
        """
        1. Gets ALL nodes from DB.
        2. Filters for the names requested by the Agent.
        3. Buys/Fetches data from them.
        """
        results = {}
        if not tool_names: return results

        try:
            # 1. Fetch the Registry from the DB (via API)
            res = requests.get(self.nodes_api_url, timeout=2)
            if res.status_code != 200: 
                print("   ❌ [Pipeline] Could not connect to Market API")
                return {}
            
            all_nodes = res.json()
            
            print(f"   🕵️ [Intel] Scanning Market for: {tool_names}...")
            
            for name in tool_names:
                # Find the node with the exact name (Case insensitive match)
                target_node = next((n for n in all_nodes if n['name'].lower() == name.lower()), None)
                
                if not target_node:
                    print(f"      ⚠️ Node not found in DB: {name}")
                    continue
                
                print(f"   🛒 [Purchase] Initiating x402 Protocol for: {target_node['name']}...")
                print(f"      💳 Price: {target_node['price']} USDC | ID: {target_node['id']}")

                # 2. Trigger Consumer (Handles Payment & Fetch)
                # Ensure the DB seed has valid 'endpointUrl' for these nodes!
                signal = fetch_node_data(
                    target_node['id'],
                    target_node.get('endpointUrl'), # Must be valid URL
                    target_node.get('apiKey'),
                    target_node['category']
                )
                
                if signal:
                    results[name] = signal.value
                else:
                    print(f"      ❌ Failed to acquire data from {name}")

        except Exception as e:
            print(f"   ⚠️ Pipeline Error: {e}")

        return results