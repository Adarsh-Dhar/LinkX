
# ...existing code...


# ...existing code...


# --- Ensure .env is loaded for environment variables ---
from dotenv import load_dotenv
load_dotenv()

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
    # --- Local fallback for simple commands ---
    msg = user_message.strip().lower()
    # Fuzzy/partial matching for pause/resume
    import difflib
    def fuzzy_match(word, options, cutoff=0.5):
        # Lower cutoff for more permissive matching
        matches = difflib.get_close_matches(word, options, n=1, cutoff=cutoff)
        if matches:
            return matches[0]
        # Substring check for even more permissive matching
        for opt in options:
            if word in opt or opt in word:
                return opt
        return None

    # Tokenize message for fuzzy matching
    tokens = msg.split()
    pause_words = ["pause", "stop", "hold"]
    resume_words = ["resume", "start", "continue"]
    for token in tokens:
        if fuzzy_match(token, pause_words):
            return {"action": "PAUSE"}
        if fuzzy_match(token, resume_words):
            return {"action": "RESUME"}
    # Add more local rules as needed

    system_prompt = """
You are an advanced crypto trading AI. Analyze the user's message and return JSON.
{
    "action": "TRADE" | "PAUSE" | "RESUME" | "SET_LIMIT" | "NONE",
    "side": "BUY" | "SELL",
    "amount": float,
    "conversational_response": "A friendly Gemini-style reply acknowledging the user"
}
If the user just wants to chat, set action to "NONE" and provide a helpful conversational_response.
Example: "Grab me fifty bucks of CRO" -> {"action": "TRADE", "side": "BUY", "amount": 50.0, "conversational_response": "Buying 50 USDC of CRO now!"}
Example: "Stop for a bit" -> {"action": "PAUSE", "conversational_response": "Pausing all trading as requested."}
Example: "How are you?" -> {"action": "NONE", "conversational_response": "I'm great! Ready to help you trade or answer questions."}
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
        if "conversational_response" in intent:
            return {"reply": intent["conversational_response"]}
        else:
            return {"reply": "⚠️ No AI response generated for PAUSE."}

    if action == "RESUME":
        pred_agent.paused = False
        if "conversational_response" in intent:
            return {"reply": intent["conversational_response"]}
        else:
            return {"reply": "⚠️ No AI response generated for RESUME."}

    if action == "TRADE":
        pred_agent.manual_command = {"side": intent.get("side"), "amount": intent.get("amount")}
        if "conversational_response" in intent:
            return {"reply": intent["conversational_response"]}
        else:
            return {"reply": "⚠️ No AI response generated for TRADE."}

    # 3. FALLBACK: Always use AI's conversational response, error if missing
    if "conversational_response" in intent:
        return {"reply": intent["conversational_response"]}
    else:
        return {"reply": "⚠️ No AI response generated. Please try again or check model configuration."}

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