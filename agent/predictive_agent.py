import asyncio
try:
    from .data_pipeline import DataPipeline
except ImportError:
    class DataPipeline: pass

from .brain import RLAgent
from datetime import datetime
import requests
import json

class PredictiveAgent:
    def __init__(self, market_manager, simulation_mode=True):
        self.pipeline = DataPipeline(market_manager)
        self.brain = RLAgent(model_path="agent/brain.pth")
        
        # We rely on the API for portfolio state now, but keep a cache
        self.last_action = "HOLD"
        self.last_state = None
        self.last_action_idx = 0
        
        # Configuration
        self.confidence_threshold = 0.70 
        self.trade_amount_usdc = 10.0
        
        # The API endpoint that the Frontend uses
        self.trade_api_url = "http://localhost:8000/trade/execute/confirmed"

    async def run_cycle(self):
        print("\n" + "="*60)
        print(f"🤖 PREDICTIVE AGENT CYCLE - {datetime.now().strftime('%H:%M:%S')}")
        print("="*60)
        
        # 1. OBSERVE
        state_vector = await self.pipeline.get_market_state()
        
        # 2. PREDICT
        action, confidence, probabilities = self.brain.get_action(state_vector, epsilon=0.05)
        
        print(f"\n🎯 DECISION: {action} ({confidence*100:.1f}%)")
        
        action_idx = ["HOLD", "BUY", "SELL"].index(action)
        result = "HOLD"

        # 3. ACT (Trigger Frontend-Compatible Trade)
        if action == "BUY" and confidence > self.confidence_threshold:
            result = self._trigger_trade("USDC", "CRO", self.trade_amount_usdc)
            self.last_action = "BUY"
            self.last_action_idx = 1
            
        elif action == "SELL" and confidence > self.confidence_threshold:
            # For sell, we'd ideally check CRO balance first, but let's try to sell 100 CRO
            result = self._trigger_trade("CRO", "USDC", 100.0) 
            self.last_action = "SELL"
            self.last_action_idx = 2
            
        else:
            print(f"⏸️  HOLD: Confidence too low ({confidence*100:.1f}%)")
            self.last_action = "HOLD"
            self.last_action_idx = 0

        # 4. REWARD (Simple logging for now)
        if result == "SUCCESS":
            print("✅ Trade Successfully Executed via API")
        
        self.last_state = state_vector
        return {"action": action, "result": result}

    def _trigger_trade(self, token_in, token_out, amount):
        """
        Sends a trade request to the Agent API, exactly like the Frontend does.
        """
        print(f"🚀 Triggering Trade: {amount} {token_in} -> {token_out} via API...")
        
        payload = {
            "token_in": token_in,
            "token_out": token_out,
            "amount": amount,
            "slippage": 0.5
        }
        
        try:
            # Call the Agent's own API to execute the trade
            # This ensures the logic matches the 'frontend setup' exactly
            response = requests.post(self.trade_api_url, json=payload, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✓ API Response: {data.get('status', 'OK')} - Tx: {data.get('txHash', 'N/A')}")
                return "SUCCESS"
            else:
                print(f"   ❌ API Error {response.status_code}: {response.text}")
                return "FAILED"
        except Exception as e:
            print(f"   ❌ Connection Error: {e}")
            return "FAILED"