import asyncio
from datetime import datetime
import requests
import json
import numpy as np
from .brain import RLAgent
# Ensure correct import based on your folder structure
try:
    from .data_pipeline import DataPipeline
except ImportError:
    from agent.data_pipeline import DataPipeline

class PredictiveAgent:
    def __init__(self, market_manager, simulation_mode=True):
        self.pipeline = DataPipeline(market_manager)
        self.brain = RLAgent(model_path="agent/brain.pth")
        self.trade_api_url = "http://localhost:8000/trade/execute/confirmed"
        self.confidence_threshold = 0.60 # Lowered slightly to encourage early action

    async def run_cycle(self):
        print("\n" + "="*60)
        print(f"🤖 PREDICTIVE AGENT CYCLE - {datetime.now().strftime('%H:%M:%S')}")
        
        # 1. OBSERVE (Will trigger Auto-Pay)
        state_vector = await self.pipeline.get_market_state()
        
        # Debug: Show the brain what it's seeing
        print(f"🧠 Input Vector Sample: {state_vector[:5]}")

        # 2. PREDICT
        action, confidence, probabilities = self.brain.get_action(state_vector)
        
        print(f"🎯 DECISION: {action} ({confidence*100:.1f}%)")
        print(f"📊 Probs: {probabilities}")

        # 3. ACT
        if action == "BUY" and confidence > self.confidence_threshold:
            self._trigger_trade("USDC", "CRO", 10.0)
        elif action == "SELL" and confidence > self.confidence_threshold:
            self._trigger_trade("CRO", "USDC", 100.0)
        else:
            print(f"⏸️  HOLD: Confidence {confidence*100:.1f}% < {self.confidence_threshold*100}%")

        return {"action": action}

    def _trigger_trade(self, token_in, token_out, amount):
        print(f"🚀 EXECUTING TRADE: {amount} {token_in} -> {token_out}")
        try:
            payload = {"token_in": token_in, "token_out": token_out, "amount": amount, "slippage": 1.0}
            res = requests.post(self.trade_api_url, json=payload, timeout=5)
            print(f"   ✅ Trade Status: {res.status_code} - {res.text[:100]}")
        except Exception as e:
            print(f"   ❌ Trade Failed: {e}")