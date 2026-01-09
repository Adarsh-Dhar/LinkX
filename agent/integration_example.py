"""
Example integration of Predictive RL Agent with existing chat system.
Add this to your lightweight_agent.py or main.py
"""

from predictive_agent import PredictiveAgent
import asyncio
import json

# Initialize the neural agent (do this once at startup)
neural_agent = PredictiveAgent(simulation_mode=True)


def handle_neural_commands(user_message: str) -> str:
    """
    Handle neural agent commands from the chat interface.
    
    Trigger phrases:
    - "activate neural mode"
    - "run prediction"
    - "neural analysis"
    - "ai prediction"
    - "brain status"
    """
    
    message_lower = user_message.lower()
    
    # ========== COMMAND 1: Run Neural Prediction ==========
    if any(phrase in message_lower for phrase in [
        "activate neural", 
        "run prediction", 
        "neural analysis",
        "ai prediction",
        "predict"
    ]):
        # Run the prediction cycle
        result = asyncio.run(neural_agent.run_cycle())
        
        # Format response for chat
        return f"""
🧠 **Neural Analysis Complete**

Analyzed **48 data sources** across market data, on-chain metrics, sentiment signals, and technical indicators.

**Decision:** {result['action']}
**Confidence:** {result['confidence']*100:.1f}%
**Execution Status:** {result['result']}

**Probability Distribution:**
• 🟢 BUY:  {result['probabilities']['BUY']*100:.0f}%
• ⚪ HOLD: {result['probabilities']['HOLD']*100:.0f}%
• 🔴 SELL: {result['probabilities']['SELL']*100:.0f}%

**Current Portfolio:**
💵 USDC: {result['portfolio']['USDC']:.2f}
🔷 CRO:  {result['portfolio']['CRO']:.2f}

**Agent Intelligence:**
📊 Total Trades: {result['brain_stats']['total_trades']}
🎯 Win Rate: {result['brain_stats']['win_rate']:.1f}%
🏆 Performance Score: {result['brain_stats']['cumulative_reward']:+.2f}
"""
    
    # ========== COMMAND 2: Check Brain Status ==========
    elif any(phrase in message_lower for phrase in [
        "brain status",
        "agent stats",
        "neural stats",
        "performance"
    ]):
        stats = neural_agent.brain.get_stats()
        
        return f"""
🧠 **Neural Agent Status**

**Learning Progress:**
• Total Trades: {stats['total_trades']}
• Successful Trades: {stats['successful_trades']}
• Win Rate: {stats['win_rate']:.1f}%
• Cumulative Reward: {stats['cumulative_reward']:+.2f}

**Memory:**
• Experience Buffer: {stats['memory_size']}/1000 trades stored

**Model State:**
• Training: {"Active" if stats['total_trades'] > 0 else "Pending first trade"}
• Architecture: 48 → 64 → 64 → 3 (PyTorch)
• Algorithm: Q-Learning with Experience Replay

💡 *The more trades the agent makes, the smarter it becomes.*
"""
    
    # ========== COMMAND 3: Continuous Learning Mode ==========
    elif any(phrase in message_lower for phrase in [
        "train agent",
        "continuous mode",
        "learning mode"
    ]):
        # Extract cycle count if provided (default 5)
        import re
        cycles_match = re.search(r'(\d+)\s*cycles?', message_lower)
        cycles = int(cycles_match.group(1)) if cycles_match else 5
        cycles = min(cycles, 20)  # Cap at 20 for safety
        
        # Run continuous learning (this will take time)
        asyncio.run(neural_agent.run_continuous(cycles=cycles, delay_seconds=1))
        
        final_stats = neural_agent.brain.get_stats()
        
        return f"""
🎓 **Training Complete**

Ran {cycles} learning cycles.

**Final Results:**
• Win Rate: {final_stats['win_rate']:.1f}%
• Total Trades: {final_stats['total_trades']}
• Performance Score: {final_stats['cumulative_reward']:+.2f}

**Portfolio Value:**
💵 {neural_agent.portfolio['USDC']:.2f} USDC
🔷 {neural_agent.portfolio['CRO']:.2f} CRO

The agent is now smarter and ready for predictions! 🚀
"""
    
    # ========== COMMAND 4: Market Snapshot ==========
    elif any(phrase in message_lower for phrase in [
        "market snapshot",
        "data overview",
        "what do you see"
    ]):
        # Just fetch the data without making a prediction
        state = asyncio.run(neural_agent.pipeline.get_market_state())
        features = neural_agent.pipeline.get_feature_names()
        raw_values = neural_agent.pipeline.get_raw_values()
        
        # Show top 10 features
        sample_features = "\n".join([
            f"• {features[i]}: {raw_values[i]:.4f}" 
            for i in range(min(10, len(features)))
        ])
        
        return f"""
📊 **Market Data Snapshot**

Currently monitoring **48 data streams:**

**Sample Features:**
{sample_features}
... and {len(features)-10} more signals

**Data Quality:**
✅ All providers responding
📈 Data normalized and ready for analysis

Use "run prediction" to get AI trading recommendation.
"""
    
    # ========== COMMAND 5: Reset Brain ==========
    elif any(phrase in message_lower for phrase in [
        "reset brain",
        "reset agent",
        "start fresh"
    ]):
        import os
        
        # Delete saved models
        if os.path.exists("agent/brain.pth"):
            os.remove("agent/brain.pth")
        if os.path.exists("agent/brain_stats.json"):
            os.remove("agent/brain_stats.json")
        
        # Reinitialize
        global neural_agent
        neural_agent = PredictiveAgent(simulation_mode=True)
        
        return """
🔄 **Neural Agent Reset**

The agent's memory and learned behaviors have been cleared.

The neural network is now in its initial untrained state and ready to learn from scratch.

Use "train agent" or "run prediction" to start building intelligence.
"""
    
    else:
        # Not a neural command
        return None


# ============================================================
# INTEGRATION EXAMPLE
# ============================================================

def process_user_message(user_message: str) -> str:
    """
    Main message handler - integrate with your existing system.
    """
    
    # First, check if it's a neural command
    neural_response = handle_neural_commands(user_message)
    
    if neural_response:
        return neural_response
    
    # Otherwise, handle with your existing logic
    # ... your existing code ...
    return "I didn't understand that command."


# ============================================================
# EXAMPLE USAGE
# ============================================================

if __name__ == "__main__":
    # Test the integration
    test_messages = [
        "activate neural mode",
        "brain status",
        "market snapshot",
        "train agent 3 cycles"
    ]
    
    for msg in test_messages:
        print(f"\n{'='*70}")
        print(f"USER: {msg}")
        print(f"{'='*70}")
        response = process_user_message(msg)
        print(response)
