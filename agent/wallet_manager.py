"""
Wallet Manager for the Alpha-Consumer Agent
Handles wallet operations, balance checks, and transaction management
"""

import os
import json
from web3 import Web3
from eth_account import Account

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
    
    def __init__(self, private_key: str, rpc_url: str):
        """
        Initialize wallet manager
        
        Args:
            private_key: Wallet private key (with or without 0x prefix)
            rpc_url: RPC endpoint for the blockchain
        """
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        if not self.w3.is_connected():
            raise ConnectionError(f"Failed to connect to RPC at {rpc_url}")
        
        # Ensure private key has 0x prefix
        if not private_key.startswith("0x"):
            private_key = "0x" + private_key
        
        self.account = Account.from_key(private_key)
        self.address = self.account.address
        
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
    
    def get_gas_price(self):
        """
        Get current gas price
        
        Returns:
            int: Gas price in wei
        """
        return self.w3.eth.gas_price
    
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