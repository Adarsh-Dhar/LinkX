import os
import asyncio
import pandas as pd
from datetime import datetime
from .data_pipeline import DataPipeline
from .trading_engine import TradingEngine
from .brain import NeuralBrain

class PredictiveAgent:
    def __init__(self, wallet_manager=None, market_manager=None, trading_engine=None, simulation_mode=False):
        # Accept new arguments for compatibility
        self.market_manager = market_manager
        self.engine = trading_engine if trading_engine is not None else TradingEngine(wallet_manager)
        self.pipeline = DataPipeline(self.engine)
        self.brain = NeuralBrain()
        self.simulation_mode = simulation_mode
        self.is_running = False
        
        # Mapping market situations to the specific tools required
        self.SITUATION_MAP = {
            "VOLATILITY_SQUEEZE": ["Alternative Intelligence & Sentiment", "Supply Chain & Global Macro"],
            "LIQUIDATION_CASCADE": ["Market Microstructure & Execution", "Alternative Intelligence & Sentiment"],
            "NORMAL_GROWTH": ["Market Microstructure & Execution"]
        }

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

        # STEP 2: ANALYZE CONTEXT
        context = self.identify_context(df)
        required_tools = self.SITUATION_MAP.get(context, [])
        print(f"   🧠 [Context] {context}")
        print(f"   📋 [Arsenal] Required: {', '.join(required_tools)}")

        # STEP 3: THINK & PURCHASE (Paid Data via x402)
        # The pipeline now fetches all nodes, chooses the best, and pays USDC
        intel = await self.pipeline.fetch_dynamic_tools(required_tools)

        # BLOCKER: Do not trade on incomplete information
        if len(intel) < len(required_tools):
            print(f"   ⚠️ [Skeptical] Failed to buy full arsenal. found {len(intel)}/{len(required_tools)} tools.")
            return

        # STEP 4: CONCLUDE & EXECUTE
        # Pass indicators + bought proprietary data to the Neural Brain
        decision, confidence = self.brain.conclude(df, intel)
        
        print(f"   🎯 [Decision] {decision} (Confidence: {confidence:.2f})")

        if decision in ["BUY", "SELL"] and confidence > 0.75:
            risk_amount = 100.0 if confidence > 0.9 else 50.0
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