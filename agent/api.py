"""
FastAPI wrapper for Alpha-Consumer Agent
Exposes the LightweightAgent via HTTP API for frontend integration
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os
import sys

# Import the agent
from lightweight_agent import LightweightAgent

app = FastAPI(title="Alpha-Consumer Agent API", version="1.0.0")

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3600",  # Frontend dev server
        "http://localhost:3000",  # Alternative port
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the agent
agent = None

@app.on_event("startup")
async def startup_event():
    """Initialize agent on startup"""
    global agent
    try:
        agent = LightweightAgent()
        print("✅ Agent initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        sys.exit(1)


# Request/Response Models
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    success: bool = True

class StatusResponse(BaseModel):
    status: str
    network: str
    wallet_address: Optional[str] = None
    cro_balance: Optional[str] = None
    usdc_balance: Optional[str] = None


# Endpoints
@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    """
    Send a message to the agent and get a response
    Handles all trading commands: balance, swap, signals, portfolio, etc.
    """
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        # Use the agent's interact method to process the message
        response = agent.interact(req.message)
        return ChatResponse(response=response, success=True)
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status", response_model=StatusResponse)
async def get_status():
    """
    Get agent status, wallet address, and balances
    """
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        # Get wallet address from agent
        wallet_address = agent.wallet_manager.address if hasattr(agent, 'wallet_manager') else None
        
        # Try to get balances using agent tools
        cro_balance = None
        usdc_balance = None
        
        try:
            # Use the get_balance tool from agent.tools
            from tools import get_balance
            cro_balance = get_balance("CRO")
            usdc_balance = get_balance("USDC")
        except Exception as e:
            print(f"Could not fetch balances: {e}")
        
        return StatusResponse(
            status="online",
            network="Cronos Mainnet",
            wallet_address=wallet_address,
            cro_balance=cro_balance,
            usdc_balance=usdc_balance
        )
    except Exception as e:
        print(f"Error in status endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/signals")
async def get_signals():
    """
    Get trading signals from the market analyst server
    """
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        # Use the agent's get_signals tool
        from tools import get_signals
        signals = get_signals()
        return {"success": True, "signals": signals}
    except Exception as e:
        print(f"Error fetching signals: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "agent_initialized": agent is not None}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
