import asyncio
import numpy as np
from datetime import datetime

# Import pipeline
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

        # --- PHASE 1: TECHNICAL ANALYSIS (The Chart) ---
        prices = self.pipeline.fetch_chart_history()
        
        if len(prices) < 5:
            print("   ⏳ Waiting for Chart Data (Next.js is compiling/loading)...")
            return

        current_price = prices[-1]
        start_price = prices[0]
        
        # Calculate Trend & Volatility
        trend_pct = (current_price - start_price) / start_price
        volatility = np.std(prices) / np.mean(prices) * 100
        
        print(f"   📊 Chart: Price=${current_price:.4f} | Trend={trend_pct*100:.2f}% | Vol={volatility:.2f}")

        # --- PHASE 2: STRATEGY & DATA BUYING ---
        needed_data = []
        context = "NEUTRAL"
        
        if trend_pct > 0.02: # Up 2%
            context = "BULLISH"
            print("   🚀 Setup: BULLISH Trend Detected. Verifying with Sentiment.")
            needed_data = ["SENTIMENT"]
            
        elif trend_pct < -0.02: # Down 2%
            context = "BEARISH"
            print("   🔻 Setup: BEARISH Trend Detected. Verifying with Whale Data.")
            needed_data = ["ON_CHAIN"]
            
        elif volatility > 1.5: # Volatile
            context = "VOLATILE"
            print("   🚨 Setup: High Volatility. Checking Technicals.")
            needed_data = ["TECHNICAL"]
            
        else:
            context = "FLAT"
            print("   😴 Setup: Market Flat. Forcing checks for 'Flash News'.")
            needed_data = ["NEWS", "SENTIMENT"] # Force buying data to show it works

        # --- PHASE 3: EXECUTION ---
        # Fetch external data (Auto-Pays 402s)
        data_signals = await self.pipeline.fetch_specific_nodes(needed_data)
        
        avg_score = np.mean(data_signals) if data_signals else 0.5
        print(f"   🧠 Data Confirmation Score: {avg_score:.2f}")

        action = "HOLD"
        
        # Decision Matrix
        if context == "BULLISH" and avg_score > 0.5: action = "BUY"
        elif context == "BEARISH" and avg_score < 0.5: action = "SELL"
        elif context == "FLAT" and avg_score > 0.7: action = "BUY"
        elif context == "FLAT": 
            # Force trade for demonstration if we bought data but market is boring
            print("   🎲 [Demo] Market is flat, forcing exploration trade.")
            action = "BUY" 

        print(f"   🎯 FINAL DECISION: {action}")

        if action == "BUY":
            self.trading_engine.execute_swap("USDC", "CRO", 10.0)
        elif action == "SELL":
            self.trading_engine.execute_swap("CRO", "USDC", 100.0)