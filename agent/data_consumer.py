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
    # TODO: Implement actual node data fetching logic
    return {}

def normalize_data(category: str, data: dict) -> Signal:
    # TODO: Implement actual normalization logic
    # For now, just extract a float from the first value
    try:
        val = float(next(iter(data.values())))
    except Exception:
        val = default_value
    return Signal(val)
