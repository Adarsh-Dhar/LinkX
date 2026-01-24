
from fastapi import FastAPI
import threading
import os
import sys

# Ensure path is correct
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from .main import IntelligentAgent
from .autonomous_loop import run_autonomous_loop

app = FastAPI()
agent_instance = None # Global variable to hold the agent

@app.on_event("startup")
async def startup_event():
    global agent_instance
    print("\n⚡ [API] Startup: Initializing Agent...")
    # 1. Initialize the Agent FIRST
    agent_instance = IntelligentAgent()
    # 2. Check if trader is loaded (Sanity Check)
    if not hasattr(agent_instance, 'trader') or agent_instance.trader is None:
        print("❌ [API] Critical Error: Agent initialized without Trader!")

    # No chat endpoint or __main__ block; handled by FastAPI server

@app.post("/trade/execute/confirmed")
def execute_trade_api(trade_data: dict):
    if not agent_instance or not agent_instance.trader:
        return {"status": "Error", "reason": "Agent not ready"}
    tx = agent_instance.trader.execute_swap(
        trade_data['token_in'],
        trade_data['token_out'],
        trade_data['amount'],
        trade_data.get('slippage', 1.0)
    )
    return {"status": "Executed", "txHash": tx}