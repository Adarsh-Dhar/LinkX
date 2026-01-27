
# ...existing code...


# ...existing code...

# Expose optimization graph data for dashboard (must be after app is defined)


from fastapi import FastAPI, Query
from contextlib import asynccontextmanager
import threading
import os
import sys

# --- OpenRouter Client Setup ---
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None
    # You must install openai: pip install openai

client = None
if OpenAI:
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY"),
    )

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agent.main import IntelligentAgent
from agent.predictive_agent import PredictiveAgent
from agent.autonomous_loop import run_autonomous_loop


from pydantic import BaseModel


app = FastAPI()
agent_instance = None

# --- INTENT PARSER USING OPENROUTER ---
import json
def parse_human_intent(user_message: str):
    if not client:
        return {"action": "IGNORE", "error": "OpenAI SDK not installed"}
    system_prompt = """
    You are a trading assistant. Convert user speech into a JSON command.
    Possible Actions: 
    - TRADE (side: \"BUY\"/\"SELL\", amount: float)
    - SET_LIMIT (limit: float)
    - PAUSE ()
    - RESUME ()
    - IGNORE ()
    
    Example: \"Grab me fifty bucks of CRO\" -> {\"action\": \"TRADE\", \"side\": \"BUY\", \"amount\": 50.0}
    Example: \"Stop for a bit\" -> {\"action\": \"PAUSE\"}
    Return ONLY JSON.
    """
    try:
        response = client.chat.completions.create(
            model="openai/gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            response_format={ "type": "json_object" }
        )
        content = response.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        return {"action": "IGNORE", "error": str(e)}

# Chat request model
class ChatRequest(BaseModel):
    message: str


# --- INTENT-DRIVEN CHAT ENDPOINT (OpenRouter) ---
@app.post("/chat")
async def handle_chat(request: ChatRequest):
    global agent_instance
    msg = request.message
    intent = parse_human_intent(msg)
    print(f"[DEBUG] User message: {msg}")
    print(f"[DEBUG] Parsed intent: {intent}")

    # Handle errors from intent parser
    if intent.get("action") == "IGNORE" and "error" in intent:
        return {"reply": f"❌ Intent parsing failed: {intent['error']}"}

    # Route intent to agent actions
    if intent.get("action") == "TRADE":
        side = intent.get("side")
        amount = intent.get("amount")
        if hasattr(agent_instance, 'current_predictive_instance') and agent_instance.current_predictive_instance:
            agent_instance.current_predictive_instance.manual_command = {
                'type': 'trade',
                'side': side,
                'amount': amount
            }
            return {"reply": f"🚀 Manual Override: Executing {side} for {amount} USDC."}
        else:
            return {"reply": "❌ Predictive agent not ready for manual trade."}

    if intent.get("action") == "SET_LIMIT":
        limit = intent.get("limit")
        if hasattr(agent_instance, 'current_predictive_instance') and agent_instance.current_predictive_instance:
            min_allowed_cost = 10.0
            if limit is not None and limit >= min_allowed_cost:
                agent_instance.current_predictive_instance.max_cost = limit
            else:
                agent_instance.current_predictive_instance.max_cost = 100.0
            agent_instance.current_predictive_instance.block_data_purchases = False  # Reset block if limit is raised
            return {"reply": f"✅ Risk profile updated. I will not spend more than {agent_instance.current_predictive_instance.max_cost} USDC on data/trades. Block reset."}
        else:
            return {"reply": "❌ Predictive agent not ready to update risk profile."}

    if intent.get("action") == "PAUSE":
        if hasattr(agent_instance, 'current_predictive_instance') and agent_instance.current_predictive_instance:
            agent_instance.current_predictive_instance.paused = True
            return {"reply": "⏸️ Agent paused. No new trades will be made until resumed."}
        else:
            return {"reply": "❌ Predictive agent not ready to pause."}

    if intent.get("action") == "RESUME":
        if hasattr(agent_instance, 'current_predictive_instance') and agent_instance.current_predictive_instance:
            agent_instance.current_predictive_instance.paused = False
            return {"reply": "▶️ Agent resumed. Trading operations are active."}
        else:
            return {"reply": "❌ Predictive agent not ready to resume."}

    if intent.get("action") == "IGNORE":
        return {"reply": "🤖 Message received. (No actionable intent detected.)"}

    return {"reply": f"🤖 Message received. (Unknown intent: {intent})"}

@asynccontextmanager
async def lifespan(app: FastAPI):
    global agent_instance
    print("\n⚡ [API] Booting...")
    try:
        agent_instance = IntelligentAgent()
        # Start Loop
        t = threading.Thread(target=run_autonomous_loop, args=(agent_instance, 10), daemon=True)
        t.start()
        print("✅ [API] Autonomous Loop Started.")
    except Exception as e:
        print(f"❌ [API] Error: {e}")
    yield

# Expose optimization graph data for dashboard
@app.get("/optimization-graph")
async def optimization_graph(
    situation: str = Query(..., description="Market situation, e.g. PARABOLIC_PUMP"),
    mode: str = Query("BALANCED", description="Node selection mode: BALANCED, ACCURATE, ECONOMY"),
    min_accuracy: int = Query(15, description="Minimum accuracy for node selection"),
    max_cost: float = Query(50.0, description="Maximum cost for node selection")
):
    agent = agent_instance or IntelligentAgent()
    all_nodes = await agent.pipeline.refresh_market_knowledge()
    # Use optimizer to get graph data for the situation
    graph_data = agent.get_optimization_graph_data(all_nodes, situation)
    return {"graph": graph_data, "situation": situation, "mode": mode}
from fastapi import FastAPI, Query
from contextlib import asynccontextmanager
import threading
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agent.main import IntelligentAgent
from agent.predictive_agent import PredictiveAgent
from agent.autonomous_loop import run_autonomous_loop

agent_instance = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global agent_instance
    print("\n⚡ [API] Booting...")
    try:
        agent_instance = IntelligentAgent()
        # Start Loop
        t = threading.Thread(target=run_autonomous_loop, args=(agent_instance, 10), daemon=True)
        t.start()
        print("✅ [API] Autonomous Loop Started.")
    except Exception as e:
        print(f"❌ [API] Error: {e}")
    yield


# Expose cost-accuracy graph for dashboard
@app.get("/cost-accuracy-graph")
async def cost_accuracy_graph(
    situation: str = Query(..., description="Market situation, e.g. PARABOLIC_PUMP"),
    mode: str = Query("BALANCED", description="Node selection mode: BALANCED, ACCURATE, ECONOMY"),
    min_accuracy: int = Query(15, description="Minimum accuracy for node selection"),
    max_cost: float = Query(50.0, description="Maximum cost for node selection")
):
    agent = agent_instance or IntelligentAgent()
    all_nodes = await agent.pipeline.refresh_market_knowledge()
    # Use optimizer to get node list for the situation
    graph = agent.cost_accuracy_graph(all_nodes, situation)
    return {"graph": graph}

@app.get("/")
def root(): return {"status": "Online"}