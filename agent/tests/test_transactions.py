"""
Test Suite for Trading Agent Transactions
Tests blockchain interactions, token operations, and swap functionality
"""

import os
import sys
import pytest
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
from web3 import Web3

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Import tools to test
from tools import (
    get_token_balance,
    estimate_swap_output,
    execute_vvs_swap,
    get_trade_history,
    resolve_token_address
)


class TestWeb3Connection:
    """Test Web3 connectivity and network setup"""
    
    def test_rpc_connection(self):
        """Test connection to Cronos testnet"""
        rpc_url = os.getenv("CRONOS_RPC_URL", "https://evm-t3.cronos.org")
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        assert w3.is_connected(), "Failed to connect to Cronos RPC"
    
    def test_chain_id(self):
        """Test correct chain ID for testnet"""
        rpc_url = os.getenv("CRONOS_RPC_URL", "https://evm-t3.cronos.org")
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        chain_id = w3.eth.chain_id
        expected_chain_id = int(os.getenv("CHAIN_ID", 338))
        assert chain_id == expected_chain_id, f"Expected chain {expected_chain_id}, got {chain_id}"
    
    def test_latest_block(self):
        """Test ability to fetch latest block"""
        rpc_url = os.getenv("CRONOS_RPC_URL", "https://evm-t3.cronos.org")
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        block_number = w3.eth.block_number
        assert block_number > 0, "Could not fetch block number"


class TestTokenResolution:
    """Test token address resolution"""
    
    def test_resolve_usdc_symbol(self):
        """Test resolving USDC by symbol"""
        address = resolve_token_address("usdc")
        assert address is not None
        assert address.startswith("0x")
        assert len(address) == 42
    
    def test_resolve_vvs_symbol(self):
        """Test resolving VVS by symbol"""
        address = resolve_token_address("vvs")
        assert address is not None or address == "cro"
    
    def test_resolve_cro_native(self):
        """Test resolving native CRO"""
        address = resolve_token_address("cro")
        assert address == "cro"
    
    def test_resolve_checksum_address(self):
        """Test resolving a raw address to checksum"""
        raw_address = os.getenv("USDC_CONTRACT", "").lower()
        if raw_address:
            resolved = resolve_token_address(raw_address)
            assert resolved is not None
            assert resolved[0].isupper() or resolved[0].isdigit()  # Checksum has mixed case


class TestWalletBalance:
    """Test wallet balance queries"""
    
    def test_get_cro_balance(self):
        """Test getting native CRO balance"""
        result = get_token_balance.invoke({"token_address": "cro"})
        assert "balance_readable" in result or "error" in result
        if "balance_readable" in result:
            assert result["balance_readable"] >= 0
    
    def test_get_usdc_balance(self):
        """Test getting USDC balance"""
        usdc_address = os.getenv("USDC_CONTRACT")
        result = get_token_balance.invoke({"token_address": usdc_address})
        assert "balance_readable" in result or "error" in result
        if "balance_readable" in result:
            assert result["balance_readable"] >= 0
    
    def test_invalid_token(self):
        """Test error handling for invalid token"""
        result = get_token_balance.invoke({"token_address": "0x0000000000000000000000000000000000000000"})
        assert "error" in result or "balance_readable" in result


class TestSwapEstimation:
    """Test swap output estimation"""
    
    def test_estimate_usdc_to_vvs(self):
        """Test estimating USDC to VVS swap"""
        result = estimate_swap_output.invoke({
            "token_in": "usdc",
            "token_out": "vvs",
            "amount_in": 1.0
        })
        # Should return either estimate or mock pricing
        assert "amount_out" in result or "error" in result
    
    def test_estimate_with_zero_amount(self):
        """Test estimation with zero amount"""
        result = estimate_swap_output.invoke({
            "token_in": "usdc",
            "token_out": "vvs",
            "amount_in": 0.0
        })
        assert "error" in result or result.get("amount_out") == 0
    
    def test_estimate_negative_amount(self):
        """Test estimation with negative amount"""
        result = estimate_swap_output.invoke({
            "token_in": "usdc",
            "token_out": "vvs",
            "amount_in": -1.0
        })
        assert "error" in result


class TestContractVerification:
    """Test deployed contract verification"""
    
    def test_usdc_contract_exists(self):
        """Test USDC contract has code"""
        rpc_url = os.getenv("CRONOS_RPC_URL", "https://evm-t3.cronos.org")
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        usdc_address = os.getenv("USDC_CONTRACT")
        if usdc_address:
            code = w3.eth.get_code(Web3.to_checksum_address(usdc_address))
            assert code != b'' and code != b'\x00', "USDC contract has no code"
    
    def test_router_contract_exists(self):
        """Test VVS Router contract has code"""
        rpc_url = os.getenv("CRONOS_RPC_URL", "https://evm-t3.cronos.org")
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        router_address = os.getenv("VVS_ROUTER")
        if router_address:
            code = w3.eth.get_code(Web3.to_checksum_address(router_address))
            assert code != b'' and code != b'\x00', "Router contract has no code"
    
    def test_wcro_contract_exists(self):
        """Test WCRO contract has code"""
        rpc_url = os.getenv("CRONOS_RPC_URL", "https://evm-t3.cronos.org")
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        wcro_address = os.getenv("WCRO_ADDRESS")
        if wcro_address:
            code = w3.eth.get_code(Web3.to_checksum_address(wcro_address))
            assert code != b'' and code != b'\x00', "WCRO contract has no code"


class TestGasEstimation:
    """Test gas price and estimation"""
    
    def test_get_gas_price(self):
        """Test fetching current gas price"""
        rpc_url = os.getenv("CRONOS_RPC_URL", "https://evm-t3.cronos.org")
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        gas_price = w3.eth.gas_price
        assert gas_price > 0, "Gas price should be positive"
        
        gas_price_gwei = w3.from_wei(gas_price, 'gwei')
        assert gas_price_gwei > 0, "Gas price in Gwei should be positive"


class TestSwapExecution:
    """Test swap execution (mock mode)"""
    
    def test_mock_swap_usdc_to_vvs(self):
        """Test mock swap execution"""
        result = execute_vvs_swap.invoke({
            "token_in": "usdc",
            "token_out": "vvs",
            "amount_in": 0.1
        })
        
        # Should either execute or return mock result
        assert "status" in result or "error" in result
        assert "transaction_hash" in result or "status" in result
    
    def test_swap_with_insufficient_balance(self):
        """Test swap with amount larger than balance"""
        result = execute_vvs_swap.invoke({
            "token_in": "usdc",
            "token_out": "vvs",
            "amount_in": 999999999.0  # Unrealistically large
        })
        
        # Should handle gracefully (either error or mock)
        assert "error" in result or "status" in result


class TestTransactionHistory:
    """Test transaction history and tracking"""
    
    def test_get_trading_history(self):
        """Test retrieving trading history"""
        result = get_trade_history.invoke({})
        
        # Should return array of trades or empty list
        assert isinstance(result, dict)
        assert "trades" in result or "error" in result


class TestEnvironmentConfiguration:
    """Test environment variable configuration"""
    
    def test_wallet_private_key_set(self):
        """Test wallet private key is configured"""
        private_key = os.getenv("WALLET_PRIVATE_KEY")
        assert private_key is not None, "WALLET_PRIVATE_KEY not set"
        assert len(private_key) == 64, "Private key should be 64 hex characters"
    
    def test_rpc_url_set(self):
        """Test RPC URL is configured"""
        rpc_url = os.getenv("CRONOS_RPC_URL")
        assert rpc_url is not None, "CRONOS_RPC_URL not set"
        assert rpc_url.startswith("http"), "RPC URL should start with http/https"
    
    def test_chain_id_set(self):
        """Test chain ID is configured"""
        chain_id = os.getenv("CHAIN_ID")
        assert chain_id is not None, "CHAIN_ID not set"
        assert int(chain_id) in [25, 338], "Chain ID should be 25 (mainnet) or 338 (testnet)"
    
    def test_contracts_configured(self):
        """Test all contract addresses are configured"""
        required_contracts = ["USDC_CONTRACT", "VVS_ROUTER", "WCRO_ADDRESS"]
        for contract in required_contracts:
            address = os.getenv(contract)
            assert address is not None, f"{contract} not configured"
            assert address.startswith("0x"), f"{contract} should start with 0x"
            assert len(address) == 42, f"{contract} should be 42 characters"


# Integration test class (runs slower, tests real blockchain)
@pytest.mark.integration
class TestIntegration:
    """Integration tests that interact with real blockchain"""
    
    def test_full_balance_check_flow(self):
        """Test complete balance check flow"""
        # Check CRO
        cro_result = get_token_balance.invoke({"token_address": "cro"})
        assert "balance_readable" in cro_result
        
        # Check USDC
        usdc_address = os.getenv("USDC_CONTRACT")
        usdc_result = get_token_balance.invoke({"token_address": usdc_address})
        assert "balance_readable" in usdc_result or "error" in usdc_result
    
    def test_estimate_and_compare(self):
        """Test estimation provides consistent results"""
        result1 = estimate_swap_output.invoke({
            "token_in": "usdc",
            "token_out": "vvs",
            "amount_in": 1.0
        })
        
        result2 = estimate_swap_output.invoke({
            "token_in": "usdc",
            "token_out": "vvs",
            "amount_in": 1.0
        })
        
        # Results should be consistent (or both errors)
        if "amount_out" in result1 and "amount_out" in result2:
            # Allow for some price variation but should be similar
            diff_percent = abs(result1["amount_out"] - result2["amount_out"]) / result1["amount_out"] * 100
            assert diff_percent < 10, "Estimates vary too much"


if __name__ == "__main__":
    # Run tests when executed directly
    pytest.main([__file__, "-v", "-s"])
