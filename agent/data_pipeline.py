import aiohttp
import asyncio
import numpy as np
import random

# A registry of your 48 provider endpoints (simulated mapping)
# In production, these are your actual URLs
DATA_PROVIDERS = {
    # --- Market Data ---
    "price": "http://localhost:3050/market/price",
    "volume_24h": "http://localhost:3050/market/volume",
    "bid_ask_spread": "http://localhost:3050/market/spread",
    "orderbook_depth": "http://localhost:3050/market/depth",
    "trade_velocity": "http://localhost:3050/market/velocity",
    
    # --- Technical Indicators ---
    "rsi_14": "http://localhost:3050/technical/rsi",
    "macd": "http://localhost:3050/technical/macd",
    "bollinger_bands": "http://localhost:3050/technical/bollinger",
    "moving_avg_50": "http://localhost:3050/technical/ma50",
    "moving_avg_200": "http://localhost:3050/technical/ma200",
    
    # --- On-Chain Data ---
    "whale_transactions": "http://localhost:3050/onchain/whales",
    "exchange_inflows": "http://localhost:3050/onchain/inflows",
    "exchange_outflows": "http://localhost:3050/onchain/outflows",
    "active_addresses": "http://localhost:3050/onchain/addresses",
    "transaction_count": "http://localhost:3050/onchain/txcount",
    
    # --- Sentiment Data ---
    "twitter_sentiment": "http://localhost:3050/sentiment/twitter",
    "reddit_sentiment": "http://localhost:3050/sentiment/reddit",
    "news_sentiment": "http://localhost:3050/sentiment/news",
    "fear_greed_index": "http://localhost:3050/sentiment/feargreed",
    "social_volume": "http://localhost:3050/sentiment/volume",
    
    # --- Liquidity Data ---
    "liquidity_pool_size": "http://localhost:3050/liquidity/poolsize",
    "impermanent_loss": "http://localhost:3050/liquidity/il",
    "yield_rate": "http://localhost:3050/liquidity/yield",
    
    # Add 25 more to reach 48 total providers
}

class DataPipeline:
    def __init__(self):
        self.feature_vector = []
        self.provider_count = 48
        
    async def fetch_provider(self, session, category, name, url):
        """Fetch a single data point from a provider."""
        try:
            # In production, uncomment this to fetch real data:
            # async with session.get(url, timeout=aiohttp.ClientTimeout(total=2)) as response:
            #     data = await response.json()
            #     return float(data.get('value', 0))
            
            # FOR DEMO: Simulate diverse data based on category
            await asyncio.sleep(0.01)  # fast IO simulation
            
            # Simulate realistic data ranges based on data type
            if "rsi" in name: 
                return random.uniform(20, 80)
            elif "sentiment" in name: 
                return random.uniform(0, 1)
            elif "whale" in name or "transaction" in name: 
                return random.choice([0, 1])  # Binary signal
            elif "inflow" in name or "outflow" in name: 
                return random.uniform(1000, 1000000)
            elif "price" in name:
                return random.uniform(0.08, 0.15)
            elif "volume" in name:
                return random.uniform(100000, 5000000)
            elif "spread" in name:
                return random.uniform(0.001, 0.01)
            elif "ma" in name or "moving" in name:
                return random.uniform(0.09, 0.14)
            elif "liquidity" in name or "pool" in name:
                return random.uniform(50000, 500000)
            elif "yield" in name:
                return random.uniform(0.05, 0.25)
            else:
                return random.uniform(0, 1)
            
        except Exception as e:
            print(f"⚠️  Error fetching {name}: {e}")
            return 0.0

    async def get_market_state(self):
        """Aggregates all 48 providers into a single normalized vector."""
        print("📡 Fetching from 48 data providers...")
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            keys = []
            
            # 1. Fetch from defined providers
            for k, v in DATA_PROVIDERS.items():
                tasks.append(self.fetch_provider(session, "market", k, v))
                keys.append(k)
            
            # 2. Pad to exactly 48 providers with simulated data
            while len(tasks) < self.provider_count:
                provider_num = len(tasks) + 1
                tasks.append(self.fetch_provider(
                    session, 
                    "simulated", 
                    f"provider_{provider_num}", 
                    "http://mock"
                ))
                keys.append(f"provider_{provider_num}")
            
            # 3. Fetch all data concurrently
            results = await asyncio.gather(*tasks)
            
            # 4. Normalization (Crucial for Neural Networks)
            # AI models need values between 0 and 1 for stable training
            vector = np.array(results, dtype=np.float32)
            
            # Min-Max normalization
            # Protect against division by zero
            vector_min = vector.min()
            vector_max = vector.max()
            if vector_max - vector_min > 0:
                vector = (vector - vector_min) / (vector_max - vector_min)
            
            # 5. Add metadata for debugging
            self.last_fetch_keys = keys
            self.last_fetch_values = results
            
            print(f"✅ Successfully fetched {len(vector)} data points")
            print(f"📊 Data range: [{vector.min():.3f}, {vector.max():.3f}]")
            
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
