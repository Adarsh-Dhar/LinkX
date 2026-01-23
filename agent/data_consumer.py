import requests
from typing import Any, Dict, Optional, Union

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
    Fetch data from a provider node and normalize it.
    """
    headers = {"x402-access-key": api_key}
    try:
        resp = requests.get(endpoint, headers=headers, timeout=10)
        resp.raise_for_status()
        payload = resp.json()
        data = payload.get('data', {})
        return normalize_data(category, data)
    except Exception as e:
        print(f"Error fetching node data: {e}")
        return None
