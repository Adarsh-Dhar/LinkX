#!/usr/bin/env python3
"""
Test swap in production mode with real liquidity
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agent'))

from web3 import Web3
from dotenv import load_dotenv
from trading_engine import TradingEngine
from wallet_manager import WalletManager

load_dotenv()

def main():
    print("🧪 Testing Production Swap")
    print("=" * 50)

    # Check simulation mode
    simulation = os.getenv("SIMULATION_MODE", "false").lower() == "true"
    print(f"📊 Simulation Mode: {simulation}")

    if simulation:
        print("\n⚠️  WARNING: SIMULATION_MODE=true detected!")
        print("   Production swaps will not execute. Set SIMULATION_MODE=false")
        return 1

    # Initialize wallet and trading engine
    wallet = WalletManager()
    trading_engine = TradingEngine(wallet)

    # Check balances
    usdc_addr = Web3.to_checksum_address(os.getenv("USDC_CONTRACT"))
    wxtz_addr = Web3.to_checksum_address(os.getenv("WXTZ_ADDRESS"))

    print(f"\n💰 Wallet: {wallet.address}")
    print(f"   USDC: {wallet.get_balance('USDC'):.2f}")

    # Test swap: 1 USDC -> WXTZ
    swap_amount = 1.0
    print(f"\n🔄 Testing swap: {swap_amount} USDC -> WXTZ")
    print(f"   Token In:  {usdc_addr}")
    print(f"   Token Out: {wxtz_addr}")

    try:
        tx_hash = trading_engine.execute_swap(
            token_in=usdc_addr,
            token_out=wxtz_addr,
            amount_in=swap_amount,
            max_slippage=5.0
        )

        if tx_hash:
            print(f"\n✅ Swap successful!")
            print(f"   TX: {tx_hash}")
            print("\n🎉 Production mode working!")
            return 0
        else:
            print("\n❌ Swap failed (returned None)")
            return 1

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
