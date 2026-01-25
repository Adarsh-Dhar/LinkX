
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

    async def fetch_dynamic_tools(self, tool_names):
        """
        Tries to find exact tool -> Falls back to Category -> Returns nothing if empty.
        """
        results = {}
        if not tool_names:
            return results

        try:
            # 1. LIVE SYNC: Fetch current inventory and build category map
            all_nodes = await self.refresh_market_knowledge()
            if not all_nodes:
                return {}

            # Filter for active nodes only to prevent buying from "dead" nodes
            active_nodes = [n for n in all_nodes if n.get('status') == 'active']

            print(f"   🕵️ [Intel] Scanning Market for: {tool_names}...")

            for name in tool_names:
                # STRATEGY A: EXACT MATCH (using live active nodes)
                target_node = next((n for n in active_nodes if n['name'].lower() == name.lower()), None)

                # STRATEGY B: CATEGORY FALLBACK (using dynamic map)
                if not target_node:
                    category = self.TOOL_CATEGORIES.get(name)
                    if category:
                        substitutes = [n for n in active_nodes if n['category'] == category]
                        if substitutes:
                            # Pick highest reputation substitute available in DB
                            target_node = sorted(substitutes, key=lambda x: x.get('reputation', 0), reverse=True)[0]
                            print(f"      ⚠️ Tool '{name}' missing. Using available substitute: '{target_node['name']}'")

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