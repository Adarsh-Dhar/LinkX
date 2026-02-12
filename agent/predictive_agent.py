import os
import time
import json
import asyncio
import pandas as pd
from datetime import datetime
from agent_state_db import AgentStateDB

class PredictiveAgent:
    def __init__(self, wallet_manager, node_connector, market_analyst, trading_engine, strategist):
        self.wallet = wallet_manager
        self.node_connector = node_connector
        self.analyst = market_analyst
        self.trading = trading_engine
        self.strategist = strategist
        self.state_db = AgentStateDB()
        self.short_term_memory = {}
        self.current_position = "NEUTRAL"
        self.last_trade_confidence = 0.0
        self.risk_threshold = 0.05
        self.forced_bias = None

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
        price_data = await self.analyst.get_historical_prices(limit=60)
        df = pd.DataFrame(price_data)
        initial_snapshot = {
            "current_price": float(df['close'].iloc[-1]),
            "price_change": float(df['close'].iloc[-1] - df['close'].iloc[-5]),
            "agent_performance": self.state_db.get_performance_context(),
            "suggested_bias": self.forced_bias if self.forced_bias else "NONE"
        }
        print("   🔎 [Scout] Assessing Node Catalog...")
        node_catalog = self.state_db.get_active_nodes_catalog()
        purchased_intel = {}
        if node_catalog:
            procurement = await self.strategist.assess_data_needs(initial_snapshot, node_catalog)
            nodes_to_buy = procurement.get('nodes_to_buy', [])
            if nodes_to_buy:
                print(f"   💳 [Procurement] Buying data from: {nodes_to_buy}")
                for node in nodes_to_buy:
                    purchased_intel[node] = f"Simulated report from {node}: CONFIRMED TREND"
                    self.state_db.update_node_score(node, 0.1)
            else:
                print("   💰 [Procurement] No paid data needed.")
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
        if should_trade and bias != "NEUTRAL":
            await self.execute_move(bias, conf)
            self.current_position = bias
            self.last_trade_confidence = conf
        else:
            print(f"   ⏳ [Hold] Maintaining {self.current_position} position.")

    async def execute_move(self, action, confidence):
        if action == "LONG":
            bal = float(await self.wallet.get_token_balance(os.getenv("USDC_ADDRESS")))
            size = bal * confidence * 0.99
            if size > 5:
                await self.trading.execute_vvs_swap("USDC", "WXTZ", size)
        elif action == "SHORT":
            bal = float(await self.wallet.get_token_balance(os.getenv("WXTZ_ADDRESS")))
            size = bal * confidence * 0.99
            if size > 0.1:
                await self.trading.execute_vvs_swap("WXTZ", "USDC", size)