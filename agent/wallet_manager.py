# --- Autonomous Loop Spend Controls (Production Logic) ---

from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path(__file__).parent.parent / '.env')

import os
import datetime
import subprocess
import sys
import threading
data_log_path = os.path.join(os.path.dirname(__file__), 'data_purchase_log.json')
DAILY_LIMIT_USDC = 50.0
_spend_lock = threading.Lock()
# Persistent blacklist
def _load_blacklist():
    try:
        result = subprocess.run([sys.executable, '-c',
            'import json; print(json.dumps(list(__import__("blacklist_persistence").loadBlacklist())))'],
            capture_output=True, text=True, cwd=os.path.dirname(__file__))
        return set(json.loads(result.stdout.strip()))
    except Exception:
        return set()

def _save_blacklist(blacklist):
    try:
        subprocess.run([sys.executable, '-c',
            f'import json; __import__("blacklist_persistence").saveBlacklist(set(json.loads("{json.dumps(list(blacklist))}")))'],
            cwd=os.path.dirname(__file__))
    except Exception:
        pass

BLACKLISTED_NODES = _load_blacklist()

def get_daily_spend() -> float:
    today = datetime.date.today().isoformat()
    if not os.path.exists(data_log_path):
        return 0.0
    with open(data_log_path, 'r') as f:
        logs = json.load(f)
    return sum(entry['amount'] for entry in logs if entry['date'] == today)

def log_data_purchase(node_id, amount):
    today = datetime.date.today().isoformat()
    logs = []
    if os.path.exists(data_log_path):
        with open(data_log_path, 'r') as f:
            logs = json.load(f)
    logs.append({'date': today, 'node_id': node_id, 'amount': amount})
    with open(data_log_path, 'w') as f:
        json.dump(logs, f)

def can_spend(amount: float) -> bool:
    """Atomically check and persist spend to avoid race conditions."""
    with _spend_lock:
        spent = get_daily_spend()
        if (spent + amount) > DAILY_LIMIT_USDC:
            return False
        # Log immediately to persist
        log_data_purchase("_atomic_check", amount)
        return True

def validate_data(node_id, data):
    # Blacklist if data is null or static for 3+ fetches (simple version)
    if data is None or (isinstance(data, dict) and all(v in [None, 0, '', '0'] for v in data.values())):
        BLACKLISTED_NODES.add(node_id)
        _save_blacklist(BLACKLISTED_NODES)
        print(f"[WalletManager] Blacklisted node {node_id} for invalid data.")
        return False
    return True

def is_blacklisted(node_id):
    return node_id in BLACKLISTED_NODES
"""
Wallet Manager for the Alpha-Consumer Agent
Handles wallet operations, balance checks, and transaction management
"""

import os
import json
from web3 import Web3
from eth_account import Account



from pathlib import Path

class WalletManager:
    """Manages blockchain wallet operations for the agent"""

    # Standard ERC20 ABI for balance checking
    ERC20_ABI = [
        {
            "constant": True,
            "inputs": [{"name": "_owner", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "balance", "type": "uint256"}],
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [],
            "name": "decimals",
            "outputs": [{"name": "", "type": "uint8"}],
            "type": "function"
        }
    ]

    TX_LOG_FILE = Path(__file__).parent / "transaction_log.json"

    def log_transaction(self, tx_hash, tx_type, details="", error=None):
        """
        Logs every single transaction hash to a JSON file with explorer URL and timestamp.
        """
        entry = {
            "timestamp": time.time(),
            "date": time.strftime('%Y-%m-%d %H:%M:%S'),
            "tx_hash": tx_hash,
            "type": tx_type,
            "details": details
        }
        try:
            with self._lock:
                logs = []
                if self.TX_LOG_FILE.exists():
                    try:
                        with open(self.TX_LOG_FILE, 'r') as f:
                            logs = json.load(f)
                    except:
                        pass
                logs.append(entry)
                with open(self.TX_LOG_FILE, 'w') as f:
                    json.dump(logs, f, indent=2)
            print(f"📝 [LOG] {tx_type} TX Saved: {tx_hash}")
        except Exception as e:
            print(f"⚠️ Log Error: {e}")
        try:
            with _spend_lock:
                logs = []
                if self.TX_LOG_FILE.exists():
                    try:
                        with open(self.TX_LOG_FILE, 'r') as f:
                            logs = json.load(f)
                    except Exception:
                        pass
                logs.append(entry)
                with open(self.TX_LOG_FILE, 'w') as f:
                    json.dump(logs, f, indent=2)
            print(f"📝 [TX LOGGED] {tx_type}: {tx_hash}")
        except Exception as e:
            print(f"⚠️ Failed to log tx: {e}")

    def log_transaction(self, tx_hash, tx_type, details=None, error=None):
        """
        Log every transaction (success or failure) to transactions.log
        """
        log_path = os.path.join(os.path.dirname(__file__), 'transactions.log')
        entry = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "tx_hash": tx_hash,
            "type": tx_type,
            "details": details,
            "error": error
        }
        try:
            if os.path.exists(log_path):
                with open(log_path, 'r') as f:
                    logs = json.load(f)
            else:
                logs = []
            logs.append(entry)
            with open(log_path, 'w') as f:
                json.dump(logs, f, indent=2)
        except Exception as e:
            print(f"[WalletManager] Logging failed: {e}")

    def __init__(self, private_key: str, rpc_url: str):
        self.rpc_url = rpc_url
        """
        Initialize wallet manager
        Args:
            private_key: Wallet private key (with or without 0x prefix)
            rpc_url: RPC endpoint for the blockchain
        """
        import traceback
        try:
            self.w3 = Web3(Web3.HTTPProvider(rpc_url))
            if not self.w3.is_connected():
                print(f"[WalletManager] WARNING: Could not connect to RPC at {rpc_url}. Blockchain operations will be disabled.")
                self.w3 = None
        except Exception as e:
            print(f"[WalletManager] ❌ Exception while creating Web3 provider for RPC '{rpc_url}': {type(e).__name__}: {e}")
            traceback.print_exc()
            self.w3 = None

        # Ensure private key has 0x prefix
        if not private_key.startswith("0x"):
            private_key = "0x" + private_key

        try:
            self.account = Account.from_key(private_key)
            self.address = self.account.address
            self.key = private_key  # Ensure key is available for TradingEngine
        except Exception as e:
            print(f"[WalletManager] ❌ Error initializing account from private key: {type(e).__name__}: {e}")
            traceback.print_exc()
            self.account = None
            self.address = None

        # Load contract addresses from environment
        self.usdc_address = os.getenv("USDC_CONTRACT", "")

    def get_tcro_balance(self):
        """
        Get native TCRO balance
        Returns:
            float: Balance in TCRO
        """
        try:
            balance_wei = self.w3.eth.get_balance(self.address)
            balance_tcro = self.w3.from_wei(balance_wei, 'ether')
            return float(balance_tcro)
        except Exception as e:
            print(f"Error getting TCRO balance: {e}")
            return 0.0

    def get_usdc_balance(self):
        """
        Get USDC token balance
        Returns:
            float: Balance in USDC
        """
        if not self.usdc_address:
            print("⚠️  USDC contract address not configured")
            return 0.0

        try:
            # Create contract instance
            contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(self.usdc_address),
                abi=self.ERC20_ABI
            )

            # Get balance
            balance_raw = contract.functions.balanceOf(self.address).call()

            # Get decimals
            try:
                decimals = contract.functions.decimals().call()
            except:
                decimals = 6  # Default for USDC

            balance = balance_raw / (10 ** decimals)
            return float(balance)

        except Exception as e:
            print(f"Error getting USDC balance: {e}")
            return 0.0

    def get_token_balance(self, token_address: str):
        """
        Get balance of any ERC20 token
        Args:
            token_address: Contract address of the token
        Returns:
            dict: Balance information with raw and formatted amounts
        """
        try:
            contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(token_address),
                abi=self.ERC20_ABI
            )

            balance_raw = contract.functions.balanceOf(self.address).call()

            try:
                decimals = contract.functions.decimals().call()
            except:
                decimals = 18  # Default for most tokens

            balance_formatted = balance_raw / (10 ** decimals)

            return {
                "address": token_address,
                "balance_raw": balance_raw,
                "balance_formatted": balance_formatted,
                "decimals": decimals
            }

        except Exception as e:
            return {
                "address": token_address,
                "error": str(e)
            }

    def sign_message(self, message: str):
        """
        Sign a message with the wallet's private key
        Args:
            message: Message to sign
        Returns:
            str: Hex-encoded signature
        """
        signed = self.account.sign_message(message)
        return signed.signature.hex()

    def get_nonce(self):
        """
        Get the current transaction nonce for the wallet
        Returns:
            int: Transaction nonce
        """
        return self.w3.eth.get_transaction_count(self.address)

    def get_gas_price(self, use_external: bool = False):
        """
        Get current gas price (wei). Optionally fetch from external API for more accuracy.
        Args:
            use_external: If True, fetch from an external gas oracle API (e.g., Cronoscan, Etherchain)
        Returns:
            int: Gas price in wei
        """
        if use_external:
            try:
                import requests
                resp = requests.get("https://cronos.org/explorer/api/v1/gastracker")
                if resp.status_code == 200:
                    data = resp.json()
                    # Example: {'result': {'SafeGasPrice': '5000', ...}}
                    price_gwei = float(data['result']['SafeGasPrice'])
                    return int(price_gwei * 1e9)
            except Exception as e:
                print(f"[WalletManager] External gas oracle failed: {e}")
        return self.w3.eth.gas_price

    def gas_cost_exceeds_profit(self, gas_limit: int, gas_price: int, potential_profit: float, cro_price: float = 0.1) -> bool:
        """
        Check if gas cost (in CRO, converted to USD) exceeds potential profit.
        Args:
            gas_limit: Estimated gas units
            gas_price: Gas price in wei
            potential_profit: Expected profit in USD
            cro_price: Price of CRO in USD (default 0.1, update as needed)
        Returns:
            bool: True if gas cost > potential profit
        """
        gas_cost_cro = gas_limit * gas_price / 1e18
        gas_cost_usd = gas_cost_cro * cro_price
        return gas_cost_usd > potential_profit

    def estimate_gas(self, transaction):
        """
        Estimate gas for a transaction
        Args:
            transaction: Transaction dictionary
        Returns:
            int: Estimated gas
        """
        try:
            return self.w3.eth.estimate_gas(transaction)
        except Exception as e:
            print(f"Error estimating gas: {e}")
            return 100000  # Default fallback

    def format_balance_display(self):
        """
        Get formatted string of all balances for display
        Returns:
            str: Formatted balance information
        """
        tcro = self.get_tcro_balance()
        usdc = self.get_usdc_balance()

        output = f"""
╔════════════════════════════════════════╗
║         Wallet Balance                 ║
╠════════════════════════════════════════╣
║ Address: {self.address[:10]}...{self.address[-8:]} ║
║                                        ║
║ TCRO:    {tcro:>10.4f}                 ║
║ USDC:    {usdc:>10.2f}                 ║
╚════════════════════════════════════════╝
"""
        return output

    def check_sufficient_balance(self, token_address: str, required_amount: int):
        """
        Check if wallet has sufficient balance for a payment
        Args:
            token_address: Address of the token
            required_amount: Required amount in smallest units
        Returns:
            dict: Balance check result with recommendation
        """
        balance_info = self.get_token_balance(token_address)

        if "error" in balance_info:
            return {
                "sufficient": False,
                "error": balance_info["error"]
            }

        balance_raw = balance_info["balance_raw"]
        sufficient = balance_raw >= required_amount

        return {
            "sufficient": sufficient,
            "current_balance": balance_raw,
            "required_amount": required_amount,
            "shortfall": max(0, required_amount - balance_raw),
            "balance_formatted": balance_info["balance_formatted"],
            "decimals": balance_info["decimals"]
        }


def create_new_wallet():
    """
    Utility function to create a new wallet
    
    Returns:
        dict: New wallet information (address and private key)
    """
    account = Account.create()
    
    return {
        "address": account.address,
        "private_key": account.key.hex(),
        "warning": "⚠️  Store the private key securely! Never commit it to version control."
    }


if __name__ == "__main__":
    # Utility script to create a new wallet
    print("🔑 Generating new wallet for testing...\n")
    
    wallet_info = create_new_wallet()
    
    print(f"Address:     {wallet_info['address']}")
    print(f"Private Key: {wallet_info['private_key']}")
    print(f"\n{wallet_info['warning']}")
    print("\n💡 Add this private key to your .env file as WALLET_PRIVATE_KEY")
    print("💰 Fund this address with TCRO and devUSDC from the testnet faucet")