import os
import asyncio
import pandas as pd
from datetime import datetime
from .data_pipeline import DataPipeline
from .trading_engine import TradingEngine
from .brain import NeuralBrain

class PredictiveAgent:

    def __init__(self, wallet_manager=None, market_manager=None, trading_engine=None, simulation_mode=False):
        self.market_manager = market_manager
        self.engine = trading_engine if trading_engine is not None else TradingEngine(wallet_manager)
        self.pipeline = DataPipeline(self.engine)
        self.brain = NeuralBrain()
        self.simulation_mode = simulation_mode
        self.is_running = False

        # Read agent config from environment variables
        self.mode = os.getenv("AGENT_MODE", "BALANCED")
        self.min_accuracy = int(os.getenv("AGENT_MIN_ACCURACY", "7"))
        # No default daily spend limit; unlimited unless set by user
        max_cost_env = os.getenv("AGENT_MAX_COST", None)
        min_allowed_cost = 10.0
        if max_cost_env is not None:
            try:
                parsed = float(max_cost_env)
                self.max_cost = parsed if parsed >= min_allowed_cost else 100.0
            except Exception:
                self.max_cost = 100.0
        else:
            self.max_cost = 100.0

        # --- Human override/intent-driven attributes ---
        self.manual_command = None  # e.g. {'type': 'trade', 'side': 'BUY', 'amount': 50.0}
        self.paused = False
        self.block_data_purchases = False  # If True, block all data purchases for the rest of the day

    def calculate_ai_importance(self, node_category, market_state):
        """
        Returns a high score (8-10) only when the data is vital, and a low score (1-3) when the data is noise.
        """
        rsi = market_state.get('rsi', 50)
        vol_ratio = market_state.get('vol_ratio', 1)
        bb_width = market_state.get('bb_width', 0.05)

        # 1. Macro/News is only relevant during "Squeezes" (low volatility)
        if bb_width < 0.02:
            if node_category in ["Macro News AI", "Neural Oracle"]:
                return 10

        # 2. Whale/Volume data is only relevant during High Volume
        if vol_ratio > 2.5:
            if node_category == "Whale Alert":
                return 10
            if node_category == "Social Pulse":
                return 8

        # 3. Liquidation data is only relevant at RSI extremes
        if rsi > 75 or rsi < 25:
            if node_category == "Chainlink Sentinel":
                return 10

        # 4. Baseline Technicals (always relevant but medium priority)
        if node_category == "Technical":
            return 7

        return 2  # Low relevance for everything else in this specific context

    def optimize_node_selection(self, market_nodes, market_state, mode="BALANCED"):
        """
        Cumulative Optimization: Adds nodes one by one until the 
        SUM of their importance scores meets the target.
        """
        scored_nodes = []
        for node in market_nodes:
            importance = self.calculate_ai_importance(node.get("category"), market_state)
            node["importance"] = importance
            scored_nodes.append(node)

        # 1. Sort by Efficiency (Importance per USDC) to get the best value first
        # Use 0.1 as a floor for price to avoid division by zero
        scored_nodes.sort(key=lambda n: n["importance"] / max(0.1, n.get("price", 0)), reverse=True)

        selected_arsenal = []
        current_cumulative_accuracy = 0
        current_total_cost = 0

        # 2. Accumulate nodes until we hit the target from environment variables
        for node in scored_nodes:
            # Only check budget if max_cost is set
            if self.max_cost is not None:
                if current_total_cost + node.get("price", 0) > self.max_cost:
                    continue
            # Add the node to the arsenal
            selected_arsenal.append(node)
            current_cumulative_accuracy += node["importance"]
            current_total_cost += node.get("price", 0)

            # 3. STOP once we meet the min_accuracy requirement (The "Adding Up" logic)
            if current_cumulative_accuracy >= self.min_accuracy:
                print(f"   ✅ Target Accuracy Reached: {current_cumulative_accuracy}/{self.min_accuracy}")
                break

        # Final check: If we couldn't reach minAccuracy even with all nodes or budget limits
        if current_cumulative_accuracy < self.min_accuracy and mode != "ECONOMY":
            print(f"   ⚠️ Could only reach {current_cumulative_accuracy} accuracy within budget.")
            # Optional: return empty if you don't want to trade on low-confidence data
            # return [] 

        return selected_arsenal

    def identify_context(self, df):
        """Analyze indicators to define the market scene."""
        # Defensive: handle missing columns
        last_rsi = df['rsi'].iloc[-1] if 'rsi' in df.columns else None
        last_vol_ratio = df['vol_ratio'].iloc[-1] if 'vol_ratio' in df.columns else None

        if last_vol_ratio is not None and last_vol_ratio < 0.5:
            return "VOLATILITY_SQUEEZE"
        elif last_rsi is not None and (last_rsi < 20 or last_rsi > 80):
            return "LIQUIDATION_CASCADE"
        return "NORMAL_GROWTH"

    async def run_cycle(self):
        """The core 4-step loop: Scene -> Arsenal -> Purchase -> Trade"""
        print(f"\n══════════════════════════════════════════════════════════════")
        print(f"♟️  PREDICTIVE AGENT CYCLE - {datetime.now().strftime('%H:%M:%S')}")
        from agent.wallet_manager import can_spend, add_spend, get_daily_spend

        # --- Block all data purchases if flag is set ---
        if self.block_data_purchases:
            print("🛑 Data purchases are currently blocked by human override. Skipping cycle.")
            return

        # --- HUMAN OVERRIDE/INTENT CHECKS ---
        if self.paused:
            print("⏸️  AGENT IS PAUSED: Skipping autonomous trade check.")
            return

        if self.manual_command:
            cmd = self.manual_command
            print(f"🚀 HUMAN INTERFERENCE: Executing manual {cmd.get('side', 'BUY')} for {cmd.get('amount', 50.0)} USDC...")
            if cmd.get('type') == 'trade':
                side = cmd.get('side', 'BUY')
                amount = cmd.get('amount', 50.0)
                if hasattr(self, 'engine') and self.engine:
                    tx_hash = self.engine.execute_swap("USDC", "WCRO", amount)
                    if tx_hash:
                        print(f"✅ [Manual Trade Success] Tx Hash: {tx_hash}")
                else:
                    print("❌ No trading engine available for manual command.")
            # Clear manual command after execution
            self.manual_command = None
            return

        # STEP 1: READ THE TAPE (Free Data)
        df = self.pipeline.fetch_candles()
        if df is None or len(df) < 20:
            print("   ⏳ [Tape] Waiting for 20 minutes of market data synchronization...")
            return

        # --- AI-POWERED NODE SELECTION ---
        # 1. Capture current market state for the AI Scorer
        rsi = df['rsi'].iloc[-1] if 'rsi' in df.columns else 50
        vol_ratio = df['vol_ratio'].iloc[-1] if 'vol_ratio' in df.columns else 1
        bb_width = df['bb_width'].iloc[-1] if 'bb_width' in df.columns else 0.05
        market_state = {'rsi': rsi, 'vol_ratio': vol_ratio, 'bb_width': bb_width}

        # 2. Get all nodes from the pipeline
        all_nodes = await self.pipeline.refresh_market_knowledge()
        if not all_nodes:
            print("   ⚠️ [AI Arsenal] No nodes available from pipeline.")
            return

        # 3. Choose the Arsenal using the AI Optimizer
        optimized_arsenal = self.optimize_node_selection(
            market_nodes=all_nodes,
            market_state=market_state,
            mode=self.mode
        )

        # Optional: Add a check here for max_cost if your optimizer doesn't handle it yet
        current_total_cost = sum(n.get('price', 0) for n in optimized_arsenal)
        if self.max_cost is not None and current_total_cost > self.max_cost:
            print(f"⚠️ [Budget] Selected nodes cost {current_total_cost} USDC, exceeding limit of {self.max_cost}")
            print("🛑 Budget exceeded. Blocking all further data purchases until explicitly unblocked.")
            self.block_data_purchases = True
            return

        print(f"🤖 AI Arsenal: Selected {len(optimized_arsenal)} nodes for this trade.")
        if len(optimized_arsenal) > 0:
            print("   📝 Node Relevance Scores:")
            for node in optimized_arsenal:
                print(f"      - {node.get('name', node.get('category'))}: category={node.get('category')}, importance={node.get('importance')}")


        # --- Enforce daily spend limit before any paid data purchase ---

        total_cost = sum(n.get('price', 0) for n in optimized_arsenal)
        # Only enforce limit if set
        if total_cost > 0 and self.max_cost is not None:
            if not can_spend(total_cost, max_cost=self.max_cost):
                print(f"🛑 Daily USDC spend limit reached ({get_daily_spend()} / {self.max_cost}). Blocking further data purchases today.")
                self.block_data_purchases = True
                return

        # 4. Fetch the chosen nodes (pass node objects)
        intel, failure_flag = await self.pipeline.fetch_dynamic_tools(optimized_arsenal)
        # If payment succeeded, record the spend
        if total_cost > 0 and not failure_flag:
            add_spend(total_cost)

        if failure_flag or len(intel) < len(optimized_arsenal):
            print(f"   ⚠️ [Skeptical] Failed to buy full arsenal. found {len(intel)}/{len(optimized_arsenal)} tools.")
            return

        # --- Weighted Decision Making ---
        if len(intel) > 0:
            total_weighted_signal = 0
            sum_of_weights = 0
            print("   📝 Node Scores:")
            for category, signal in intel.items():
                # Try to match node by both category and name for robustness
                node = next((n for n in optimized_arsenal if n.get('category') == category or n.get('name') == category), None)
                if node and 'importance' in node:
                    weight = node['importance']
                else:
                    print(f"      [DEBUG] Could not find node for category '{category}' in optimized_arsenal, defaulting weight to 2. Arsenal: {[n.get('category') for n in optimized_arsenal]}")
                    weight = 2
                # If signal is a Signal object, extract its value
                if hasattr(signal, 'value'):
                    signal_value = signal.value
                else:
                    signal_value = signal
                # Handle NoneType signal values gracefully
                if signal_value is None:
                    print(f"      [WARN] Signal value for {category} is None. Skipping in consensus.")
                    continue
                score = (signal_value - 0.5) * 2
                print(f"      - {category}: weight={weight}")
                total_weighted_signal += (score * weight)
                sum_of_weights += weight
            confidence = total_weighted_signal / sum_of_weights if sum_of_weights > 0 else 0
            decision = "BUY" if confidence > 0.2 else ("SELL" if confidence < -0.2 else "HOLD")
            print(f"   🎯 [Decision] {decision} (Confidence: {confidence:.2f})")

            if decision in ["BUY", "SELL"] and abs(confidence) > 0.75:
                risk_amount = 100.0 if abs(confidence) > 0.9 else 50.0
                print(f"   🚀 Executing {decision} for {risk_amount} USDC...")
                tx_hash = self.engine.execute_swap("USDC", "WCRO", risk_amount)
                if tx_hash:
                    print(f"   ✅ [Success] Tx Hash: {tx_hash}")

    async def run_loop(self):
        self.is_running = True
        while self.is_running:
            try:
                await self.run_cycle()
            except Exception as e:
                print(f"   ❌ [Loop Error] {e}")
            await asyncio.sleep(15) # Pulse every 15 seconds