import requests
from typing import Any, Dict, Optional, Union
from .wallet_manager import WalletManager
import time

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
    """
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
    # WalletManager should be initialized elsewhere and passed in, but for now, load from env
    import os
    private_key = os.getenv("WALLET_PRIVATE_KEY", "")
    rpc_url = os.getenv("RPC_URL", "")
    wallet = WalletManager(private_key, rpc_url)
    max_retries = 2
    for attempt in range(max_retries):
        try:
            print(f"[fetch_node_data] Fetching from {endpoint} (category: {category})")
            resp = requests.get(endpoint, headers=headers, timeout=10)
            print(f"[fetch_node_data] Status: {resp.status_code}, Response: {resp.text}")
            if resp.status_code == 402:
                # Extract payment info
                try:
                    price = float(resp.headers.get("X-Price", 0))
                    pay_to = resp.headers.get("X-Payment-Address", "")
                    currency = resp.headers.get("X-Currency", "USDC")
                    # Optionally, parse from body if not in headers
                    if not price or not pay_to:
                        body = resp.json()
                        price = float(body.get("price", 0))
                        pay_to = body.get("pay_to", "")
                        currency = body.get("currency", "USDC")
                except Exception as e:
                    print(f"Failed to parse 402 payment info: {e}")
                    return None
                print(f"402 Payment Required: {price} {currency} to {pay_to}")
                # Check atomic spend limit, blacklist, etc. (to be implemented)
                # Send payment
                decimals = 6 if currency.upper() == "USDC" else 18
                amount_wei = int(price * (10 ** decimals))
                # TODO: Add can_spend and blacklist logic here
                # Send USDC payment
                try:
                    contract = wallet.w3.eth.contract(address=wallet.w3.to_checksum_address(wallet.usdc_address), abi=wallet.ERC20_ABI)
                    nonce = wallet.get_nonce()
                    tx = contract.functions.transfer(pay_to, amount_wei).build_transaction({
                        'from': wallet.address,
                        'nonce': nonce,
                        'gas': 100000,
                        'gasPrice': wallet.get_gas_price(),
                    })
                    signed_tx = wallet.w3.eth.account.sign_transaction(tx, private_key)
                    tx_hash = wallet.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
                    print(f"Payment sent, tx hash: {tx_hash.hex()}")
                except Exception as e:
                    print(f"Payment failed: {e}")
                    return None
                # Wait for confirmation (optional, or just sleep briefly)
                time.sleep(2)
                # Retry with payment proof
                headers["X-Payment-Proof"] = tx_hash.hex()
                continue
            resp.raise_for_status()
            payload = resp.json()
            data = payload.get('data', {})
            print(f"[fetch_node_data] Parsed data: {data}")
            signal = normalize_data(category, data)
            print(f"[fetch_node_data] Normalized signal: {signal}")
            return signal
        except Exception as e:
            print(f"Error fetching node data: {e}")
            return None
    print("Failed to fetch node data after payment attempt.")
    return None
