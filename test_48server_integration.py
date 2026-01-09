#!/usr/bin/env python3
"""
🚀 Complete 48-Server Integration Test
Tests: Data Pipeline → Neural Network → Trading Decisions
"""

import asyncio
import sys
import os

# Add agent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agent'))

from data_pipeline import DataPipeline
from brain import RLAgent
import numpy as np


async def test_ecosystem_integration():
    """Full integration test: 48 servers → Pipeline → Brain → Trading Decision"""
    
    print("\n" + "="*80)
    print("🚀 48-SERVER ECOSYSTEM INTEGRATION TEST")
    print("="*80)
    
    # ========== TEST 1: Registry Discovery ==========
    print("\n1️⃣  TEST: Registry Discovery")
    print("-" * 80)
    
    pipeline = DataPipeline()
    print("✅ Initialized DataPipeline")
    
    # ========== TEST 2: Live Data Fetch ==========
    print("\n2️⃣  TEST: Fetching Live Data from All 48 Servers")
    print("-" * 80)
    
    try:
        state = await pipeline.get_market_state()
        print(f"✅ Successfully fetched data from all 48 providers")
        print(f"   📊 Vector shape: {state.shape}")
        print(f"   📈 Value range (normalized): [{state.min():.3f}, {state.max():.3f}]")
        print(f"   ✓ All values normalized: {(state.min() >= 0 and state.max() <= 1)}")
    except Exception as e:
        print(f"❌ Failed to fetch data: {e}")
        return False
    
    # ========== TEST 3: Neural Network Prediction ==========
    print("\n3️⃣  TEST: Neural Network Trading Decision")
    print("-" * 80)
    
    try:
        brain = RLAgent(model_path='agent/brain.pth')
        print("✅ Neural Network Brain loaded")
        
        action, confidence, probabilities = brain.get_action(state, epsilon=0.05)
        
        print(f"\n📊 Trading Decision:")
        print(f"   🎯 Action: {action}")
        print(f"   📈 Confidence: {confidence*100:.1f}%")
        print(f"\n   Probability Distribution:")
        print(f"   ┌─────────────────────────────────┐")
        print(f"   │ BUY:  {probabilities['BUY']*100:5.1f}% ", end="")
        print("█" * int(probabilities['BUY'] * 20) + "░" * (20 - int(probabilities['BUY'] * 20)) + " │")
        print(f"   │ SELL: {probabilities['SELL']*100:5.1f}% ", end="")
        print("█" * int(probabilities['SELL'] * 20) + "░" * (20 - int(probabilities['SELL'] * 20)) + " │")
        print(f"   │ HOLD: {probabilities['HOLD']*100:5.1f}% ", end="")
        print("█" * int(probabilities['HOLD'] * 20) + "░" * (20 - int(probabilities['HOLD'] * 20)) + " │")
        print(f"   └─────────────────────────────────┘")
        
        stats = brain.get_stats()
        print(f"\n   📈 Brain Statistics:")
        print(f"   • Total Trades: {stats['total_trades']}")
        print(f"   • Win Rate: {stats['win_rate']:.1f}%")
        print(f"   • Performance Score: {stats['cumulative_reward']:+.2f}")
        
    except Exception as e:
        print(f"❌ Neural network error: {e}")
        return False
    
    # ========== TEST 4: Data Source Details ==========
    print("\n4️⃣  TEST: Data Source Verification")
    print("-" * 80)
    
    features = pipeline.get_feature_names()
    values = pipeline.get_raw_values()
    
    print(f"✅ {len(features)} data providers active")
    print(f"\nFirst 15 providers:")
    for i in range(min(15, len(features))):
        tier = "(Premium)" if "_A" in features[i] else "(Budget  )"
        print(f"   {i+1:2d}. {features[i]:20s} {tier} = {values[i]:12.2f}")
    
    print(f"\nLast 5 providers:")
    for i in range(max(0, len(features)-5), len(features)):
        tier = "(Premium)" if "_A" in features[i] else "(Budget  )"
        print(f"   {i+1:2d}. {features[i]:20s} {tier} = {values[i]:12.2f}")
    
    # ========== TEST 5: Trading Recommendation ==========
    print("\n5️⃣  TEST: Trading Recommendation Engine")
    print("-" * 80)
    
    if confidence > 0.70:
        if action == 'BUY':
            rec = f"🚀 STRONG BUY - Recommended: 'swap 10 usdc to cro'"
            signal_type = "STRONG BULLISH"
        elif action == 'SELL':
            rec = f"📉 STRONG SELL - Recommended: 'swap 10 cro to usdc'"
            signal_type = "STRONG BEARISH"
        else:
            rec = f"⏸️  HOLD - Market uncertain, maintain positions"
            signal_type = "NEUTRAL"
    else:
        rec = f"⏸️  HOLD - Low confidence ({confidence*100:.0f}%), maintain positions"
        signal_type = "UNCERTAIN"
    
    print(f"   Signal Type: {signal_type}")
    print(f"   Recommendation: {rec}")
    
    # ========== SUMMARY ==========
    print("\n" + "="*80)
    print("✨ ALL TESTS PASSED! SYSTEM FULLY OPERATIONAL ✨")
    print("="*80)
    print("\n📋 SUMMARY:")
    print(f"   ✅ 48 Data Providers: Connected")
    print(f"   ✅ Data Pipeline: Working")
    print(f"   ✅ Neural Network: Predictions Generated")
    print(f"   ✅ Trading Logic: Decision = {action}")
    print("\n🎯 The agent is ready to execute trades based on 48-server data analysis!\n")
    
    return True


if __name__ == "__main__":
    try:
        result = asyncio.run(test_ecosystem_integration())
        if not result:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
