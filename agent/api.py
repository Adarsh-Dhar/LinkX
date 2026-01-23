from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
import sys
import os

# Import the new Intelligent Agent
from main import IntelligentAgent

app = FastAPI()

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