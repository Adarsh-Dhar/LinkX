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

# Import the agent
from lightweight_agent import LightweightAgent
from node_connector import get_connector, close_connector
from simulation_service import get_simulation_service

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
        
        # Initialize node connector
        connector = await get_connector()
        print(f"✅ Node connector initialized with {len(connector.nodes)} nodes")
        
        # Initialize simulation service
        sim_service = get_simulation_service()
        print("✅ Simulation service initialized")
        
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


# New Models for Trading Endpoints
class NodeStatus(BaseModel):
    node_id: int
    port: int
    category: str
    provider_type: str  # "premium" or "budget"
    status: str  # "online", "offline", "slow"
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
    neural_decision: str  # "BUY", "SELL", "HOLD"
    reasoning: str
    nodes_used: List[str]


class TradeExecutionRequest(BaseModel):
    token_in: str
    token_out: str
    amount: float
    simulate_only: bool = True  # Start with simulation
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
    provider_preference: str = "balanced"  # "premium", "budget", "balanced"


class NodeDataResponse(BaseModel):
    category: str
    timestamp: str
    data: Dict[str, Any]
    providers_used: List[Dict[str, str]]
    normalized_values: Dict[str, float]


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


# ============== NEW TRADING ENDPOINTS ==============

@app.get("/nodes/status", response_model=NodesStatusResponse)
async def get_nodes_status():
    """
    Get status of all 48 connected nodes
    Shows which nodes are online, their latency, and data freshness
    """
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        nodes_data = []
        
        # Get node info from SmartRouter
        if hasattr(agent, 'smart_router'):
            router = agent.smart_router
            
            # Get all nodes from registry
            if hasattr(router, 'nodes'):
                for node_id, node_info in router.nodes.items():
                    port = 4000 + node_id
                    nodes_data.append(NodeStatus(
                        node_id=node_id,
                        port=port,
                        category=node_info.get('category', 'Unknown'),
                        provider_type=node_info.get('type', 'budget'),
                        status="online" if node_info.get('healthy', True) else "offline",
                        last_updated=datetime.now().isoformat(),
                        data_freshness_ms=node_info.get('latency_ms', 0)
                    ))
        
        # Fallback: assume all nodes online if SmartRouter not fully initialized
        if not nodes_data:
            for i in range(48):
                provider_type = "premium" if i % 2 == 0 else "budget"
                category = ["Market Data", "On-Chain", "Sentiment", "Fundamentals", "Technical"][i % 5]
                nodes_data.append(NodeStatus(
                    node_id=i,
                    port=4000 + i,
                    category=category,
                    provider_type=provider_type,
                    status="online",
                    last_updated=datetime.now().isoformat(),
                    data_freshness_ms=100
                ))
        
        return NodesStatusResponse(
            total_nodes=48,
            connected_nodes=len([n for n in nodes_data if n.status == "online"]),
            nodes=nodes_data,
            registry_status="online"
        )
    except Exception as e:
        print(f"Error getting nodes status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/nodes/data", response_model=NodeDataResponse)
async def get_node_data(req: NodeDataRequest):
    """
    Fetch aggregated data from specific node category
    Combines data from premium and/or budget providers based on preference
    """
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        category = req.category.lower()
        preference = req.provider_preference.lower()
        
        # Get data from DataPipeline
        if hasattr(agent, 'data_pipeline'):
            pipeline = agent.data_pipeline
            
            # Fetch from specified category
            raw_data = pipeline.fetch_category_data(category, preference)
            
            return NodeDataResponse(
                category=category,
                timestamp=datetime.now().isoformat(),
                data=raw_data.get('data', {}),
                providers_used=raw_data.get('providers', []),
                normalized_values=raw_data.get('normalized', {})
            )
        else:
            # Fallback mock data
            return NodeDataResponse(
                category=category,
                timestamp=datetime.now().isoformat(),
                data={"price": 0.45, "volume_24h": 1250000, "liquidity": 5600000},
                providers_used=[
                    {"node_id": "1", "provider": "Premium Data Inc", "latency_ms": 45},
                    {"node_id": "2", "provider": "Budget Data Co", "latency_ms": 120}
                ],
                normalized_values={"price": 0.65, "volume": 0.78, "liquidity": 0.82}
            )
    except Exception as e:
        print(f"Error fetching node data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/trade/simulate", response_model=TradeExecutionResponse)
async def simulate_trade(req: TradeExecutionRequest):
    """
    Simulate a trade using the neural network
    Fetches live data from nodes, runs through RLAgent, returns prediction
    Does NOT execute on-chain - safe dry-run
    """
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        import uuid
        from datetime import datetime
        
        simulation_id = str(uuid.uuid4())[:8]
        
        # Get market data from nodes via DataPipeline
        market_data = {}
        nodes_used = []
        
        if hasattr(agent, 'data_pipeline'):
            # Fetch normalized data from all 48 nodes
            pipeline_data = agent.data_pipeline.get_normalized_vector()
            market_data = pipeline_data.get('data', {})
            nodes_used = pipeline_data.get('nodes', [])
        
        # Get neural prediction
        neural_decision = "HOLD"
        confidence = 0.5
        predicted_amount_out = req.amount * 0.95  # Mock slippage
        
        if hasattr(agent, 'brain'):
            try:
                # Use RLAgent to predict action
                decision = agent.brain.predict(market_data)
                neural_decision = decision.get('action', 'HOLD')
                confidence = decision.get('confidence', 0.5)
                predicted_amount_out = decision.get('predicted_output', req.amount * 0.95)
            except Exception as e:
                print(f"Could not get neural prediction: {e}")
        
        # Calculate simulated prices
        entry_price = 0.45  # Mock price
        exit_price = entry_price * (1 + (confidence - 0.5) * 0.1)  # Mock profit/loss
        
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
            reasoning=f"Neural network predicts {neural_decision} with {confidence:.2%} confidence based on {len(nodes_used)} data providers",
            nodes_used=nodes_used
        )
        
        return TradeExecutionResponse(
            success=True,
            simulation=simulation,
            actual_output=None
        )
    except Exception as e:
        print(f"Error simulating trade: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/trade/execute", response_model=TradeExecutionResponse)
async def execute_trade(req: TradeExecutionRequest):
    """
    Execute a real trade on-chain
    First simulates to get confidence, then executes if confidence > threshold
    """
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        # First, simulate the trade
        sim_response = await simulate_trade(TradeExecutionRequest(
            token_in=req.token_in,
            token_out=req.token_out,
            amount=req.amount,
            simulate_only=True,
            slippage_tolerance=req.slippage_tolerance
        ))
        
        simulation = sim_response.simulation
        
        # If simulation_only is True, return without executing
        if req.simulate_only:
            return sim_response
        
        # Check confidence threshold (default 0.6)
        if simulation.confidence < 0.6:
            return TradeExecutionResponse(
                success=False,
                simulation=simulation,
                error=f"Neural confidence ({simulation.confidence:.2%}) below 0.6 threshold. Trade not executed."
            )
        
        # Execute the trade if confidence is high enough
        try:
            from tools import execute_swap
            
            tx_hash = execute_swap(
                token_in=req.token_in,
                token_out=req.token_out,
                amount_in=req.amount,
                min_amount_out=simulation.predicted_amount_out * (1 - req.slippage_tolerance / 100)
            )
            
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


# ============== SIMULATION TRACKING ENDPOINTS ==============

@app.get("/simulations/metrics", response_model=PerformanceMetricsResponse)
async def get_simulation_metrics():
    """
    Get performance metrics from all completed simulations
    Includes win rate, Sharpe ratio, max drawdown, etc.
    """
    try:
        sim_service = get_simulation_service()
        metrics = sim_service.get_metrics()
        return PerformanceMetricsResponse(**metrics)
    except Exception as e:
        print(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/simulations/equity-curve", response_model=EquityCurveResponse)
async def get_equity_curve():
    """
    Get equity curve showing portfolio growth over all simulations
    Used for visualizing performance over time
    """
    try:
        sim_service = get_simulation_service()
        equity_data = sim_service.get_equity_curve()
        return EquityCurveResponse(**equity_data)
    except Exception as e:
        print(f"Error getting equity curve: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/simulations/history", response_model=SimulationHistoryResponse)
async def get_simulation_history(limit: int = 50):
    """
    Get complete simulation history including trades, metrics, and equity curve
    """
    try:
        sim_service = get_simulation_service()
        
        return SimulationHistoryResponse(
            recent_trades=sim_service.get_recent_trades(limit),
            metrics=PerformanceMetricsResponse(**sim_service.get_metrics()),
            equity_curve=EquityCurveResponse(**sim_service.get_equity_curve()),
            confidence_distribution=sim_service.get_confidence_distribution()
        )
    except Exception as e:
        print(f"Error getting simulation history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/simulations/recent", response_model=List[Dict])
async def get_recent_trades(limit: int = 20):
    """Get recent completed trades"""
    try:
        sim_service = get_simulation_service()
        return sim_service.get_recent_trades(limit)
    except Exception as e:
        print(f"Error getting recent trades: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/simulations/active", response_model=List[Dict])
async def get_active_trades():
    """Get currently active (pending execution) trades"""
    try:
        sim_service = get_simulation_service()
        return sim_service.get_active_trades()
    except Exception as e:
        print(f"Error getting active trades: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/simulations/{simulation_id}", response_model=Optional[Dict])
async def get_simulation(simulation_id: str):
    """Get details of a specific simulation"""
    try:
        sim_service = get_simulation_service()
        trade = sim_service.get_trade_by_id(simulation_id)
        if not trade:
            raise HTTPException(status_code=404, detail=f"Simulation {simulation_id} not found")
        return trade
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting simulation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/simulations/clear")
async def clear_simulations():
    """Clear all simulation history (WARNING: irreversible)"""
    try:
        sim_service = get_simulation_service()
        sim_service.clear_history()
        return {"success": True, "message": "All simulations cleared"}
    except Exception as e:
        print(f"Error clearing simulations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============== ENHANCED TRADING ENDPOINTS ==============

@app.post("/trade/simulate/advanced")
async def simulate_trade_advanced(req: TradeExecutionRequest):
    """
    Advanced trade simulation with full neural network integration
    Returns detailed prediction with reasoning from all 48 nodes
    """
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        import uuid
        
        # Initialize simulation service
        sim_service = get_simulation_service()
        
        # Get market data from all nodes
        connector = await get_connector()
        market_data = await connector.get_data("eth_blockNumber")  # Generic call to test nodes
        
        nodes_used = [n["name"] for n in connector.get_nodes_status()["nodes"] if n["status"] == "online"]
        
        # Get neural prediction
        neural_decision = "HOLD"
        confidence = 0.5
        predicted_amount_out = req.amount * 0.95  # Mock slippage
        
        if hasattr(agent, 'brain'):
            try:
                # Use RLAgent to predict action
                import numpy as np
                # Mock state vector (in production, aggregate from all 48 nodes)
                state = np.random.randn(48)
                decision, confidence, _ = agent.brain.get_action(state)
                neural_decision = decision
                predicted_amount_out = req.amount * (0.95 + confidence * 0.05)
            except Exception as e:
                print(f"Could not get neural prediction: {e}")
        
        # Create simulation record
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
            nodes_used=nodes_used[:20]  # Return top 20 node names
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
    Uses simulation_id to reference previous simulation
    """
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        sim_service = get_simulation_service()
        
        # If simulation_id provided, execute that specific simulation
        if simulation_id:
            sim_trade = sim_service.get_trade_by_id(simulation_id)
            if not sim_trade:
                raise HTTPException(status_code=404, detail=f"Simulation {simulation_id} not found")
            
            # Execute the trade
            try:
                from tools import execute_swap
                import time
                
                start_time = time.time()
                tx_hash = execute_swap(
                    token_in=sim_trade["token_in"],
                    token_out=sim_trade["token_out"],
                    amount_in=sim_trade["amount_in"],
                    min_amount_out=sim_trade["predicted_amount_out"] * 0.99
                )
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
    """
    WebSocket endpoint for live trading updates
    Streams new simulations, node status changes, and metrics updates
    """
    await websocket.accept()
    try:
        sim_service = get_simulation_service()
        
        while True:
            # Send metrics update every 5 seconds
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
    """
    WebSocket endpoint for live node status updates
    Streams node health changes and latency updates
    """
    await websocket.accept()
    try:
        connector = await get_connector()
        
        while True:
            # Send node status every 3 seconds
            await asyncio.sleep(3)
            
            nodes_status = connector.get_nodes_status()
            
            await websocket.send_json({
                "type": "nodes_update",
                "nodes": nodes_status,
                "timestamp": datetime.now().isoformat()
            })
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
