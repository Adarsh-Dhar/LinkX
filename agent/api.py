from fastapi import FastAPI
from contextlib import asynccontextmanager
import threading
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agent.main import IntelligentAgent
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

app = FastAPI(lifespan=lifespan)

@app.get("/")
def root(): return {"status": "Online"}