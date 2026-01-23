import asyncio
try:
    from .data_pipeline import DataPipeline
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
from .brain import RLAgent
import time
from datetime import datetime
import json
import os

# Import existing tools if available
try:
    from .tools import execute_vvs_swap, get_token_balance
    TOOLS_AVAILABLE = True
except ImportError:
    TOOLS_AVAILABLE = False
    print("⚠️  Trading tools not imported (optional for simulation mode)")


class PredictiveAgent:
    """
    Reinforcement Learning Trading Agent
    
    Implements the Observe -> Predict -> Act -> Reward cycle:
    1. OBSERVE: Collect 48 data points from providers
    2. PREDICT: Neural network makes decision
    3. ACT: Execute trade if confidence threshold met
    4. REWARD: Learn from outcome and update neural network
    """
    
    def __init__(self, market_manager, simulation_mode=True):
        self.pipeline = DataPipeline(market_manager)
        self.brain = RLAgent(model_path="agent/brain.pth")
        
        # Trading state
        self.last_trade_price = 0
        self.last_action = "HOLD"
        self.last_state = None
        self.last_action_idx = 0
        
        # Portfolio tracking (virtual for simulation)
        self.portfolio = {
            "USDC": 100.0,
            "CRO": 0.0
        }
        
        # Configuration
        self.simulation_mode = simulation_mode
        self.confidence_threshold = 0.70  # Minimum confidence to act
        self.trade_amount_usdc = 10.0
        
        # Performance tracking
        self.trades_executed = 0
        self.total_profit_loss = 0.0
        self.trade_history = []

    async def run_cycle(self):
        """Execute one complete RL cycle."""
        print("\n" + "="*60)
        print(f"🤖 PREDICTIVE AGENT CYCLE - {datetime.now().strftime('%H:%M:%S')}")
        print("="*60)
        
        # ========== STEP 1: OBSERVE (Sensory Input) ==========
        print("\n🔎 STEP 1: OBSERVE - Scanning 48 Data Providers...")
        state_vector = await self.pipeline.get_market_state()
        
        # Display sample features for transparency
        feature_names = self.pipeline.get_feature_names()
        raw_values = self.pipeline.get_raw_values()
        print("\n📊 Sample Market Features:")
        for i in range(min(5, len(feature_names))):
            print(f"   • {feature_names[i]}: {raw_values[i]:.4f}")
        print(f"   ... and {len(feature_names)-5} more features")
        
        # ========== STEP 2: PREDICT (Neural Network) ==========
        print("\n🧠 STEP 2: PREDICT - Neural Network Analysis...")
        action, confidence, probabilities = self.brain.get_action(state_vector, epsilon=0.05)
        
        print("\n🎯 PREDICTION RESULTS:")
        print(f"   ┌─ Decision: {action}")
        print(f"   ├─ Confidence: {confidence*100:.2f}%")
        print(f"   └─ Probability Distribution:")
        for act, prob in probabilities.items():
            bar = "█" * int(prob * 50)
            print(f"      {act:5s} [{bar:50s}] {prob*100:.1f}%")
        
        # Get action index for training later
        action_idx = ["HOLD", "BUY", "SELL"].index(action)
        
        # ========== STEP 3: ACT (Execute Trade) ==========
        print("\n⚡ STEP 3: ACT - Trade Execution Decision...")
        
        result = None
        if action == "BUY" and confidence > self.confidence_threshold:
            result = await self._execute_buy(confidence)
            self.last_action = "BUY"
            self.last_action_idx = 1
            
        elif action == "SELL" and confidence > self.confidence_threshold:
            result = await self._execute_sell(confidence)
            self.last_action = "SELL"
            self.last_action_idx = 2
            
        else:
            print(f"⏸️  HOLD: {self._get_hold_reason(action, confidence)}")
            result = "HOLD"
            self.last_action = "HOLD"
            self.last_action_idx = 0
        
        # ========== STEP 4: REWARD (Learn from outcome) ==========
        # Only train if we have a previous state to compare
        if self.last_state is not None and result in ["BUY_EXECUTED", "SELL_EXECUTED"]:
            print("\n🎓 STEP 4: REWARD - Learning from Trade Outcome...")
            reward = self._calculate_reward(result)
            
            print(f"   Reward Signal: {reward:+.2f}")
            print(f"   Training Neural Network...")
            
            self.brain.train(self.last_state, self.last_action_idx, reward, state_vector)
            
            # Display updated statistics
            stats = self.brain.get_stats()
            print(f"\n📈 Agent Learning Progress:")
            print(f"   ├─ Total Trades: {stats['total_trades']}")
            print(f"   ├─ Win Rate: {stats['win_rate']:.1f}%")
            print(f"   └─ Cumulative Reward: {stats['cumulative_reward']:+.2f}")
        
        # Store state for next cycle
        self.last_state = state_vector
        
        # ========== SUMMARY ==========
        print("\n" + "="*60)
        print("✅ CYCLE COMPLETE")
        print("="*60)
        
        return {
            "action": action,
            "confidence": confidence,
            "probabilities": probabilities,
            "result": result,
            "portfolio": self.portfolio.copy(),
            "brain_stats": self.brain.get_stats()
        }

    async def _execute_buy(self, confidence):
        """Execute a BUY trade."""
        print(f"🚀 EXECUTING BUY SIGNAL (Confidence: {confidence*100:.2f}%)")
        
        if self.simulation_mode:
            # Simulated execution
            mock_price = 0.12
            amount_usdc = min(self.trade_amount_usdc, self.portfolio["USDC"])
            amount_cro = amount_usdc / mock_price
            
            self.portfolio["USDC"] -= amount_usdc
            self.portfolio["CRO"] += amount_cro
            self.last_trade_price = mock_price
            
            print(f"   ✓ Bought {amount_cro:.2f} CRO for {amount_usdc:.2f} USDC")
            print(f"   ✓ Price: ${mock_price:.4f}")
            print(f"   ✓ Portfolio: {self.portfolio['USDC']:.2f} USDC, {self.portfolio['CRO']:.2f} CRO")
            
            self.trades_executed += 1
            return "BUY_EXECUTED"
            
        else:
            # Real execution using your tools
            if TOOLS_AVAILABLE:
                try:
                    result = execute_vvs_swap.invoke({
                        "token_in": "usdc",
                        "token_out": "cro",
                        "amount_in": self.trade_amount_usdc
                    })
                    print(f"   ✓ {result}")
                    self.trades_executed += 1
                    return "BUY_EXECUTED"
                except Exception as e:
                    print(f"   ✗ Trade failed: {e}")
                    return "BUY_FAILED"
            else:
                print("   ⚠️  Real trading tools not available")
                return "BUY_FAILED"

    async def _execute_sell(self, confidence):
        """Execute a SELL trade."""
        print(f"📉 EXECUTING SELL SIGNAL (Confidence: {confidence*100:.2f}%)")
        
        if self.simulation_mode:
            # Simulated execution
            mock_price = 0.11
            amount_cro = min(self.portfolio["CRO"], 100)
            amount_usdc = amount_cro * mock_price
            
            if amount_cro > 0:
                self.portfolio["CRO"] -= amount_cro
                self.portfolio["USDC"] += amount_usdc
                
                # Calculate profit/loss
                profit_loss = amount_usdc - (amount_cro * self.last_trade_price)
                self.total_profit_loss += profit_loss
                
                print(f"   ✓ Sold {amount_cro:.2f} CRO for {amount_usdc:.2f} USDC")
                print(f"   ✓ Price: ${mock_price:.4f}")
                print(f"   ✓ P/L: {profit_loss:+.2f} USDC")
                print(f"   ✓ Portfolio: {self.portfolio['USDC']:.2f} USDC, {self.portfolio['CRO']:.2f} CRO")
                
                self.trades_executed += 1
                return "SELL_EXECUTED"
            else:
                print("   ⚠️  No CRO to sell")
                return "SELL_FAILED"
                
        else:
            # Real execution
            if TOOLS_AVAILABLE:
                try:
                    result = execute_vvs_swap.invoke({
                        "token_in": "cro",
                        "token_out": "usdc",
                        "amount_in": self.trade_amount_usdc
                    })
                    print(f"   ✓ {result}")
                    self.trades_executed += 1
                    return "SELL_EXECUTED"
                except Exception as e:
                    print(f"   ✗ Trade failed: {e}")
                    return "SELL_FAILED"
            else:
                print("   ⚠️  Real trading tools not available")
                return "SELL_FAILED"

    def _calculate_reward(self, result):
        """
        Calculate the reward signal for reinforcement learning.
        Positive reward for successful trades, negative for losses.
        """
        if result == "BUY_EXECUTED":
            # For BUY, reward is based on potential upside
            # In a real system, you'd wait for the trade to close
            return 0.5  # Neutral reward until we see outcome
            
        elif result == "SELL_EXECUTED":
            # For SELL, calculate actual profit/loss
            if hasattr(self, 'last_trade_price') and self.last_trade_price > 0:
                # Simulated P/L calculation
                current_price = 0.11
                profit_pct = (current_price - self.last_trade_price) / self.last_trade_price
                
                # Reward is proportional to profit
                if profit_pct > 0:
                    return min(profit_pct * 10, 1.0)  # Cap at 1.0
                else:
                    return max(profit_pct * 10, -1.0)  # Cap at -1.0
            else:
                return 0.0
        else:
            return 0.0

    def _get_hold_reason(self, action, confidence):
        """Get human-readable reason for HOLD decision."""
        if action == "HOLD":
            return f"Model suggests HOLD (Confidence: {confidence*100:.1f}%)"
        else:
            return f"Confidence too low for {action} ({confidence*100:.1f}% < {self.confidence_threshold*100:.0f}%)"

    async def run_continuous(self, cycles=10, delay_seconds=5):
        """Run multiple prediction cycles for continuous learning."""
        print(f"\n🔄 Starting continuous mode: {cycles} cycles with {delay_seconds}s delay\n")
        
        for i in range(cycles):
            print(f"\n{'='*60}")
            print(f"CYCLE {i+1}/{cycles}")
            print(f"{'='*60}")
            
            result = await self.run_cycle()
            
            if i < cycles - 1:  # Don't wait after last cycle
                print(f"\n⏳ Waiting {delay_seconds} seconds before next cycle...")
                await asyncio.sleep(delay_seconds)
        
        print("\n\n" + "="*60)
        print("🏁 FINAL SUMMARY")
        print("="*60)
        print(f"Total Cycles: {cycles}")
        print(f"Trades Executed: {self.trades_executed}")
        print(f"Final Portfolio: {self.portfolio}")
        print(f"Total P/L: ${self.total_profit_loss:+.2f}")
        print(f"\nBrain Statistics:")
        stats = self.brain.get_stats()
        for key, value in stats.items():
            print(f"  {key}: {value}")


# ========== ENTRY POINTS ==========

async def main():
    """Run a single prediction cycle."""
    agent = PredictiveAgent(simulation_mode=True)
    result = await agent.run_cycle()
    return result


async def continuous():
    """Run continuous learning mode."""
    agent = PredictiveAgent(simulation_mode=True)
    await agent.run_continuous(cycles=10, delay_seconds=3)


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║        🤖  PREDICTIVE RL TRADING AGENT  🧠               ║
║                                                          ║
║  Powered by Neural Networks & Reinforcement Learning    ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    # Run a single cycle
    asyncio.run(main())
    
    # Uncomment to run continuous mode:
    # asyncio.run(continuous())
