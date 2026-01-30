
import time
from agent.wallet_manager import WalletManager

class TradingEngine:
    def __init__(self, wallet=None):
        self.wallet = wallet or WalletManager()

    def trade(self, *args, **kwargs):
        # Implement trading logic here
        pass

    def execute_swap(self, token_in, token_out, amount_in):
        try:
            print(f"[TradingEngine] Swapping {amount_in} {token_in} to {token_out}...")
            # CRITICAL FIX: Use 'latest' and wait for pending txs to confirm
            nonce = self.wallet.w3.eth.get_transaction_count(self.wallet.address)
            from agent.tools import VVS_ROUTER_ADDR, ROUTER_ABI, resolve_address
            from web3 import Web3
            w3 = self.wallet.w3
            router_addr = Web3.to_checksum_address(VVS_ROUTER_ADDR)
            token_in_addr = resolve_address(token_in)
            token_out_addr = resolve_address(token_out)
            path = [token_in_addr, token_out_addr]
            deadline = int(time.time()) + 600
            if token_in.lower() in ['cro', 'tcro', 'native']:
                amount_in_wei = w3.to_wei(amount_in, 'ether')
            else:
                # For ERC20 tokens, get decimals and convert to int
                erc20 = w3.eth.contract(address=token_in_addr, abi=[{"constant":True,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"}])
                decimals = erc20.functions.decimals().call()
                amount_in_wei = int(float(amount_in) * (10 ** decimals))
            router = w3.eth.contract(address=router_addr, abi=ROUTER_ABI)
            # Example: swapExactTokensForTokens (update as needed for your swap type)
            swap_tx = router.functions.swapExactTokensForTokens(
                amount_in_wei, 1, path, self.wallet.address, deadline
            ).build_transaction({
                'from': self.wallet.address,
                'nonce': nonce,
                'gas': 300000,
                'gasPrice': int(w3.eth.gas_price * 1.2),
                'chainId': w3.eth.chain_id
            })
            tx = swap_tx
            signed_tx = self.wallet.w3.eth.account.sign_transaction(tx, private_key=self.wallet.private_key)
            tx_hash = self.wallet.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            print(f"   ⏳ Waiting for Swap confirmation (Hash: {tx_hash.hex()})...")
            self.wallet.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            print(f"   ✅ Swap Confirmed!")
            return tx_hash.hex()
        except Exception as e:
            if "invalid sequence" in str(e) or "nonce" in str(e):
                print("   ⚠️ Nonce mismatch detected. Retrying with incremented nonce...")
                # Optional: recursive retry logic here
            print(f"❌ [TradingEngine] Production Swap Failed: {e}")
            return None
