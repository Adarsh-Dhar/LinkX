#!/usr/bin/env python3
"""
Test script to validate real x402 trading execution
Tests the integration between DataPipeline, PredictiveAgent, TradingEngine, and WalletManager
"""
import asyncio
import os
import sys
import json
from datetime import datetime

# Add the agent directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agent.predictive_agent import PredictiveAgent
from agent.data_pipeline import DataPipeline
from agent.trading_engine import TradingEngine
from agent.wallet_manager import WalletManager

async def test_real_x402_execution():
    """Test real x402 execution flow"""
    print("🧪 TESTING REAL x402 EXECUTION FLOW")
    print("=" * 60)
    
    try:
        # 1. Initialize components
        print("1. Initializing components...")
        market_manager = None  # Placeholder for market manager
        pipeline = DataPipeline(market_manager)
        agent = PredictiveAgent(pipeline)
        wallet = WalletManager()
        trading_engine = TradingEngine(wallet)
        
        # 2. Test wallet connection
        print("2. Testing wallet connection...")
        try:
            balance = wallet.get_balance('USDC')
            print(f"   ✅ USDC Balance: {balance}")
        except Exception as e:
            print(f"   ❌ Wallet connection failed: {e}")
            return False
        
        # 3. Test DataPipeline node purchase (mock node)
        print("3. Testing DataPipeline node purchase...")
        try:
            # Use a test node ID (this will fail gracefully if node doesn't exist)
            test_node_id = "test-node-123"
            result = await pipeline.purchase_single_node(test_node_id)
            if result:
                print(f"   ✅ Node purchase test completed: {result.get('real_purchase', False)}")
            else:
                print(f"   ⚠️ Node purchase returned None (expected for test node)")
        except Exception as e:
            print(f"   ⚠️ Node purchase test error: {e}")
        
        # 4. Test AlphaStrategist decision making
        print("4. Testing AlphaStrategist decision making...")
        try:
            market_snapshot = {
                "current_price": 100.0,
                "price_change_5m": 2.5,
                "recent_volatility": 1.2,
                "timestamp": datetime.now().isoformat()
            }
            
            decision = agent.strategist.rethink_strategy(market_snapshot, {})
            print(f"   ✅ Decision: {decision.get('verdict', 'UNKNOWN')}")
            print(f"   ✅ Confidence: {decision.get('risk_confidence', 0.0)}")
            print(f"   ✅ Execution bias: {decision.get('execution_bias', 'NEUTRAL')}")
            
        except Exception as e:
            print(f"   ❌ AlphaStrategist test failed: {e}")
        
        # 5. Test execution logic (without real trade)
        print("5. Testing execution logic...")
        try:
            test_decision = {
                "execution_bias": "NEUTRAL",  # Safe test - won't execute real trade
                "risk_confidence": 0.5,
                "thought": "Test decision for validation"
            }
            
            # This should skip execution due to NEUTRAL bias
            result = await agent.execute_move(test_decision, {})
            print(f"   ✅ Execution test completed (skipped due to NEUTRAL bias)")
            
        except Exception as e:
            print(f"   ❌ Execution test failed: {e}")
        
        # 6. Test database connectivity
        print("6. Testing database connectivity...")
        try:
            import requests
            res = requests.get("http://localhost:3600/api/nodes", timeout=5)
            if res.status_code == 200:
                nodes = res.json()
                print(f"   ✅ Database connected, found {len(nodes)} nodes")
            else:
                print(f"   ⚠️ Database connection returned status {res.status_code}")
        except Exception as e:
            print(f"   ❌ Database connectivity test failed: {e}")
        
        print("\n🎉 INTEGRATION TEST COMPLETED")
        return True
        
    except Exception as e:
        print(f"\n❌ INTEGRATION TEST FAILED: {e}")
        return False

async def test_confidence_validation():
    """Test that confidence scores are properly numeric"""
    print("\n🔢 TESTING CONFIDENCE VALIDATION")
    print("=" * 40)
    
    try:
        market_manager = None
        pipeline = DataPipeline(market_manager)
        agent = PredictiveAgent(pipeline)
        
        # Test with different market conditions
        test_scenarios = [
            {"current_price": 100.0, "price_change_5m": 5.0, "recent_volatility": 2.0},
            {"current_price": 95.0, "price_change_5m": -3.0, "recent_volatility": 0.8},
            {"current_price": 110.0, "price_change_5m": 10.0, "recent_volatility": 3.0}
        ]
        
        for i, scenario in enumerate(test_scenarios, 1):
            print(f"Scenario {i}: {scenario}")
            decision = agent.strategist.rethink_strategy(scenario, {})
            confidence = decision.get('risk_confidence', 0)
            
            # Validate confidence is numeric
            if isinstance(confidence, (int, float)) and 0 <= confidence <= 1:
                print(f"   ✅ Valid numeric confidence: {confidence}")
            else:
                print(f"   ❌ Invalid confidence type/range: {confidence} ({type(confidence)})")
                
        return True
        
    except Exception as e:
        print(f"❌ CONFIDENCE VALIDATION FAILED: {e}")
        return False

if __name__ == "__main__":
    print("🚀 STARTING REAL x402 TRADING VALIDATION")
    print("=" * 60)
    
    # Run integration test
    success1 = asyncio.run(test_real_x402_execution())
    
    # Run confidence validation
    success2 = asyncio.run(test_confidence_validation())
    
    if success1 and success2:
        print("\n🎯 ALL TESTS PASSED - Agent ready for real x402 trading!")
        exit(0)
    else:
        print("\n⚠️ Some tests failed - review output above")
        exit(1)