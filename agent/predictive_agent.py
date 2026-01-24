
import asyncio
from datetime import datetime
import numpy as np


# We keep the pipeline to fetch data
try:
    from .data_pipeline import DataPipeline
except ImportError:
    from .data_pipeline import DataPipeline


class PredictiveAgent:
    def __init__(self, market_manager, trading_engine, simulation_mode=True):
        self.pipeline = DataPipeline(market_manager)
        self.trading_engine = trading_engine  # Store the engine
        self.previous_price = None
        self.min_price_change = 0.001  # 0.1% movement required to confirm trend


    async def run_cycle(self):
        print("\n" + "="*60)
        print(f"🤖 EXPERT TRADER CYCLE - {datetime.now().strftime('%H:%M:%S')}")

        import asyncio
        from datetime import datetime
        import numpy as np

        # Try importing pipeline
        try:
            from .data_pipeline import DataPipeline
        except ImportError:
            from agent.data_pipeline import DataPipeline

        class PredictiveAgent:
            def __init__(self, market_manager, trading_engine, simulation_mode=True):
                self.pipeline = DataPipeline(market_manager)
                self.trading_engine = trading_engine
                self.previous_price = None
                # Lower threshold for detecting trends
                self.min_price_change = 0.0001 

            async def run_cycle(self):
                print("="*60)
                print(f"🤖 EXPERT TRADER ANALYZING - {datetime.now().strftime('%H:%M:%S')}")
        
                # 1. Get Data (This triggers fetching & paying if needed)
                state_vector = await self.pipeline.get_market_state()
                current_price = float(state_vector[0])
        
                # Calculate Average Sentiment
                data_signals = state_vector[1:11] 
                valid_signals = [x for x in data_signals if x > 0.0]
                avg_signal = np.mean(valid_signals) if valid_signals else 0.5
        
                # 2. Trend Analysis
                trend = "NEUTRAL"
                if self.previous_price:
                    change = (current_price - self.previous_price) / self.previous_price
                    if change > self.min_price_change: trend = "UPTREND"
                    elif change < -self.min_price_change: trend = "DOWNTREND"
        
                self.previous_price = current_price
        
                print(f"📊 Market: Price ${current_price:.4f} [{trend}] | Sentiment: {avg_signal:.2f}")
        
                action = "HOLD"
        
                # 3. Decision Logic (Simplified for Activity)
                # Always trade if there is ANY trend or signal divergence
                if trend == "UPTREND" or avg_signal > 0.55:
                    action = "BUY"
                elif trend == "DOWNTREND" or avg_signal < 0.45:
                    action = "SELL"
                else:
                    # Random exploration if neutral (to force tx for testing)
                    # Remove this 'else' block in production
                    import random
                    action = random.choice(["BUY", "SELL"]) 
                    print("🎲 Market Neutral -> Forcing Exploration Trade")

                print(f"🎯 DECISION: {action}")

                # 4. Execute
                if action == "BUY":
                    self._trigger_trade("USDC", "CRO", 1.0) # Small amount
                elif action == "SELL":
                    self._trigger_trade("CRO", "USDC", 10.0)

                return {"action": action}

            def _trigger_trade(self, token_in, token_out, amount):
                print(f"🚀 EXECUTING: {amount} {token_in} -> {token_out}")
                try:
                    tx = self.trading_engine.execute_swap(token_in, token_out, amount)
                    if tx:
                        print(f"   ✅ TX SUCCESS: {tx}")
                    else:
                        print(f"   ❌ TX FAILED (See TradingEngine logs)")
                except Exception as e:
                    print(f"   ❌ CRITICAL FAIL: {e}")