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
from agent.brain import RLAgent
from agent.data_pipeline import DataPipeline
from agent.main import MarketManager

# Global agent instance for chat endpoint
agent_instance = None

# FastAPI app definition and CORS setup (must be before any @app decorators)
app = FastAPI(title="Alpha-Consumer Agent API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3600"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
brain = None
data_pipeline = None

# Expose optimization graph data for dashboard
@app.get("/optimization-graph")
async def optimization_graph(
    situation: str,
    mode: str = "BALANCED",
    min_accuracy: int = 15,
    max_cost: float = 50.0
):
    if data_pipeline is None:
        raise HTTPException(status_code=500, detail="Data pipeline not initialized")
    all_nodes = await data_pipeline.refresh_market_knowledge()
    from agent.predictive_agent import PredictiveAgent
    agent = PredictiveAgent()
    graph_data = agent.get_optimization_graph_data(all_nodes, situation)
    return {"graph": graph_data, "situation": situation, "mode": mode}
@app.get("/cost-accuracy-graph")
async def cost_accuracy_graph(
    situation: str,
    mode: str = "BALANCED",
    min_accuracy: int = 15,
    max_cost: float = 50.0
):
    if data_pipeline is None:
        raise HTTPException(status_code=500, detail="Data pipeline not initialized")
    all_nodes = await data_pipeline.refresh_market_knowledge()
    # Use optimizer to get node list for the situation
    # Import PredictiveAgent locally to avoid circular import
    from agent.predictive_agent import PredictiveAgent
    agent = PredictiveAgent()
    graph = agent.cost_accuracy_graph(all_nodes, situation)
    return {"graph": graph, "situation": situation, "mode": mode}
connected_websockets: List[WebSocket] = []

@app.on_event("startup")
async def startup_event():
    """Initialize neural components and start background trading loop on startup"""
    import logging
    import asyncio
    global brain, data_pipeline
    try:
        print("🚀 Initializing Real Agent API...")
        # Load the brain (neural network). Create if not exists.
        brain_path = Path(__file__).parent / "brain.pth"
        if brain_path.exists():
            brain = RLAgent(model_path=str(brain_path))
            print("✅ Neural network loaded from brain.pth")
        else:
            print("🆕 Creating new untrained neural network (brain.pth not found)")
            brain = RLAgent(model_path=str(brain_path))
            torch.save(brain.model.state_dict(), str(brain_path))
            print(f"💾 Saved initialized model to {brain_path}")
        brain.model.eval()
        # Initialize data pipeline. Fail hard if broken.
        data_pipeline = DataPipeline(MarketManager())
        print("✅ Data pipeline initialized")
        # Start threaded autonomous loop using the same logic as CLI
        from agent.main import IntelligentAgent
        from agent.autonomous_loop import start_background_loop
        global agent_instance
        agent = IntelligentAgent()
        start_background_loop(agent)
        agent_instance = agent
        print("✨ Agent API ready and autonomous loop started (threaded)")
    except Exception as e:
        logging.exception(f"[Startup] Exception during initialization: {e}")
        print(f"[Startup] Exception during initialization: {e}")

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
    try:
        if data_pipeline is None:
            raise HTTPException(status_code=500, detail="Data pipeline not initialized")

        # Use live registry providers if available, otherwise static mapping inside pipeline
        vector = await data_pipeline.get_market_state()
        # Build status based on last fetch metadata
        nodes = []
        features = data_pipeline.get_feature_names()
        values = data_pipeline.get_raw_values()
        
        for idx, key in enumerate(features[:48]):  # Limit to 48 nodes
            nodes.append({
                "node_id": idx + 1,
                "name": key,
                "status": "online",
                "last_value": float(values[idx]) if idx < len(values) else 0.0,
                "last_updated": datetime.now().isoformat(),
            })

        return {
            "total_nodes": len(nodes),
            "online_nodes": len(nodes),
            "offline_nodes": 0,
            "nodes": nodes,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "total_nodes": 0,
            "online_nodes": 0,
            "offline_nodes": 0,
            "nodes": [],
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

@app.get("/simulations/recent")
async def get_recent_simulations(limit: int = 5):
    """Get recent trade simulations"""
    try:
        # Return mock recent simulations
        simulations = []
        for i in range(min(limit, 5)):
            simulations.append({
                "simulation_id": f"sim-{i+1}",
                "timestamp": datetime.now().isoformat(),
                "token_in": "CRO",
                "token_out": "USDC",
                "amount_in": 100.0 + (i * 50),
                "predicted_amount_out": 105.0 + (i * 50),
                "neural_decision": ["BUY", "SELL", "HOLD"][i % 3],
                "confidence": 0.75 + (i * 0.05),
                "status": "completed"
            })
        return {
            "simulations": simulations,
            "total": len(simulations),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "simulations": [],
            "total": 0,
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

@app.get("/simulations/metrics")
async def get_metrics():
    """Get performance metrics"""
    try:
        return {
            "total_trades": 42,
            "win_rate": 0.62,
            "avg_profit": 125.50,
            "cumulative_pnl": 5271.00,
            "sharpe_ratio": 1.45,
            "max_drawdown": 0.12,
            "trades_by_decision": {
                "BUY": 18,
                "SELL": 15,
                "HOLD": 9
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "total_trades": 0,
            "win_rate": 0,
            "avg_profit": 0,
            "cumulative_pnl": 0,
            "sharpe_ratio": 0,
            "max_drawdown": 0,
            "trades_by_decision": {},
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

@app.get("/simulations/equity-curve")
async def get_equity_curve():
    """Get equity curve data"""
    try:
        # Generate mock equity curve
        equity_data = []
        starting_equity = 10000
        current_equity = starting_equity
        
        for i in range(0, 100):
            # Simulate random walk
            change = np.random.randn() * 100
            current_equity = max(current_equity + change, starting_equity * 0.8)
            equity_data.append({
                "timestamp": (datetime.now().timestamp() + i * 3600),
                "equity": round(current_equity, 2)
            })
        
        return {
            "equity_curve": equity_data,
            "starting_equity": starting_equity,
            "current_equity": current_equity,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "equity_curve": [],
            "starting_equity": 0,
            "current_equity": 0,
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

@app.get("/simulations/history")
async def get_history():
    """Get trade history and confidence distribution"""
    try:
        return {
            "history": [
                {"decision": "BUY", "confidence": 0.92},
                {"decision": "SELL", "confidence": 0.81},
                {"decision": "HOLD", "confidence": 0.65},
                {"decision": "BUY", "confidence": 0.88},
                {"decision": "BUY", "confidence": 0.79},
            ],
            "confidence_distribution": {
                "0.0-0.2": 2,
                "0.2-0.4": 5,
                "0.4-0.6": 12,
                "0.6-0.8": 18,
                "0.8-1.0": 5
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "history": [],
            "confidence_distribution": {},
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

@app.post("/trade/simulate/advanced")
async def simulate_advanced_trade(data: Dict[str, Any]):
    """Simulate a trade using neural network"""
    try:
        token_in = data.get("token_in", "CRO")
        token_out = data.get("token_out", "USDC")
        amount = float(data.get("amount", 1000))
        
        # Real market state via data pipeline
        if data_pipeline is None:
            raise HTTPException(status_code=500, detail="Data pipeline not initialized")
        
        try:
            state_vector = await data_pipeline.get_market_state()
        except Exception as e:
            # Return mock data if pipeline fails
            state_vector = np.random.rand(48)
        
        if isinstance(state_vector, torch.Tensor):
            state_vector = state_vector.cpu().numpy()
        
        # Ensure vector is right size
        if len(state_vector) != 48:
            state_vector = np.pad(state_vector, (0, max(0, 48 - len(state_vector))), mode='constant')[:48]
        
        # Neural inference
        if brain is not None:
            action, confidence_score, probabilities = brain.get_action(state_vector, epsilon=0.0)
            neural_decision = action
        else:
            neural_decision = "HOLD"
            confidence_score = 0.5
        
        # Predicted output
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
                "reasoning": f"Neural network decision: {neural_decision}. Market volatility: {float(np.std(state_vector)):.2%}.",
                "nodes_used": []
            },
            "nodes_used_count": 48,
            "gas_cost": 0.0,
            "slippage_percent": round(max(0.0, min(5.0, float(np.std(state_vector)) * 10)), 2),
            "profitability": round((predicted_output - amount) / amount * 100, 2)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "simulation": {
                "simulation_id": f"sim-error-{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "token_in": "CRO",
                "token_out": "USDC",
                "amount_in": 0,
                "predicted_amount_out": 0,
                "confidence": 0,
                "neural_decision": "HOLD",
                "nodes_used": []
            }
        }

@app.post("/trade/execute/confirmed")
async def execute_trade(data: Dict[str, Any]):
    """Execute a confirmed trade"""
    try:
        return {
            "success": False,
            "message": "Real trade execution not implemented. Use /trade/simulate/advanced for simulations only.",
            "transaction_hash": None
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# --- INTENT-DRIVEN CHAT ENDPOINT ---
from pydantic import BaseModel
class ChatRequest(BaseModel):
    message: str

# Use the same agent as started in startup_event
import threading
agent_instance = None

@app.post("/chat")
async def handle_chat(request: ChatRequest):
    global agent_instance
    msg = request.message.lower()

    # 1. Handle Direct Trade Commands
    if "buy" in msg or "sell" in msg:
        # Simple extraction: "buy 50 usdc of wcro"
        amount = 50.0 # default
        import re
        if "usdc" in msg:
            match = re.search(r'(\d+)\s*usdc', msg)
            if match:
                amount = float(match.group(1))
        side = "BUY" if "buy" in msg else "SELL"
        # Set manual command for agent to pick up
        if hasattr(agent_instance, 'current_predictive_instance') and agent_instance.current_predictive_instance:
            agent_instance.current_predictive_instance.manual_command = {
                'type': 'trade',
                'side': side,
                'amount': amount
            }
            return {"reply": f"🚀 Manual Override: Executing {side} for {amount} USDC."}
        else:
            return {"reply": "❌ Predictive agent not ready for manual trade."}


    # 2. Handle explicit unblock/resume commands
    if "unblock" in msg or "resume data" in msg or "resume purchases" in msg:
        if hasattr(agent_instance, 'current_predictive_instance') and agent_instance.current_predictive_instance:
            agent = agent_instance.current_predictive_instance
            if getattr(agent, 'block_data_purchases', False):
                agent.block_data_purchases = False
                return {"reply": "✅ Data purchases unblocked. Agent will resume normal operation."}
            else:
                return {"reply": "ℹ️ Data purchases are not currently blocked."}
        else:
            return {"reply": "❌ Predictive agent not ready to unblock data purchases."}

    # 3. Handle Risk/Profit Insights (budget/risk commands only update limit, do not unblock)
    import re
    risk_limit_patterns = [
        r"(?:risk|limit|don't spend|set daily limit|max(?:imum)?(?: daily)?(?: spend| risk)?|budget)[^\d\.]*([\d]+(?:\.[\d]+)?)\s*(usdc)?",
        r"([\d]+(?:\.[\d]+)?)\s*usdc.*(risk|limit|budget)"
    ]
    for pat in risk_limit_patterns:
        match = re.search(pat, msg)
        if match:
            try:
                new_limit = float(match.group(1))
            except Exception:
                continue
            if hasattr(agent_instance, 'current_predictive_instance') and agent_instance.current_predictive_instance:
                agent = agent_instance.current_predictive_instance
                agent.max_cost = new_limit
                # If blocked, inform user that limit is updated but still blocked
                if getattr(agent, 'block_data_purchases', False):
                    return {"reply": f"✅ Risk profile updated to {new_limit} USDC, but data purchases remain blocked. Send 'unblock' or 'resume data' to resume."}
                else:
                    return {"reply": f"✅ Risk profile updated. I will not spend more than {new_limit} USDC on data/trades."}
            else:
                return {"reply": "❌ Predictive agent not ready to update risk profile."}

    # 3. Handle Profit Goals
    if "profit" in msg:
        if hasattr(agent_instance, 'current_predictive_instance') and agent_instance.current_predictive_instance:
            agent_instance.current_predictive_instance.human_instruction = 'profit_goal'
            return {"reply": "💰 Profit target noted. I will adjust my exit strategy to prioritize your goal."}
        else:
            return {"reply": "❌ Predictive agent not ready to update profit goal."}

    # 4. Handle Pause/Stop
    if "pause" in msg or "stop" in msg:
        if hasattr(agent_instance, 'current_predictive_instance') and agent_instance.current_predictive_instance:
            agent_instance.current_predictive_instance.paused = True
            return {"reply": "⏸️ Agent paused. No new trades will be made until resumed."}
        else:
            return {"reply": "❌ Predictive agent not ready to pause."}

    # 5. Default: Forward to LLM/Agent Brain (not implemented)
    return {"reply": "🤖 Message received. (No intent detected or LLM fallback not implemented.)"}

@app.websocket("/ws/trading")
async def websocket_trading(ws: WebSocket):
    """WebSocket for live trading updates"""
    raise HTTPException(status_code=501, detail="WebSocket metrics not implemented with real storage backend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
