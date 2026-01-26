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

    def calculate_ai_importance(self, node_category, market_state):
        """
        AI-powered logic to determine how important a node is 
        given the current technical state.
        """
        rsi = market_state.get('rsi', 50)
        vol_ratio = market_state.get('vol_ratio', 1)
        bb_width = market_state.get('bb_width', 0.05)

        # AI logic: If RSI is extreme, 'Chainlink Sentinel' (liquidations) becomes critical.
        if node_category == "Chainlink Sentinel":
            return 10 if (rsi > 75 or rsi < 25) else 3

        # AI logic: If Volume is spiking, 'Whale Alert' importance scales with volume.
        if node_category == "Whale Alert":
            return min(10, int(vol_ratio * 4))

        # AI logic: If Volatility is low (Squeeze), 'Macro News' and 'Neural Oracle' spike.
        if bb_width < 0.02:
            if node_category in ["Macro News AI", "Neural Oracle"]:
                return 9

        return 5 # Default baseline importance

    def optimize_node_selection(self, market_nodes, market_state, mode="BALANCED"):
        """
        Selects the best set of nodes based on AI importance scoring and mode.
        """
        # Score all nodes
        scored_nodes = []
        for node in market_nodes:
            category = node.get("category", "Unknown")
            importance = self.calculate_ai_importance(category, market_state)
            node["importance"] = importance
            scored_nodes.append(node)

        # Sort nodes by importance (descending)
        scored_nodes.sort(key=lambda n: n["importance"], reverse=True)

        # Mode logic: ACCURATE = top 15, ECONOMY = top 7, BALANCED = top 10
        if mode == "ACCURATE":
            num = 15
        elif mode == "ECONOMY":
            num = 7
        else:
            num = 10
        return scored_nodes[:num]

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
            mode="BALANCED"
        )

        print(f"🤖 AI Arsenal: Selected {len(optimized_arsenal)} nodes for this trade.")

        # 4. Fetch the chosen nodes (pass node objects)
        intel, failure_flag = await self.pipeline.fetch_dynamic_tools(optimized_arsenal)

        if failure_flag or len(intel) < len(optimized_arsenal):
            print(f"   ⚠️ [Skeptical] Failed to buy full arsenal. found {len(intel)}/{len(optimized_arsenal)} tools.")
            return

        # --- Weighted Decision Making ---
        if len(intel) > 0:
            weighted_sum = 0
            total_weight = 0
            print("   📝 Node Scores:")
            for node in optimized_arsenal:
                category = node.get("category", "Unknown")
                name = node.get("name", "Unknown")
                signal = intel.get(name, 0.5)
                # If signal is a Signal object, extract its value
                if hasattr(signal, 'value'):
                    signal_value = signal.value
                else:
                    signal_value = signal
                weight = self.calculate_ai_importance(category, market_state)
                score = 1 if signal_value > 0.6 else (-1 if signal_value < 0.4 else 0)
                print(f"      - {name} [{category}]: signal={signal_value:.3f}, score={score}, weight={weight}")
                weighted_sum += (score * weight)
                total_weight += weight
            confidence = weighted_sum / total_weight if total_weight > 0 else 0
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