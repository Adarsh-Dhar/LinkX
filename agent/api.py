
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


from fastapi import FastAPI
from contextlib import asynccontextmanager
import threading
import os
import sys
import time

# Ensure path is correct
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


# (Removed: use relative imports above)

# Global variable
agent_instance = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Modern startup/shutdown handler for FastAPI.
    Guarantees the Agent and Background Thread start correctly.
    """
    global agent_instance
    print("\n⚡ [API] Lifespan Startup: Initializing Agent...")
    
    try:
        # 1. Initialize Agent
        agent_instance = IntelligentAgent()
        
        if not hasattr(agent_instance, 'trader') or agent_instance.trader is None:
            print("❌ [API] Critical Error: Agent initialized without Trader!")
        else:
            print("✅ [API] Agent & Trader Ready.")

        # 2. Start Background Loop (10s Interval)
        print("🔄 [API] Launching Autonomous Trading Thread...")
        loop_thread = threading.Thread(
            target=run_autonomous_loop, 
            args=(agent_instance, 10),  # <--- FORCE 10 SECOND INTERVAL
            daemon=True
        )
        loop_thread.start()
        print("✅ [API] Background Thread Started.")
        
    except Exception as e:
        print(f"❌ [API] Startup Failed: {e}")
        import traceback
        traceback.print_exc()
        
    yield  # Application runs here
    
    print("🛑 [API] Shutting down...")

# Initialize App with Lifespan
app = FastAPI(lifespan=lifespan)

@app.get("/")
def root():
    status = "Active" if agent_instance else "Initializing"
    addr = agent_instance.wallet.address if agent_instance and agent_instance.wallet else "Unknown"
    return {"status": status, "agent_address": addr}

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