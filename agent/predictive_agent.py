import asyncio
import numpy as np
from datetime import datetime

try:
    from .data_pipeline import DataPipeline
except ImportError:
    from agent.data_pipeline import DataPipeline

class PredictiveAgent:
    def __init__(self, market_manager, trading_engine, simulation_mode=True):
        self.pipeline = DataPipeline(market_manager)
        self.trading_engine = trading_engine

    async def run_cycle(self):
        print("\n" + "─"*50)
        print(f"🤖 EXPERT AGENT (ETH/USDC) - {datetime.now().strftime('%H:%M:%S')}")

        # 1. READ CHART (ETH PRICE)
        prices = self.pipeline.fetch_chart_history()
        
        if len(prices) < 5:
            print("   ⏳ Waiting for ETH Chart Data...")
            return

        current_price = prices[-1]
        start_price = prices[0]
        
        # 2. METRICS
        trend_pct = ((current_price - start_price) / start_price) * 100
        volatility = np.std(prices[-20:]) if len(prices) > 20 else 0
        
        direction = "FLAT"
        if trend_pct > 0.02: direction = "UP 🟢"
        if trend_pct < -0.02: direction = "DOWN 🔴"

        print(f"   💎 ETH Price: ${current_price:.2f} | Trend: {trend_pct:.3f}% [{direction}]")

        # 3. STRATEGY
        needed_data = []
        if direction == "UP 🟢":
            print("   🚀 Setup: ETH Rally. Checking Sentiment.")
            needed_data = ["SENTIMENT", "NEWS"]
        elif direction == "DOWN 🔴":
            print("   🔻 Setup: ETH Dump. Checking On-Chain Support.")
            needed_data = ["ON_CHAIN"]
        else:
            print("   💤 Setup: ETH Ranging. Scanning News.")
            needed_data = ["NEWS"]

        # 4. DATA & EXECUTION
        data_signals = await self.pipeline.fetch_specific_nodes(needed_data)
        score = np.mean(data_signals) if data_signals else 0.5
        
        print(f"   🧠 Alpha Score: {score:.2f}")

        action = "HOLD"
        if score > 0.6: action = "BUY"
        elif score < 0.4: action = "SELL"
            
        print(f"   🎯 DECISION: {action}")

        # SWAP EXECUTION (Using WETH)
        if action == "BUY":
            self.trading_engine.execute_swap("USDC", "WETH", 50.0) # Buy $50 ETH
        elif action == "SELL":
            self.trading_engine.execute_swap("WETH", "USDC", 0.02) # Sell 0.02 ETH

        return {"action": action}