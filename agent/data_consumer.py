# agent/data_consumer.py
"""
Stub for fetch_node_data, normalize_data, and Signal class to resolve import errors.
Expand with real logic as needed.
"""
from typing import Any
import asyncio

# Dummy Signal class for compatibility
default_value = 0.0
class Signal:
    def __init__(self, value: float = default_value):
        self.value = value

def fetch_node_data(*args, **kwargs) -> Any:
    """
    Synchronous wrapper for x402 payment and data fetch.
    IMPORTANT: This function is called via run_in_executor in data_pipeline.py
    to avoid blocking the async event loop.
    """
    import requests
    from agent.wallet_manager import WalletManager
    node_url = kwargs.get('node_url') or (args[0] if args else None)
    api_key = kwargs.get('api_key')
    price = kwargs.get('price')
    category = kwargs.get('category')
    
    if not node_url:
        print("   ❌ [fetch_node_data] No node URL provided")
        return None
    
    wallet = WalletManager()
    headers = {}
    if api_key:
        headers['x-api-key'] = api_key
    
    try:
        # Initial request to trigger 402 Payment Required
        res = requests.get(node_url, headers=headers, timeout=5)
        
        if res.status_code == 402:
            # Extract payment details from response headers
            target_wallet = res.headers.get("X-Payment-Wallet")
            if not target_wallet:
                print(f"   ❌ [x402] No payment wallet in headers")
                return None
                
            print(f"   💸 [x402 Target] {target_wallet}")
            actual_price = float(res.headers.get("X-Payment-Price", price or 0))
            print(f"   💰 [x402 Payment] Sending {actual_price} USDC to {target_wallet}")
            
            # Execute on-chain USDC transfer
            tx_hash = wallet.transfer_usdc(target_wallet, actual_price)
            
            if not tx_hash:
                print(f"   ❌ [x402] Payment transaction failed")
                return None
                
            print(f"   ✅ [x402 Tx Hash] {tx_hash}")
            
            # Retry with payment proof in header
            headers["PAYMENT-SIGNATURE"] = tx_hash
            res = requests.get(node_url, headers=headers, timeout=5)
        
        if res.status_code == 200:
            data = res.json()
            # Extract signal value from response
            signal_value = data.get('value') or data.get('signal', 0.5)
            from collections import namedtuple
            SignalTuple = namedtuple('Signal', ['value'])
            print(f"   ✅ [x402 Data] Received signal: {signal_value}")
            return SignalTuple(value=float(signal_value))
        else:
            print(f"   ⚠️  [x402] Unexpected status: {res.status_code}")
            return None
            
    except Exception as e:
        print(f"   ❌ [x402 Error] {e}")
        import traceback
        traceback.print_exc()
        return None

def normalize_data(category: str, data: dict) -> Signal:
    # TODO: Implement actual normalization logic
    # For now, just extract a float from the first value
    try:
        val = float(next(iter(data.values())))
    except Exception:
        val = default_value
    return Signal(val)
