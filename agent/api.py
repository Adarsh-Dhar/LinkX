# ...existing code...


# ...existing code...



# --- Ensure .env is loaded for environment variables ---
from dotenv import load_dotenv
from pathlib import Path
from pydantic import BaseModel
load_dotenv(Path(__file__).parent.parent / '.env')

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

app = FastAPI(lifespan=lifespan)
agent_instance = None

# --- INTENT PARSER USING OPENROUTER ---
import json
def parse_human_intent(user_message: str):
    # --- Local fallback for simple commands ---
    msg = user_message.strip().lower()

    # Only trigger PAUSE or RESUME on explicit commands
    if msg in ["pause", "pause trading", "pause all trading", "pause agent"]:
        return {"action": "PAUSE"}
    if msg in ["resume", "resume trading", "resume all trading", "resume agent", "unpause", "start trading", "continue trading"]:
        return {"action": "RESUME"}
    # Add more local rules as needed

    system_prompt = """
You are an advanced crypto trading AI. Analyze the user's message and return JSON.
You support financial mandates, including spending limits and refill logic. You can:
- Set a maximum price per data request
- Set a global monthly allowance
- Define refill logic (e.g., auto-replenish wallet with 10 USDC when below a threshold)

Return a JSON object with these fields:
{
    "action": "TRADE" | "PAUSE" | "RESUME" | "SET_LIMIT" | "SET_REFILL" | "NONE",
    "side": "BUY" | "SELL" | null,
    "amount": float | null,
    "limit_type": "MAX_PRICE_PER_REQUEST" | "MONTHLY_ALLOWANCE" | null,
    "limit_value": float | null,
    "refill_amount": float | null,
    "refill_threshold": float | null,
    "conversational_response": "A friendly Gemini-style reply acknowledging the user"
}
If the user just wants to chat, set action to "NONE" and provide a helpful conversational_response.

Examples:
- "Grab me fifty bucks of CRO" -> {"action": "TRADE", "side": "BUY", "amount": 50.0, "conversational_response": "Buying 50 USDC of CRO now!"}
- "Stop for a bit" -> {"action": "PAUSE", "conversational_response": "Pausing all trading as requested."}
- "How are you?" -> {"action": "NONE", "conversational_response": "I'm great! Ready to help you trade or answer questions."}
- "Never spend more than $2 per data request" -> {"action": "SET_LIMIT", "limit_type": "MAX_PRICE_PER_REQUEST", "limit_value": 2.0, "conversational_response": "Understood! I will not spend more than $2 per data request."}
- "Set my monthly trading allowance to $1000" -> {"action": "SET_LIMIT", "limit_type": "MONTHLY_ALLOWANCE", "limit_value": 1000.0, "conversational_response": "Your monthly trading allowance is now set to $1000."}
- "If my wallet drops below $5, refill with $10 automatically" -> {"action": "SET_REFILL", "refill_threshold": 5.0, "refill_amount": 10.0, "conversational_response": "I'll automatically refill your wallet with $10 whenever it drops below $5."}
Return ONLY JSON.
    """
    if not client:
        return {"action": "IGNORE", "error": "OpenAI SDK not installed"}
    try:
        response = client.chat.completions.create(
            model="google/gemini-2.0-flash-exp:free",
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

# --- GEMINI-LIKE INTENT-DRIVEN CHAT ENDPOINT ---
@app.post("/chat")
async def handle_chat(request: ChatRequest):
    global agent_instance
    msg = request.message.lower()

    # Get the actual running instance from the loop
    pred_agent = getattr(agent_instance, 'current_predictive_instance', None)
    if not pred_agent:
        return {"reply": "🤖 Brain is still warming up. Try again in 5 seconds."}

    # 1. Use the LLM to get the Intent JSON
    intent = parse_human_intent(msg)
    print(f"[DEBUG] User message: {msg}")
    print(f"[DEBUG] Parsed intent: {intent}")


    # 2. IMPLEMENT THE INTENT
    action = intent.get("action")

    if action == "PAUSE":
        pred_agent.paused = True
        resp = intent.get("conversational_response")
        return {"reply": resp if resp and str(resp).strip() else "Trading paused as requested."}

    if action == "SET_LIMIT":
        # Example: set spending limits or monthly allowance
        limit_type = intent.get("limit_type")
        limit_value = intent.get("limit_value")
        # Map legacy or ambiguous types to new variable
        if limit_type == "MAX_PRICE_PER_REQUEST":
            limit_type = "MAX_TOTAL_SPEND_PER_TRADE"
        # Store or apply these limits as needed (implement logic in PredictiveAgent)
        if hasattr(pred_agent, 'set_limit'):
            pred_agent.set_limit(limit_type, limit_value)
        # Robust fallback for conversational response
        resp = intent.get("conversational_response")
        if resp and str(resp).strip():
            return {"reply": resp}
        # Hardcoded fallback for per-trade spend limit
        if limit_type == "MAX_TOTAL_SPEND_PER_TRADE":
            if limit_value is not None and str(limit_value).strip():
                return {"reply": f"Understood! I will never spend more than {limit_value} USDC in a single trade."}
            else:
                return {"reply": "Understood! I will never spend more than the specified amount per trade."}
        # Fallback for monthly allowance
        if limit_type == "MONTHLY_ALLOWANCE":
            if limit_value is not None and str(limit_value).strip():
                return {"reply": f"Monthly trading allowance set to {limit_value} USDC."}
            else:
                return {"reply": "Monthly trading allowance set as requested."}
        # Generic fallback
        return {"reply": "Limit set as requested!"}

    if action == "SET_REFILL":
        refill_amount = intent.get("refill_amount")
        refill_threshold = intent.get("refill_threshold")
        if hasattr(pred_agent, 'set_refill_logic'):
            pred_agent.set_refill_logic(refill_threshold, refill_amount)
        resp = intent.get("conversational_response")
        if resp and str(resp).strip():
            return {"reply": resp}
        if refill_amount is not None and refill_threshold is not None:
            return {"reply": f"I'll auto-refill your wallet with {refill_amount} USDC whenever it drops below {refill_threshold} USDC."}
        return {"reply": "Refill logic set!"}

    # 3. UNIVERSAL FALLBACK: Always use AI's conversational response, or provide a generic friendly reply if missing/empty
    resp = intent.get("conversational_response")
    if resp and str(resp).strip():
        return {"reply": resp}
    if action == "SET_LIMIT":
        return {"reply": "Limit set as requested!"}
    if action == "SET_REFILL":
        return {"reply": "Refill logic set as requested!"}
    if action == "TRADE":
        return {"reply": "Trade command received!"}
    if action == "PAUSE":
        return {"reply": "Trading paused as requested."}
    if action == "RESUME":
        pred_agent.paused = False
        pred_agent.block_data_purchases = False  # <-- Clear spend block on resume
        resp = intent.get("conversational_response")
        return {"reply": resp if resp and str(resp).strip() else "▶️ Resuming! I have cleared spend blocks and am ready to trade."}
    return {"reply": "✅ Command received and processed!"}

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