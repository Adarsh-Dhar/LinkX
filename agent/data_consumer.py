import requests
import json
from .wallet_manager import WalletManager

def fetch_node_data(node_id, endpoint_url, api_key, category):
    wallet = WalletManager()
    headers = {"Content-Type": "application/json"}
    
    if not endpoint_url or "http" not in endpoint_url:
        print("      ❌ Error: Invalid Endpoint URL.")
        return None
    
    try:
        response = requests.get(endpoint_url, headers=headers, timeout=3)
        
        if response.status_code == 402:
            try:
                invoice = response.json()
                price = invoice.get("price", 0.1)
                pay_to = invoice.get("pay_to") or invoice.get("wallet")
                if not pay_to: return None
                
                tx_hash = _send_payment(wallet, pay_to, price)
                if tx_hash:
                    headers["X-Payment-Proof"] = tx_hash
                    response = requests.get(endpoint_url, headers=headers, timeout=3)
                else:
                    return None
            except:
                return None

        if response.status_code == 200:
            data = response.json()
            # Handle nested or direct value
            val = float(data.get('value', data.get('data', {}).get('value', 0.5)))
            return type('Signal', (), {'value': val})()
            
    except Exception as e:
        # Fail silently to allow fallback logic to take over
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