"""
Real FastAPI Agent - Minimal implementation without broken dependencies
Uses real neural network and data pipeline without crypto_com_agent_client
"""
from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import sys
from datetime import datetime
import json
import asyncio
import numpy as np
import torch
from pathlib import Path

# Import neural components directly
from brain import RLAgent
from data_pipeline import DataPipeline

app = FastAPI(title="Alpha-Consumer Agent API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3600", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
brain = None
data_pipeline = None
connected_websockets: List[WebSocket] = []

@app.on_event("startup")
async def startup_event():
    """Initialize neural components on startup"""
    global brain, data_pipeline
    
    print("🚀 Initializing Real Agent API...")
    
    # Load the brain (neural network). Create if not exists.
    brain_path = Path(__file__).parent / "brain.pth"
    
    if brain_path.exists():
        brain = RLAgent(model_path=str(brain_path))
        print("✅ Neural network loaded from brain.pth")
    else:
        print("🆕 Creating new untrained neural network (brain.pth not found)")
        brain = RLAgent(model_path=str(brain_path))
        # Save the freshly initialized model
        torch.save(brain.model.state_dict(), str(brain_path))
        print(f"💾 Saved initialized model to {brain_path}")
    
    brain.model.eval()
    
    # Initialize data pipeline. Fail hard if broken.
    data_pipeline = DataPipeline()
    print("✅ Data pipeline initialized")
    
    print("✨ Agent API ready")

@app.get("/")
async def root():
    return {
        "status": "ok",
        "message": "Alpha-Consumer Real Agent API",
        "neural_network_loaded": True,
        "data_pipeline_ready": True
    }

@app.get("/nodes/status")
async def get_nodes_status():
    """Get status of 48 data nodes"""
    if data_pipeline is None:
        raise HTTPException(status_code=500, detail="Data pipeline not initialized")

    # Use live registry providers if available, otherwise static mapping inside pipeline
    vector = await data_pipeline.get_market_state()
    # Build status based on last fetch metadata
    nodes = []
    for idx, key in enumerate(getattr(data_pipeline, "last_fetch_keys", [])):
        nodes.append({
            "node_id": idx + 1,
            "name": key,
            "status": "online",
            "last_value": float(data_pipeline.last_fetch_values[idx]),
            "last_updated": datetime.now().isoformat(),
        })

    return {
        "total_nodes": len(nodes),
        "online_nodes": len(nodes),
        "offline_nodes": 0,
        "nodes": nodes,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/simulations/recent")
async def get_recent_simulations(limit: int = 5):
    """Get recent trade simulations"""
    raise HTTPException(status_code=501, detail="Recent simulations not persisted yet")

@app.get("/simulations/metrics")
async def get_metrics():
    """Get performance metrics"""
    raise HTTPException(status_code=501, detail="Metrics endpoint not implemented with real storage")

@app.get("/simulations/equity-curve")
async def get_equity_curve():
    """Get equity curve data"""
    raise HTTPException(status_code=501, detail="Equity curve not implemented with real storage")

@app.get("/simulations/history")
async def get_history():
    """Get trade history and confidence distribution"""
    raise HTTPException(status_code=501, detail="History endpoint not implemented with real storage")

@app.post("/trade/simulate/advanced")
async def simulate_advanced_trade(data: Dict[str, Any]):
    """Simulate a trade using neural network"""
    token_in = data.get("token_in", "CRO")
    token_out = data.get("token_out", "USDC")
    amount = float(data.get("amount", 1000))
    
    # Real market state via data pipeline
    if data_pipeline is None:
        raise HTTPException(status_code=500, detail="Data pipeline not initialized")
    state_vector = await data_pipeline.get_market_state()
    if len(state_vector) != 48:
        raise HTTPException(status_code=500, detail="Unexpected state vector length")

    # Convert to numpy if needed
    if isinstance(state_vector, torch.Tensor):
        state_vector = state_vector.cpu().numpy()
    
    # Neural inference (returns action, confidence, probabilities dict)
    action, confidence_score, probabilities = brain.get_action(state_vector, epsilon=0.0)
    # action is already a string: "BUY", "SELL", or "HOLD"
    neural_decision = action

    # Predicted output: use normalized signal to scale expected output
    # For simplicity, use mean of vector as signal strength
    signal = float(np.mean(state_vector))
    predicted_output = round(amount * (0.95 + 0.1 * signal), 6)
    
    return {
        "success": True,
        "simulation": {
            "simulation_id": f"sim-{datetime.now().timestamp()}",
            "timestamp": datetime.now().isoformat(),
            "token_in": token_in,
            "token_out": token_out,
            "amount_in": amount,
            "predicted_amount_out": predicted_output,
            "entry_price": round(0.1 * (0.5 + float(np.mean(state_vector))), 6),
            "exit_price": round(0.1 * (0.5 + float(np.mean(state_vector)) + float(np.std(state_vector))), 6),
            "confidence": confidence_score,
            "neural_decision": neural_decision,
            "reasoning": f"Neural network analyzed data from {len(getattr(data_pipeline, 'last_fetch_keys', []))} data providers. "
                        f"Market sentiment is {'bullish' if neural_decision == 'BUY' else 'bearish' if neural_decision == 'SELL' else 'neutral'}. "
                        f"Market volatility: {float(np.std(state_vector)):.2%}.",
            "nodes_used": getattr(data_pipeline, 'last_fetch_keys', [])
        },
        "nodes_used_count": len(getattr(data_pipeline, "last_fetch_keys", [])),
        "gas_cost": 0.0,
        "slippage_percent": round(max(0.0, min(5.0, float(np.std(state_vector)) * 10)), 2),
        "profitability": round((predicted_output - amount) / amount * 100, 2)
    }

@app.post("/trade/execute/confirmed")
async def execute_trade(data: Dict[str, Any]):
    """Execute a confirmed trade"""
    raise HTTPException(status_code=501, detail="Real trade execution not implemented. Use /trade/simulate/advanced for simulations only.")

@app.post("/chat")
async def chat(request: Dict[str, str]):
    """Handle chat messages"""
    message = request.get("message", "")
    return {
        "response": f"Echo: {message}",
        "success": True
    }

@app.websocket("/ws/trading")
async def websocket_trading(ws: WebSocket):
    """WebSocket for live trading updates"""
    raise HTTPException(status_code=501, detail="WebSocket metrics not implemented with real storage backend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
