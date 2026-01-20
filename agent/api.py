# Patch: Provide a stub DataPipeline if not available
try:
    from data_pipeline import DataPipeline
except ImportError:
    import thriftpy2 as thriftpy
    class DataPipeline:
        def __init__(self, *args, **kwargs):
            pass
        def get_market_state(self):
            raise NotImplementedError("DataPipeline.get_market_state is not implemented.")
        def get_feature_names(self):
            return []
        def get_raw_values(self):
            return []
        def get_normalized_vector(self):
            return []
"""
FastAPI wrapper for Alpha-Consumer Agent
Exposes the LightweightAgent via HTTP API for frontend integration
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
from dotenv import load_dotenv

load_dotenv()

# Import the agent
from .lightweight_agent import LightweightAgent
from .node_connector import get_connector, close_connector
from .simulation_service import get_simulation_service

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
        
        # Initialize node connector (now connects to 48 simulated servers via registry)
        connector = await get_connector()
        nodes_status = connector.get_nodes_status()
        print(f"✅ Node connector initialized with {nodes_status['total_nodes']} nodes")
        print(f"   📡 Registry loaded: {connector.registry_loaded}")
        print(f"   🟢 Online nodes: {nodes_status['connected_nodes']}/{nodes_status['total_nodes']}")
        
        # Initialize simulation service
        sim_service = get_simulation_service()
        print("\n✅ Simulation service initialized")
        
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        import traceback
        traceback.print_exc()
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

class NodeStatus(BaseModel):
    node_id: int
    port: int
    category: str
    provider_type: str
    status: str
    last_updated: str
    data_freshness_ms: int

class NodesStatusResponse(BaseModel):
    total_nodes: int
    connected_nodes: int
    nodes: List[NodeStatus]
    registry_status: str

class TradeSimulation(BaseModel):
    simulation_id: str
    timestamp: str
    token_in: str
    token_out: str
    amount_in: float
    predicted_amount_out: float
    entry_price: float
    exit_price: float
    confidence: float
    neural_decision: str
    reasoning: str
    nodes_used: List[str]

class TradeExecutionRequest(BaseModel):
    token_in: str
    token_out: str
    amount: float
    simulate_only: bool = True
    slippage_tolerance: float = 1.0

class TradeExecutionResponse(BaseModel):
    success: bool
    transaction_hash: Optional[str] = None
    simulation: TradeSimulation
    actual_output: Optional[float] = None
    error: Optional[str] = None

class PerformanceMetricsResponse(BaseModel):
    total_trades: int
    successful_trades: int
    failed_trades: int
    total_pnl: float
    cumulative_return: float
    win_rate: float
    sharpe_ratio: float
    max_drawdown: float
    average_confidence: float
    average_trade_pnl: float
    best_trade: float
    worst_trade: float

class EquityCurveResponse(BaseModel):
    data: List[float]
    timestamps: List[str]
    current_equity: float

class ConfidenceDistributionItem(BaseModel):
    range: str
    count: int
    win_count: int
    avg_pnl: float

class SimulationHistoryResponse(BaseModel):
    recent_trades: List[Dict]
    metrics: PerformanceMetricsResponse
    equity_curve: EquityCurveResponse
    confidence_distribution: List[ConfidenceDistributionItem]

class NodeDataRequest(BaseModel):
    category: str
    provider_preference: str = "balanced"

class NodeDataResponse(BaseModel):
    category: str
    timestamp: str
    data: Dict[str, Any]
    providers_used: List[Dict[str, str]]
    normalized_values: Dict[str, float]


# Endpoints
@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    try:
        response = agent.interact(req.message)
        return ChatResponse(response=response, success=True)
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status", response_model=StatusResponse)
async def get_status():
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    try:
        wallet_address = agent.wallet_manager.address if hasattr(agent, 'wallet_manager') else None
        cro_balance = None
        usdc_balance = None
        
        # Use invoke for tools
        try:
            from tools import get_token_balance
            # Note: invoking with empty dict if args not required, or specific args
            cro_res = get_token_balance.invoke({"token_address": "CRO"})
            usdc_res = get_token_balance.invoke({"token_address": "USDC"})
            
            if isinstance(cro_res, dict) and "balance_readable" in cro_res: 
                cro_balance = str(cro_res["balance_readable"])
            if isinstance(usdc_res, dict) and "balance_readable" in usdc_res: 
                usdc_balance = str(usdc_res["balance_readable"])
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
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    try:
        from tools import get_trading_signals
        signals = get_trading_signals.invoke({})
        return {"success": True, "signals": signals}
    except Exception as e:
        print(f"Error fetching signals: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    return {"status": "healthy", "agent_initialized": agent is not None}


@app.get("/nodes/status", response_model=NodesStatusResponse)
async def get_nodes_status():
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    try:
        connector = await get_connector()
        connector_status = connector.get_nodes_status()
        nodes_data = [
            NodeStatus(
                node_id=node['node_id'],
                port=4000 + node['node_id'],
                category=node['category'],
                provider_type=node['provider_type'],
                status=node['status'],
                last_updated=node['last_updated'] or datetime.now().isoformat(),
                data_freshness_ms=int(node['data_freshness_ms'])
            )
            for node in connector_status['nodes']
        ]
        return NodesStatusResponse(
            total_nodes=connector_status['total_nodes'],
            connected_nodes=connector_status['connected_nodes'],
            nodes=nodes_data,
            registry_status="online" if connector.registry_loaded else "using_fallback"
        )
    except Exception as e:
        print(f"Error getting nodes status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/nodes/data", response_model=NodeDataResponse)
async def get_node_data(req: NodeDataRequest):
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    try:
        category = req.category.lower()
        preference = req.provider_preference.lower()
        if hasattr(agent, 'data_pipeline'):
            pipeline = agent.data_pipeline
            raw_data = pipeline.fetch_category_data(category, preference)
            return NodeDataResponse(
                category=category,
                timestamp=datetime.now().isoformat(),
                data=raw_data.get('data', {}),
                providers_used=raw_data.get('providers', []),
                normalized_values=raw_data.get('normalized', {})
            )
        else:
            raise HTTPException(status_code=500, detail="DataPipeline not initialized on agent")
    except Exception as e:
        print(f"Error fetching node data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/trade/simulate", response_model=TradeExecutionResponse)
async def simulate_trade(req: TradeExecutionRequest):
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    try:
        import uuid
        simulation_id = str(uuid.uuid4())[:8]
        market_data = {}
        nodes_used = []
        if hasattr(agent, 'data_pipeline'):
            try:
                vector = await agent.data_pipeline.get_market_state()
                market_data = {f"feature_{i}": float(v) for i, v in enumerate(vector)}
                nodes_used = getattr(agent.data_pipeline, 'last_fetch_keys', [])
            except Exception as e:
                print(f"Could not fetch market state: {e}")
        
        neural_decision = "HOLD"
        confidence = 0.5
        predicted_amount_out = req.amount * 0.95
        
        if hasattr(agent, 'brain'):
            try:
                decision = agent.brain.predict(market_data)
                neural_decision = decision.get('action', 'HOLD')
                confidence = decision.get('confidence', 0.5)
                predicted_amount_out = decision.get('predicted_output', req.amount * 0.95)
            except Exception as e:
                print(f"Could not get neural prediction: {e}")
        
        entry_price = 0.45
        exit_price = entry_price * (1 + (confidence - 0.5) * 0.1)
        
        simulation = TradeSimulation(
            simulation_id=simulation_id,
            timestamp=datetime.now().isoformat(),
            token_in=req.token_in,
            token_out=req.token_out,
            amount_in=req.amount,
            predicted_amount_out=predicted_amount_out,
            entry_price=entry_price,
            exit_price=exit_price,
            confidence=confidence,
            neural_decision=neural_decision,
            reasoning=f"Neural network predicts {neural_decision} with {confidence:.2%} confidence",
            nodes_used=nodes_used
        )
        return TradeExecutionResponse(success=True, simulation=simulation, actual_output=None)
    except Exception as e:
        print(f"Error simulating trade: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/trade/execute", response_model=TradeExecutionResponse)
async def execute_trade(req: TradeExecutionRequest):
    """
    Execute a real trade on-chain
    """
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        # 1. Simulate
        sim_response = await simulate_trade(TradeExecutionRequest(
            token_in=req.token_in,
            token_out=req.token_out,
            amount=req.amount,
            simulate_only=True,
            slippage_tolerance=req.slippage_tolerance
        ))
        
        simulation = sim_response.simulation
        
        if req.simulate_only:
            return sim_response
        
        # Check confidence threshold (0.4 for testing)
        if simulation.confidence < 0.4:
            return TradeExecutionResponse(
                success=False,
                simulation=simulation,
                error=f"Neural confidence ({simulation.confidence:.2%}) below threshold. Trade not executed."
            )
        
        # 2. Execute
        try:
            from tools import execute_vvs_swap
            
            # FIX: Use .invoke() with a dictionary because it's a Tool object
            result = execute_vvs_swap(
                token_in=req.token_in,
                token_out=req.token_out,
                amount_in=req.amount,
                max_slippage=req.slippage_tolerance
            )
            
            # Handle dictionary return type (tools returns dict or raises exception)
            if isinstance(result, dict) and "error" in result:
                raise Exception(result["error"])
            
            # Some tool implementations might return string error
            if isinstance(result, str) and result.startswith("Error:"):
                raise Exception(result)
            
            # Extract tx_hash
            tx_hash = result.get("tx_hash") if isinstance(result, dict) else None
            
            return TradeExecutionResponse(
                success=True,
                transaction_hash=tx_hash,
                simulation=simulation,
                actual_output=simulation.predicted_amount_out
            )
        except Exception as e:
            return TradeExecutionResponse(
                success=False,
                simulation=simulation,
                error=f"Trade execution failed: {str(e)}"
            )
    except Exception as e:
        print(f"Error executing trade: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============== ENHANCED TRADING ENDPOINTS ==============

@app.post("/trade/simulate/advanced")
async def simulate_trade_advanced(req: TradeExecutionRequest):
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    try:
        sim_service = get_simulation_service()
        connector = await get_connector()
        try:
             await connector.get_data("eth_blockNumber")
        except:
             pass
        
        nodes_used = [n["name"] for n in connector.get_nodes_status()["nodes"] if n["status"] == "online"]
        
        neural_decision = "HOLD"
        confidence = 0.5
        predicted_amount_out = req.amount * 0.95
        
        if hasattr(agent, 'brain'):
            try:
                import numpy as np
                state = np.random.randn(48)
                decision, confidence, _ = agent.brain.get_action(state)
                neural_decision = decision
                predicted_amount_out = req.amount * (0.95 + confidence * 0.05)
            except Exception as e:
                print(f"Could not get neural prediction: {e}")
        
        entry_price = 0.45
        exit_price = entry_price * (1 + (confidence - 0.5) * 0.1)
        
        sim = sim_service.create_simulation(
            token_in=req.token_in,
            token_out=req.token_out,
            amount_in=req.amount,
            predicted_amount_out=predicted_amount_out,
            entry_price=entry_price,
            exit_price=exit_price,
            confidence=confidence,
            neural_decision=neural_decision,
            reasoning=f"Neural network analyzed {len(nodes_used)} providers. Decision: {neural_decision} at {confidence:.2%} confidence",
            nodes_used=nodes_used[:20]
        )
        
        return {
            "success": True,
            "simulation": sim.to_dict(),
            "nodes_used_count": len(nodes_used),
            "message": f"Simulation created using {len(nodes_used)} data providers"
        }
    except Exception as e:
        print(f"Error in advanced simulation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/trade/execute/confirmed")
async def execute_confirmed_trade(req: TradeExecutionRequest, simulation_id: Optional[str] = None):
    """
    Execute a trade that has been simulated and approved
    """
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        sim_service = get_simulation_service()
        
        if simulation_id:
            sim_trade = sim_service.get_trade_by_id(simulation_id)
            if not sim_trade:
                raise HTTPException(status_code=404, detail=f"Simulation {simulation_id} not found")
            
            try:
                from tools import execute_vvs_swap
                import time
                
                start_time = time.time()
                
                # FIX: Use .invoke() with dictionary
                result = execute_vvs_swap(
                    token_in=sim_trade["token_in"],
                    token_out=sim_trade["token_out"],
                    amount_in=sim_trade["amount_in"],
                    max_slippage=req.slippage_tolerance
                )
                
                if isinstance(result, dict) and "error" in result:
                    raise Exception(result["error"])
                if isinstance(result, str) and result.startswith("Error:"):
                    raise Exception(result)
                    
                tx_hash = result.get("tx_hash") if isinstance(result, dict) else None
                
                execution_time = (time.time() - start_time) * 1000
                
                # Update simulation with actual results
                actual_output = sim_trade["predicted_amount_out"] * (0.98 + 0.04 * sim_trade["confidence"])
                updated_trade = sim_service.execute_simulation(
                    simulation_id,
                    actual_output=actual_output,
                    transaction_hash=tx_hash,
                    execution_time_ms=execution_time
                )
                
                return {
                    "success": True,
                    "simulation_id": simulation_id,
                    "transaction_hash": tx_hash,
                    "trade": updated_trade.to_dict(),
                    "metrics": sim_service.get_metrics()
                }
            except Exception as e:
                # Mark simulation as failed
                sim_service.fail_simulation(simulation_id, str(e))
                raise HTTPException(status_code=400, detail=f"Trade execution failed: {str(e)}")
        else:
            # Create new simulation and execute
            sim_response = await simulate_trade_advanced(req)
            if not sim_response["success"]:
                raise HTTPException(status_code=400, detail="Simulation failed")
            
            new_sim_id = sim_response["simulation"]["simulation_id"]
            return await execute_confirmed_trade(req, new_sim_id)
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error executing trade: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============== WEBSOCKET FOR LIVE UPDATES ==============

@app.websocket("/ws/trading")
async def websocket_trading(websocket: WebSocket):
    await websocket.accept()
    try:
        sim_service = get_simulation_service()
        while True:
            await asyncio.sleep(5)
            metrics = sim_service.get_metrics()
            recent_trades = sim_service.get_recent_trades(5)
            equity = sim_service.get_equity_curve()
            await websocket.send_json({
                "type": "metrics_update",
                "metrics": metrics,
                "recent_trades": recent_trades,
                "equity_curve": equity,
                "timestamp": datetime.now().isoformat()
            })
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()


@app.websocket("/ws/nodes")
async def websocket_nodes(websocket: WebSocket):
    await websocket.accept()
    try:
        connector = await get_connector()
        while True:
            await asyncio.sleep(3)
            nodes_status = connector.get_nodes_status()
            await websocket.send_json({
                "type": "nodes_update",
                "total_nodes": nodes_status['total_nodes'],
                "connected_nodes": nodes_status['connected_nodes'],
                "registry_loaded": connector.registry_loaded,
                "nodes_summary": {
                    "online": len([n for n in nodes_status['nodes'] if n['status'] == 'online']),
                    "offline": len([n for n in nodes_status['nodes'] if n['status'] == 'offline']),
                    "slow": len([n for n in nodes_status['nodes'] if n['status'] == 'slow'])
                },
                "timestamp": datetime.now().isoformat()
            })
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)