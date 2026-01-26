
import asyncio
import numpy as np
import pandas as pd
from datetime import datetime
import os
from agent.situational_logic import SITUATION_WEIGHTS

try:
    from .data_pipeline import DataPipeline
except ImportError:
    from agent.data_pipeline import DataPipeline

class PredictiveAgent:
    def optimize_node_selection(self, market_nodes, situation, mode="BALANCED", min_accuracy=15, max_cost=50.0):
        """
        Selects nodes based on situation, mode, min_accuracy, and max_cost.
        Returns a list of selected node dicts.
        """
        # 1. Assign importance from SITUATION_WEIGHTS
        cat_weights = SITUATION_WEIGHTS.get(situation, {})
        for node in market_nodes:
            node["importance"] = cat_weights.get(node["category"], 1)
            node["price"] = float(node.get("price", 0.0))
            node["efficiency"] = node["importance"] / max(node["price"], 0.1)
        # 2. Sort and select nodes by mode
        selected = []
        total_cost, total_accuracy = 0.0, 0
        sorted_nodes = []
        if mode == "ACCURATE":
            sorted_nodes = sorted(market_nodes, key=lambda n: -n["importance"])
            for node in sorted_nodes:
                if total_cost + node["price"] > max_cost:
                    break
                selected.append(node)
                total_cost += node["price"]
        elif mode == "ECONOMY":
            sorted_nodes = sorted(market_nodes, key=lambda n: -n["efficiency"])
            for node in sorted_nodes:
                if total_accuracy >= min_accuracy:
                    break
                selected.append(node)
                total_accuracy += node["importance"]
        else:  # BALANCED
            sorted_nodes = sorted(market_nodes, key=lambda n: -n["efficiency"])
            for node in sorted_nodes:
                if total_cost + node["price"] > max_cost/2 and total_accuracy >= min_accuracy/2:
                    break
                selected.append(node)
                total_cost += node["price"]
                total_accuracy += node["importance"]
        return selected

    def cost_accuracy_graph(self, market_nodes, situation):
        """
        Returns array of {nodes_count, cumulative_cost, cumulative_accuracy} for graphing.
        """
        cat_weights = SITUATION_WEIGHTS.get(situation, {})
        for node in market_nodes:
            node["importance"] = cat_weights.get(node["category"], 1)
            node["price"] = float(node.get("price", 0.0))
            node["efficiency"] = node["importance"] / max(node["price"], 0.1)
        sorted_nodes = sorted(market_nodes, key=lambda n: -n["efficiency"])
        arr = []
        cost, acc = 0.0, 0
        for i, node in enumerate(sorted_nodes, 1):
            cost += node["price"]
            acc += node["importance"]
            arr.append({"nodes_count": i, "cumulative_cost": cost, "cumulative_accuracy": acc})
        return arr
    # Map market situations to consensus thresholds only (arsenal is now dynamic)
    SITUATION_REQUIREMENTS = {
        "PARABOLIC_PUMP": {"consensus": 0.8},
        "LIQUIDATION_CASCADE": {"consensus": 0.7},
        "VOLATILITY_SQUEEZE": {"consensus": 0.6},
        "PRICE_ANOMALY": {"consensus": 0.7},
        "ESTABLISHED_TREND": {"consensus": 0.5},
        "NOISE": {"consensus": 0.5},
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

    async def run_cycle(self, min_accuracy=15, max_cost=50.0, mode="BALANCED"):
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

        # 4. Fetch all nodes and optimize selection
        all_nodes = await self.pipeline.refresh_market_knowledge()
        selected_nodes = self.optimize_node_selection(all_nodes, situation, mode, min_accuracy, max_cost)
        toolkit_names = [n["name"] for n in selected_nodes]
        # Allow override via environment variable
        env_threshold = os.getenv("CONSENSUS_THRESHOLD")
        if env_threshold is not None:
            try:
                consensus_threshold = float(env_threshold)
            except ValueError:
                consensus_threshold = self.SITUATION_REQUIREMENTS.get(situation, {}).get("consensus", 0.7)
        else:
            consensus_threshold = self.SITUATION_REQUIREMENTS.get(situation, {}).get("consensus", 0.7)

        print(f"   🧠 Context: {situation}")
        print(f"   📋 [OPTIMIZED] Arsenal: {', '.join(toolkit_names)}")
        print(f"   📊 Consensus Threshold: {consensus_threshold*100:.0f}%")

        # 5. FILTERED FETCH FROM DB (Proactive: Fetch All, Filter, Buy)
        result = await self.pipeline.fetch_dynamic_tools(toolkit_names)
        if result is None:
            intel, fetch_failed = {}, True
        else:
            intel, fetch_failed = result

        acquired_count = len(intel)
        needed_count = len(toolkit_names)
        if needed_count > 0 and (fetch_failed or acquired_count < needed_count):
            print(f"   ⚠️ [SKEPTICAL] Incomplete arsenal. Required {needed_count}, acquired {acquired_count}. Returning HOLD.")
            self.log_decision("HOLD", "INCOMPLETE_INTEL", f"Required {needed_count}, but only bought {acquired_count}")
            return

        # 6. Weighted Consensus calculation
        node_reports = {}
        now = datetime.utcnow()
        stale_nodes = []
        weighted_sum = 0.0
        total_weight = 0.0
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
            # Find node weight (importance)
            node_weight = 1
            for n in selected_nodes:
                if n["name"] == name:
                    node_weight = n.get("importance", 1)
                    break
            # Signal binning
            signal = 0
            if val is not None:
                if val > 0.6:
                    signal = 1
                elif val < 0.4:
                    signal = -1
            weighted_sum += signal * node_weight
            total_weight += node_weight
            print(f"      ✅ Report from {name}: {val:.2f} (Age: {node_reports[name]['age_sec'] if node_reports[name]['age_sec'] is not None else 'N/A'}s, Weight: {node_weight})")

        confidence = weighted_sum / total_weight if total_weight > 0 else 0
        print(f"   📈 Weighted Consensus: {confidence:.2f} | Weighted Sum: {weighted_sum} | Total Weight: {total_weight}")
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