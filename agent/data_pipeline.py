import aiohttp
import asyncio
import numpy as np
import random
from agent.data_consumer import fetch_node_data

# 🌐 LIVE 48-SERVER ECOSYSTEM MAPPING
# Maps to the 48 autonomous nodes (ports 4000-4047)
# Each category has 2 competitors: A (Premium) and B (Budget)

# Discovery registry URL
REGISTRY_URL = "http://localhost:3999/directory"

# Fallback static mapping (24 categories × 2 competitors = 48 nodes)
DATA_PROVIDERS = {
    # Market Data (Ports 4000-4011)
    "price_A": "http://localhost:4000/data",
    "price_B": "http://localhost:4001/data",
    "volume_A": "http://localhost:4002/data",
    "volume_B": "http://localhost:4003/data",
    "spread_A": "http://localhost:4004/data",
    "spread_B": "http://localhost:4005/data",
    "depth_A": "http://localhost:4006/data",
    "depth_B": "http://localhost:4007/data",
    "mcap_A": "http://localhost:4008/data",
    "mcap_B": "http://localhost:4009/data",
    "funding_A": "http://localhost:4010/data",
    "funding_B": "http://localhost:4011/data",
    
    # On-Chain Data (Ports 4012-4023)
    "inflows_A": "http://localhost:4012/data",
    "inflows_B": "http://localhost:4013/data",
    "outflows_A": "http://localhost:4014/data",
    "outflows_B": "http://localhost:4015/data",
    "whales_A": "http://localhost:4016/data",
    "whales_B": "http://localhost:4017/data",
    "active_addr_A": "http://localhost:4018/data",
    "active_addr_B": "http://localhost:4019/data",
    "fees_A": "http://localhost:4020/data",
    "fees_B": "http://localhost:4021/data",
    "age_A": "http://localhost:4022/data",
    "age_B": "http://localhost:4023/data",
    
    # Sentiment Data (Ports 4024-4031)
    "social_vol_A": "http://localhost:4024/data",
    "social_vol_B": "http://localhost:4025/data",
    "sentiment_A": "http://localhost:4026/data",
    "sentiment_B": "http://localhost:4027/data",
    "search_A": "http://localhost:4028/data",
    "search_B": "http://localhost:4029/data",
    "dominance_A": "http://localhost:4030/data",
    "dominance_B": "http://localhost:4031/data",
    
    # Fundamental Data (Ports 4032-4039)
    "devs_A": "http://localhost:4032/data",
    "devs_B": "http://localhost:4033/data",
    "tvl_A": "http://localhost:4034/data",
    "tvl_B": "http://localhost:4035/data",
    "unlocks_A": "http://localhost:4036/data",
    "unlocks_B": "http://localhost:4037/data",
    "burn_A": "http://localhost:4038/data",
    "burn_B": "http://localhost:4039/data",
    
    # Technical Data (Ports 4040-4047)
    "rsi_A": "http://localhost:4040/data",
    "rsi_B": "http://localhost:4041/data",
    "ma_A": "http://localhost:4042/data",
    "ma_B": "http://localhost:4043/data",
    "volatility_A": "http://localhost:4044/data",
    "volatility_B": "http://localhost:4045/data",
    "correlation_A": "http://localhost:4046/data",
    "correlation_B": "http://localhost:4047/data",
}

class DataPipeline:
    def __init__(self, market_manager):
        self.market = market_manager
        self.last_fetch_keys = []
        self.last_fetch_values = []

    async def get_market_state(self):
        """
        1. Get list of purchased nodes from MarketManager
        2. Fetch data from each node using fetch_node_data (x402 logic)
        3. Pad to 48 features (fixed input size for Brain)
        """
        print("📡 Connecting to 48-node ecosystem (purchased nodes)...")
        state = self.market.get_market_state()
        nodes = state.get('nodes', []) if state else []
        features = []
        keys = []
        for node in nodes:
            if node.get('isPurchased'):
                signal = fetch_node_data(
                    node['id'],
                    node['endpointUrl'],
                    node.get('apiKey', ''),
                    node['category']
                )
                features.append(signal.value if signal else 0.0)
                keys.append(node['name'])
        # Pad to 48 features
        while len(features) < 48:
            features.append(0.0)
            keys.append(f"pad_{len(keys)}")
        features = features[:48]
        keys = keys[:48]
        vector = np.array(features, dtype=np.float32)
        self.last_fetch_keys = keys
        self.last_fetch_values = features
        print(f"✅ Successfully fetched {len(vector)} data points (purchased nodes)")
        print(f"📊 Data range: [{np.min(features):.2f}, {np.max(features):.2f}]")
        return vector
    
    def get_feature_names(self):
        """Returns the list of all 48 feature names for debugging."""
        return self.last_fetch_keys if hasattr(self, 'last_fetch_keys') else []
    
    def get_raw_values(self):
        """Returns the raw (non-normalized) values for transparency."""
        return self.last_fetch_values if hasattr(self, 'last_fetch_values') else []


# Standalone test
async def test_pipeline():
    pipeline = DataPipeline()
    state = await pipeline.get_market_state()
    
    print("\n🧪 TEST RESULTS:")
    print(f"Vector shape: {state.shape}")
    print(f"Sample values: {state[:5]}")
    print(f"\nFeature names:")
    for i, name in enumerate(pipeline.get_feature_names()[:10]):
        print(f"  {i+1}. {name}: {pipeline.get_raw_values()[i]:.2f}")


if __name__ == "__main__":
    asyncio.run(test_pipeline())
