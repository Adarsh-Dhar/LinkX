
from fastapi import FastAPI
from contextlib import asynccontextmanager
import threading
import os
import sys
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import IntelligentAgent
from autonomous_loop import run_autonomous_loop

agent_instance = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("\n⚡ [API] Lifespan: Booting Agent...")
    global agent_instance
    try:
        agent_instance = IntelligentAgent()
        
        print("🔄 [API] Starting Autonomous Thread...")
        # Start the loop with 10s interval
        t = threading.Thread(target=run_autonomous_loop, args=(agent_instance, 10), daemon=True)
        t.start()
        print("✅ [API] Autonomous Loop Running.")
    except Exception as e:
        print(f"❌ [API] Error: {e}")
    
    yield
    # Shutdown logic if needed

app = FastAPI(lifespan=lifespan)

@app.get("/")
def root():
    return {"status": "Online"}