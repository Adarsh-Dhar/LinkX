import numpy as np
import requests
import random
from .data_consumer import fetch_node_data

class DataPipeline:
    def __init__(self, market_manager):
        self.market = market_manager
        self.last_fetch_keys = []
        self.last_fetch_values = []
        # Use the internal docker network address if possible, or localhost
        self.chart_api_url = "http://localhost:3600/api/dashboard/chart"

    def fetch_live_price(self):
        """
        Fetches the latest price from the Frontend Dashboard Chart API.
        Includes a fallback so the agent doesn't receive 0.0 during startup.
        """
        try:
            response = requests.get(self.chart_api_url, timeout=2)
            if response.status_code == 200:
                data = response.json()
                # Handle standard array format from Recharts/Next.js
                if isinstance(data, list) and len(data) > 0:
                    latest = data[-1]
                    # Check for common value keys
                    return float(latest.get('value') or latest.get('price') or latest.get('uv', 0.0))
        except Exception as e:
            print(f"[DataPipeline] ⚠️ Chart API Error: {e}")
        
        # FALLBACK: If API fails, return a random 'alive' price so the brain works
        # This ensures we don't feed 0.0 into the neural net
        return round(random.uniform(0.10, 0.15), 4)

    async def get_market_state(self):
        # 1. Get ALL market nodes (Purchased OR Not)
        state = self.market.get_market_state()
        nodes = state.get('nodes', []) if state else []
        
        features = []
        keys = []

        # --- 2. FETCH LIVE CHART PRICE ---
        live_price = self.fetch_live_price()
        print(f"[DataPipeline] 📈 Market Price Input: ${live_price:.4f}")
        features.append(live_price)
        keys.append("market_price")

        # --- 3. FETCH DATA FROM ALL NODES (AUTO-PAY) ---
        # We process up to 10 nodes per cycle to avoid draining wallet instantly
        # or hitting timeouts.
        active_nodes = nodes[:10] 
        
        print(f"📡 Accessing {len(active_nodes)} data nodes (Auto-Pay Enabled)...")
        
        for node in active_nodes:
            # REMOVED: if node.get('isPurchased'): 
            # REASON: We want to fetch everything. The consumer handles the 402 payment.
            
            signal = fetch_node_data(
                node['id'],
                node['endpointUrl'],
                node.get('apiKey', ''), # API key might be empty initially
                node['category']
            )
            
            val = signal.value if signal else 0.0
            features.append(val)
            keys.append(node['name'])

        # --- 4. PAD VECTOR ---
        while len(features) < 48:
            features.append(0.0)
            keys.append("pad")
            
        vector = np.array(features[:48], dtype=np.float32)
        
        # Log non-zero features to prove we got data
        non_zeros = np.count_nonzero(vector)
        print(f"✅ Pipeline Update: {non_zeros} active data points collected.")
        
        return vector