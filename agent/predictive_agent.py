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
                        self.state_db.record_node_purchase(node, 1.0)  # 1.0 is a demo cost
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
        # Log the AI analysis as a structured decision for the frontend
        self.state_db.record_trade_decision({
            "action": bias,
            "ticker": "WXTZ/USDC",
            "signal": conf,
            "reason": decision.get('reasoning', '')
        })
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
                    # NEW: Log to DB so it shows in 'Decision Log'
                    trade_size = 0  # Default fallback
                    if bias == "LONG":
                        usdc_addr = os.getenv("USDC_CONTRACT") or os.getenv("USDC_ADDRESS")
                        if usdc_addr:
                            try:
                                trade_size = float(await self.wallet.get_token_balance(usdc_addr)) * conf * 0.99
                            except Exception:
                                trade_size = 0
                    elif bias == "SHORT":
                        wxtz_addr = os.getenv("WXTZ_ADDRESS")
                        if wxtz_addr:
                            try:
                                trade_size = float(await self.wallet.get_token_balance(wxtz_addr)) * conf * 0.99
                            except Exception:
                                trade_size = 0
                    # If a trade was executed, try to log the tradeId if available
                    trade_id = None
                    if hasattr(self.trading, 'last_trade_id'):
                        trade_id = getattr(self.trading, 'last_trade_id', None)
                    self.state_db.record_trade_decision(
                        context={
                            "action": decision.get('action', 'N/A'),
                            "ticker": decision.get('ticker', 'N/A'),
                            "signal": decision.get('confidence', 'N/A'),
                            "reason": decision.get('reasoning', "Strategy execution.")
                        },
                        trade_id=trade_id
                    )
                    print(f"   ✅ [Decision Log] Trade recorded successfully.")
                    print(f"   ✅ [Position Updated] Agent is now {bias}")
                else:
                    print(f"   ❌ [Position Error] Trade failed. Position remains {self.current_position}")
            else:
                # NEW: Smart Exit logic scales out based on AI confidence
                print(f"   🛑 [Exit] Trend weakened. Scaling out of {self.current_position} (Conviction: {conf:.2f}).")
                # Pass the actual AI 'conf' instead of a hardcoded 0.0
                success = await self.execute_move("NEUTRAL", conf)
                if success:
                    # If AI is highly confident about neutralizing (>80%), fully reset the state
                    if conf > 0.80:
                        self.current_position = "NEUTRAL"
                    self.last_trade_confidence = conf
                    print(f"   ✅ [Position Updated] Agent scaled out. Current stance: {self.current_position}")
                else:
                    print(f"   ❌ [Exit Error] Failed to scale out position.")
        else:
            print(f"   ⏳ [Hold] Maintaining {self.current_position} position.")

    async def execute_move(self, action, confidence):
        wxtz_addr = os.getenv("WXTZ_ADDRESS")
        usdc_addr = os.getenv("USDC_CONTRACT") or os.getenv("USDC_ADDRESS")

        if not wxtz_addr or not usdc_addr:
            print(f"   ❌ [DEBUG] Env Error: WXTZ={wxtz_addr}, USDC={usdc_addr}")
            return False

        # FIX DIRECTION: LONG = Sell WXTZ for USDC | SHORT = Sell USDC for WXTZ
        if action == "LONG":
            token_in, token_out, addr_in = "WXTZ", "USDC", wxtz_addr
        elif action == "SHORT":
            token_in, token_out, addr_in = "USDC", "WXTZ", usdc_addr
        elif action == "NEUTRAL":
            token_in, token_out, addr_in = "WXTZ", "USDC", wxtz_addr
        else:
            print(f"   ❌ [Trade Error] Unknown action: {action}")
            return False

        bal = float(await self.wallet.get_token_balance(addr_in))
        print(f"   🔍 [DEBUG] Balance of {token_in}: {bal}")
        if bal <= 0:
            print(f"   ❌ [Trade Error] No {token_in} balance to go {action}")
            return False

        factor = confidence if action != "NEUTRAL" else 1.0
        amount_in = bal * factor * 0.99

        result = await self.trading.execute_swap(token_in, token_out, amount_in)
        if result:
            # Update state so it doesn't stay NEUTRAL
            self.current_position = action
            # Log structured JSON so the frontend doesn't show N/A
            if hasattr(self, "db"):
                self.db.record_trade_decision({
                    "action": action,
                    "amount": f"{amount_in:.2f} {token_in}"
                })
            elif hasattr(self, "state_db"):
                self.state_db.record_trade_decision({
                    "action": action,
                    "amount": f"{amount_in:.2f} {token_in}",
                    "ticker": f"{token_in}/{token_out}"
                })
            return True
        else:
            print(f"   ❌ [DEBUG] Blockchain Execution Failed. Check Gas (XTZ) or Router Allowance.")
            return False