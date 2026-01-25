import requests
import time
from .wallet_manager import WalletManager
from collections import namedtuple

Signal = namedtuple('Signal', ['value'])

def fetch_node_data(node_id, endpoint_url, api_key, category, price=0.0):
    """
    x402 Demo Protocol:
    1. Identify the target wallet and price from the database/headers.
    2. Execute a REAL USDC transfer on Cronos.
    3. Return test data only if the payment broadcast is successful.
    """
    import os
    from dotenv import load_dotenv
    from pathlib import Path
    # Load .env from project root if not already loaded
    load_dotenv(Path(__file__).parent.parent / '.env')
    private_key = os.getenv("WALLET_PRIVATE_KEY")
    rpc_url = os.getenv("CRONOS_RPC_URL", os.getenv("RPC_URL"))
    wallet = WalletManager(private_key, rpc_url)
    # In demo phase, if endpoint is null or external, we use a fixed demo treasury address
    DEMO_TREASURY = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e" 
    try:
        if price > 0:
            print(f"   💸 [x402] Node '{node_id}' requires {price} USDC. Initiating payment...")
            # Execute the actual blockchain transaction
            tx_hash = wallet.transfer_usdc(DEMO_TREASURY, price)
            if tx_hash:
                print(f"   ✅ [Paid] Transaction Hash: {tx_hash}")
                print(f"   📥 [Demo] Unlocking test data for {category}...")
                time.sleep(1)
                test_values = {
                    "Sentiment": 0.82,
                    "On-Chain": 0.65,
                    "Technical": 0.44,
                    "News": 0.91
                }
                return Signal(value=test_values.get(category, 0.5))
            else:
                print(f"   ❌ [x402] Payment failed for {node_id}. Access denied.")
                return None
        else:
            # Free node logic
            return Signal(value=0.5)
    except Exception as e:
        print(f"   ❌ [x402 Error] {str(e)}")
        return None

    # No longer used: _send_payment, legacy logic removed