# ==========================================
# 🧠 LinkX Production-Ready Tools & Brain
# ==========================================
import json
import os
import time
import re
from datetime import datetime
from openai import OpenAI

from web3 import Web3
from dotenv import load_dotenv

# --- VVS ROUTER ABI (imported from abi/vvsrouter.ts) ---
import pathlib

# Load the ABI from the TypeScript file (as a Python list)
VVSROUTER_ABI_PATH = os.path.join(os.path.dirname(__file__), '..', 'abi', 'vvsrouter.ts')
def _load_vvsrouter_abi():
    try:
        with open(VVSROUTER_ABI_PATH, 'r') as f:
            content = f.read()
        import re, json
        match = re.search(r'VVSRouter_ABI\s*=\s*(\[.*\])', content, re.DOTALL)
        if match:
            abi_json = match.group(1)
            return json.loads(abi_json)
    except Exception as e:
        print(f"[tools.py] Warning: Could not load VVSRouter_ABI: {e}")
    return []

ROUTER_ABI = _load_vvsrouter_abi()

load_dotenv()

# --- 1. ALPHA STRATEGIST (THE BRAIN) ---

class AlphaStrategist:
    def __init__(self, api_key=None):
        self.token = api_key or os.getenv("GITHUB_TOKEN")
        if not self.token:
            raise ValueError("❌ GITHUB_TOKEN not found in environment.")
        self.client = OpenAI(
            base_url="https://models.inference.ai.azure.com",
            api_key=self.token,
        )
        self.model_name = "gpt-4o-mini"

    async def assess_data_needs(self, market_snapshot, node_catalog):
        # Pre-process: Calculate 'Seconds Since Last Buy' for the AI
        from datetime import datetime
        import json
        for n in node_catalog:
            sec_ago = 999999
            if n.get('last_bought_at'):
                try:
                    dt = datetime.fromisoformat(n['last_bought_at'].replace('Z', ''))
                    sec_ago = (datetime.utcnow() - dt).total_seconds()
                except: pass
            n['seconds_since_last_buy'] = int(sec_ago)

        scout_prompt = f"""
        You are a Data Procurement Officer.
        MARKET: {json.dumps(market_snapshot)}
        CATALOG: {json.dumps(node_catalog)}

        STRATEGY:
        1. VALIDITY: Data is valid for 300 seconds (5m). REUSE it if 'seconds_since_last_buy' < 300.
        2. baseline: If you have NO node data, you MUST buy at least one to understand the market.
        3. thirft: If technicals are neutral and you have fresh data, buy nothing.
        
        Respond in JSON: {{"nodes_to_buy": ["Exact Node Name"], "reasoning": "..."}}
        """
        try:
            response = await self._generate_content(scout_prompt)
            return json.loads(response)
        except Exception as e:
            print(f"   ⚠️ Scout Error: {e}")
            return {"nodes_to_buy": []}

    async def get_strategy(self, market_data, memory):
        user_message = f"""
        MARKET SNAPSHOT: {json.dumps(market_data, indent=2)}
        SHORT TERM MEMORY: {json.dumps(memory, indent=2)}
        """
        system_prompt = """
You are the 'AlphaStrategist', an advanced AI Portfolio Manager for a decentralized hedge fund.
INPUT CONTEXT:
1. MARKET DATA: Recent price action and trends.
2. NODE INTELLIGENCE: Status of data providers (e.g., 'Sentiment Node', 'Macro Node'). Trust data from recently updated nodes more.
3. PERFORMANCE HISTORY: Your recent win/loss record. If you are on a losing streak, REDUCE your confidence and trade size.
4. QUALITATIVE INTEL: External alerts.

DECISION RULES:
1. SEEK EDGE: Do not default to 0.60. If technicals are bullish but you have no node data, set confidence to 0.1 (Wait for data).
    2. INVEST IN INFO: If you have no node data and the technical trend is changing, you MUST buy data to confirm.
    3. CONFIRMATION: If purchased intelligence confirms technicals, increase confidence to 0.85+.
4. NEVER stay at exactly 0.50 unless there is literally zero data. As a trader, you must find an edge.
5. **MASTER SIGNAL:** If `human_intel` suggests "downside risks", "liquidity exits", or "protocol alerts", you MUST bias towards SHORT. This overrides bullish technicals.
6. **PROBABILISTIC OUTPUT:** Never return 1.0 confidence. The maximum is 0.99.
7. **RISK MANAGEMENT:** If `agent_performance` shows recent losses, be conservative.
8. **SAFETY:** Do not use words like 'attack', 'kill', or 'destroy'. Use 'volatility', 'correction', and 'defensive positioning'.

Respond STRICTLY in JSON format with:
{
    "execution_bias": "LONG" | "SHORT" | "NEUTRAL",
    "risk_confidence": <float between 0.0 and 0.99>,
    "reasoning": "<concise explanation citing specific nodes or history>"
}
"""
        try:
            response = await self._generate_content(user_message, system_override=system_prompt)
            return json.loads(response)
        except Exception as e:
            print(f"   ⚠️ Strategist Error: {e}")
            return {"execution_bias": "NEUTRAL", "risk_confidence": 0.0, "reasoning": "Error in reasoning engine."}

    async def _generate_content(self, content, system_override=None):
        messages = [
            {"role": "system", "content": system_override or "You are a helpful assistant."},
            {"role": "user", "content": content}
        ]
        completion = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages
        )
        # Remove any leading/trailing ```json or ``` tags
        result = completion.choices[0].message.content
        if result.strip().startswith('```json'):
            result = result.strip()[7:]
        result = result.strip().strip('`').strip()
        return result