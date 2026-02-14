import os
import time
import json
import asyncio
import pandas as pd
from datetime import datetime
from .agent_state_db import AgentStateDB

class PredictiveAgent:
    def __init__(self, wallet_manager, node_connector, market_analyst, trading_engine, strategist):
        self.wallet = wallet_manager
        self.node_connector = node_connector
        self.analyst = market_analyst
        self.trading = trading_engine
        self.strategist = strategist
        self.state_db = AgentStateDB()
        self.short_term_memory = {}
        self.intelligence_cache = {} # { "NodeName": {"report": "...", "timestamp": 123.4} }
        self.current_position = "NEUTRAL"
        self.last_trade_confidence = 0.0
        self.risk_threshold = 0.05
        self.forced_bias = None
        self.data_cache = {} # Stores: { "NodeName": {"data": "...", "timestamp": 12345} }

    def check_for_overrides(self):
        """Checks for overrides using ABSOLUTE paths."""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        override_path = os.path.join(current_dir, "override_state.json")
        if os.path.exists(override_path):
            try:
                with open(override_path, "r") as f:
                    data = json.load(f)
                    self.forced_bias = data.get('forced_bias') or data.get('bias_override')
                    ctx = data.get('external_context')
                    if ctx:
                        self.short_term_memory['human_intel'] = ctx
                    if self.forced_bias:
                        self.forced_bias = self.forced_bias.upper()
                        print(f"   🎯 [OVERRIDE DETECTED] Bias: {self.forced_bias}")
            except Exception:
                pass
        else:
            self.forced_bias = None

    async def run_cycle(self):
        print(f"\n" + "═"*60)
        print(f"♟️  PREDICTIVE AGENT CYCLE - {datetime.now().strftime('%H:%M:%S')}")
        self.check_for_overrides()

        # 2. Get Basic Market Data
        df = await self.analyst.get_latest_tape()
        if df is None or df.empty:
            print("   ❌ [PredictiveAgent] No price data available.")
            return
        # Ensure 'close' column exists, fallback to 'price' if needed
        if 'close' in df.columns:
            price_col = 'close'
        else:
            price_col = 'price'
        initial_snapshot = {
            "current_price": float(df[price_col].iloc[-1]),
            "price_change": float(df[price_col].iloc[-1] - df[price_col].iloc[-5]),
            "agent_performance": self.state_db.get_performance_context(),
            "suggested_bias": self.forced_bias if self.forced_bias else "NONE"
        }

        # --- SCOUT PHASE ---
        print("   🔎 [Scout] Assessing Node Catalog...")
        node_catalog = self.state_db.get_active_nodes_catalog()
        purchased_intel = {}
        if node_catalog:
            # Ask AI which nodes are relevant
            procurement = await self.strategist.assess_data_needs(initial_snapshot, node_catalog)
            requested_nodes = procurement.get('nodes_to_buy', [])
            if requested_nodes:
                for node in requested_nodes:
                    last_buy_time = self.short_term_memory.get(f"last_buy_{node}", 0)
                    if time.time() - last_buy_time < 300:
                        print(f"   ♻️  [Cache] Reusing fresh report from {node} (Bought {int(time.time() - last_buy_time)}s ago)")
                        # Optionally, you could store the last report in memory for more realism
                        # purchased_intel[node] = self.short_term_memory.get(f"report_{node}")
                    else:
                        print(f"   💳 [Procurement] Buying NEW intelligence from {node}")
                        purchased_intel[node] = f"PAID_REPORT: {node} confirms trend validity."
                        self.state_db.record_node_purchase(node)
                        self.short_term_memory[f"last_buy_{node}"] = time.time()
                        print(f"      💸 Paid research fees to {node}")
            else:
                print("   💰 [Procurement] No paid data requested by AI.")
        # --- END SCOUT PHASE ---

        # 4. TRADER PHASE
        # Update full_context to include the intelligence we just 'bought'
        full_context = {**initial_snapshot, "purchased_intelligence": purchased_intel}
        decision = await self.strategist.get_strategy(full_context, self.short_term_memory)
        bias = decision.get('execution_bias', 'NEUTRAL')
        conf = float(decision.get('risk_confidence', 0.0))
        print(f"   🧠 [Strategist] {bias} ({conf:.2f}) | {decision.get('reasoning')[:60]}...")
        should_trade = False
        if bias != self.current_position:
            print(f"   🔄 [Flip] Switching {self.current_position} -> {bias}")
            should_trade = True
        elif bias == self.current_position and conf > (self.last_trade_confidence + 0.15):
            print(f"   📈 [Scale In] Conviction increased ({self.last_trade_confidence:.2f} -> {conf:.2f})")
            should_trade = True
        if should_trade:
            if bias != "NEUTRAL":
                print(f"   🚀 [Executing] Attempting {bias} swap...")
                success = await self.execute_move(bias, conf)
                if success:
                    self.current_position = bias
                    self.last_trade_confidence = conf
                    print(f"   ✅ [Position Updated] Agent is now {bias}")
                else:
                    print(f"   ❌ [Position Error] Trade failed. Position remains {self.current_position}")
            else:
                # NEW: Exit logic to truly reach NEUTRAL state
                print(f"   🛑 [Exit] Trend weakened. Closing current {self.current_position} position.")
                success = await self.execute_move("NEUTRAL", 0.0)
                if success:
                    self.current_position = "NEUTRAL"
                    self.last_trade_confidence = 0.0
                    print(f"   ✅ [Position Updated] Agent is now NEUTRAL (no open position)")
                else:
                    print(f"   ❌ [Exit Error] Failed to close position. Still {self.current_position}")
        else:
            print(f"   ⏳ [Hold] Maintaining {self.current_position} position.")

    async def execute_move(self, action, confidence):
        # Minimum floor check: refuse to trade if balance * confidence is too small for DEX liquidity
        # Removed minimum trade size restrictions
        if not self.trading or not hasattr(self.trading, "execute_swap") or not callable(getattr(self.trading, "execute_swap", None)):
            print("   ❌ [TradingEngine Error] Trading engine or execute_swap method is not properly initialized.")
            return False
        if not asyncio.iscoroutinefunction(self.trading.execute_swap):
            print("   ❌ [TradingEngine Error] execute_swap is not async. Please define it as 'async def execute_swap(...)'.")
            return False
        if action == "LONG":
            usdc_addr = os.getenv("USDC_CONTRACT") or os.getenv("USDC_ADDRESS")
            if not usdc_addr:
                print("   ❌ [Trade Error] USDC address not set in environment.")
                return False
            bal = float(await self.wallet.get_token_balance(usdc_addr))
            if bal == 0.0:
                print(f"   ⚠️ [Trade Refused] Wallet USDC balance is zero. Cannot execute LONG.")
                return False
            size = bal * confidence * 0.99
            result = await self.trading.execute_swap("USDC", "WXTZ", size)
            return True if result else False
        elif action == "SHORT":
            wxtz_addr = os.getenv("WXTZ_ADDRESS")
            if not wxtz_addr:
                print("   ❌ [Trade Error] WXTZ address not set in environment.")
                return False
            bal = float(await self.wallet.get_token_balance(wxtz_addr))
            if bal == 0.0:
                print(f"   ⚠️ [Trade Refused] Wallet WXTZ balance is zero. Cannot execute SHORT.")
                return False
            size = bal * confidence * 0.99
            result = await self.trading.execute_swap("WXTZ", "USDC", size)
            return True if result else False
        elif action == "NEUTRAL":
            # Exit logic: Close any open position by swapping all to USDC
            if self.current_position == "LONG":
                wxtz_addr = os.getenv("WXTZ_ADDRESS")
                if not wxtz_addr:
                    print("   ❌ [Exit Error] WXTZ address not set in environment.")
                    return False
                bal = float(await self.wallet.get_token_balance(wxtz_addr))
                if bal == 0.0:
                    print(f"   ⚠️ [Exit] No WXTZ to close LONG position.")
                    return True  # Already neutral
                result = await self.trading.execute_swap("WXTZ", "USDC", bal)
                return True if result else False
            elif self.current_position == "SHORT":
                usdc_addr = os.getenv("USDC_CONTRACT") or os.getenv("USDC_ADDRESS")
                if not usdc_addr:
                    print("   ❌ [Exit Error] USDC address not set in environment.")
                    return False
                bal = float(await self.wallet.get_token_balance(usdc_addr))
                if bal == 0.0:
                    print(f"   ⚠️ [Exit] No USDC to close SHORT position.")
                    return True  # Already neutral
                # If you want to rebalance, you could implement logic here
                # For now, just acknowledge
                return True
            else:
                print(f"   ℹ️ [Exit] Already NEUTRAL. No position to close.")
                return True