#!/usr/bin/env python3
"""
🧠 Neural Agent Demo
Demonstrates the Predictive RL Agent in continuous learning mode
"""

import asyncio
import sys
from predictive_agent import PredictiveAgent

async def demo_single_cycle():
    """Demo: Single prediction cycle"""
    print("=" * 70)
    print("DEMO MODE 1: Single Prediction Cycle")
    print("=" * 70)
    
    agent = PredictiveAgent(simulation_mode=True)
    result = await agent.run_cycle()
    
    print("\n" + "=" * 70)
    print("📊 RESULT SUMMARY")
    print("=" * 70)
    print(f"Action: {result['action']}")
    print(f"Confidence: {result['confidence']*100:.1f}%")
    print(f"Execution: {result['result']}")
    print(f"\nPortfolio: {result['portfolio']}")
    print(f"Brain Stats: {result['brain_stats']}")

async def demo_continuous_learning():
    """Demo: Continuous learning with 5 cycles"""
    print("=" * 70)
    print("DEMO MODE 2: Continuous Learning (5 cycles)")
    print("=" * 70)
    
    agent = PredictiveAgent(simulation_mode=True)
    await agent.run_continuous(cycles=5, delay_seconds=2)

async def demo_neural_evolution():
    """Demo: Watch the neural network learn over time"""
    print("=" * 70)
    print("DEMO MODE 3: Neural Network Evolution")
    print("=" * 70)
    print("Watch how the agent's confidence changes as it learns...\n")
    
    agent = PredictiveAgent(simulation_mode=True)
    
    for cycle in range(10):
        print(f"\n{'─' * 70}")
        print(f"LEARNING CYCLE {cycle + 1}/10")
        print(f"{'─' * 70}")
        
        result = await agent.run_cycle()
        
        # Show evolution metrics
        print(f"\n📈 Evolution Metrics:")
        print(f"   Confidence: {result['confidence']*100:.1f}%")
        print(f"   Win Rate: {result['brain_stats']['win_rate']:.1f}%")
        print(f"   Total Trades: {result['brain_stats']['total_trades']}")
        
        if cycle < 9:
            await asyncio.sleep(1)
    
    print("\n" + "=" * 70)
    print("🎓 LEARNING COMPLETE!")
    print("=" * 70)
    print(f"Final Win Rate: {agent.brain.get_win_rate():.1f}%")
    print(f"Total Trades: {agent.brain.total_trades}")
    print(f"Cumulative Reward: {agent.brain.cumulative_reward:+.2f}")

async def main():
    """Main menu"""
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║        🤖  PREDICTIVE RL AGENT - DEMO SUITE  🧠                  ║
║                                                                  ║
║  Showcasing Neural Network Trading Intelligence                  ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝

Select a demo mode:

1. Single Prediction Cycle
   └─ Run one complete Observe→Predict→Act→Reward cycle

2. Continuous Learning (5 cycles)
   └─ Watch the agent make multiple decisions over time

3. Neural Network Evolution (10 cycles)
   └─ See how the agent improves with experience

4. Exit

    """)
    
    choice = input("Enter your choice (1-4): ").strip()
    
    if choice == "1":
        await demo_single_cycle()
    elif choice == "2":
        await demo_continuous_learning()
    elif choice == "3":
        await demo_neural_evolution()
    elif choice == "4":
        print("\n👋 Goodbye!")
        sys.exit(0)
    else:
        print("\n❌ Invalid choice. Please run again.")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏸️  Demo interrupted by user")
        sys.exit(0)
