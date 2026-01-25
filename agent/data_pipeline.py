
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
        Fetches data from all required nodes in parallel using NodeConnector.execute_batch.
        Returns (results, failure_flag): failure_flag is True if any required tool could not be bought.
        """
        from agent.node_connector import get_connector
        results = {}
        failure_flag = False
        if not toolkit_names:
            return results, failure_flag
        try:
            # Fetch all nodes from DB to map names to categories
            res = requests.get(self.nodes_api_url, timeout=5)
            if res.status_code != 200:
                print("   ⚠️ Database API unreachable.")
                return results, True
            inventory = res.json()
            active_inventory = [n for n in inventory if n.get('status') == 'active']
            print(f"   📂 [DB] Fetched {len(active_inventory)} active nodes from inventory.")

            # Build batch requests for all toolkit_names
            batch_requests = []
            name_to_node = {}
            for name in toolkit_names:
                # Try to find the node by name
                node = next((n for n in active_inventory if n['name'].lower() == name.lower()), None)
                if not node:
                    # Fallback: find by category if name not found
                    category = next((n['category'] for n in inventory if n['name'].lower() == name.lower()), None)
                    if category:
                        substitutes = [n for n in active_inventory if n['category'] == category]
                        if substitutes:
                            node = sorted(substitutes, key=lambda x: x.get('reputation', 0), reverse=True)[0]
                if node:
                    batch_requests.append({
                        "method": "fetch",
                        "params": [],
                        "category": node['category'],
                        "node_name": node['name'],
                    })
                    name_to_node[name] = node['name']
                else:
                    print(f"      ❌ [DB] No active nodes found for '{name}'.")
                    failure_flag = True

            # If no valid nodes, return early
            if not batch_requests:
                return results, True

            connector = await get_connector()
            batch_results = await connector.execute_batch(batch_requests)

            for idx, res in enumerate(batch_results):
                requested_name = toolkit_names[idx]
                node_name = name_to_node.get(requested_name, requested_name)
                if res.get("success", True) and res.get("data") is not None:
                    val = res["data"].get("value")
                    ts = res["data"].get("timestamp", datetime.utcnow())
                    results[requested_name] = (val, ts)
                else:
                    print(f"      ❌ Failed to acquire data for {requested_name} (node: {node_name}). Error: {res.get('error')}")
                    failure_flag = True

            return results, failure_flag
        except Exception as e:
            print(f"   ⚠️ Pipeline Sync Error: {e}")
            failure_flag = True
            return results, failure_flag