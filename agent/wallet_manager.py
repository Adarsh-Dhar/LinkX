# agent/wallet_manager.py
"""
Stub for WalletManager to resolve import errors.
Expand with real logic as needed.
"""

def get_daily_spend(*args, **kwargs):
    """Return total USDC spent today (persisted in a file)."""
    import json, os
    from datetime import datetime
    spend_file = os.path.join(os.path.dirname(__file__), 'daily_spend.json')
    today = datetime.now().strftime('%Y-%m-%d')
    if not os.path.exists(spend_file):
        return 0.0
    try:
        with open(spend_file, 'r') as f:
            data = json.load(f)
        return float(data.get(today, 0.0))
    except Exception:
        return 0.0

def can_spend(amount, *args, **kwargs):
    """Return True if spending 'amount' will not exceed today's limit."""
    import os
    max_limit = kwargs.get('max_cost', 500.0)
    # If no limit is set, always allow
    if max_limit is None:
        return True
    spent = get_daily_spend()
    return (spent + float(amount)) <= max_limit

def add_spend(amount):
    """Add amount to today's spend (persisted in a file)."""
    import json, os
    from datetime import datetime
    spend_file = os.path.join(os.path.dirname(__file__), 'daily_spend.json')
    today = datetime.now().strftime('%Y-%m-%d')
    data = {}
    if os.path.exists(spend_file):
        try:
            with open(spend_file, 'r') as f:
                data = json.load(f)
        except Exception:
            data = {}
    data[today] = float(data.get(today, 0.0)) + float(amount)
    with open(spend_file, 'w') as f:
        json.dump(data, f)


from web3 import Web3
import os

class WalletManager:
    def __init__(self, private_key=None, rpc_url=None):
        self.private_key = private_key or os.getenv("WALLET_PRIVATE_KEY")
        self.rpc_url = rpc_url or os.getenv("RPC_URL", "https://node.shadownet.etherlink.com")
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        self.account = self.w3.eth.account.from_key(self.private_key)
        self.address = self.account.address

    def get_balance(self, token_address=None):
        if not token_address:
            return self.w3.eth.get_balance(self.address)
        # For ERC20, call balanceOf
        erc20 = self.w3.eth.contract(address=token_address, abi=self._erc20_abi())
        return erc20.functions.balanceOf(self.address).call()

    def send_transaction(self, destination=None, amount=None, token_in=None, token_out=None):
        # For swaps, this should call the router contract. For USDC transfer, call transfer_usdc.
        if token_in and token_out:
            return self.execute_swap(token_in, token_out, amount)
        if destination and amount:
            return self.transfer_usdc(destination, amount)
        return None

    def transfer_usdc(self, destination, amount):
        # Etherlink USDC address and dynamic chainId
        usdc_address = os.getenv("USDC_CONTRACT", "0xff16f6b57736e4f358603681677c38666579998b")
        erc20 = self.w3.eth.contract(address=usdc_address, abi=self._erc20_abi())
        decimals = erc20.functions.decimals().call()
        amt_wei = int(float(amount) * (10 ** decimals))
        nonce = self.w3.eth.get_transaction_count(self.address)
        tx = erc20.functions.transfer(destination, amt_wei).build_transaction({
            'from': self.address,
            'nonce': nonce,
            'gas': 100000,
            'gasPrice': int(self.w3.eth.gas_price * 1.2),
            'chainId': self.w3.eth.chain_id
        })
        signed = self.w3.eth.account.sign_transaction(tx, self.private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed.rawTransaction)
        print(f"   💸 [WalletManager] Sent {amount} USDC to {destination}. Tx: {tx_hash.hex()}")
        self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=10)
        return tx_hash.hex()

    def execute_swap(self, token_in, token_out, amount):
        # Implement router swap logic here (simplified, replace with your router contract logic)
        # This is a placeholder for a real DEX swap
        print(f"   ⚡ [WalletManager] Swap {amount} {token_in} to {token_out} (stub, implement real logic)")
        return "0xNOT_IMPLEMENTED"

    def _erc20_abi(self):
        # Minimal ERC20 ABI for balanceOf, transfer, decimals
        return [
            {"constant":True,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"},
            {"constant":True,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"},
            {"constant":False,"inputs":[{"name":"_to","type":"address"},{"name":"_value","type":"uint256"}],"name":"transfer","outputs":[{"name":"","type":"bool"}],"type":"function"}
        ]
