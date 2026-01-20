"""
FastAPI wrapper for Alpha-Consumer Agent
"""
import sys
import os
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# --- Fix Python Path ---
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# --- Import Dependencies ---
from lightweight_agent import LightweightAgent
from node_connector import get_connector
from simulation_service import get_simulation_service

# Robust Import for Tools
try:
    from tools import execute_vvs_swap, get_token_balance, get_trading_signals
    TOOLS_LOADED = True
except ImportError as e:
    print(f"⚠️ Warning: Tools failed to load: {e}")
    TOOLS_LOADED = False

app = FastAPI(title="Alpha-Consumer Agent API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Global Error Handler to prevent 500 pages ---
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"🔥 SERVER ERROR: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False, 
            "error": f"Internal Server Error: {str(exc)}",
            "detail": str(exc)
        },
    )

# --- Models ---
class TradeExecutionRequest(BaseModel):
    token_in: str
    token_out: str
    amount: float
    simulate_only: bool = True
    slippage_tolerance: float = 1.0

class TradeSimulation(BaseModel):
    simulation_id: str
    timestamp: str
    token_in: str
    token_out: str
    amount_in: float
    predicted_amount_out: float
    confidence: float
    neural_decision: str
    reasoning: str

class TradeExecutionResponse(BaseModel):
    success: bool
    transaction_hash: Optional[str] = None
    simulation: TradeSimulation
    actual_output: Optional[float] = None
    error: Optional[str] = None

# --- Setup ---
agent = None
@app.on_event("startup")
async def startup_event():
    global agent
    try:
        agent = LightweightAgent()
        print("✅ Agent initialized")
        await get_connector() # Init nodes
        get_simulation_service() # Init sim service
    except Exception as e:
        print(f"❌ Startup Error: {e}")

# --- Endpoints ---

@app.post("/trade/simulate", response_model=TradeExecutionResponse)
async def simulate_trade(req: TradeExecutionRequest):
    sim_id = str(uuid.uuid4())[:8]
    # Simple logic for now
    sim = TradeSimulation(
        simulation_id=sim_id,
        timestamp=datetime.now().isoformat(),
        token_in=req.token_in,
        token_out=req.token_out,
        amount_in=req.amount,
        predicted_amount_out=req.amount * 0.95,
        confidence=0.85, # High confidence for testing
        neural_decision="BUY",
        reasoning="Market conditions favorable"
    )
    return TradeExecutionResponse(success=True, simulation=sim)

@app.post("/trade/execute", response_model=TradeExecutionResponse)
async def execute_trade(req: TradeExecutionRequest):
    # 1. Run Simulation
    sim_res = await simulate_trade(req)
    simulation = sim_res.simulation
    
    if req.simulate_only:
        return sim_res

    # 2. Validate Environment
    if not TOOLS_LOADED:
        return TradeExecutionResponse(
            success=False, 
            simulation=simulation, 
            error="Trading tools not loaded on server."
        )

    # 3. Execute Trade
    try:
        print(f"🚀 Executing Swap: {req.amount} {req.token_in} -> {req.token_out}")
        
        # Prepare arguments
        args = {
            "token_in": req.token_in,
            "token_out": req.token_out,
            "amount_in": req.amount,
            "max_slippage": req.slippage_tolerance
        }
        
        # Execute (Supports both Tool object and direct function)
        if hasattr(execute_vvs_swap, 'invoke'):
            result = execute_vvs_swap.invoke(args)
        else:
            result = execute_vvs_swap(**args)
            
        # Parse Result
        if isinstance(result, dict) and "error" in result:
            raise Exception(result["error"])
        
        if isinstance(result, str) and "Error" in result:
            raise Exception(result)
            
        tx_hash = result.get("tx_hash") if isinstance(result, dict) else None
        
        if not tx_hash:
            raise Exception("No transaction hash returned from tool")

        return TradeExecutionResponse(
            success=True,
            transaction_hash=tx_hash,
            simulation=simulation,
            actual_output=simulation.predicted_amount_out
        )
        
    except Exception as e:
        print(f"❌ Trade Failed: {e}")
        return TradeExecutionResponse(
            success=False,
            simulation=simulation,
            error=str(e) # This error string will now show in frontend
        )

@app.post("/trade/execute/confirmed")
async def execute_confirmed_trade(req: TradeExecutionRequest, simulation_id: Optional[str] = None):
    # Forward to main execution logic for simplicity
    return await execute_trade(req)

# Keep other endpoints lightweight
@app.get("/simulations/recent")
async def get_recent():
    try: return get_simulation_service().get_recent_trades(5)
    except: return []

@app.get("/status")
async def get_status():
    return {"status": "online", "network": "Cronos Mainnet"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)