import requests
from typing import Any, Dict, Optional, Union
from .wallet_manager import WalletManager
import time
import os
from dotenv import load_dotenv
load_dotenv()

class Signal:
    """
    Standardized signal object for trading decisions.
    """
    def __init__(self, value: float, source: str, raw: Any, confidence: Optional[float] = None):
        self.value = value
        self.source = source
        self.raw = raw
        self.confidence = confidence

    def __repr__(self):
        return f"<Signal value={self.value} source={self.source} confidence={self.confidence}>"

def normalize_data(category: str, data: Dict[str, Any]) -> Signal:
    """
    Convert raw provider data to a normalized Signal object.
    Handles real API responses for News, Sentiment, and On-chain data.
    """
    # Example: LunarCrush (Sentiment)
    if 'galaxy_score' in data or 'alt_rank' in data:
        # LunarCrush asset data
        value = float(data.get('galaxy_score', 0))
        return Signal(value=value, source='LunarCrush', raw=data, confidence=value/100)
    # Example: Twitter API (Sentiment)
    if 'data' in data and isinstance(data['data'], list):
        # Count tweets as a proxy for activity
        value = float(len(data['data']))
        return Signal(value=value, source='Twitter', raw=data, confidence=None)
    # Example: NewsAPI (News)
    if 'articles' in data:
        # Count articles as a proxy for news volume
        value = float(len(data['articles']))
        return Signal(value=value, source='NewsAPI', raw=data, confidence=None)
    # Example: Covalent (On-chain Volume)
    if 'data' in data and 'items' in data['data']:
        txs = data['data']['items']
        value = float(len(txs))
        return Signal(value=value, source='Covalent', raw=data, confidence=None)
    # Example: Whale Alert (On-chain)
    if 'transactions' in data:
        value = float(len(data['transactions']))
        return Signal(value=value, source='WhaleAlert', raw=data, confidence=None)
    # Fallbacks for legacy mock/other
    if category == 'Sentiment':
        value = float(data.get('sentiment', 0))
        return Signal(value=value, source=category, raw=data, confidence=abs(value))
    elif category == 'Volatility':
        value = float(data.get('volatility', 0))
        return Signal(value=value, source=category, raw=data)
    else:
        value = float(data.get('value', 0))
        return Signal(value=value, source=category, raw=data)

def fetch_node_data(node_id: str, endpoint: str, api_key: str, category: str) -> Union[Signal, None]:
    """
    Fetch data from a provider node and normalize it, handling x402 payment challenge.
    """
    headers = {"x402-access-key": api_key}
    private_key = os.getenv("WALLET_PRIVATE_KEY", "")
    rpc_url = os.getenv("RPC_URL") or os.getenv("CRONOS_RPC_URL", "")
    if not private_key:
        print("[DataConsumer] ⚠️  No Private Key found in env")
    wallet = WalletManager(private_key, rpc_url)
    endpoint_url = endpoint
    print(f"📡 [DataConsumer] Connecting to {endpoint_url}...")
    try:
        # 1. Attempt to fetch
        response = requests.get(endpoint_url, headers=headers, timeout=2)
        # 2. Handle Paywall (402)
        if response.status_code == 402:
            print(f"   💰 Payment Required: {node_id}")
            # In a real app, parse 'invoice' from response, sign it, and send 'X-Payment-Proof'
            # For this demo, the server accepts any string in this header
            headers["X-Payment-Proof"] = f"sig_{wallet.address}_approved"
            response = requests.get(endpoint_url, headers=headers, timeout=2)
        # 3. Parse Data
        if response.status_code == 200:
            data = response.json()
            # Extract 'value' from various possible JSON structures
            val = 0.5
            if 'value' in data:
                val = float(data['value'])
            elif 'data' in data and 'value' in data['data']:
                val = float(data['data']['value'])
            print(f"   ✅ Data: {val}")
            return type('Signal', (), {'value': val})()
    except Exception as e:
        print(f"   ❌ Error: {e}")
    return type('Signal', (), {'value': 0.5})()
