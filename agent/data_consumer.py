import requests
from typing import Any, Dict, Optional, Union
from .wallet_manager import WalletManager
import time
import os

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
    private_key = os.getenv("WALLET_PRIVATE_KEY", "")
    rpc_url = os.getenv("RPC_URL", "")
    if not private_key:
        print("[DataConsumer] ⚠️  No Private Key found in env")
        return None
    wallet = WalletManager(private_key, rpc_url)
    max_retries = 2
    for attempt in range(max_retries):
        try:
            resp = requests.get(endpoint, headers=headers, timeout=5)
            if resp.status_code == 402:
                try:
                    body = resp.json()
                    invoice = body.get("invoice", {})
                    price = float(resp.headers.get("X-Price", 0)) or float(body.get("price", 0)) or float(invoice.get("amount", 0))
                    pay_to = resp.headers.get("X-Payment-Address", "") or body.get("pay_to", "") or invoice.get("to", "")
                    currency = resp.headers.get("X-Currency", "USDC") or body.get("currency", "USDC") or invoice.get("currency", "USDC")
                    if not price or not pay_to:
                        print(f"[DataConsumer] ❌ Invalid 402 format from {endpoint}")
                        return None
                except Exception as e:
                    print(f"[DataConsumer] ❌ Failed to parse 402: {e}")
                    return None
                print(f"[DataConsumer] 💰 Paying {price} {currency} to {pay_to} for {category}...")
                try:
                    decimals = 6 if "USDC" in currency.upper() else 18
                    amount_wei = int(price * (10 ** decimals))
                    contract = wallet.w3.eth.contract(
                        address=wallet.w3.to_checksum_address(wallet.usdc_address),
                        abi=wallet.ERC20_ABI
                    )
                    nonce = wallet.get_nonce()
                    tx = contract.functions.transfer(
                        wallet.w3.to_checksum_address(pay_to),
                        amount_wei
                    ).build_transaction({
                        'from': wallet.address,
                        'nonce': nonce,
                        'gas': 150000,
                        'gasPrice': wallet.get_gas_price(),
                    })
                    signed_tx = wallet.w3.eth.account.sign_transaction(tx, private_key)
                    tx_hash = wallet.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
                    tx_hex = tx_hash.hex()
                    print(f"[DataConsumer] ✅ Payment Sent: {tx_hex}")
                    time.sleep(2)
                    headers["X-Payment-Proof"] = tx_hex
                    continue
                except Exception as e:
                    print(f"[DataConsumer] ❌ Payment Transaction Failed: {e}")
                    return None
            if resp.status_code == 200:
                payload = resp.json()
                data = payload.get('data', payload)
                return normalize_data(category, data)
            resp.raise_for_status()
        except Exception as e:
            if "402" not in str(e):
                print(f"[DataConsumer] Error fetching {endpoint}: {str(e)[:100]}")
            return None
    return None
