
# ...existing code...


# ...existing code...

# Expose optimization graph data for dashboard (must be after app is defined)

from fastapi import FastAPI, Query
from contextlib import asynccontextmanager
import threading
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agent.main import IntelligentAgent
from agent.predictive_agent import PredictiveAgent
from agent.autonomous_loop import run_autonomous_loop


from pydantic import BaseModel

app = FastAPI()
agent_instance = None

# Chat request model
class ChatRequest(BaseModel):
    message: str

# --- INTENT-DRIVEN CHAT ENDPOINT ---
@app.post("/chat")
async def handle_chat(request: ChatRequest):
    global agent_instance
    msg = request.message.lower()

    # 1. Handle Direct Trade Commands
    if "buy" in msg or "sell" in msg:
        # Simple extraction: "buy 50 usdc of wcro"
        amount = 50.0 # default
        import re
        if "usdc" in msg:
            match = re.search(r'(\d+)\s*usdc', msg)
            if match:
                amount = float(match.group(1))
        side = "BUY" if "buy" in msg else "SELL"
        # Set manual command for agent to pick up
        if hasattr(agent_instance, 'current_predictive_instance') and agent_instance.current_predictive_instance:
            agent_instance.current_predictive_instance.manual_command = {
                'type': 'trade',
                'side': side,
                'amount': amount
            }
            return {"reply": f"🚀 Manual Override: Executing {side} for {amount} USDC."}
        else:
            return {"reply": "❌ Predictive agent not ready for manual trade."}

    # 2. Handle Risk/Profit Insights
    if "risk" in msg or "don't spend" in msg:
        import re
        match = re.search(r'(\d+)', msg)
        if match:
            new_limit = float(match.group(1))
            if hasattr(agent_instance, 'current_predictive_instance') and agent_instance.current_predictive_instance:
                agent_instance.current_predictive_instance.max_cost = new_limit
                return {"reply": f"✅ Risk profile updated. I will not spend more than {new_limit} USDC on data/trades."}
            else:
                return {"reply": "❌ Predictive agent not ready to update risk profile."}

    # 3. Handle Profit Goals
    if "profit" in msg:
        if hasattr(agent_instance, 'current_predictive_instance') and agent_instance.current_predictive_instance:
            agent_instance.current_predictive_instance.human_instruction = 'profit_goal'
            return {"reply": "💰 Profit target noted. I will adjust my exit strategy to prioritize your goal."}
        else:
            return {"reply": "❌ Predictive agent not ready to update profit goal."}

    # 4. Handle Pause/Stop
    if "pause" in msg or "stop" in msg:
        if hasattr(agent_instance, 'current_predictive_instance') and agent_instance.current_predictive_instance:
            agent_instance.current_predictive_instance.paused = True
            return {"reply": "⏸️ Agent paused. No new trades will be made until resumed."}
        else:
            return {"reply": "❌ Predictive agent not ready to pause."}

    # 5. Default: Forward to LLM/Agent Brain (not implemented)
    return {"reply": "🤖 Message received. (No intent detected or LLM fallback not implemented.)"}

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