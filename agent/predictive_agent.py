import asyncio
from datetime import datetime
import requests
import json

import numpy as np
import pandas as pd
import pandas_ta as ta
from .brain import RLAgent
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

        # --- NEW: Fetch price history for indicators ---
        price_history = self.get_price_history()
        indicators = self.calculate_indicators(price_history)
        print(f"📈 RSI: {indicators['rsi']:.2f} | MACD: {indicators['macd']:.2f} | EMA: {indicators['ema']:.4f}")

        # 2. PREDICT (optionally, use indicators as extra features)
        action, confidence, probabilities = self.brain.get_action(state_vector)

        # --- Example: Use indicators to filter/override actions ---
        if indicators['rsi'] > 70:
            print("⚠️ RSI > 70 (Overbought): Forcing HOLD")
            action = "HOLD"
        elif indicators['rsi'] < 30:
            print("⚠️ RSI < 30 (Oversold): Forcing BUY")
            action = "BUY"

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

    def get_price_history(self, length: int = 100):
        # Fetch price history from the pipeline or API (stub: random walk for now)
        # Replace with real price history fetch as needed
        try:
            # Try to fetch from pipeline if available
            if hasattr(self.pipeline, 'fetch_price_history'):
                return self.pipeline.fetch_price_history(length)
        except Exception:
            pass
        # Fallback: generate synthetic price history
        np.random.seed(42)
        prices = np.cumsum(np.random.randn(length)) + 100
        return prices.tolist()

    def calculate_indicators(self, prices):
        # Calculate RSI, MACD, EMA using pandas-ta
        df = pd.DataFrame({'close': prices})
        rsi = ta.rsi(df['close'], length=14).iloc[-1]
        macd = ta.macd(df['close']).iloc[-1]['MACD_12_26_9']
        ema = ta.ema(df['close'], length=21).iloc[-1]
        return {
            'rsi': float(rsi) if rsi is not None else 50.0,
            'macd': float(macd) if macd is not None else 0.0,
            'ema': float(ema) if ema is not None else df['close'].iloc[-1],
        }

    def _trigger_trade(self, token_in, token_out, amount):
        print(f"🚀 EXECUTING TRADE: {amount} {token_in} -> {token_out}")
        try:
            payload = {"token_in": token_in, "token_out": token_out, "amount": amount, "slippage": 1.0}
            res = requests.post(self.trade_api_url, json=payload, timeout=5)
            print(f"   ✅ Trade Status: {res.status_code} - {res.text[:100]}")
            # Send trade status to frontend SSE endpoint
            try:
                sse_payload = {
                    "token_in": token_in,
                    "token_out": token_out,
                    "amount": amount,
                    "status_code": res.status_code,
                    "status_text": res.text[:100],
                }
                requests.post("http://localhost:3000/api/dashboard/trade-status", json=sse_payload, timeout=2)
            except Exception as sse_err:
                print(f"   ⚠️  SSE Notify Failed: {sse_err}")
        except Exception as e:
            print(f"   ❌ Trade Failed: {e}")