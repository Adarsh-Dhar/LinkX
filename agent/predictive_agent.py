import asyncio
import numpy as np
import pandas as pd
from datetime import datetime
import os

try:
    from .data_pipeline import DataPipeline
except ImportError:
    from agent.data_pipeline import DataPipeline

class PredictiveAgent:
    async def execute_trade(self, action, risk_factor=1.0):
        """
        Execute a forced BUY or SELL action with the given risk factor.
        """
        if action == "BUY":
            amount = 100.0 * risk_factor
            print(f"   🚀 [FORCED] Executing BUY for {amount} USDC")
            tx_hash = self.trading_engine.execute_swap("USDC", "WETH", amount)
            if tx_hash:
                self.log_decision("BUY", "SUCCESS", f"Tx: {tx_hash}")
            else:
                print(f"   ⚠️ [TRADE_FAILED] Agent aborting cycle due to execution error.")
                self.log_decision("BUY", "FAILED", "Execution engine returned no hash")
        elif action == "SELL":
            amount = 0.1 * risk_factor
            print(f"   📉 [FORCED] Executing SELL for {amount} WETH")
            tx_hash = self.trading_engine.execute_swap("WETH", "USDC", amount)
            if tx_hash:
                self.log_decision("SELL", "SUCCESS", f"Tx: {tx_hash}")
            else:
                print(f"   ⚠️ [TRADE_FAILED] Agent aborting cycle due to execution error.")
                self.log_decision("SELL", "FAILED", "Execution engine returned no hash")
        else:
            print(f"   ⚠️ [FORCED] Unknown action: {action}")
            self.log_decision(action, "FAILED", "Unknown forced action")

    def log_decision(self, action, status, details):
        """Log trade decision (stub: print, or extend to file/db as needed)."""
        print(f"[DecisionLog] {action} | {status} | {details}")

    def __init__(self, market_manager, trading_engine, simulation_mode=True):
        self.pipeline = DataPipeline(market_manager)
        self.trading_engine = trading_engine

    async def run_cycle(self):
        print("\n" + "═"*70)
        print(f"♟️  EXPERT TRADER CONTEXT ENGINE - {datetime.now().strftime('%H:%M:%S')}")
        decision_mode = "STANDARD"
        risk_multiplier = 1.0

        # --- FORCE_ACTION OVERRIDE BLOCK ---
        force_action = os.getenv("FORCE_ACTION")
        if force_action == "SELL":
            print(f"🚨 [OVERRIDE] Manual SELL triggered via environment variable.")
            await self.execute_trade("SELL", risk_factor=1.0)
            return  # End cycle after forced trade
        elif force_action == "BUY":
            print(f"🚨 [OVERRIDE] Manual BUY triggered via environment variable.")
            await self.execute_trade("BUY", risk_factor=1.0)
            return  # End cycle after forced trade
        # --- END OVERRIDE BLOCK ---

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


        # 4. FILTERED FETCH FROM DB (Proactive: Fetch All, Filter, Buy)
        # This call now performs the 'Fetch All -> Filter -> Buy' logic
        result = await self.pipeline.fetch_dynamic_tools(toolkit_names)
        if result is None:
            intel, fetch_failed = {}, True
        else:
            intel, fetch_failed = result

        acquired_count = len(intel)
        needed_count = len(toolkit_names)

        # NEW REQUIREMENT: Only proceed if all filtered tools are purchased
        if needed_count > 0 and (fetch_failed or acquired_count < needed_count):
            print(f"   ⚠️ [SKEPTICAL] Incomplete arsenal. Buying data failed for required nodes.")
            self.log_decision("HOLD", "INCOMPLETE_INTEL", f"Required {needed_count}, but only bought {acquired_count}")
            return

        # 5. CONCLUSION (Only proceeds if paid data is present)
        score = 0
        for name, val in intel.items():
            print(f"      ✅ Report from {name}: {val:.2f}")
            if val > 0.6: score += 1
            elif val < 0.4: score -= 1

        # 6. EXECUTION
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
            tx_hash = self.trading_engine.execute_swap("USDC", "WETH", amount)
            if tx_hash:
                self.log_decision("BUY", "SUCCESS", f"Tx: {tx_hash}")
            else:
                print(f"   ⚠️ [TRADE_FAILED] Agent aborting cycle due to execution error.")
                self.log_decision("BUY", "FAILED", "Execution engine returned no hash")
        elif action == "SELL":
            amount = 0.1 * risk_multiplier
            print(f"   📉 Executing SELL for {amount} WETH")
            tx_hash = self.trading_engine.execute_swap("WETH", "USDC", amount)
            if tx_hash:
                self.log_decision("SELL", "SUCCESS", f"Tx: {tx_hash}")
            else:
                print(f"   ⚠️ [TRADE_FAILED] Agent aborting cycle due to execution error.")
                self.log_decision("SELL", "FAILED", "Execution engine returned no hash")