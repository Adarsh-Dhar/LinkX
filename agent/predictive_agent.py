import asyncio
from datetime import datetime
import requests
import json

import numpy as np
import pandas as pd
import asyncio
from datetime import datetime
import requests
import json
import numpy as np

# We keep the pipeline to fetch data, but we bypass the 'Brain'
try:
    from .data_pipeline import DataPipeline
except ImportError:
    from agent.data_pipeline import DataPipeline

class PredictiveAgent:
    def __init__(self, market_manager, simulation_mode=True):
        self.pipeline = DataPipeline(market_manager)
        self.trade_api_url = "http://localhost:8000/trade/execute/confirmed"
        self.previous_price = None
        self.min_price_change = 0.001  # 0.1% movement required to confirm trend

    async def run_cycle(self):
        print("\n" + "="*60)
        print(f"🤖 EXPERT TRADER CYCLE - {datetime.now().strftime('%H:%M:%S')}")
        # 1. ACQUIRE & ANALYZE DATA
        state_vector = await self.pipeline.get_market_state()
        # Extract components (Price is index 0, Data Signals are 1-10)
        current_price = float(state_vector[0])
        data_signals = state_vector[1:11]
        # Calculate Average Sentiment (Filter out 0.0 failures)
        valid_signals = [x for x in data_signals if x > 0.0]
        avg_signal = np.mean(valid_signals) if valid_signals else 0.5
        # 2. ANALYZE PRICE TREND
        trend = "NEUTRAL"
        if self.previous_price:
            price_change = (current_price - self.previous_price) / self.previous_price
            if price_change > self.min_price_change: trend = "UPTREND"
            elif price_change < -self.min_price_change: trend = "DOWNTREND"
        self.previous_price = current_price
        # 3. EXPERT DECISION LOGIC
        print(f"📊 ANALYSIS: Price ${current_price:.4f} ({trend}) | Sentiment: {avg_signal:.2f}")
        action = "HOLD"
        # BUY: Price is rising AND Sentiment is Good (> 0.5)
        if trend == "UPTREND" and avg_signal >= 0.5:
            action = "BUY"
        # STRONG BUY: Sentiment is Very High (Predictive)
        elif avg_signal > 0.75:
            action = "BUY"
        # SELL: Price is falling AND Sentiment is Bad (< 0.5)
        elif trend == "DOWNTREND" and avg_signal <= 0.5:
            action = "SELL"
        # PANIC SELL: Sentiment is Very Low
        elif avg_signal < 0.25:
            action = "SELL"
        print(f"🎯 EXPERT DECISION: {action}")
        # 4. EXECUTE
        if action == "BUY":
            self._trigger_trade("USDC", "CRO", 10.0)
        elif action == "SELL":
            self._trigger_trade("CRO", "USDC", 100.0)
        return {"action": action}

    def _trigger_trade(self, token_in, token_out, amount):
        print(f"🚀 EXECUTING TRADE: {amount} {token_in} -> {token_out}")
        try:
            payload = {"token_in": token_in, "token_out": token_out, "amount": amount, "slippage": 1.0}
            res = requests.post(self.trade_api_url, json=payload, timeout=5)
            print(f"   ✅ Trade Status: {res.status_code}")
        except Exception as e:
            print(f"   ❌ Execution Failed: {e}")
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