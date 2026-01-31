import time
from .tools import OpenRouterClient
from .agent_state_db import AgentStateDB

class PredictiveAgentReAct:
    """
    ReAct-based PredictiveAgent using OpenRouter for reasoning, memory, and model routing.
    Persists memory and last intel timestamp using AgentStateDB.
    """
    SYSTEM_PROMPT = """
    ## ROLE: Institutional Alpha Strategist
    You are an experienced algorithmic trader specializing in the Etherlink/Tezos ecosystem. Your goal is to maximize ROI while strictly minimizing operational overhead (data acquisition costs).

    ## TRADING PROTOCOL:
    1. ANALYZE shared market state (Price/Trend).
    2. CONSULT internal memory of purchased intel.
    3. REASON:
       - Is current data stale? (Age > 5 mins)
       - Is the market in a Regime Shift? (e.g., NORMAL -> CRASH)
       - Is a trade imminent? (If HOLD, do not buy data).
    4. DECIDE: Either USE_CACHE, PURCHASE_INTEL, or ABORT.

    ## ECONOMIC CONSTRAINT:
    Every 402 payment reduces our net profit. You are forbidden from buying data for 'Technical Analysis' if the market trend has not changed since the last purchase.

    ## RESPONSE FORMAT (JSON):
    {
      "thought": "Deep reasoning about current market vs memory",
      "regime": "VOLATILE | TRENDING | STABLE",
      "action": "CACHE | PURCHASE | EXECUTE",
      "target_node": "NodeID or null",
      "confidence": 0.0-1.0
    }
    """


    def __init__(self, pipeline=None, state_path="agent_state.db"):
        self.client = OpenRouterClient()
        self.state = AgentStateDB(state_path)
        self.memory = self.state.memory  # {node_id: {"data": ..., "ts": ...}}
        self.last_regime = None
        self.pipeline = pipeline

    async def run_cycle(self, chart_data, market_nodes):
        # STEP 1: Pre-Assessment (The 'Think' Phase)
        assessment_prompt = self._build_assessment_prompt(chart_data)
        decision = await self.client.route_model(
            phase="assessment",
            prompt=assessment_prompt,
            system_prompt=self.SYSTEM_PROMPT
        )
        print(f"🧠 [Agent Reasoning] {decision['thought']}")

        # STEP 2: Intelligent Data Selection

        intel = {}
        now = time.time()
        if decision['action'] == "PURCHASE":
            node_id = decision['target_node']
            node = next((n for n in market_nodes if n.get('id') == node_id), None)
            if node:
                intel[node_id] = await self.pipeline.purchase_single_tool(node_id)
                self.memory[node_id] = {"data": intel[node_id], "ts": now}
                self.state.memory = self.memory
                self.state.set_last_intel_ts(node_id, now)
        else:
            # Use data from memory if valid
            intel = {k: v['data'] for k, v in self.memory.items() if now - v['ts'] < 300}

        # STEP 3: Neural Brain Execution
        if decision['confidence'] > 0.7:
            await self.execute_trade(decision['regime'], intel)

    def _build_assessment_prompt(self, chart_data):
        # Compose a summary of the current market state and memory
        import json
        prompt = {
            "market_state": chart_data,
            "memory": {k: {"ts": v["ts"]} for k, v in self.memory.items()}
        }
        return json.dumps(prompt)

    async def execute_trade(self, regime, intel):
        # Route to a more powerful model for trade execution
        prompt = f"Regime: {regime}\nIntel: {intel}"
        decision = await self.client.route_model(
            phase="execution",
            prompt=prompt,
            system_prompt="You are a trading agent. Decide and return JSON."
        )
        print(f"[TRADE EXECUTION] {decision}")
import os
import asyncio
import pandas as pd
from datetime import datetime
from .data_pipeline import DataPipeline
from .trading_engine import TradingEngine
from .brain import NeuralBrain

class PredictiveAgent:
    # --- Financial Mandate Methods ---
    def set_limit(self, limit_type, limit_value):
        """
        Set financial limits such as max total spend per trade or monthly allowance.
        limit_type: 'MAX_TOTAL_SPEND_PER_TRADE' or 'MONTHLY_ALLOWANCE'
        limit_value: float
        """
        if limit_type in ["MAX_TOTAL_SPEND_PER_TRADE", "MAX_PRICE_PER_REQUEST"]:
            self.max_total_spend_per_trade = float(limit_value)
            print(f"[Mandate] Max total spend per trade set to {self.max_total_spend_per_trade} USDC")
        elif limit_type == "MONTHLY_ALLOWANCE":
            self.monthly_allowance = float(limit_value)
            print(f"[Mandate] Monthly trading allowance set to {self.monthly_allowance} USDC")
        else:
            print(f"[Mandate] Unknown limit type: {limit_type}")

    def set_refill_logic(self, refill_threshold, refill_amount):
        """
        Set wallet auto-refill logic: when balance < threshold, add refill_amount.
        """
        self.refill_threshold = float(refill_threshold)
        self.refill_amount = float(refill_amount)
        print(f"[Mandate] Will auto-refill wallet with {self.refill_amount} USDC when below {self.refill_threshold} USDC")

    def __init__(self, wallet_manager=None, market_manager=None, trading_engine=None, simulation_mode=False,
                 agent_mode="BALANCED", agent_min_accuracy=7, agent_max_cost=1000000.0):
        self.market_manager = market_manager
        self.engine = trading_engine if trading_engine is not None else TradingEngine(wallet_manager)
        self.pipeline = DataPipeline(self.engine)
        self.brain = NeuralBrain()
        self.simulation_mode = simulation_mode
        self.is_running = False

        # --- Financial Mandate Defaults ---
        self.max_total_spend_per_trade = None  # Enforced per-trade spend limit (set by user)

        # Always load .env.etherlink from workspace root
        from dotenv import load_dotenv
        from pathlib import Path
        load_dotenv(Path(__file__).parent.parent / '.env.etherlink')
        # Read agent config from frontend (constructor arguments)
        self.mode = agent_mode
        self.min_accuracy = int(agent_min_accuracy)
        try:
            self.max_cost = float(agent_max_cost)
        except Exception:
            self.max_cost = 1000000.0
        self.max_total_spend_per_trade = self.max_cost

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
        Enforces self.max_cost as a max total spend per trade (cycle).
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

        max_spend = self.max_cost if self.max_cost is not None else 1000000.0

        for node in scored_nodes:
            node_price = node.get("price", 0)
            # Check if adding THIS node will put us over the dynamic per-trade budget
            if current_total_cost + node_price > max_spend:
                print(f"⚠️ Skipping {node.get('name', node.get('category'))} - would exceed trade limit of {max_spend}")
                continue
            selected_arsenal.append(node)
            current_cumulative_accuracy += node["importance"]
            current_total_cost += node_price
            # STOP once we meet the min_accuracy requirement (The "Adding Up" logic)
            if current_cumulative_accuracy >= self.min_accuracy:
                print(f"   ✅ Target Accuracy Reached: {current_cumulative_accuracy}/{self.min_accuracy}")
                break

        # Debug: Print selected arsenal and total price
        print("[DEBUG] Selected arsenal for this trade (max total spend limit):")
        for n in selected_arsenal:
            print(f"   - {n.get('name', n.get('category'))}: price={n.get('price', 0)} USDC, importance={n.get('importance')}")
        print(f"[DEBUG] Total arsenal price: {sum(n.get('price', 0) for n in selected_arsenal)} USDC (limit: {max_spend})")
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


        # 2. Get all nodes from the pipeline and filter to whitelisted only
        all_nodes = await self.pipeline.refresh_market_knowledge()
        if not all_nodes:
            print("   ⚠️ [AI Arsenal] No nodes available from pipeline.")
            return
        whitelisted_nodes = [n for n in all_nodes if n.get('whitelisted') is True and n.get('status') == 'active']
        if not whitelisted_nodes:
            print("   ⚠️ [AI Arsenal] No whitelisted nodes available from pipeline.")
            return

        # 3. Choose the Arsenal using the AI Optimizer (only whitelisted nodes)
        optimized_arsenal = self.optimize_node_selection(
            market_nodes=whitelisted_nodes,
            market_state=market_state,
            mode=self.mode
        )

        # No daily/cumulative spend check: only enforce per-trade (per-cycle) budget via optimizer

        print(f"🤖 AI Arsenal: Selected {len(optimized_arsenal)} nodes for this trade.")
        if len(optimized_arsenal) > 0:
            print("   📝 Node Relevance Scores:")
            for node in optimized_arsenal:
                print(f"      - {node.get('name', node.get('category'))}: category={node.get('category')}, importance={node.get('importance')}")

        # ...existing code...

        # 4. Fetch the chosen nodes (pass node objects)
        total_cost = sum(n.get('price', 0) for n in optimized_arsenal)
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
                risk_amount = 200.0 if abs(confidence) > 0.9 else 50.0
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