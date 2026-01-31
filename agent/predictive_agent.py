

import time
import asyncio
import pandas as pd
from datetime import datetime
from .tools import AlphaStrategist

class PredictiveAgent:
    def __init__(self, pipeline):
        self.pipeline = pipeline
        self.strategist = AlphaStrategist()
        self.short_term_memory = {}  # Store: {node_id: {"data": x, "ts": y, "regime": z}}
        self.paused = False
        self.block_data_purchases = False
        self.is_running = False

    async def run_cycle(self):
        """The Cognitive Decision Loop."""
        print(f"\n══════════════════════════════════════════════════════════════")
        print(f"♟️  PREDICTIVE AGENT CYCLE - {time.strftime('%H:%M:%S')}")

        if self.paused:
            print("⏸️  AGENT IS PAUSED: Skipping cycle.")
            return

        # 1. PERCEPTION: Fetch the Tape from the fixed Pipeline method
        df = await self.pipeline.get_latest_tape()

        # 2. SYNC CHECK: This will now pass immediately because of seeding
        if df is None or len(df) < 20:
            count = len(df) if df is not None else 0
            print(f"   ⏳ [Tape] Waiting for synchronization... (Current: {count}/20)")
            return

        print(f"   ✅ [Tape] Synced: Using {len(df)} most recent data points.")

        # 3. PREPARE CONTEXT: Convert DataFrame to a snapshot for OpenRouter
        market_snapshot = {
            "current_price": float(df['price'].iloc[-1]),
            "price_change_5m": float(df['price'].iloc[-1] - df['price'].iloc[-5]),
            "recent_volatility": float(df['price'].tail(10).std()),
            "timestamp": df['timestamp'].iloc[-1]
        }

        # 4. REASONING: Consult DeepSeek R1 via OpenRouter
        # Pass the short_term_memory so it knows what it already bought
        decision = self.strategist.rethink_strategy(market_snapshot, self.short_term_memory)
        print(f"🧠 [Strategist Thought]: {decision['thought']}")

        # 5. SELECTIVE ACTION: Economic Data Acquisition
        intel = {}
        if decision['verdict'] == "PURCHASE_DATA":
            node_id = decision.get('target_node_id')
            if node_id:
                print(f"   💸 [x402] Strategist justified purchase of Node: {node_id}")
                signal = await self.pipeline.execute_targeted_buy(node_id)
                
                if signal:
                    # Update Memory with TTL
                    self.short_term_memory[node_id] = {
                        "value": signal,
                        "timestamp": time.time(),
                        "at_price": market_snapshot['current_price']
                    }
                    intel[node_id] = signal
        
        elif decision['verdict'] == "USE_MEMORY":
            # Filter memory for data < 5 minutes old
            now = time.time()
            valid_memory = {k: v['value'] for k, v in self.short_term_memory.items() if now - v['timestamp'] < 300}
            print(f"   🧠 [Memory] Reusing {len(valid_memory)} valid signals. Saving USDC.")
            intel = valid_memory

        # 6. EXECUTION: Only move if confidence is institutional-grade
        if decision.get('risk_confidence', 0) > 0.85:
            await self.execute_move(decision, intel)
        else:
            print(f"   🛡️  [Risk Management] Decision confidence ({decision.get('risk_confidence', 0)}) below threshold. Holding.")

    async def execute_move(self, decision, intel):
        """Execute the final trade on Etherlink."""
        bias = decision.get('execution_bias', 'NEUTRAL')
        if bias == "NEUTRAL":
            return

        print(f"   🚀 [EXECUTION] Action: {bias} | Basis: {decision['thought'][:50]}...")
        # Your trading_engine.execute_swap logic goes here
        pass

    async def run_loop(self):
        self.is_running = True
        while self.is_running:
            try:
                await self.run_cycle()
            except Exception as e:
                print(f"   ❌ [Critical Agent Error] {e}")
            await asyncio.sleep(15) 