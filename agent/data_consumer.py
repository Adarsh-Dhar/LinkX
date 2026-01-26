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
    """
    Fetch data from a node endpoint, handling x402 handshake if required.
    Args:
        node_url (str): The endpoint URL to fetch from.
        api_key (str, optional): API key for the node, if required.
        wallet_manager (WalletManager, optional): WalletManager instance for payments.
        price (float, optional): Expected price for the data (for test/mocks).
        destination (str, optional): Payment destination (for test/mocks).
    Returns:
        dict: The fetched data.
    """
    import requests
    from agent.wallet_manager import WalletManager
    node_url = kwargs.get('node_url') or (args[0] if args else None)
    api_key = kwargs.get('api_key')
    wallet_manager = kwargs.get('wallet_manager')
    headers = {}
    if api_key:
        headers['x-api-key'] = api_key
    resp = requests.get(node_url, headers=headers, timeout=5)
    if resp.status_code == 200:
        return resp.json()
    if resp.status_code == 402:
        invoice = resp.json()
        price = float(invoice.get("price", 0))
        destination = invoice.get("destination")
        if not price or not destination:
            raise Exception("Invalid x402 invoice")
        if not wallet_manager:
            raise Exception("WalletManager required for payment")
        # 1. Pay via WalletManager (returns tx_hash)
        tx_hash = wallet_manager.send_transaction(destination=destination, amount=price)
        if not tx_hash:
            raise Exception("USDC payment failed")
        # 2. Retry with X-Payment-Proof
        headers['x-payment-proof'] = tx_hash
        paid_resp = requests.get(node_url, headers=headers, timeout=5)
        if paid_resp.status_code == 200:
            return paid_resp.json()
        raise Exception(f"Payment proof rejected: {paid_resp.text}")
    raise Exception(f"Node fetch failed: {resp.status_code} {resp.text}")

def normalize_data(category: str, data: dict) -> Signal:
    # TODO: Implement actual normalization logic
    # For now, just extract a float from the first value
    try:
        val = float(next(iter(data.values())))
    except Exception:
        val = default_value
    return Signal(val)
