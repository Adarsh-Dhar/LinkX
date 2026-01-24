from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
import sys
import os


# Import the new Intelligent Agent (always use absolute import for FastAPI/uvicorn)

# Import TradingEngine for trade execution endpoint
from agent.trading_engine import TradingEngine
from agent.data_pipeline import DataPipeline
from agent.main import IntelligentAgent


app = FastAPI()

# Initialize TradingEngine for trade execution endpoint
import os
from dotenv import load_dotenv
load_dotenv()
trading_engine = TradingEngine(
    smart_router=None,  # Provide actual router if needed
    data_pipeline=DataPipeline(None),
    neural_brain=None
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

print("🚀 Initializing Intelligent Alpha Agent...")
agent = IntelligentAgent()
print("✅ Agent Ready.")

@app.post("/chat")
async def chat_endpoint(payload: dict = Body(...)):
    user_message = payload.get("message", "")
    print(f"📩 Input: {user_message}")
    
    try:
        reply = agent.interact(user_message)
        return {"reply": reply, "success": True}
    except Exception as e:
        return {"reply": f"🔥 Error: {str(e)}", "success": False}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


# --- Trade Execution Endpoint ---
from fastapi import Request
@app.post("/trade/execute/confirmed")
async def trade_execute_confirmed(payload: dict = Body(...)):
    token_in = payload.get("token_in")
    token_out = payload.get("token_out")
    amount = payload.get("amount")
    slippage = payload.get("slippage", 0.01)
    try:
        result = trading_engine.execute_swap_with_slippage(token_in, token_out, amount, slippage)
        tx_hash = result.get("tx_hash")
        return {"tx_hash": tx_hash, "result": result, "success": True}
    except Exception as e:
        return {"error": str(e), "success": False}