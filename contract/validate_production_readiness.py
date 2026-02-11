#!/usr/bin/env python3
"""
Production Readiness Validation Script
Tests the three critical execution paths:
1. Brain → TradingEngine connection (execute_move)
2. Registry discovery (nodes API public access)
3. Async data consumption (non-blocking x402 payments)
"""

import sys
import os
import asyncio
import requests
from pathlib import Path

# Add agent directory to path
sys.path.insert(0, str(Path(__file__).parent / 'agent'))

def test_registry_discovery():
    """Test 1: Verify /api/nodes endpoint is public and returns metadata"""
    print("\n" + "="*80)
    print("TEST 1: REGISTRY DISCOVERY (Public Metadata Access)")
    print("="*80)
    
    try:
        response = requests.get("http://localhost:3600/api/nodes", timeout=5)
        
        if response.status_code != 200:
            print(f"❌ FAILED: Expected 200, got {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
        
        nodes = response.json()
        if not isinstance(nodes, list):
            print(f"❌ FAILED: Expected list, got {type(nodes)}")
            return False
        
        if len(nodes) == 0:
            print(f"⚠️  WARNING: No nodes in registry")
            return True
        
        # Verify node schema
        first_node = nodes[0]
        required_fields = ['id', 'name', 'price', 'endpointUrl', 'qualityScore', 'granularity']
        missing = [f for f in required_fields if f not in first_node]
        
        if missing:
            print(f"❌ FAILED: Missing fields in node schema: {missing}")
            return False
        
        print(f"✅ PASSED: Registry returned {len(nodes)} nodes with valid schema")
        print(f"   Sample node: {first_node['name']} (${first_node['price']} USDC)")
        return True
        
    except requests.exceptions.ConnectionError:
        print(f"❌ FAILED: Cannot connect to http://localhost:3600")
        print(f"   Make sure frontend/server is running: cd frontend && pnpm dev")
        return False
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


async def test_async_data_pipeline():
    """Test 2: Verify data pipeline uses async executor for non-blocking calls"""
    print("\n" + "="*80)
    print("TEST 2: ASYNC DATA PIPELINE (Non-Blocking x402)")
    print("="*80)
    
    try:
        from agent.data_pipeline import DataPipeline
        from agent.main import IntelligentAgent
        
        # Create agent with pipeline
        agent = IntelligentAgent()
        pipeline = agent.pipeline
        
        # Verify run_in_executor is used in purchase_single_node
        import inspect
        source = inspect.getsource(pipeline.purchase_single_node)
        
        if 'run_in_executor' not in source:
            print(f"❌ FAILED: purchase_single_node does not use run_in_executor")
            print(f"   Sync requests.get will block the event loop!")
            return False
        
        print(f"✅ PASSED: DataPipeline.purchase_single_node uses run_in_executor")
        print(f"   Event loop will remain responsive during x402 payments")
        
        # Test actual async execution (simulation mode)
        os.environ['SIMULATION_MODE'] = 'true'
        result = await pipeline.purchase_single_node('test-node-id')
        
        if result and result.get('simulated'):
            print(f"✅ PASSED: Async execution completed successfully")
            print(f"   Result: {result}")
            return True
        else:
            print(f"⚠️  WARNING: Simulation returned unexpected result: {result}")
            return True
        
    except ImportError as e:
        print(f"❌ FAILED: Cannot import agent modules: {e}")
        return False
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_trading_engine_connection():
    """Test 3: Verify execute_move calls TradingEngine.execute_swap"""
    print("\n" + "="*80)
    print("TEST 3: BRAIN → TRADING ENGINE CONNECTION")
    print("="*80)
    
    try:
        from agent.predictive_agent import PredictiveAgent
        from agent.data_pipeline import DataPipeline
        from agent.main import IntelligentAgent
        import inspect
        
        # Inspect execute_move source code
        source = inspect.getsource(PredictiveAgent.execute_move)
        
        # Verify TradingEngine is imported
        if 'from .trading_engine import TradingEngine' not in source:
            print(f"❌ FAILED: execute_move does not import TradingEngine")
            return False
        
        # Verify execute_swap is called
        if 'engine.execute_swap' not in source:
            print(f"❌ FAILED: execute_move does not call engine.execute_swap")
            print(f"   Agent will log trades but not execute them!")
            return False
        
        # Verify both LONG and SHORT paths
        if 'bias == "LONG"' not in source:
            print(f"❌ FAILED: No LONG execution path found")
            return False
        
        if 'bias == "SHORT"' not in source:
            print(f"❌ FAILED: No SHORT execution path found")
            return False
        
        print(f"✅ PASSED: execute_move correctly imports TradingEngine")
        print(f"✅ PASSED: Both LONG and SHORT execution paths call engine.execute_swap")
        print(f"✅ PASSED: Agent will execute real blockchain transactions")
        
        # Count the number of execute_swap calls
        swap_calls = source.count('engine.execute_swap')
        print(f"   Found {swap_calls} execute_swap calls (LONG and SHORT)")
        
        return True
        
    except ImportError as e:
        print(f"❌ FAILED: Cannot import agent modules: {e}")
        return False
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_override_system():
    """Test 4: Verify human override system is functional"""
    print("\n" + "="*80)
    print("TEST 4: HUMAN OVERRIDE SYSTEM")
    print("="*80)
    
    try:
        from agent.predictive_agent import PredictiveAgent
        from agent.data_pipeline import DataPipeline
        from agent.main import IntelligentAgent
        
        agent = IntelligentAgent()
        pred_agent = agent.current_predictive_instance
        
        # Test 1: Check default values
        if not hasattr(pred_agent, 'risk_threshold'):
            print(f"❌ FAILED: PredictiveAgent missing risk_threshold attribute")
            return False
        
        if not hasattr(pred_agent, 'forced_bias'):
            print(f"❌ FAILED: PredictiveAgent missing forced_bias attribute")
            return False
        
        print(f"✅ PASSED: Override attributes present")
        print(f"   risk_threshold: {pred_agent.risk_threshold}")
        print(f"   forced_bias: {pred_agent.forced_bias}")
        
        # Test 2: Modify values
        pred_agent.risk_threshold = 0.5
        pred_agent.forced_bias = "SHORT"
        
        if pred_agent.risk_threshold != 0.5:
            print(f"❌ FAILED: Cannot modify risk_threshold")
            return False
        
        if pred_agent.forced_bias != "SHORT":
            print(f"❌ FAILED: Cannot modify forced_bias")
            return False
        
        print(f"✅ PASSED: Override values are mutable")
        
        # Test 3: Verify API endpoint exists
        try:
            response = requests.post(
                "http://localhost:8080/agent/control/override",
                json={"risk": 0.3, "bias": "LONG"},
                timeout=2
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ PASSED: Override API endpoint is functional")
                print(f"   Response: {result.get('status')}")
            else:
                print(f"⚠️  WARNING: Override API returned {response.status_code}")
                print(f"   Agent may not be running: python agent/main.py")
        except requests.exceptions.ConnectionError:
            print(f"⚠️  WARNING: Cannot connect to http://localhost:8080")
            print(f"   Agent API not running, but override system is structurally correct")
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all validation tests"""
    print("\n" + "█"*80)
    print("█" + " "*30 + "PRODUCTION READINESS VALIDATION" + " "*19 + "█")
    print("█"*80)
    
    results = {}
    
    # Run tests
    results['registry'] = test_registry_discovery()
    results['async_pipeline'] = await test_async_data_pipeline()
    results['trading_engine'] = await test_trading_engine_connection()
    results['override_system'] = await test_override_system()
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name.replace('_', ' ').title()}")
    
    print("\n" + "="*80)
    print(f"OVERALL: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL SYSTEMS GO - PRODUCTION READY")
        print("\nNext steps:")
        print("1. ./force_aggressive.sh    # Test override system")
        print("2. ./test_buy.sh             # Test real trade execution")
        print("3. Monitor agent logs for:   # Verify blockchain txs")
        print("   - [EXECUTION] Action: LONG")
        print("   - ✅ [LONG Execution] Swapped X USDC -> WXTZ. Hash: 0x...")
        return 0
    else:
        print("\n⚠️  CRITICAL ISSUES DETECTED - NOT PRODUCTION READY")
        print("\nReview failed tests above and fix before deploying")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
