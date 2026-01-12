import aiohttp
import asyncio
import numpy as np
import random

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
    def __init__(self):
        self.feature_vector = []
        self.provider_count = 48
        self.providers = None  # Will be populated from registry
        
    async def discover_providers(self, session):
        """Fetch provider directory from the registry."""
        try:
            async with session.get(REGISTRY_URL, timeout=aiohttp.ClientTimeout(total=3)) as response:
                if response.status == 200:
                    providers = await response.json()
                    print(f"✅ Discovered {len(providers)} providers from registry")
                    return providers
        except Exception as e:
            print(f"⚠️  Registry unreachable, using static mapping: {e}")
        
        # Fallback to static mapping
        return None
        
    async def fetch_provider(self, session, provider_info):
        """Fetch data from a single provider with payment flow simulation."""
        name = provider_info.get('name', provider_info.get('id', 'unknown'))
        url = provider_info.get('url')
        
        try:
            # Step 1: Request data (expect 402 Payment Required)
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=2)) as response:
                if response.status == 402:
                    # Paywall detected - simulate payment
                    invoice = await response.json()
                    
                    # Step 2: Send payment proof (simulated for demo)
                    payment_url = url.replace('/data', '/data/payment')
                    async with session.post(
                        payment_url, 
                        json={"tx_hash": "0xsimulated_payment"},
                        timeout=aiohttp.ClientTimeout(total=2)
                    ) as payment_response:
                        if payment_response.status == 200:
                            result = await payment_response.json()
                            data = result.get('data', {})
                            
                            # Extract first numeric value from data
                            for key, value in data.items():
                                if isinstance(value, (int, float)):
                                    return float(value)
                            
                            # If no numeric value, extract from nested data
                            if 'value' in data:
                                return float(data['value'])
                            
                            # No valid data structure - return 0.0
                            print(f"⚠️  No numeric data in response from {name}")
                            return 0.0
                        
                elif response.status == 200:
                    # Direct access (no paywall)
                    result = await response.json()
                    data = result.get('data', result)
                    
                    # Extract numeric value
                    if isinstance(data, (int, float)):
                        return float(data)
                    elif 'value' in data:
                        return float(data['value'])
                    
                    # No valid numeric data - return 0.0
                    print(f"⚠️  No numeric data in response from {name}")
                    return 0.0
                    
            return 0.0
            
        except asyncio.TimeoutError:
            print(f"⏱️  Timeout: {name}")
            return 0.0
        except Exception as e:
            print(f"⚠️  Error fetching {name}: {e}")
            return 0.0

    async def get_market_state(self):
        """Aggregates all 48 providers into a single normalized vector."""
        print("📡 Connecting to 48-node ecosystem...")
        
        async with aiohttp.ClientSession() as session:
            # Step 1: Discover providers from registry
            providers = await self.discover_providers(session)
            
            if providers:
                # Use dynamic provider list from registry
                print(f"🌐 Using {len(providers)} live providers")
                self.providers = providers
                tasks = [self.fetch_provider(session, p) for p in providers]
                keys = [p.get('id', f"provider_{i}") for i, p in enumerate(providers)]
            else:
                # Fallback to static mapping
                print("📋 Using static provider mapping")
                tasks = []
                keys = []
                for k, v in DATA_PROVIDERS.items():
                    provider_info = {'id': k, 'name': k, 'url': v}
                    tasks.append(self.fetch_provider(session, provider_info))
                    keys.append(k)
            
            # Step 2: Fetch all data concurrently
            print(f"⚡ Fetching from {len(tasks)} endpoints...")
            results = await asyncio.gather(*tasks)
            
            # Step 3: Normalization (Crucial for Neural Networks)
            # AI models need values between 0 and 1 for stable training
            vector = np.array(results, dtype=np.float32)
            
            # Min-Max normalization with safeguards
            vector_min = vector.min()
            vector_max = vector.max()
            if vector_max - vector_min > 0:
                vector = (vector - vector_min) / (vector_max - vector_min)
            else:
                # All values are the same, default to 0.5
                vector = np.full_like(vector, 0.5)
            
            # Step 4: Store metadata for debugging
            self.last_fetch_keys = keys
            self.last_fetch_values = results
            
            print(f"✅ Successfully fetched {len(vector)} data points")
            print(f"📊 Data range: [{np.min(results):.2f}, {np.max(results):.2f}]")
            print(f"🔢 Normalized: [{vector.min():.3f}, {vector.max():.3f}]")
            
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
