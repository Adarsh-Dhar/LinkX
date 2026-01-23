import aiohttp
import asyncio
import numpy as np
import requests
from agent.data_consumer import fetch_node_data

class DataPipeline:
    def __init__(self, market_manager):
        self.market = market_manager
        self.last_fetch_keys = []
        self.last_fetch_values = []
        # Target your specific frontend chart API
        self.chart_api_url = "http://localhost:3600/api/dashboard/chart"

    def fetch_live_price(self):
        """
        Fetches the latest price from the Frontend Dashboard Chart API.
        Returns 0.0 if the API is offline or empty.
        """
        try:
            # The agent is running in Docker/Local, needing access to localhost:3000
            response = requests.get(self.chart_api_url, timeout=2)
            if response.status_code == 200:
                data = response.json()
                if data and isinstance(data, list) and len(data) > 0:
                    # Get the 'value' of the last data point (latest price)
                    latest_point = data[-1]
                    return float(latest_point.get('value', 0.0))
        except Exception as e:
            print(f"[DataPipeline] ⚠️ Failed to fetch chart price: {e}")
        return 0.0

    async def get_market_state(self):
        """
        1. Get list of purchased nodes
        2. Fetch data from nodes (x402)
        3. INTEGRATE LIVE CHART PRICE
        """
        print("📡 Connecting to 48-node ecosystem (purchased nodes)...")
        state = self.market.get_market_state()
        nodes = state.get('nodes', []) if state else []
        features = []
        keys = []

        # --- 1. FETCH LIVE CHART PRICE (High Priority Feature) ---
        live_price = self.fetch_live_price()
        print(f"[DataPipeline] 📈 Live Dashboard Price: ${live_price:.4f}")
        features.append(live_price)
        keys.append("dashboard_price_feed")

        # --- 2. FETCH PURCHASED NODES ---
        for node in nodes:
            if node.get('isPurchased'):
                signal = fetch_node_data(
                    node['id'],
                    node['endpointUrl'],
                    node.get('apiKey', ''),
                    node['category']
                )
                val = signal.value if signal else 0.0
                features.append(val)
                keys.append(node['name'])
        
        # --- 3. PAD VECTOR ---
        # Pad to 48 features (fixed input size for Brain)
        while len(features) < 48:
            features.append(0.0)
            keys.append(f"pad_{len(keys)}")
            
        # Truncate if over 48
        features = features[:48]
        keys = keys[:48]
            
        vector = np.array(features, dtype=np.float32)
        self.last_fetch_keys = keys
        self.last_fetch_values = features
        
        print(f"✅ Pipeline Update: Used {len(nodes)} nodes + Live Chart Feed")
        return vector

    def get_feature_names(self):
        return self.last_fetch_keys
    
    def get_raw_values(self):
        return self.last_fetch_values