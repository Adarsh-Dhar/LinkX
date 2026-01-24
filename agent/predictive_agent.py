import asyncio
import numpy as np
import pandas as pd
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
        print("\n" + "─"*65)
        print(f"🧠 EXPERT CONTEXT ANALYSIS - {datetime.now().strftime('%H:%M:%S')}")

        # 1. FETCH & PROCESS DATA (The Tape)
        df = self.pipeline.fetch_candles()
        
        if df is None:
            print("   ⏳ [Tape] Insufficient market data. Collecting candles...")
            return

        current_price = df['close'].iloc[-1]
        
        # 2. INTERNAL TOOLKIT CALCULATIONS
        # RSI (14)
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs)).iloc[-1]

        # Bollinger Band Width
        sma = df['close'].rolling(window=20).mean()
        std = df['close'].rolling(window=20).std()
        bb_width = ((sma + (std * 2)) - (sma - (std * 2)) / sma).iloc[-1] * 100

        # VWAP
        vwap = (df['volume'] * (df['high'] + df['low'] + df['close']) / 3).cumsum() / df['volume'].cumsum()
        vwap_val = vwap.iloc[-1]

        # Volume Delta
        vol_ma = df['volume'].rolling(window=20).mean().iloc[-1]
        vol_current = df['volume'].iloc[-1]
        vol_ratio = vol_current / vol_ma if vol_ma > 0 else 0

        # Trend (5-candle slope)
        trend_slope = (current_price - df['close'].iloc[-5]) / 5
        
        print(f"   📉 Chart: ${current_price:.2f} | RSI: {rsi:.1f} | VWAP: ${vwap_val:.2f}")
        print(f"   📊 Volatility: {bb_width:.3f} | Vol Ratio: {vol_ratio:.2f}x")

        # 3. FORMULATE THESIS & SHOPPING LIST
        hypothesis = "NEUTRAL"
        required_alpha = []

        # SCENARIO A: SQUEEZE BREAKOUT
        if bb_width < 0.5 and vol_ratio > 1.5:
            hypothesis = "BREAKOUT"
            print("   🚀 Setup: Volatility Squeeze with Volume Spike!")
            required_alpha = ["NEWS", "ON_CHAIN"] 

        # SCENARIO B: OVERBOUGHT/OVERSOLD
        elif rsi > 70:
            hypothesis = "SHORT"
            print("   ⚠️ Setup: RSI Overbought. Looking for Top.")
            required_alpha = ["SENTIMENT", "TECHNICAL"]
        elif rsi < 30:
            hypothesis = "LONG"
            print("   💎 Setup: RSI Oversold. Looking for Bounce.")
            required_alpha = ["SENTIMENT", "ON_CHAIN"]
            
        # SCENARIO C: TREND CONTINUATION
        elif current_price > vwap_val and trend_slope > 0:
             hypothesis = "LONG"
             print("   📈 Setup: Price above VWAP. Trend Following.")
             required_alpha = ["ON_CHAIN"]
             
        # SCENARIO D: CONSOLIDATION (The "Chopping" Fix)
        else:
            hypothesis = "ACCUMULATION_WATCH"
            print("   😴 Setup: Market is chopping (Consolidation).")
            print("      👉 Expert Thesis: Checking for hidden whale accumulation or pending news.")
            # Even in chop, we want to know if whales are buying the floor
            required_alpha = ["ON_CHAIN", "NEWS"]

        # 4. ACQUIRE & VERIFY EXTERNAL DATA
        # This will try to buy the data. If it fails (DB issue), 'intel' will be missing keys.
        intel = await self.pipeline.fetch_specific_nodes(required_alpha)
        
        # LOG MISSING DATA EXPLICITLY
        missing_data = [req for req in required_alpha if req not in intel]
        
        if missing_data:
            print(f"   ⚠️ [INCOMPLETE INTELLIGENCE] I cannot make a decision.")
            print(f"      I specifically need the following data sources:")
            for req in missing_data:
                 print(f"      ❌ [MISSING] {req} Provider")
            
            print("   🛑 [DECISION] HOLD. Waiting for data providers to come online.")
            return

        # 5. EXECUTION (Only if we have data)
        score = 0
        for cat, val in intel.items():
            if hypothesis in ["LONG", "BREAKOUT", "ACCUMULATION_WATCH"] and val > 0.6: score += 1
            if hypothesis == "SHORT" and val < 0.4: score += 1
            
        print(f"   ⚖️ Thesis Score: {score}/{len(required_alpha)}")

        if score == len(required_alpha):
            print(f"   ✅ [EXECUTE] {hypothesis} Confirmed.")
            if hypothesis in ["LONG", "BREAKOUT", "ACCUMULATION_WATCH"]:
                self.trading_engine.execute_swap("USDC", "WETH", 50.0)
            elif hypothesis == "SHORT":
                self.trading_engine.execute_swap("WETH", "USDC", 0.1)
        else:
            print("   ⏸️ [ABORT] Data does not confirm hypothesis.")