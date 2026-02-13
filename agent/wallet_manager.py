# agent/wallet_manager.py
"""
WalletManager for Etherlink with x402 payment integration.
Supports simulation mode for testing without real blockchain transactions.
"""

import os
import json
import uuid
from datetime import datetime
from web3 import Web3


def get_daily_spend(*args, **kwargs):
    """Return total USDC spent today (persisted in a file)."""
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
    max_limit = kwargs.get('max_cost', 500.0)
    # If no limit is set, always allow
    if max_limit is None:
        return True
    spent = get_daily_spend()
    return (spent + float(amount)) <= max_limit


def add_spend(amount):
    """Add amount to today's spend (persisted in a file)."""
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


class WalletManager:
    def __init__(self, private_key=None, rpc_url=None):
        self.private_key = private_key or os.getenv("WALLET_PRIVATE_KEY")
        self.rpc_url = rpc_url or os.getenv("RPC_URL", "https://node.shadownet.etherlink.com")
        self.simulation_mode = os.getenv("SIMULATION_MODE", "false").lower() == "true"
        # Map token addresses from environment
        usdc_addr = os.getenv("USDC_ADDRESS") or os.getenv("USDC_CONTRACT")
        wxtz_addr = os.getenv("WXTZ_ADDRESS")
        # Update this dictionary to match your Shadownet addresses:
        self.tokens = {
            "0x9D8166D4B4ac353B0269655E55cB137000ba8624": "WXTZ",
            "0xD2BE74974d5A50C2C131C9A0E9751c9449dc9888": "USDC"
        }
        
        if self.simulation_mode:
            print("⚠️  [WalletManager] SIMULATION_MODE enabled - using mock transactions")
            self.w3 = None
            self.account = None
            self.address = os.getenv("WALLET_ADDRESS", "0x" + "0" * 40)
        else:
            self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
            try:
                self.account = self.w3.eth.account.from_key(self.private_key)
                self.address = self.account.address
                print(f"✅ [WalletManager] Connected to {self.rpc_url}")
                print(f"   Wallet: {self.address}")
            except Exception as e:
                print(f"❌ [WalletManager] Failed to initialize: {e}")
                raise

    def get_balance(self, token_address=None):
        # If no token_address, default to USDC_CONTRACT from env
        if not token_address:
            token_address = os.getenv("USDC_CONTRACT")
        # If still None, fallback to WXTZ_ADDRESS
        if not token_address:
            token_address = os.getenv("WXTZ_ADDRESS")
        if not token_address:
            print(f"⚠️ [WalletManager] Unknown token: None")
            return 0.0
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
        """Transfer USDC to destination address. In simulation mode, returns mock tx hash."""
        # Support simulation mode for testing
        if self.simulation_mode:
            mock_tx_hash = "0x" + uuid.uuid4().hex[:64]
            print(f"   💳 [SIMULATION] Mock USDC transfer: {amount} USDC to {destination}")
            print(f"   📋 [Mock TX] {mock_tx_hash}")
            add_spend(amount)
            return mock_tx_hash
        
        # Get USDC address from env or contract/.env
        usdc_address = os.getenv("USDC_CONTRACT")
        if not usdc_address:
            env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "contract", ".env")
            try:
                with open(env_path) as f:
                    for line in f:
                        if line.startswith("USDC_ADDRESS="):
                            usdc_address = line.strip().split("=", 1)[1]
                            break
            except Exception as e:
                print(f"[WalletManager] Error reading .env for USDC_ADDRESS: {e}")
                usdc_address = None
        
        if not usdc_address:
            usdc_address = "0xD2BE74974d5A50C2C131C9A0E9751c9449dc9888"  # Fallback to latest deployed
        
        if not destination:
            destination = os.getenv("PROVIDER_ADDRESS", "0xFe5e03799Fe833D93e950d22406F9aD901Ff3Bb9")
        
        try:
            erc20 = self.w3.eth.contract(address=usdc_address, abi=self._erc20_abi())
            decimals = erc20.functions.decimals().call()
            amt_wei = int(float(amount) * (10 ** decimals))
            nonce = self.w3.eth.get_transaction_count(self.address)
            
            # Build transaction
            tx_base = erc20.functions.transfer(destination, amt_wei).build_transaction({
                'from': self.address,
                'nonce': nonce,
                'chainId': self.w3.eth.chain_id,
                'gasPrice': int(self.w3.eth.gas_price * 1.2)
            })
            
            # Estimate gas with fallback
            try:
                estimated_gas = erc20.functions.transfer(destination, amt_wei).estimate_gas({'from': self.address})
                gas_limit = int(estimated_gas * 1.2)
            except Exception as eg:
                print(f"[WalletManager] Gas estimation failed, using default 1000000. Error: {eg}")
                gas_limit = 1000000
            
            tx_base['gas'] = gas_limit
            
            # Sign and send
            signed = self.w3.eth.account.sign_transaction(tx_base, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
            print(f"   💸 [WalletManager] Sent {amount} USDC to {destination}. Tx: {tx_hash.hex()}")
            
            # Wait for confirmation
            try:
                self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=10)
                print(f"   ✅ [WalletManager] Transaction confirmed")
            except Exception as e:
                print(f"   ⚠️  [WalletManager] Transaction may still be pending: {e}")
            
            add_spend(amount)
            return tx_hash.hex()
            
        except Exception as e:
            print(f"   ❌ [WalletManager] Transfer failed: {e}")
            import traceback
            traceback.print_exc()
            return None

    def get_balance(self, token='USDC'):
        """Get current token balance for the wallet."""
        # In simulation mode, return mock balances
        if self.simulation_mode:
            if token == 'USDC':
                return 1000.0  # Mock 1000 USDC
            elif token in ['CRO', 'TCRO', 'native']:
                return 100.0   # Mock 100 CRO
            else:
                return 0.0
        
        try:
            if token == 'USDC':
                # Get USDC balance
                usdc_address = os.getenv("USDC_CONTRACT")
                if not usdc_address:
                    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "contract", ".env")
                    try:
                        with open(env_path) as f:
                            for line in f:
                                if line.startswith("USDC_ADDRESS="):
                                    usdc_address = line.strip().split("=", 1)[1]
                                    break
                    except:
                        pass
                if not usdc_address:
                    usdc_address = "0xD2BE74974d5A50C2C131C9A0E9751c9449dc9888"
                
                erc20 = self.w3.eth.contract(address=usdc_address, abi=self._erc20_abi())
                balance_wei = erc20.functions.balanceOf(self.address).call()
                decimals = erc20.functions.decimals().call()
                balance = balance_wei / (10 ** decimals)
                return float(balance)
            elif token == 'WXTZ':
                wxtz_address = os.getenv("WXTZ_ADDRESS")
                if not wxtz_address:
                    return 0.0
                erc20 = self.w3.eth.contract(address=wxtz_address, abi=self._erc20_abi())
                balance_wei = erc20.functions.balanceOf(self.address).call()
                decimals = erc20.functions.decimals().call()
                balance = balance_wei / (10 ** decimals)
                return float(balance)
            elif token in ['CRO', 'TCRO', 'native']:
                # Get native token balance
                balance_wei = self.w3.eth.get_balance(self.address)
                balance = self.w3.from_wei(balance_wei, 'ether')
                return float(balance)
            else:
                print(f"   ⚠️ [WalletManager] Unknown token: {token}")
                return 0.0
        except Exception as e:
            print(f"   ❌ [WalletManager] Error getting {token} balance: {e}")
            return 0.0
    
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

    async def get_token_balance(self, token_address=None):
        # Async wrapper for compatibility with PredictiveAgent
        return self.get_balance(token_address)
