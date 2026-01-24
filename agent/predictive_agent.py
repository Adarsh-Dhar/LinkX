
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
        print("="*60)
        print(f"🤖 EXPERT TRADER ANALYZING - {datetime.now().strftime('%H:%M:%S')}")

        # 1. Fetch Price from Frontend (The "Chart")
        # This is handled inside pipeline.get_market_state() -> fetch_live_price()
        state_vector = await self.pipeline.get_market_state()
        current_price = float(state_vector[0])

        # 2. Check Data (This triggers fetching from 'server' + paying 402s)
        # The 402 payment logic is inside DataConsumer, triggered by pipeline
        data_signals = state_vector[1:11]
        valid_signals = [x for x in data_signals if x > 0.0]
        avg_signal = np.mean(valid_signals) if valid_signals else 0.5

        # 3. Decision
        trend = "NEUTRAL"
        if self.previous_price:
            change = (current_price - self.previous_price) / self.previous_price
            if change > self.min_price_change:
                trend = "UPTREND"
            elif change < -self.min_price_change:
                trend = "DOWNTREND"
        self.previous_price = current_price

        print(f"📊 Market: Price ${current_price:.4f} | Sentiment: {avg_signal:.2f}")

        # 4. Trade
        if trend == "UPTREND" or avg_signal > 0.55:
            self._trigger_trade("USDC", "CRO", 10.0)
        elif trend == "DOWNTREND" or avg_signal < 0.45:
            self._trigger_trade("CRO", "USDC", 10.0)

        return {"action": "HOLD"}

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