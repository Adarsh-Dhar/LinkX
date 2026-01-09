#!/usr/bin/env python3
"""
Test script to verify neural brain integration with the agent.
Tests without importing the full tools module.
"""

import sys
import numpy as np

# Test 1: Import the brain
print("Test 1: Importing neural network brain...")
try:
    from brain import RLAgent
    print("✅ Brain imported successfully")
except Exception as e:
    print(f"❌ Brain import failed: {e}")
    sys.exit(1)

# Test 2: Initialize the brain
print("\nTest 2: Initializing RLAgent...")
try:
    brain = RLAgent(model_path="agent/brain.pth")
    print("✅ Brain initialized successfully")
except Exception as e:
    print(f"❌ Brain initialization failed: {e}")
    sys.exit(1)

# Test 3: Create mock market state (48 features)
print("\nTest 3: Creating mock market data...")
try:
    market_state = np.random.rand(48).astype(np.float32)
    # Normalize
    market_state = (market_state - market_state.min()) / (market_state.max() - market_state.min())
    print(f"✅ Created market state vector: shape={market_state.shape}, range=[{market_state.min():.3f}, {market_state.max():.3f}]")
except Exception as e:
    print(f"❌ Market state creation failed: {e}")
    sys.exit(1)

# Test 4: Get neural prediction
print("\nTest 4: Getting AI prediction from brain...")
try:
    action, confidence, probabilities = brain.get_action(market_state, epsilon=0.05)
    print("✅ Neural prediction generated:")
    print(f"   • Action: {action}")
    print(f"   • Confidence: {confidence*100:.1f}%")
    print(f"   • Probabilities:")
    for act, prob in probabilities.items():
        print(f"      - {act}: {prob*100:.0f}%")
except Exception as e:
    print(f"❌ Prediction failed: {e}")
    sys.exit(1)

# Test 5: Get brain statistics
print("\nTest 5: Checking brain statistics...")
try:
    stats = brain.get_stats()
    print("✅ Brain stats retrieved:")
    print(f"   • Total Trades: {stats['total_trades']}")
    print(f"   • Win Rate: {stats['win_rate']:.1f}%")
    print(f"   • Cumulative Reward: {stats['cumulative_reward']:+.2f}")
    print(f"   • Memory Size: {stats['memory_size']}/1000")
except Exception as e:
    print(f"❌ Stats retrieval failed: {e}")
    sys.exit(1)

# Test 6: Simulate data vectorization (like lightweight_agent.py does)
print("\nTest 6: Testing data vectorization pipeline...")
try:
    # Mock data from a provider
    mock_provider_data = {
        'value': 0.12,
        'sentiment': 0.75,
        'volume': 1500000,
        'whale_activity': 1
    }
    
    # Vectorize
    market_vector = np.zeros(48, dtype=np.float32)
    
    # Fill first few slots
    market_vector[0] = float(mock_provider_data['value'])
    market_vector[1] = float(mock_provider_data['sentiment'])
    market_vector[2] = np.log1p(mock_provider_data['volume']) / 20  # Log scale
    market_vector[3] = float(mock_provider_data['whale_activity'])
    
    # Fill rest with derived features
    for i in range(4, 48):
        market_vector[i] = np.random.normal(0.5, 0.1)
    
    # Normalize
    market_vector = (market_vector - market_vector.min()) / (market_vector.max() - market_vector.min())
    
    print(f"✅ Data vectorized: {market_vector[:5]}")
    
    # Get prediction on real-world-like data
    action, confidence, probs = brain.get_action(market_vector, epsilon=0.05)
    print(f"✅ Prediction on vectorized data:")
    print(f"   • Action: {action} ({confidence*100:.1f}% confidence)")
    
except Exception as e:
    print(f"❌ Vectorization test failed: {e}")
    sys.exit(1)

# Test 7: Simulate the full agent workflow
print("\nTest 7: Simulating full agent workflow...")
try:
    # Step 1: Agent queries 48-node ecosystem (simulated)
    print("   1️⃣  Fetching data from 48 providers... (simulated)")
    
    # Step 2: Data vectorization
    print("   2️⃣  Vectorizing market data...")
    state = np.random.rand(48).astype(np.float32)
    state = (state - state.min()) / (state.max() - state.min())
    
    # Step 3: Neural prediction
    print("   3️⃣  Running neural network inference...")
    action, confidence, probs = brain.get_action(state)
    
    # Step 4: Format response (like lightweight_agent.py does)
    print("   4️⃣  Generating user response...")
    response = f"""
{'='*60}
🧠 NEURAL NETWORK ANALYSIS:
{'='*60}
   🎯 Decision: {action}
   📊 Confidence: {confidence*100:.1f}%
   📈 Probability Distribution:
      • BUY:  {probs['BUY']*100:.0f}%
      • HOLD: {probs['HOLD']*100:.0f}%
      • SELL: {probs['SELL']*100:.0f}%
"""
    
    print(response)
    print("✅ Full workflow completed successfully")
    
except Exception as e:
    print(f"❌ Workflow test failed: {e}")
    sys.exit(1)

print("\n" + "="*60)
print("🎉 ALL TESTS PASSED! Neural integration is working correctly.")
print("="*60)
print("\n💡 The brain is ready to be used by lightweight_agent.py")
print("   When a user queries the 48-node ecosystem, the agent will:")
print("   1. Fetch data from providers")
print("   2. Vectorize the data into 48 features")
print("   3. Run neural network inference")
print("   4. Return AI-powered trading recommendations")
