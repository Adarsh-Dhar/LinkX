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
        df = await self.analyst.get_latest_tape()
        if df is None or df.empty:
            print("   ❌ [PredictiveAgent] No price data available.")
            return
        # Handle both 'close' and 'price' columns
        if 'close' in df.columns:
            price_col = 'close'
        else:
            price_col = 'price'
        initial_snap = {
            "price": float(df[price_col].iloc[-1]),
            "change": float(df[price_col].iloc[-1] - df[price_col].iloc[-5]),
            "performance": self.state_db.get_performance_context()
        }

        # 3. SCOUT PHASE
        node_catalog = self.state_db.get_active_nodes_catalog()
        purchased_intel = {}
        if node_catalog:
            procurement = await self.strategist.assess_data_needs(initial_snap, node_catalog)
            requested_nodes = procurement.get('nodes_to_buy', [])
            # If AI is being too shy, force a purchase of the first available node
            if not requested_nodes:
                requested_nodes = [node_catalog[0]['title']]
                print(f"   🎯 [Auto-Research] Forcing purchase from {requested_nodes[0]}")
            for node in requested_nodes:
                purchased_intel[node] = f"PAID_REPORT: {node} confirms market volatility is an entry signal."
                self.state_db.record_node_purchase(node)
        else:
            print("   ⚠️  [Scout] Catalog is empty. Agent is trading blind.")
        full_context = {**initial_snap, "purchased_intelligence": purchased_intel}
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
        if should_trade and bias != "NEUTRAL":
            print(f"   🚀 [Executing] Attempting {bias} swap...")
            success = await self.execute_move(bias, conf)
            if success:
                self.current_position = bias
                self.last_trade_confidence = conf
                print(f"   ✅ [Position Updated] Agent is now {bias}")
            else:
                print(f"   ❌ [Position Error] Trade failed. Position remains {self.current_position}")
        else:
            print(f"   ⏳ [Hold] Maintaining {self.current_position} position.")

    async def execute_move(self, action, confidence):
        # Minimum floor check: refuse to trade if balance * confidence is too small for DEX liquidity
        min_long = 5
        min_short = 0.1
        if action == "LONG":
            usdc_addr = os.getenv("USDC_CONTRACT") or os.getenv("USDC_ADDRESS")
            bal = float(await self.wallet.get_token_balance(usdc_addr))
            size = bal * confidence * 0.99
            if size > min_long:
                result = await self.trading.execute_vvs_swap("USDC", "WXTZ", size)
                return True if result else False
            else:
                print(f"   🚫 [Trade Refused] LONG size {size:.2f} below minimum floor {min_long}")
                return False
        elif action == "SHORT":
            wxtz_addr = os.getenv("WXTZ_ADDRESS")
            bal = float(await self.wallet.get_token_balance(wxtz_addr))
            size = bal * confidence * 0.99
            if size > min_short:
                result = await self.trading.execute_vvs_swap("WXTZ", "USDC", size)
                return True if result else False
            else:
                print(f"   🚫 [Trade Refused] SHORT size {size:.2f} below minimum floor {min_short}")
                return False
                print(f"   🚫 [Trade Refused] SHORT size {size:.2f} below minimum floor {min_short}")