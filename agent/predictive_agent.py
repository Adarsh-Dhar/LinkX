
import asyncio
from datetime import datetime
import numpy as np


# We keep the pipeline to fetch data
try:
    from .data_pipeline import DataPipeline
except ImportError:
    from agent.data_pipeline import DataPipeline

class PredictiveAgent:
    def __init__(self, market_manager, trading_engine, simulation_mode=True):
        self.pipeline = DataPipeline(market_manager)
        self.trading_engine = trading_engine

    async def run_cycle(self):
        print("\n" + "="*60)
        print(f"🤖 EXPERT AGENT ANALYSIS - {datetime.now().strftime('%H:%M:%S')}")

        # --- STEP 1: MARKET CONTEXT ANALYSIS ---
        prices = self.pipeline.fetch_chart_history()
        
        if len(prices) < 2:
            print("   ⏳ Not enough chart data yet. Waiting...")
            return

        current_price = prices[-1]
        start_price = prices[0]
        
        # Calculate Volatility (Standard Deviation of returns)
        returns = np.diff(prices) / prices[:-1]
        volatility = np.std(returns) if len(returns) > 0 else 0
        
        # Calculate Trend
        trend_pct = (current_price - start_price) / start_price
        
        print(f"   📊 Chart Stats: Price=${current_price:.4f} | Trend={trend_pct*100:.2f}% | Volatility={volatility:.4f}")

        # --- STEP 2: DETERMINE DATA NEEDS ---
        needed_data = []
        context = "NEUTRAL"
        
        if volatility > 0.05: # High Volatility
            context = "VOLATILE"
            print("   🚨 Market is VOLATILE! requesting Risk & Whale data.")
            needed_data = ["TECHNICAL", "ON_CHAIN"]
            
        elif trend_pct > 0.02: # Strong Uptrend
            context = "BULLISH"
            print("   🚀 Market is PUMPING! Requesting Sentiment validation.")
            needed_data = ["SENTIMENT", "NEWS"]
            
        elif trend_pct < -0.02: # Strong Downtrend
            context = "BEARISH"
            print("   🔻 Market is DUMPING! Requesting Whale Volume data.")
            needed_data = ["ON_CHAIN", "NEWS"]
            
        else: # Ranging/Boring
            print("   😴 Market is Flat. Checking News for catalysts.")
            needed_data = ["NEWS"]

        # --- STEP 3: BUY & ANALYZE DATA ---
        # The agent now pays for specific nodes based on the context above
        data_signals = await self.pipeline.fetch_specific_nodes(needed_data)
        
        avg_signal = np.mean(data_signals) if data_signals else 0.5
        print(f"   🧠 Aggregated Data Score: {avg_signal:.2f} (0=Bearish, 1=Bullish)")

        # --- STEP 4: EXECUTE TRADE ---
        action = "HOLD"
        
        if context == "BULLISH" and avg_signal > 0.6:
            action = "BUY"
            print("   ✅ CONFIRMED: Trend is up and Sentiment agrees.")
            
        elif context == "BEARISH" and avg_signal < 0.4:
            action = "SELL"
            print("   ✅ CONFIRMED: Trend is down and On-Chain data agrees.")
            
        elif context == "VOLATILE":
            if avg_signal > 0.8: 
                action = "BUY" # Buying the dip/breakout
            elif avg_signal < 0.2: 
                action = "SELL" # Panic selling
        
        # Execution
        if action == "BUY":
            self.trading_engine.execute_swap("USDC", "CRO", 10.0)
        elif action == "SELL":
            self.trading_engine.execute_swap("CRO", "USDC", 100.0)
        else:
            print("   ⏸️ Decision: HOLD (No edge found)")