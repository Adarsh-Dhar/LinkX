
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
        # TOOL_CATEGORIES will be dynamically populated
        self.TOOL_CATEGORIES = {}
    async def refresh_market_knowledge(self):
        """Fetches all nodes to map names to categories dynamically."""
        try:
            res = requests.get(self.nodes_api_url, timeout=2)
            if res.status_code == 200:
                all_nodes = res.json()
                # Dynamically build the map from the DB
                self.TOOL_CATEGORIES = {n['name']: n['category'] for n in all_nodes}
                return all_nodes
        except Exception as e:
            print(f"   ⚠️ Market Sync Error: {e}")
        return []


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

    async def fetch_dynamic_tools(self, toolkit_names):
        """
        x402 Payment Flow (Async):
        1. Get ALL from DB first (Thinking phase)
        2. Filter for the specific tool or category fallback
        3. Execute x402 payment in parallel and return (value, timestamp) if payment is successful
        Returns (results, failure_flag): failure_flag is True if any required tool could not be bought.
        """
        results = {}
        failure_flag = False
        if not toolkit_names:
            return results, failure_flag
        try:
            res = requests.get(self.nodes_api_url, timeout=5)
            if res.status_code != 200:
                print("   ⚠️ Database API unreachable.")
                return results, True
            inventory = res.json()
            active_inventory = [n for n in inventory if n.get('status') == 'active']
            print(f"   📂 [DB] Fetched {len(active_inventory)} active nodes from inventory.")

            async def fetch_one(name):
                # Filter for the specific tool
                target_node = next((n for n in active_inventory if n['name'].lower() == name.lower()), None)
                # Category Fallback logic
                if not target_node:
                    category = next((n['category'] for n in inventory if n['name'].lower() == name.lower()), None)
                    if category:
                        substitutes = [n for n in active_inventory if n['category'] == category]
                        if substitutes:
                            target_node = sorted(substitutes, key=lambda x: x.get('reputation', 0), reverse=True)[0]
                if target_node:
                    # Simulate async x402 payment flow (wrap sync in executor if needed)
                    loop = asyncio.get_event_loop()
                    signal = await loop.run_in_executor(None, fetch_node_data,
                        target_node['id'],
                        target_node.get('endpointUrl'),
                        target_node.get('apiKey'),
                        target_node['category'],
                        float(target_node.get('price', 0.0))
                    )
                    if signal:
                        # Expect signal.value and signal.timestamp
                        return (name, (getattr(signal, 'value', None), getattr(signal, 'timestamp', datetime.utcnow())))
                    else:
                        print(f"      ❌ Failed to acquire data for {name}.")
                        return (name, None)
                else:
                    print(f"      ❌ [DB] No active nodes found for '{name}'.")
                    return (name, None)

            fetch_tasks = [fetch_one(name) for name in toolkit_names]
            fetch_results = await asyncio.gather(*fetch_tasks)
            for name, result in fetch_results:
                if result is not None and result[0] is not None:
                    results[name] = result
                else:
                    failure_flag = True
            return results, failure_flag
        except Exception as e:
            print(f"   ⚠️ Pipeline Sync Error: {e}")
            failure_flag = True
            return results, failure_flag