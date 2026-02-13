# ==========================================
# 🧠 LinkX Production-Ready Tools & Brain
# ==========================================
import json
import os
import time
import re
from datetime import datetime

from openai import AsyncOpenAI

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
        self.client = AsyncOpenAI(
            base_url="https://models.inference.ai.azure.com",
            api_key=self.token,
        )
        self.model_name = "gpt-4o"
        self.system_prompt = "You are a world-class trading strategist. Analyze the provided market data and recommend the optimal trading action."

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

        REASONING RULES:
        1. MANDATORY BASELINE: If 'purchased_intelligence' is empty, you MUST buy at least one node (Sentiment or Macro) immediately to establish a market baseline. 
        2. DO NOT STAY BLIND: You are currently blind. A professional trader never trades without data. Spend the budget now.
        3. VALIDITY: Data is valid for 300 seconds (5m). REUSE it if 'seconds_since_last_buy' < 300.
        4. baseline: If you have NO node data, you MUST buy at least one to understand the market.
        5. thrift: If technicals are neutral and you have fresh data, buy nothing.
        
        Respond in JSON: {{"nodes_to_buy": ["Exact Node Name"], "reasoning": "..."}}
        """
        try:
            response = await self._generate_content(scout_prompt)
            return json.loads(response)
        except Exception as e:
            print(f"   ⚠️ Scout Error: {e}")
            return {"nodes_to_buy": []}

    async def get_strategy(self, market_data, memory):
        user_message = f"MARKET SNAPSHOT: {json.dumps(market_data, indent=2)}"
        try:
            response = await self._generate_content(user_message, system_override=self.system_prompt)
            return json.loads(response)
        except Exception as e:
            print(f"   ⚠️ Strategist Error: {e}")
            try:
                print(f"   ⚠️ Raw strategist response: {response}")
            except Exception:
                pass
            return {"execution_bias": "NEUTRAL", "risk_confidence": 0.0, "reasoning": "Fallback due to error."}

    async def _generate_content(self, content, system_override=None):
        messages = [
            {"role": "system", "content": system_override or "You are a helpful assistant."},
            {"role": "user", "content": content}
        ]
        completion = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.2
        )
        text = completion.choices[0].message.content
        # FIX: Robustly extract JSON even if there is markdown or leading text
        import re
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            return json_match.group(0)
        return text.strip()