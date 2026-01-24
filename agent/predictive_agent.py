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
        print("\n" + "═"*70)
        print(f"♟️  EXPERT TRADER CONTEXT ENGINE - {datetime.now().strftime('%H:%M:%S')}")

        # 1. READ THE TAPE
        df = self.pipeline.fetch_candles()
        if df is None or len(df) < 20:
            print("   ⏳ [Tape] Insufficient market data. Collecting candles...")
            return

        curr = df['close'].iloc[-1]
        
        # 2. COMPUTE METRICS
        # Volatility (BB Width)
        sma = df['close'].rolling(20).mean()
        std = df['close'].rolling(20).std()
        bb_width = ((sma + (std * 2)) - (sma - (std * 2))) / sma
        # Momentum (RSI)
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs)).iloc[-1]
        # Volume
        vol_ma = df['volume'].rolling(20).mean().iloc[-1]
        vol_ratio = df['volume'].iloc[-1] / vol_ma if vol_ma > 0 else 0
        
        print(f"   📉 Price: ${curr:.2f} | RSI: {rsi:.1f} | Vol Ratio: {vol_ratio:.2f}x")

        # 3. SITUATION MAPPING (Identify Missing Data)
        situation = "NOISE"
        toolkit_names = [] # This list will be sent to the pipeline to find in DB

        # A: PUMP -> Check Whales & Retail Hype
        if rsi > 70 and vol_ratio > 1.5:
            situation = "PARABOLIC_PUMP"
            # Exact names from your DB Seed
            toolkit_names = ["Whale Alert", "Social Pulse"] 

        # B: CRASH -> Check Safety & Peak Fear
        elif rsi < 30:
            situation = "LIQUIDATION_CASCADE"
            toolkit_names = ["Chainlink Sentinel", "Sentiment Surge"]

        # C: SQUEEZE -> Check Catalysts
        elif bb_width.iloc[-1] < 0.005:
            situation = "VOLATILITY_SQUEEZE"
            toolkit_names = ["Macro News AI", "Neural Oracle"]

        # D: GLITCH -> Check Anomalies
        elif abs(df['close'].pct_change().iloc[-1]) > 0.005 and vol_ratio < 0.8:
            situation = "PRICE_ANOMALY"
            toolkit_names = ["Quantum Scanner", "Flash Arbitrage"]

        # E: TREND -> Check Flows
        else:
            situation = "ESTABLISHED_TREND"
            toolkit_names = ["On-Chain Watcher"]

        print(f"   🧠 Context: {situation}")
        print(f"   📋 [REQUIREMENTS] I need data from: {', '.join(toolkit_names)}")

        # 4. FETCH DATA (This triggers the DB Lookup + Payment)
        intel = await self.pipeline.fetch_dynamic_tools(toolkit_names)
        
        # 5. VERIFY & EXECUTE
        # If we didn't get data (payment failed or node missing), ABORT.
        missing = [t for t in toolkit_names if t not in intel]
        if missing:
            print(f"   🛑 [BLOCK] Missing critical data from: {missing}")
            print("   🛡️ [Risk Protocol] Trade Aborted. Waiting for data providers.")
            return

        # Simple Scoring for Demo
        score = 0
        for name, val in intel.items():
            print(f"      ✅ Report from {name}: {val:.2f}")
            # Logic: If trend is UP, we want High scores. If trend DOWN, we want Low scores.
            if situation in ["PARABOLIC_PUMP", "LIQUIDATION_CASCADE"] and val < 0.4: score += 1
            elif val > 0.6: score += 1

        action = "HOLD"
        if score == len(toolkit_names):
            print(f"   🚀 [EXECUTE] Data confirms thesis.")
            action = "BUY" if situation != "PARABOLIC_PUMP" else "SELL"
            
            if action == "BUY":
                self.trading_engine.execute_swap("USDC", "WETH", 50.0)
            else:
                self.trading_engine.execute_swap("WETH", "USDC", 0.1)
        else:
            print("   ⏸️ [HOLD] Data contradicts thesis.")