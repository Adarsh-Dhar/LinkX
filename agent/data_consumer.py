# agent/data_consumer.py
"""
Stub for fetch_node_data, normalize_data, and Signal class to resolve import errors.
Expand with real logic as needed.
"""
from typing import Any

# Dummy Signal class for compatibility
default_value = 0.0
class Signal:
    def __init__(self, value: float = default_value):
        self.value = value

def fetch_node_data(*args, **kwargs) -> Any:
    import requests
    from agent.wallet_manager import WalletManager
    node_url = kwargs.get('node_url') or (args[0] if args else None)
    api_key = kwargs.get('api_key')
    price = kwargs.get('price')
    category = kwargs.get('category')
    wallet = WalletManager()
    headers = {}
    if api_key:
        headers['x-api-key'] = api_key
    try:
        res = requests.get(node_url, headers=headers, timeout=5)
        if res.status_code == 402:
            target_wallet = res.headers.get("X-Payment-Wallet")
            actual_price = float(res.headers.get("X-Payment-Price", price or 0))
            print(f"   💸 [x402] Paying {actual_price} USDC to unlock {category or node_url}...")
            tx_hash = wallet.transfer_usdc(target_wallet, actual_price)
            if tx_hash:
                res = requests.get(node_url, headers={"X-Payment-Proof": tx_hash}, timeout=5)
        if res.status_code == 200:
            data = res.json()
            # Return a real Signal object with the value
            from collections import namedtuple
            Signal = namedtuple('Signal', ['value'])
            return Signal(value=data.get('value', 0.5))
    except Exception as e:
        print(f"   ❌ [x402 Error] {e}")
    return None

def normalize_data(category: str, data: dict) -> Signal:
    # TODO: Implement actual normalization logic
    # For now, just extract a float from the first value
    try:
        val = float(next(iter(data.values())))
    except Exception:
        val = default_value
    return Signal(val)
