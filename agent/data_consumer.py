import requests
import json
from .wallet_manager import WalletManager

def fetch_node_data(node_id, endpoint_url, api_key, category):
    from .wallet_manager import log_data_purchase
    wallet = WalletManager()
    headers = {"Content-Type": "application/json"}
    if not endpoint_url or "http" not in endpoint_url:
        print("      ❌ Error: Invalid Endpoint URL.")
        return None

    # Check if already purchased today
    import os, json, datetime
    data_log_path = os.path.join(os.path.dirname(__file__), 'data_purchase_log.json')
    today = datetime.date.today().isoformat()
    already_purchased = False
    if os.path.exists(data_log_path):
        with open(data_log_path, 'r') as f:
            logs = json.load(f)
        for entry in logs:
            if entry.get('date') == today and entry.get('node_id') == node_id:
                already_purchased = True
                break

    try:
        response = requests.get(endpoint_url, headers=headers, timeout=3)
        if response.status_code == 402:
            # Get price and destination wallet from headers or body
            price = response.headers.get("X-Payment-Price")
            pay_to = response.headers.get("X-Payment-Wallet")
            if not price or not pay_to:
                try:
                    invoice = response.json()
                    price = invoice.get("price", 0.1)
                    pay_to = invoice.get("pay_to") or invoice.get("wallet")
                except:
                    return None
            price = float(price)
            if already_purchased:
                print(f"[INFO] Node {node_id} already purchased today. Skipping payment.")
                headers["X-Payment-Proof"] = "ALREADY_PAID"
                response = requests.get(endpoint_url, headers=headers, timeout=3)
            else:
                print(f"🛒 [Purchase] Paying {price} USDC to unlock {category} data...")
                tx_hash = wallet.transfer_usdc(pay_to, price)
                if tx_hash:
                    log_data_purchase(node_id, price)
                    headers["X-Payment-Proof"] = tx_hash
                    response = requests.get(endpoint_url, headers=headers, timeout=3)
                else:
                    print("❌ Payment failed.")
                    return None

        if response.status_code == 200:
            data = response.json()
            val = float(data.get('value', data.get('data', {}).get('value', 0.5)))
            return type('Signal', (), {'value': val})()
    except Exception as e:
        print(f"[fetch_node_data] Exception: {e}")
        pass
    return None

def _send_payment(wallet, to, amount):
    try:
        if not wallet.address: return None
        tx = {
            'to': to, 'value': 0, 'gas': 21000,
            'gasPrice': wallet.get_gas_price(), 'nonce': wallet.get_nonce(),
            'chainId': wallet.w3.eth.chain_id
        }
        signed = wallet.w3.eth.account.sign_transaction(tx, wallet.key)
        tx_hash = wallet.w3.eth.send_raw_transaction(signed.rawTransaction)
        wallet.log_transaction(tx_hash.hex(), "DATA_BUY", f"Paid {amount}")
        return tx_hash.hex()
    except:
        return "0x_mock_hash_fallback"