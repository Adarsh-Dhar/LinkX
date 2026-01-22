from fastapi import FastAPI, Body, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import sys
import os

# --- 1. Import the Agent from main.py ---
# We make sure the current directory is in the path so we can import 'main'
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Import the class you just updated in the previous step
from main import LightweightAgent

app = FastAPI()

# --- 2. Enable CORS ---
# This allows your Next.js frontend (localhost:3000) to talk to this Python server (localhost:8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 3. Initialize the Agent ---
print("🚀 Initializing Alpha Agent...")
agent = LightweightAgent()
print("✅ Agent Ready.")


@app.post("/chat")
async def chat_endpoint(payload: dict = Body(...)):
    """
    Receives chat messages from the frontend and passes them to the Agent.
    """
    user_message = payload.get("message", "")
    print(f"📩 Received: {user_message}")
    try:
        reply = agent.interact(user_message)
        return JSONResponse(content={"reply": reply, "success": True}, status_code=200)
    except Exception as e:
        print(f"❌ Error: {e}")
        return JSONResponse(content={"reply": f"🔥 Agent Error: {str(e)}", "success": False}, status_code=500)

@app.get("/status")
async def get_status():
    return {"status": "online", "agent": "connected"}

if __name__ == "__main__":
    import uvicorn
    # Runs the server on port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)