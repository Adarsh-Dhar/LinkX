

import os
import time
import asyncio
import pandas as pd
import requests
from datetime import datetime
from .tools import AlphaStrategist

class PredictiveAgent:
        def check_for_overrides(self):
            """Check for override_state.json and inject external_context if present."""
            import json
            if os.path.exists('override_state.json'):
                with open('override_state.json', 'r') as f:
                    override = json.load(f)
                    # Inject the external context into the agent's reasoning memory
                    if 'external_context' in override:
                        self.short_term_memory['human_intelligence'] = {
                            'value': override['external_context'],
                            'timestamp': time.time(),
                            'granularity': '1h'
                        }
                    return override
            return None
    def __init__(self, pipeline):
        self.pipeline = pipeline
        self.strategist = AlphaStrategist()
        self.short_term_memory = {}  # Store: {node_id: {"data": x, "ts": y, "regime": z}}
        self.paused = False
        self.block_data_purchases = False
        self.is_running = False
        # --- HUMAN OVERRIDE STATE ---
        self.risk_threshold = 0.15  # Default institutional-grade threshold
        self.forced_bias = None  # Can be "LONG", "SHORT", "NEUTRAL", or None for AI discretion

    def apply_human_interference(self, risk: float = None, bias: str = None):
        """Inject human overrides into the agent's state in real time."""
        if risk is not None:
            print(f"[C2] Human override: Setting risk_threshold to {risk}")
            self.risk_threshold = float(risk)
        if bias is not None:
            print(f"[C2] Human override: Setting forced_bias to {bias}")
            self.forced_bias = bias.upper() if bias else None

    async def log_activity(self, activity_data):
        """Log agent activity to the frontend database."""
        try:
            response = requests.post(
                "http://localhost:3600/api/agent/activity",
                json=activity_data,
                timeout=2
            )
            if response.status_code != 201:
                print(f"   ⚠️  [Activity Log] Failed to log activity: {response.status_code}")
        except Exception as e:
            print(f"   ⚠️  [Activity Log] Error logging activity: {e}")

    async def run_cycle(self):
        """The Cognitive Decision Loop with Real x402 Payment Integration."""
        print(f"\n══════════════════════════════════════════════════════════════")
        print(f"♟️  PREDICTIVE AGENT CYCLE - {time.strftime('%H:%M:%S')}")

        if self.paused:
            print("⏸️  AGENT IS PAUSED: Skipping cycle.")
            return

        # Log cycle start
        await self.log_activity({
            "type": "cycle_start",
            "title": "Agent Cycle Started",
            "description": f"Beginning predictive cycle at {datetime.now().isoformat()}"
        })

        # 1. PERCEPTION: Fetch the Tape from the fixed Pipeline method
        df = await self.pipeline.get_latest_tape()

        # 2. SYNC CHECK: This will now pass immediately because of seeding
        if df is None or len(df) < 20:
            count = len(df) if df is not None else 0
            print(f"   ⏳ [Tape] Waiting for synchronization... (Current: {count}/20)")
            return

        print(f"   ✅ [Tape] Synced: Using {len(df)} most recent data points.")

        # 3. PREPARE CONTEXT: Convert DataFrame to a snapshot for GitHub Models
        price_col = "price" if "price" in df.columns else "value" if "value" in df.columns else None
        if price_col is None:
            print("   ❌ [Tape] Missing price/value column in tape data; skipping cycle.")
            return

        market_snapshot = {
            "current_price": float(df[price_col].iloc[-1]),
            "price_change_5m": float(df[price_col].iloc[-1] - df[price_col].iloc[-5]),
            "recent_volatility": float(df[price_col].tail(10).std()),
            "timestamp": df['timestamp'].iloc[-1] if "timestamp" in df.columns else datetime.utcnow().isoformat()
        }

        # 4. FETCH FREE METADATA (Discovery Layer - no payment required)
        try:
            res = requests.get("http://localhost:3600/api/nodes", timeout=5)
            if res.status_code != 200:
                print(f"   ⚠️  [Discovery] Failed to fetch node metadata: {res.status_code}")
                return
            nodes_metadata = res.json()
            print(f"   📊 [Discovery] Window-shopped {len(nodes_metadata)} available nodes (FREE)")
            # Store more_context in short_term_memory for each node
            for node in nodes_metadata:
                node_id = node.get('id')
                if node_id:
                    self.short_term_memory.setdefault(node_id, {})['more_context'] = node.get('more_context')
        except Exception as e:
            print(f"   ❌ [Discovery Error] {e}")
            return

        # 5. REASONING: Consult gpt-4o-mini via GitHub Models with full node metadata
        # Package Human Override Rules for LLM
        human_rules = {
            "risk_threshold": self.risk_threshold,
            "forced_bias": self.forced_bias
        }
        print(f"   🧠 [Reasoning] Consulting AlphaStrategist with {len(nodes_metadata)} nodes...")
        print(f"   🎯 [Human Override] Threshold: {self.risk_threshold:.2f} | Bias: {self.forced_bias or 'AI Discretion'}")
        decision = self.strategist.rethink_strategy(market_snapshot, self.short_term_memory, human_rules=human_rules)
        print(f"🧠 [Strategist Thought]: {decision['thought']}")
        print(f"   📈 [Score] Utility: {decision.get('utility_score', 'N/A')}, Alpha/USDC: {decision.get('alpha_per_usdc', 'N/A')}")

        # Log utility score computation
        await self.log_activity({
            "type": "utility_score",
            "title": f"Utility Score Computed",
            "description": decision['thought'],
            "utilityScore": float(decision.get('utility_score', 0)),
            "alphaPerUsdcRatio": float(decision.get('alpha_per_usdc', 0)),
            "tradeBias": decision.get('execution_bias', 'NEUTRAL'),
            "tradeConfidence": float(decision.get('risk_confidence', 0)),
            "agentThought": decision['thought']
        })

        # 6. SELECTIVE ACTION: Real x402 Payment for High-Confidence Purchases
        intel = {}
        if decision['verdict'] == "PURCHASE_DATA":
            target_node_id = decision.get('target_node_id')
            if target_node_id:
                # Find target node metadata
                target_node = next((n for n in nodes_metadata if n.get('id') == target_node_id), None)
                if not target_node:
                    print(f"   ❌ [x402] Target node {target_node_id} not found in metadata")
                    return
                # --- Use new schema fields ---
                node_title = target_node.get('title')
                node_ratings = target_node.get('ratings', 0)
                print(f"   💳 [x402] Initiating real blockchain payment for {node_title}")
                print(f"      Price: {target_node['price']} USDC | Ratings: {node_ratings}/100")
                # --- Staleness check using node timestamp ---
                node_timestamp = target_node.get('timestamp')
                last_seen = self.short_term_memory.get(target_node_id, {}).get('timestamp')
                if node_timestamp and last_seen and node_timestamp <= last_seen:
                    print(f"   ⏩ [Staleness] Node data not updated since last purchase. Skipping buy.")
                    return
                # Log node purchase
                await self.log_activity({
                    "type": "node_purchase",
                    "title": f"Purchased {node_title}",
                    "description": f"Acquired data node at {target_node['price']} USDC",
                    "nodeId": target_node_id,
                    "nodePrice": float(target_node['price']),
                    "nodeRatings": int(node_ratings)
                })
                try:
                    from .wallet_manager import WalletManager
                    wallet = WalletManager()
                    provider_address = os.getenv("PROVIDER_ADDRESS", "0xFe5e03799Fe833D93e950d22406F9aD901Ff3Bb9")
                    tx_hash = wallet.transfer_usdc(provider_address, target_node['price'])
                    if tx_hash:
                        print(f"   ✅ [x402] Payment confirmed! TX: {tx_hash}")
                        signal = await self.pipeline.fetch_with_proof(
                            target_node['endpointUrl'],
                            tx_hash,
                            target_node['id']
                        )
                        if signal:
                            print(f"   ✅ [Data Feed] Received signal: {signal}")
                            await self.log_activity({
                                "type": "signal_received",
                                "title": f"Signal from {node_title}",
                                "description": f"Received signal value: {signal}",
                                "signalValue": float(signal)
                            })
                            granularity = target_node.get('granularity', '5m')
                            # Store node timestamp if available, else fallback to now
                            memory_timestamp = node_timestamp if node_timestamp else time.time()
                            self.short_term_memory[target_node_id] = {
                                "value": signal,
                                "timestamp": memory_timestamp,
                                "at_price": market_snapshot['current_price'],
                                "granularity": granularity,
                                "tx_hash": tx_hash,
                                "title": node_title,
                                "description": target_node.get('description'),
                                "more_context": target_node.get('more_context'),
                                "ratings": node_ratings
                            }
                            intel[target_node_id] = signal
                            try:
                                requests.post(
                                    "http://localhost:3600/api/agent/data-log",
                                    json={
                                        "nodeId": target_node_id,
                                        "data": str(signal),
                                        "fetchedAt": datetime.utcnow().isoformat()
                                    },
                                    timeout=2
                                )
                            except Exception as e:
                                print(f"   ⚠️  [DataLog] Failed to log DataLog: {e}")
                        else:
                            print(f"   ❌ [Data Feed] Failed to retrieve locked data despite payment")
                    else:
                        print(f"   ❌ [x402] Payment transfer failed - insufficient funds or network error")
                except Exception as e:
                    print(f"   ❌ [x402 Error] {e}")
                    import traceback
                    traceback.print_exc()
        
        elif decision['verdict'] == "USE_MEMORY":
            # Filter memory for data that is NOT stale based on granularity
            now = time.time()
            valid_memory = {}
            for node_id, data in self.short_term_memory.items():
                granularity = data.get('granularity', '5m')
                age_seconds = now - data['timestamp']
                
                # Define staleness thresholds based on granularity
                staleness_map = {
                    '1m': 120,    # 2 minutes
                    '5m': 600,    # 10 minutes
                    '1h': 7200,   # 2 hours
                }
                max_age = staleness_map.get(granularity, 300)  # Default 5 min
                
                if age_seconds < max_age:
                    valid_memory[node_id] = data['value']
            
            print(f"   🧠 [Memory] Reusing {len(valid_memory)}/{len(self.short_term_memory)} cached signals. Saving USDC.")
            intel = valid_memory

        # 7. FINAL CHECK FOR PRIORITY OVERRIDE BEFORE EXECUTION
        priority_override = self.check_for_priority_overrides() if hasattr(self, 'check_for_priority_overrides') else None
        if priority_override:
            decision['execution_bias'] = priority_override.get('bias', decision.get('execution_bias'))
            decision['risk_confidence'] = 1.0
            decision['verdict'] = "FORCE_ACTION"
            print(f"   🧭 [Priority Override] Forcing {decision['execution_bias']} bias before execution")

        # 8. EXECUTION: Only move if confidence meets dynamic threshold (or forced)
        if decision.get('risk_confidence', 0) >= self.risk_threshold and decision.get('execution_bias') != "NEUTRAL":
            await self.execute_move(decision, intel)
        else:
            print(f"   🛡️  [Risk Management] Decision confidence ({decision.get('risk_confidence', 0):.2f}) below {self.risk_threshold:.2f} threshold. Holding.")

        # Log risk skip if confidence too low
        if decision.get('risk_confidence', 0) < self.risk_threshold:
            await self.log_activity({
                "type": "risk_skip",
                "title": "Risk Management - Execution Skipped",
                "description": f"Decision confidence ({decision.get('risk_confidence', 0):.2f}) below threshold",
                "riskAction": "SKIP",
                "riskReason": f"Low confidence: {decision.get('risk_confidence', 0):.2f} < 0.15"
            })
        # Log cycle end
        await self.log_activity({
            "type": "cycle_end",
            "title": "Agent Cycle Complete",
            "description": f"Completed cycle with verdict: {decision['verdict']}"
        })

    async def execute_move(self, decision, intel):
        """Execute the final trade on Etherlink using TradingEngine."""
        from .trading_engine import TradingEngine
        from .wallet_manager import WalletManager
        
        bias = decision.get('execution_bias', 'NEUTRAL')
        risk_confidence = decision.get('risk_confidence', 0)

        # Check for forced action (prioritize instance variable over env)
        force_action = os.getenv("FORCE_ACTION", "").strip().upper()
        active_override = self.forced_bias or force_action
        forced = False

        if active_override:
            if active_override in ["BUY", "LONG"]:
                bias = "LONG"
                forced = True
            elif active_override in ["SELL", "SHORT"]:
                bias = "SHORT"
                forced = True
            elif active_override in ["HOLD", "NEUTRAL"]:
                bias = "NEUTRAL"
                forced = True
            if forced:
                risk_confidence = 1.0
                override_source = "Instance Override" if self.forced_bias else "ENV Override"
                print(f"   🧭 [{override_source}] Forcing {bias} in execute_move")

        # Apply dynamic risk threshold instead of hardcoded 0.15
        if (bias == "NEUTRAL" or risk_confidence < self.risk_threshold) and not forced:
            print(f"   🛡️ [Risk Management] Skipping execution: bias={bias}, confidence={risk_confidence:.2f} < threshold={self.risk_threshold:.2f}")
            return

        print(f"   🚀 [EXECUTION] Action: {bias} | Confidence: {risk_confidence:.2f} | Threshold: {self.risk_threshold:.2f}")
        print(f"   💭 [Basis] {decision['thought'][:80]}...")

        try:
            # Initialize trading engine with shared wallet
            wallet = WalletManager()
            engine = TradingEngine(wallet=wallet)

            # Fetch real balances for USDC and WXTZ
            current_usdc_balance = wallet.get_balance('USDC') if hasattr(wallet, 'get_balance') else 0.0
            current_wxtz_balance = wallet.get_balance('WXTZ') if hasattr(wallet, 'get_balance') else 0.0

            if bias == "LONG":
                # Use 10% of real USDC balance scaled by AI confidence
                trade_amount = current_usdc_balance * 0.1 * risk_confidence
                if current_usdc_balance <= 0 or trade_amount <= 0:
                    print(f"   🛑 [Risk Management] Skipping trade: USDC balance is {current_usdc_balance}")
                    await self.log_activity({
                        "type": "risk_skip",
                        "title": "Execution Skipped - Insufficient Balance",
                        "description": f"USDC balance is {current_usdc_balance}; trade amount computed as {trade_amount}",
                        "riskAction": "SKIP",
                        "riskReason": "Insufficient USDC balance"
                    })
                    return None
                await self.log_activity({
                    "type": "trade_decision",
                    "title": f"Trade Decision: {bias}",
                    "description": f"Executing {bias} position with {risk_confidence:.2f} confidence | Amount: {trade_amount:.4f} USDC",
                    "tradeBias": bias,
                    "tradeConfidence": float(risk_confidence),
                    "agentThought": decision.get('thought', ''),
                    "metadata": {
                        "tradeAmount": float(trade_amount),
                        "tokenIn": "USDC",
                        "tokenOut": "WXTZ",
                        "forceAction": active_override or None,
                        "humanOverride": {
                            "risk_threshold": self.risk_threshold,
                            "forced_bias": self.forced_bias
                        }
                    }
                })
                # Execute long position: USDC -> WXTZ
                tx_hash = engine.execute_swap("USDC", "WXTZ", trade_amount)
                if tx_hash:
                    print(f"   ✅ [LONG Execution] Swapped {trade_amount:.4f} USDC -> WXTZ")
                    print(f"   📋 [Tx Hash] {tx_hash}")
                else:
                    print(f"   ❌ [LONG Execution Failed] Swap returned None")
                return tx_hash
            elif bias == "SHORT":
                # Use real WXTZ balance for the exit/short position
                trade_amount = current_wxtz_balance * risk_confidence
                if current_wxtz_balance <= 0 or trade_amount <= 0:
                    print(f"   🛑 [Risk Management] Skipping short: WXTZ balance is {current_wxtz_balance}")
                    await self.log_activity({
                        "type": "risk_skip",
                        "title": "Execution Skipped - Insufficient Balance",
                        "description": f"WXTZ balance is {current_wxtz_balance}; short amount computed as {trade_amount}",
                        "riskAction": "SKIP",
                        "riskReason": "Insufficient WXTZ balance"
                    })
                    return None
                await self.log_activity({
                    "type": "trade_decision",
                    "title": f"Trade Decision: {bias}",
                    "description": f"Executing {bias} position with {risk_confidence:.2f} confidence | Amount: {trade_amount:.4f} WXTZ",
                    "tradeBias": bias,
                    "tradeConfidence": float(risk_confidence),
                    "agentThought": decision.get('thought', ''),
                    "metadata": {
                        "tradeAmount": float(trade_amount),
                        "tokenIn": "WXTZ",
                        "tokenOut": "USDC",
                        "forceAction": active_override or None,
                        "humanOverride": {
                            "risk_threshold": self.risk_threshold,
                            "forced_bias": self.forced_bias
                        }
                    }
                })
                tx_hash = engine.execute_swap("WXTZ", "USDC", trade_amount)
                if tx_hash:
                    print(f"   ✅ [SHORT Execution] Swapped {trade_amount:.4f} WXTZ -> USDC")
                    print(f"   📋 [Tx Hash] {tx_hash}")
                else:
                    print(f"   ❌ [SHORT Execution Failed] Swap returned None")
                return tx_hash

            return tx_hash

        except Exception as e:
            print(f"   ❌ [Execution Error] {e}")
            return None

    async def run_loop(self):
        self.is_running = True
        while self.is_running:
            try:
                await self.run_cycle()
            except Exception as e:
                print(f"   ❌ [Critical Agent Error] {e}")
            await asyncio.sleep(15)