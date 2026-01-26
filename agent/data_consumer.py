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
    load_dotenv(Path(__file__).parent.parent / '.env')
    private_key = os.getenv("WALLET_PRIVATE_KEY")
    rpc_url = os.getenv("CRONOS_RPC_URL", os.getenv("RPC_URL"))
    wallet = WalletManager(private_key, rpc_url)
    try:
        if not endpoint_url:
            return None

        # 1. First attempt (Expect 402)
        res = requests.get(endpoint_url, timeout=5)

        if res.status_code == 402:
            target_wallet = res.headers.get("X-Payment-Wallet")
            requested_price = float(res.headers.get("X-Payment-Price", price))
            print(f"   💰 [x402] Paying {requested_price} USDC for {category} data...")
            tx_hash = wallet.transfer_usdc(target_wallet, requested_price)
            if tx_hash:
                # 2. Second attempt (With both Proof headers for compatibility)
                res = requests.get(
                    endpoint_url,
                    headers={
                        "X-Payment-Proof": tx_hash,
                        "x402-payment-proof": tx_hash
                    },
                    timeout=5
                )
            else:
                print(f"   ❌ [x402] Payment failed for {node_id}. Access denied.")
                return None

        if res.status_code == 200:
            data = res.json()
            print(f"      ✅ Received from {category}: {data.get('value')} ({data.get('logic')})")
            return data
        else:
            print(f"   ❌ [Provider Error] Status {res.status_code}: {res.text}")
            return None
    except Exception as e:
        print(f"   ❌ [Provider Error] {e}")
        return None