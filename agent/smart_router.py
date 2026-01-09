import requests
import json

DISCOVERY_URL = "http://localhost:3999/directory"

class SmartRouter:
    def __init__(self):
        self.directory = []
        self.refresh_directory()

    def refresh_directory(self):
        """Fetches the list of 48 active nodes."""
        try:
            res = requests.get(DISCOVERY_URL)
            self.directory = res.json()
            print(f"📘 SmartRouter: Loaded {len(self.directory)} active data nodes.")
        except Exception as e:
            print(f"❌ SmartRouter: Could not connect to Registry (Port 3999). Error: {e}")

    def find_providers(self, query):
        """
        Maps a user query (e.g., 'check whale movement') 
        to the relevant server category (e.g., 'whales').
        """
        # Simple Keyword Mapping
        keywords = {
            "price": "price", "cost": "price", "ticker": "price",
            "volume": "volume", "trading": "volume", "traded": "volume",
            "spread": "spread", "liquidity": "spread", "liquid": "spread",
            "depth": "depth", "order book": "depth", "book": "depth",
            "whale": "whales", "smart money": "whales", "large tx": "whales",
            "sentiment": "sentiment", "social": "social_vol", "mention": "social_vol",
            "rsi": "rsi", "tech": "rsi", "technical": "rsi",
            "dev": "devs", "github": "devs", "commit": "devs",
            "tvl": "tvl", "locked": "tvl", "value locked": "tvl",
            "unlock": "unlocks", "vesting": "unlocks",
            "burn": "burn", "burning": "burn", "deflationary": "burn",
            "correlation": "correlation", "btc": "correlation",
            "search": "search", "google": "search", "trend": "search",
            "dominance": "dominance", "percent": "dominance",
            "inflow": "inflows", "inbound": "inflows",
            "outflow": "outflows", "outbound": "outflows",
            "address": "active_addr", "active": "active_addr", "dau": "active_addr",
            "fee": "fees", "gas": "fees", "congestion": "fees",
            "age": "age", "consumed": "age", "token age": "age",
            "mcap": "mcap", "market cap": "mcap", "rank": "mcap",
            "funding": "funding", "rate": "funding"
        }
        
        target_cat = "price"  # Default
        query_lower = query.lower()
        
        for key, val in keywords.items():
            if key in query_lower:
                target_cat = val
                break
        
        # Filter the 48 nodes down to the 2 relevant competitors
        options = [n for n in self.directory if n['category'] == target_cat]
        return options

    def select_best_provider(self, providers, strategy="balanced"):
        """
        Decides which of the 2 competitors to use.
        Strategy: 'cheap', 'premium', or 'balanced'
        """
        if not providers:
            return None
        
        print(f"\n⚖️  COMPETITION: Comparing {len(providers)} nodes for this category...")
        for p in providers:
            print(f"   - Node {p['id']}: Price ${p['price']} USDC | Tier: {p['tier']}")

        # Logic: If strategy is cheap, pick lowest price
        # If premium, pick highest price
        # Balanced = pick the cheaper one by default (cost-efficient)
        
        if strategy == "premium":
            winner = max(providers, key=lambda x: x['price'])
        else:
            winner = min(providers, key=lambda x: x['price'])
             
        print(f"\n🏆 WINNER: {winner['name']} (Port {winner['port']}, Strategy: {strategy})")
        return winner
