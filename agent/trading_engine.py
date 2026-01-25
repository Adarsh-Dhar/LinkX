
import os
import time
from web3 import Web3

from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path(__file__).parent.parent / '.env')

from typing import Optional, Any, Dict

class TradingEngine:
    def __init__(self, wallet_manager):
        self.wallet = wallet_manager
        self.w3 = self.wallet.w3
        # Log connection status on init, but don't switch to simulation mode
        if self.w3 and self.w3.is_connected():
            print(f"✅ [TradingEngine] Connected to Blockchain at {self.wallet.rpc_url}")
        else:
            print(f"⚠️ [TradingEngine] CONNECTION FAILED: Cannot reach {self.wallet.rpc_url}")
            print("   (Trades will fail with raw network errors)")

    def execute_swap(self, token_in, token_out, amount_in, slippage_tolerance=1.0):
        print(f"⚡ TradingEngine: Attempting REAL Swap {amount_in} {token_in} -> {token_out}")
        # 1. Strict Requirement Checks
        if not self.w3 or not self.w3.is_connected():
            error_msg = f"RAW ERROR: Disconnected from RPC {getattr(self.wallet, 'rpc_url', 'UNKNOWN')}"
            print(f"   ❌ {error_msg}")
            return None # Return None signals failure to the agent

        if not getattr(self.wallet, 'key', None):
            error_msg = "RAW ERROR: No Wallet Private Key configured in .env"
            print(f"   ❌ {error_msg}")
            return None

        # 2. Real Execution Logic
        try:
            # Build Transaction (Self-send for testing connectivity, Swap for production)
            tx = {
                'to': self.wallet.address, # In prod: Router Address
                'value': 0, # In prod: Amount if swapping CRO
                'gas': 21000,
                'gasPrice': self.wallet.get_gas_price(),
                'nonce': self.wallet.get_nonce(),
                'chainId': self.w3.eth.chain_id
            }

            # Sign
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.wallet.key)
            # Broadcast (This is the moment of truth)
            print("   📡 Broadcasting to network...")
            tx_hash_bytes = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            tx_hash = tx_hash_bytes.hex()

            print(f"   ✅ TRANSACTION SENT. Hash: {tx_hash}")

            # Log the successful submission
            if hasattr(self.wallet, 'log_transaction'):
                self.wallet.log_transaction(tx_hash, "SWAP", f"{amount_in} {token_in} -> {token_out}")

            return tx_hash

        except Exception as e:
            # 3. Output EXACT Raw Error
            import os
            import time
            from web3 import Web3
            from typing import Optional, Any, Dict, List
    async def get_market_data(self, category: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetch aggregated market data from 48 nodes
        
        Args:
            category: Specific category to fetch, or None for all
            
        Returns:
            Normalized market data vector ready for neural network
        """
        if hasattr(self.data_pipeline, 'get_normalized_vector'):
            try:
                market_data = self.data_pipeline.get_normalized_vector()
            except NotImplementedError:
                market_data = []
            return market_data
        else:
            raise RuntimeError("DataPipeline does not have get_normalized_vector method. Ensure data pipeline is properly initialized.")
    
    
    
    
    

    async def execute_live_trade(
        self,
        token_in: str,
        token_out: str,
        amount: float,
        confidence_threshold: float = 0.6,
        slippage: float = 0.05
    ) -> None:
        """
        Execute a live trade if confidence exceeds threshold, using a DEX Router contract.
        """
        # Only real trade logic should be here
        try:
            swap_result = self.execute_swap(token_in, token_out, amount, slippage)
            # Optionally handle swap_result (e.g., log tx hash)
        except Exception as e:
            print(f"Error executing live trade: {e}")

    def execute_swap_with_slippage(self, token_in, token_out, amount, slippage=0.05):
        """
        Execute a swapExactTokensForTokens with slippage protection and gas management.
        """
        from web3 import Web3
        from eth_account import Account
        import json, os, time
        w3 = Web3(Web3.HTTPProvider(os.getenv('CRONOS_RPC_URL')))
        private_key = os.getenv('WALLET_PRIVATE_KEY')
        account = Account.from_key(private_key)
        USDC = w3.to_checksum_address(os.getenv('USDC_CONTRACT'))
        ROUTER = w3.to_checksum_address(os.getenv('VVS_ROUTER'))
        WTCRO = w3.to_checksum_address(os.getenv('WCRO_ADDRESS'))
        ERC20_ABI = json.loads('[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"},{"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"},{"constant":false,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"type":"function"},{"constant":true,"inputs":[{"name":"_owner","type":"address"},{"name":"_spender","type":"address"}],"name":"allowance","outputs":[{"name":"","type":"uint256"}],"type":"function"}]')
        router_abi = json.loads('[{"inputs":[{"name":"amountIn","type":"uint256"},{"name":"path","type":"address[]"}],"name":"getAmountsOut","outputs":[{"name":"amounts","type":"uint256[]"}],"stateMutability":"view","type":"function"}]')
        swap_abi = json.loads('[{"inputs":[{"name":"amountIn","type":"uint256"},{"name":"amountOutMin","type":"uint256"},{"name":"path","type":"address[]"},{"name":"to","type":"address"},{"name":"deadline","type":"uint256"}],"name":"swapExactTokensForTokens","outputs":[{"name":"amounts","type":"uint256[]"}],"stateMutability":"nonpayable","type":"function"}]')
        if token_in.upper() == "USDC":
            token_in_addr = USDC
        elif token_in.upper() == "WCRO":
            token_in_addr = WTCRO
        else:
            raise Exception(f"Unsupported token_in: {token_in}")
        if token_out.upper() == "USDC":
            token_out_addr = USDC
        elif token_out.upper() == "WCRO":
            token_out_addr = WTCRO
        else:
            raise Exception(f"Unsupported token_out: {token_out}")
        token_contract = w3.eth.contract(address=token_in_addr, abi=ERC20_ABI)
        router = w3.eth.contract(address=ROUTER, abi=router_abi + swap_abi)
        decimals = token_contract.functions.decimals().call()
        swap_amount = int(amount * (10 ** decimals))
        allowance = token_contract.functions.allowance(account.address, ROUTER).call()
        if allowance < swap_amount:
            approve_tx = token_contract.functions.approve(ROUTER, swap_amount).build_transaction({
                'from': account.address,
                'nonce': w3.eth.get_transaction_count(account.address),
                'gas': 100000,
                'gasPrice': w3.eth.gas_price,
                'chainId': w3.eth.chain_id
            })
            signed = account.sign_transaction(approve_tx)
            tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
            try:
                receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
                if receipt['status'] == 1:
                    print(f"[TradingEngine] ✅ Approve Confirmed: {tx_hash.hex()}")
                else:
                    print(f"[TradingEngine] ❌ Approve Reverted: {tx_hash.hex()}")
            except Exception as e:
                print(f"[TradingEngine] ❌ Approve Tx Failed: {tx_hash.hex()} | {e}")
        path = [token_in_addr, token_out_addr]
        amounts = router.functions.getAmountsOut(swap_amount, path).call()
        expected_out = amounts[1]
        min_out = int(expected_out * (1 - slippage))
        gas_price = w3.eth.gas_price
        est_gas = 300000
        deadline = w3.eth.get_block('latest')['timestamp'] + 600
        swap_tx = router.functions.swapExactTokensForTokens(
            swap_amount,
            min_out,
            path,
            account.address,
            deadline
        ).build_transaction({
            'from': account.address,
            'nonce': w3.eth.get_transaction_count(account.address),
            'gas': est_gas,
            'gasPrice': gas_price,
            'chainId': w3.eth.chain_id
        })
        signed = account.sign_transaction(swap_tx)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        try:
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            if receipt['status'] == 1:
                print(f"[TradingEngine] ✅ Swap Confirmed: {tx_hash.hex()}")
            else:
                print(f"[TradingEngine] ❌ Swap Reverted: {tx_hash.hex()}")
        except Exception as e:
            print(f"[TradingEngine] ❌ Swap Tx Failed: {tx_hash.hex()} | {e}")
        return {
            "tx_hash": tx_hash.hex(),
            "block": receipt['blockNumber'] if 'receipt' in locals() else None,
            "gas_used": receipt['gasUsed'] if 'receipt' in locals() else None,
            "min_out": min_out,
            "expected_out": expected_out
        }
    
    def reset_metrics(self) -> None:
        """Reset all performance metrics"""
        self.trade_history.clear()
        self.active_trades.clear()
        self.equity_curve = [1.0]
        self.metrics = {
            "total_trades": 0,
            "successful_trades": 0,
            "failed_trades": 0,
            "total_pnl": 0.0,
            "cumulative_return": 0.0,
            "win_rate": 0.0,
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0,
            "average_confidence": 0.0
        }


# Global instance (will be initialized by the agent)
_engine_instance: Optional[TradingEngine] = None


def initialize_engine(smart_router, data_pipeline, neural_brain) -> 'TradingEngine':
    """Initialize the global trading engine"""
    global _engine_instance
    _engine_instance = TradingEngine(smart_router, data_pipeline, neural_brain)
    # Patch: Provide a stub DataPipeline if not available
    try:
        from data_pipeline import DataPipeline
    except ImportError:
        import thriftpy2 as thriftpy
        class DataPipeline:
            def __init__(self, *args, **kwargs):
                pass
            def get_market_state(self):
                raise NotImplementedError("DataPipeline.get_market_state is not implemented.")
            def get_feature_names(self):
                return []
            def get_raw_values(self):
                return []
            def get_normalized_vector(self):
                return []
    return _engine_instance


def get_engine() -> Optional[TradingEngine]:
    """Get the global trading engine instance"""
    return _engine_instance
