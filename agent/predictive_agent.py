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
    # Map market situations to required nodes and consensus thresholds
    SITUATION_REQUIREMENTS = {
        "PARABOLIC_PUMP": {
            "nodes": ["Whale Alert", "Social Pulse", "Chainlink Sentinel", "Sentiment Surge", "Macro News AI"],
            "consensus": 0.8
        },
        "LIQUIDATION_CASCADE": {
            "nodes": ["Chainlink Sentinel", "Sentiment Surge", "Whale Alert"],
            "consensus": 0.7
        },
        "VOLATILITY_SQUEEZE": {
            "nodes": ["Macro News AI", "Neural Oracle", "On-Chain Watcher"],
            "consensus": 0.6
        },
        "PRICE_ANOMALY": {
            "nodes": ["Quantum Scanner", "Flash Arbitrage", "Chainlink Sentinel"],
            "consensus": 0.7
        },
        "ESTABLISHED_TREND": {
            "nodes": ["On-Chain Watcher", "Macro News AI"],
            "consensus": 0.5
        },
        "NOISE": {
            "nodes": ["On-Chain Watcher"],
            "consensus": 0.5
        }
    }

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
        # Determine situation
        if rsi > 70 and vol_ratio > 1.5:
            situation = "PARABOLIC_PUMP"
        elif rsi < 30:
            situation = "LIQUIDATION_CASCADE"
        elif bb_width.iloc[-1] < 0.005:
            situation = "VOLATILITY_SQUEEZE"
        elif abs(df['close'].pct_change().iloc[-1]) > 0.005 and vol_ratio < 0.8:
            situation = "PRICE_ANOMALY"
        else:
            situation = "ESTABLISHED_TREND"


        toolkit_names = self.SITUATION_REQUIREMENTS[situation]["nodes"]
        consensus_threshold = self.SITUATION_REQUIREMENTS[situation]["consensus"]

        print(f"   🧠 Context: {situation}")
        print(f"   📋 [REQUIREMENTS] Ideal Arsenal: {', '.join(toolkit_names)}")
        print(f"   📊 Consensus Threshold: {consensus_threshold*100:.0f}%")

        # 4. FILTERED FETCH FROM DB (Proactive: Fetch All, Filter, Buy)
        result = await self.pipeline.fetch_dynamic_tools(toolkit_names)
        if result is None:
            intel, fetch_failed = {}, True
        else:
            intel, fetch_failed = result

        acquired_count = len(intel)
        needed_count = len(toolkit_names)

        # Skeptical check: must acquire all required nodes for this situation
        if needed_count > 0 and (fetch_failed or acquired_count < needed_count):
            print(f"   ⚠️ [SKEPTICAL] Incomplete arsenal. Required {needed_count}, acquired {acquired_count}. Returning HOLD.")
            self.log_decision("HOLD", "INCOMPLETE_INTEL", f"Required {needed_count}, but only bought {acquired_count}")
            return

        # 5. Consensus calculation
        total_signals = 0
        node_reports = {}
        now = datetime.utcnow()
        stale_nodes = []
        for name, report in intel.items():
            if isinstance(report, tuple) and len(report) == 2:
                val, ts = report
                age_sec = (now - ts).total_seconds() if isinstance(ts, datetime) else None
                if age_sec is not None and age_sec > 60:
                    stale_nodes.append(name)
                node_reports[name] = {"value": val, "age_sec": age_sec}
            else:
                val = report
                node_reports[name] = {"value": val, "age_sec": None}
            print(f"      ✅ Report from {name}: {val:.2f} (Age: {node_reports[name]['age_sec'] if node_reports[name]['age_sec'] is not None else 'N/A'}s)")
            if val is not None:
                if val > 0.6:
                    total_signals += 1
                elif val < 0.4:
                    total_signals -= 1

        # Consensus is normalized by number of acquired nodes
        confidence = total_signals / acquired_count if acquired_count > 0 else 0
        print(f"   📈 Consensus: {confidence:.2f} | Total Signals: {total_signals} | Nodes: {acquired_count}")
        print(f"   📝 Node Reports: {node_reports}")

        # Data Age Check: If any node is stale, re-verify others
        if stale_nodes:
            print(f"   ⏳ [DATA AGE] Stale node data detected: {', '.join(stale_nodes)}. Re-verifying other nodes...")
            self.log_decision("HOLD", "STALE_DATA", f"Stale nodes: {', '.join(stale_nodes)}")
            return

        # Threshold-based execution
        action = "HOLD"
        if confidence >= consensus_threshold:
            action = "BUY"
        elif confidence <= -consensus_threshold:
            action = "SELL"

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