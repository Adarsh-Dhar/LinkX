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
        # This condition now enforces your '20 discrete minutes' rule
        if df is None or len(df) < 20:
            print("   ⏳ [Tape] Synchronizing real-time minutes (Waiting for 20/20)...")
            return

        curr = df['close'].iloc[-1]
        
        # 2. METRICS
        sma = df['close'].rolling(20).mean()
        std = df['close'].rolling(20).std()
        bb_width = ((sma + (std * 2)) - (sma - (std * 2))) / sma
        
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs)).iloc[-1]
        
        vol_ma = df['volume'].rolling(20).mean().iloc[-1]
        vol_ratio = df['volume'].iloc[-1] / vol_ma if vol_ma > 0 else 0
        
        print(f"   📉 Price: ${curr:.2f} | RSI: {rsi:.1f} | Vol Ratio: {vol_ratio:.2f}x")

        # 3. SITUATION MAPPING
        situation = "NOISE"
        toolkit_names = []

        if rsi > 70 and vol_ratio > 1.5:
            situation = "PARABOLIC_PUMP"
            toolkit_names = ["Whale Alert", "Social Pulse"] 
        elif rsi < 30:
            situation = "LIQUIDATION_CASCADE"
            toolkit_names = ["Chainlink Sentinel", "Sentiment Surge"]
        elif bb_width.iloc[-1] < 0.005:
            situation = "VOLATILITY_SQUEEZE"
            toolkit_names = ["Macro News AI", "Neural Oracle"]
        elif abs(df['close'].pct_change().iloc[-1]) > 0.005 and vol_ratio < 0.8:
            situation = "PRICE_ANOMALY"
            toolkit_names = ["Quantum Scanner", "Flash Arbitrage"]
        else:
            situation = "ESTABLISHED_TREND"
            toolkit_names = ["On-Chain Watcher"]

        print(f"   🧠 Context: {situation}")
        print(f"   📋 [REQUIREMENTS] Ideal Arsenal: {', '.join(toolkit_names)}")

        # 4. DYNAMIC FETCH (With Fallback)
        intel = await self.pipeline.fetch_dynamic_tools(toolkit_names)

        # Handle missing data gracefully
        acquired_count = len(intel)
        needed_count = len(toolkit_names)

        risk_multiplier = 1.0
        decision_mode = "STANDARD"

        if needed_count > 0 and acquired_count == 0:
            decision_mode = "BLIND_TECHNICALS"
            risk_multiplier = 0.1 # Trade 10% size only
            print("   ⚠️ [SKEPTICAL] Zero external data found. Relying purely on Chart.")
        elif acquired_count < needed_count:
            decision_mode = "PARTIAL_INTEL"
            risk_multiplier = 0.5 # Trade 50% size
            print(f"   ⚠️ [CAUTION] Only {acquired_count}/{needed_count} tools available. Reducing size.")
        
        # 6. SCORING LOGIC
        score = 0
        # If we have NO data, we infer score from the chart itself (Fallback)
        if decision_mode == "BLIND_TECHNICALS":
            if situation == "PARABOLIC_PUMP": score = -1 # Assume fade
            elif situation == "LIQUIDATION_CASCADE": score = 1 # Assume bounce
            elif situation == "ESTABLISHED_TREND": score = 1
        else:
            # Standard Data Scoring
            for name, val in intel.items():
                print(f"      ✅ Report from {name}: {val:.2f}")
                if val > 0.6: score += 1
                elif val < 0.4: score -= 1

        # 7. EXECUTION
        action = "HOLD"
        
        # Bullish Situations
        if situation in ["LIQUIDATION_CASCADE", "VOLATILITY_SQUEEZE", "ESTABLISHED_TREND"]:
            if score > 0: action = "BUY"
            
        # Bearish/Fading Situations
        elif situation in ["PARABOLIC_PUMP", "PRICE_ANOMALY"]:
            if score < 0: action = "SELL"
            
        # Specific overrides for Blind Mode
        if decision_mode == "BLIND_TECHNICALS" and situation == "NOISE":
            action = "HOLD"

        print(f"   🎯 Decision: {action} (Mode: {decision_mode}, Risk: {risk_multiplier}x)")

        if action == "BUY":
            amount = 100.0 * risk_multiplier
            print(f"   🚀 Executing BUY for {amount} USDC")
            self.trading_engine.execute_swap("USDC", "WETH", amount)
        elif action == "SELL":
            amount = 0.1 * risk_multiplier
            print(f"   📉 Executing SELL for {amount} WETH")
            self.trading_engine.execute_swap("WETH", "USDC", amount)