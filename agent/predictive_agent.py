

import os
import time
import asyncio
import pandas as pd
import requests
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
        market_snapshot = {
            "current_price": float(df['price'].iloc[-1]),
            "price_change_5m": float(df['price'].iloc[-1] - df['price'].iloc[-5]),
            "recent_volatility": float(df['price'].tail(10).std()),
            "timestamp": df['timestamp'].iloc[-1]
        }

        # 4. FETCH FREE METADATA (Discovery Layer - no payment required)
        try:
            res = requests.get("http://localhost:3600/api/nodes", timeout=5)
            if res.status_code != 200:
                print(f"   ⚠️  [Discovery] Failed to fetch node metadata: {res.status_code}")
                return
            nodes_metadata = res.json()
            print(f"   📊 [Discovery] Window-shopped {len(nodes_metadata)} available nodes (FREE)")
        except Exception as e:
            print(f"   ❌ [Discovery Error] {e}")
            return

        # 5. REASONING: Consult gpt-4o via GitHub Models with full node metadata
        decision = self.strategist.rethink_strategy(market_snapshot, self.short_term_memory)
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
                
                print(f"   💳 [x402] Initiating real blockchain payment for {target_node['name']}")
                print(f"      Price: {target_node['price']} USDC | Quality: {target_node['qualityScore']}/100")
                
                # Execute REAL USDC transfer to provider
                # Log node purchase
                await self.log_activity({
                    "type": "node_purchase",
                    "title": f"Purchased {target_node['name']}",
                    "description": f"Acquired data node at {target_node['price']} USDC",
                    "nodeId": target_node_id,
                    "nodePrice": float(target_node['price']),
                    "nodeQuality": int(target_node.get('qualityScore', 0))
                })
                
                # Execute REAL USDC transfer to provider
                try:
                    from .wallet_manager import WalletManager
                    wallet = WalletManager()
                    
                    # Get provider address from env or use default
                    provider_address = os.getenv("PROVIDER_ADDRESS", "0xFe5e03799Fe833D93e950d22406F9aD901Ff3Bb9")
                    
                    # Execute transfer
                    tx_hash = wallet.transfer_usdc(provider_address, target_node['price'])
                    
                    if tx_hash:
                        print(f"   ✅ [x402] Payment confirmed! TX: {tx_hash}")
                        
                        # Use tx_hash as proof header to fetch locked data
                        signal = await self.pipeline.fetch_with_proof(
                            target_node['endpointUrl'],
                            tx_hash,
                            target_node['id']
                        )
                        
                        if signal:
                            print(f"   ✅ [Data Feed] Received signal: {signal}")

                            # Log signal received
                            await self.log_activity({
                                "type": "signal_received",
                                "title": f"Signal from {target_node['name']}",
                                "description": f"Received signal value: {signal}",
                                "signalValue": float(signal)
                            })

                            # Update Memory with TTL based on granularity
                            # Log signal received
                            await self.log_activity({
                                "type": "signal_received",
                                "title": f"Signal from {target_node['name']}",
                                "description": f"Received signal value: {signal}",
                                "signalValue": float(signal)
                            })
                            
                            # Update Memory with TTL based on granularity
                            granularity = target_node.get('granularity', '5m')
                            self.short_term_memory[target_node_id] = {
                                "value": signal,
                                "timestamp": time.time(),
                                "at_price": market_snapshot['current_price'],
                                "granularity": granularity,
                                "tx_hash": tx_hash
                            }
                            intel[target_node_id] = signal
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

        # 7. EXECUTION: Only move if confidence is institutional-grade
        if decision.get('risk_confidence', 0) >= 0.15:
            await self.execute_move(decision, intel)
        else:
            print(f"   🛡️  [Risk Management] Decision confidence ({decision.get('risk_confidence', 0):.2f}) below 0.15 threshold. Holding.")

        # Log risk skip if confidence too low
        if decision.get('risk_confidence', 0) < 0.15:
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
        
        if bias == "NEUTRAL" or risk_confidence < 0.15:
            print(f"   🛡️ [Risk Management] Skipping execution: bias={bias}, confidence={risk_confidence}")
            return

        # Log trade decision
        await self.log_activity({
            "type": "trade_decision",
            "title": f"Trade Decision: {bias}",
            "description": f"Executing {bias} position with {risk_confidence:.2f} confidence",
            "tradeBias": bias,
            "tradeConfidence": float(risk_confidence),
            "agentThought": decision.get('thought', '')
        })

        print(f"   🚀 [EXECUTION] Action: {bias} | Confidence: {risk_confidence} | Basis: {decision['thought'][:50]}...")
        
        try:
            # Initialize trading engine with shared wallet
            wallet = WalletManager()
            engine = TradingEngine(wallet=wallet)
            
            # Calculate trade amount based on confidence and available balance
            # Get current USDC balance
            current_balance = wallet.get_balance('USDC') if hasattr(wallet, 'get_balance') else 100.0
            trade_amount = min(current_balance * risk_confidence * 0.1, 50.0)  # Max 10% of balance, cap at 50 USDC
            
            if bias == "LONG":
                # Execute long position: USDC -> WXTZ
                tx_hash = engine.execute_swap("USDC", "WXTZ", trade_amount)
                print(f"   ✅ [LONG Execution] Swapped {trade_amount} USDC -> WXTZ. Hash: {tx_hash}")
            elif bias == "SHORT":
                # Execute short position: WXTZ -> USDC (if we have WXTZ)
                # For now, use a smaller amount for short positions
                short_amount = trade_amount * 0.5
                tx_hash = engine.execute_swap("WXTZ", "USDC", short_amount)
                print(f"   ✅ [SHORT Execution] Swapped {short_amount} WXTZ -> USDC. Hash: {tx_hash}")
                
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