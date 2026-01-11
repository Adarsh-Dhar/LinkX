# 🚀 48-Node Trading Integration - Complete Guide

## Overview

The agent is now **fully integrated** with the 48-node ecosystem for real-time trading with neural network predictions and live UI simulations.

---

## ✅ What Was Implemented

### 1. **Enhanced API Endpoints** ([api.py](agent/api.py))

#### New Trading Endpoints:
- **`GET /nodes/status`** - Real-time status of all 48 nodes
  - Node connectivity (online/offline)
  - Data freshness and latency
  - Provider types (premium/budget)
  - Category distribution

- **`POST /nodes/data`** - Fetch aggregated data from specific node categories
  - Request: `{"category": "market_data", "provider_preference": "balanced"}`
  - Returns normalized data + providers used

- **`POST /trade/simulate`** - Simulate trade with neural network
  - Fetches live data from 48 nodes
  - Runs through neural network brain
  - Returns prediction + confidence + reasoning
  - **Does NOT execute on-chain** (safe dry-run)

- **`POST /trade/execute`** - Execute real trade (with simulation first)
  - Simulates first to check confidence
  - Executes only if confidence > 0.6 threshold
  - Returns transaction hash + actual output

---

### 2. **Trading Engine Module** ([trading_engine.py](agent/trading_engine.py))

New orchestration layer that:
- **Aggregates data** from all 48 nodes via DataPipeline
- **Normalizes vectors** for neural network input
- **Tracks simulations** with full history
- **Calculates performance metrics**:
  - Win rate
  - Sharpe ratio
  - Max drawdown
  - Average confidence
  - Equity curve
  - Cumulative P&L

**Key Classes:**
- `TradingEngine` - Main orchestrator
- `SimulatedTrade` - Trade data model with full tracking

---

### 3. **Enhanced Agent** ([lightweight_agent.py](agent/lightweight_agent.py))

**Initialization Chain:**
```
LightweightAgent.__init__()
  ├─> SmartRouter (discovers 48 nodes)
  ├─> DataPipeline (aggregates node data)
  ├─> RLAgent/Brain (neural network)
  └─> TradingEngine (orchestrates trades)
```

The agent now:
- Validates node connections on startup
- Provides real-time data streaming from DataPipeline
- Executes trades through neural network predictions
- Tracks simulation mode vs live execution

---

### 4. **Frontend Components**

#### **Trading Dashboard** ([trading-dashboard.tsx](frontend/components/trading-dashboard.tsx))
- **48-Node Status Panel** - Heatmap showing connected nodes
- **Live Trade Feed** - Real-time simulated trades
- **Performance Metrics** - Win rate, P&L, Sharpe ratio
- **Node Category Breakdown** - Data quality by category
- **Auto-refresh** every 5 seconds

#### **Simulation View** ([simulation-view.tsx](frontend/components/simulation-view.tsx))
- **Equity Curve Chart** - Portfolio value over time
- **Confidence Distribution** - Histogram of prediction confidence
- **Risk Analysis** - Max drawdown, recovery time
- **Node Performance Impact** - Premium vs budget provider analysis

#### **Updated Navigation** ([page.tsx](frontend/app/page.tsx) + [sidebar.tsx](frontend/components/sidebar.tsx))
- Added "Trading" page → TradingDashboard
- Added "Simulation" page → SimulationView
- Reorganized sidebar with new icons

---

## 🔌 How It Works

### Data Flow Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  Frontend (Next.js)                                          │
│  ├─ TradingDashboard   ────────────┐                        │
│  ├─ SimulationView     ────────────┤                        │
│  └─ Chat Interface     ────────────┤                        │
└────────────────────────────────────┼──────────────────────────┘
                                     │ HTTP/REST
                                     ▼
┌──────────────────────────────────────────────────────────────┐
│  Agent API (FastAPI - Port 8000)                            │
│  ├─ /nodes/status                                           │
│  ├─ /nodes/data                                             │
│  ├─ /trade/simulate                                         │
│  └─ /trade/execute                                          │
└────────────────────────────────────┬──────────────────────────┘
                                     │
                                     ▼
┌──────────────────────────────────────────────────────────────┐
│  TradingEngine                                               │
│  ├─ Market Data Aggregation                                 │
│  ├─ Neural Network Prediction                               │
│  ├─ Simulation Tracking                                     │
│  └─ Performance Metrics                                     │
└────────────────────────────────────┬──────────────────────────┘
                                     │
           ┌─────────────────────────┼─────────────────────────┐
           ▼                         ▼                         ▼
    ┌─────────────┐         ┌──────────────┐        ┌──────────────┐
    │ SmartRouter │         │ DataPipeline │        │ RLAgent      │
    │ (Node       │         │ (48-Node     │        │ (Neural      │
    │  Discovery) │         │  Aggregation)│        │  Network)    │
    └──────┬──────┘         └──────┬───────┘        └──────────────┘
           │                       │
           └───────────┬───────────┘
                       ▼
┌──────────────────────────────────────────────────────────────┐
│  48-Node Ecosystem (Ports 4000-4047)                        │
│  ├─ Registry (Port 3999) - Node discovery                   │
│  ├─ 24 Categories × 2 Providers = 48 Nodes                  │
│  └─ Premium + Budget data sources                           │
└──────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start Guide

### Step 1: Start the Complete System

```bash
cd /Users/adarsh/Documents/alpha-consumer

# Option A: Start everything with validation
./start_complete_system.sh

# Option B: Start 48 nodes only (then start agent manually)
./start_ecosystem.sh
```

This starts:
- 48 data provider nodes (Ports 4000-4047)
- Registry service (Port 3999)

---

### Step 2: Start the Agent API

```bash
cd agent

# Ensure Python environment is configured
source venv/bin/activate  # if using venv

# Install dependencies (if not already)
pip install -r requirements.txt

# Start the agent API
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

Agent will initialize:
- ✅ SmartRouter → Discovers 48 nodes
- ✅ DataPipeline → Connects to nodes
- ✅ Neural Brain → Loads brain.pth
- ✅ TradingEngine → Ready for trading

---

### Step 3: Start the Frontend

```bash
cd frontend

# Install dependencies (if not already)
pnpm install

# Start dev server
pnpm dev
```

Frontend runs on: **http://localhost:3600**

---

### Step 4: Verify Integration

#### Test Node Connectivity
```bash
curl http://localhost:8000/nodes/status | jq
```

Expected output:
```json
{
  "total_nodes": 48,
  "connected_nodes": 48,
  "nodes": [...],
  "registry_status": "online"
}
```

#### Test Trade Simulation
```bash
curl -X POST http://localhost:8000/trade/simulate \
  -H "Content-Type: application/json" \
  -d '{
    "token_in": "USDC",
    "token_out": "CRO",
    "amount": 10.0,
    "simulate_only": true
  }' | jq
```

Expected output:
```json
{
  "success": true,
  "simulation": {
    "simulation_id": "abc123",
    "neural_decision": "BUY",
    "confidence": 0.78,
    "reasoning": "Neural network recommends BUY with 78% confidence...",
    "nodes_used": ["Node_0", "Node_1", ...]
  }
}
```

---

## 📊 Using the UI

### Trading Dashboard

Navigate to **Trading** in the sidebar:

1. **Node Status Panel** (top-left)
   - Shows 48 nodes connection status
   - Categories breakdown
   - Average latency

2. **Performance Metrics** (top)
   - Connected Nodes: 48/48
   - Win Rate: 65.2%
   - Total P&L: $24.50
   - Avg Confidence: 72.4%

3. **Live Trade Feed** (right)
   - Real-time simulated trades
   - Neural decision (BUY/SELL/HOLD)
   - Confidence scores
   - Click for detailed reasoning

4. **Auto-refresh Toggle**
   - Updates every 5 seconds automatically

---

### Simulation View

Navigate to **Simulation** in the sidebar:

1. **Equity Curve** - Portfolio value over time
2. **Confidence Distribution** - Histogram of predictions
3. **Risk Analysis** - Max drawdown, Sharpe ratio
4. **Node Quality Impact** - Premium vs budget data

---

## 🧠 Neural Network Integration

### How the Brain Works

1. **Data Collection** (DataPipeline)
   - Fetches from all 48 nodes concurrently
   - Normalizes to 48-dimensional vector
   - Min-Max scaling to [0, 1] range

2. **Neural Prediction** (RLAgent)
   - Input: 48 features from nodes
   - Architecture: 48 → 64 → 64 → 3
   - Output: BUY/SELL/HOLD probabilities
   - Uses epsilon-greedy (10% exploration)

3. **Trade Decision** (TradingEngine)
   - Confidence threshold: 0.6 (60%)
   - High confidence → Execute trade
   - Low confidence → Hold/wait

---

## 🔧 Configuration

### Agent Settings ([.env](agent/.env))

```bash
# OpenRouter LLM
OPENROUTER_API_KEY=your_key_here
OPENROUTER_MODEL=openai/gpt-4o-mini

# Wallet Configuration
PRIVATE_KEY=your_wallet_private_key
RPC_URL=https://evm.cronos.org

# Trading Parameters
CONFIDENCE_THRESHOLD=0.6
MAX_SLIPPAGE=1.0
```

### Frontend Settings

Update API base URL in components if needed:
```typescript
const API_BASE = "http://localhost:8000"
```

---

## 🧪 Testing the Integration

### Test Script

Create `test_integration.py`:

```python
import requests
import time

API_BASE = "http://localhost:8000"

# Test 1: Check nodes
print("Testing node connectivity...")
response = requests.get(f"{API_BASE}/nodes/status")
data = response.json()
print(f"✅ {data['connected_nodes']}/{data['total_nodes']} nodes online")

# Test 2: Simulate a trade
print("\nSimulating trade...")
response = requests.post(f"{API_BASE}/trade/simulate", json={
    "token_in": "USDC",
    "token_out": "CRO",
    "amount": 10.0,
    "simulate_only": True
})
sim = response.json()
print(f"✅ Neural Decision: {sim['simulation']['neural_decision']}")
print(f"✅ Confidence: {sim['simulation']['confidence']*100:.1f}%")
print(f"✅ Reasoning: {sim['simulation']['reasoning'][:100]}...")

# Test 3: Check multiple simulations
print("\nRunning 5 simulations...")
for i in range(5):
    response = requests.post(f"{API_BASE}/trade/simulate", json={
        "token_in": "USDC",
        "token_out": "CRO",
        "amount": 10.0
    })
    sim = response.json()['simulation']
    print(f"  {i+1}. {sim['neural_decision']:4s} @ {sim['confidence']*100:.0f}% confidence")
    time.sleep(0.5)

print("\n✅ Integration test complete!")
```

Run:
```bash
python test_integration.py
```

---

## 📈 Performance Monitoring

### Metrics Available

| Metric | Description | API Endpoint |
|--------|-------------|--------------|
| **Node Status** | 48-node health check | `GET /nodes/status` |
| **Win Rate** | % of profitable trades | Via TradingEngine metrics |
| **Sharpe Ratio** | Risk-adjusted returns | Via TradingEngine metrics |
| **Max Drawdown** | Largest decline from peak | Via TradingEngine metrics |
| **Avg Confidence** | Neural prediction quality | Via TradingEngine metrics |
| **Equity Curve** | Portfolio value over time | Via TradingEngine equity_curve |

---

## 🐛 Troubleshooting

### Issue: Nodes not connecting

**Solution:**
```bash
# Check if ecosystem is running
curl http://localhost:3999/directory

# Restart ecosystem
pkill -f "node ecosystem.js"
cd server && node ecosystem.js &
```

---

### Issue: Agent API not starting

**Solution:**
```bash
# Check Python dependencies
cd agent
pip install -r requirements.txt

# Check for port conflicts
lsof -i :8000

# Start with verbose logging
uvicorn api:app --host 0.0.0.0 --port 8000 --log-level debug
```

---

### Issue: Neural network not loading

**Solution:**
```bash
# Check if brain.pth exists
ls -lh agent/brain.pth

# If missing, the agent will run in "non-neural mode"
# Predictions will use fallback logic
```

---

## 🎯 Next Steps

### Immediate Actions
1. ✅ Start all services (`./start_all.sh`)
2. ✅ Open frontend (http://localhost:3600)
3. ✅ Navigate to "Trading" page
4. ✅ Verify 48 nodes are connected
5. ✅ Run a test simulation via UI

### Future Enhancements
- [ ] WebSocket support for real-time updates (currently polling)
- [ ] Add `/trades/history` endpoint for historical data
- [ ] Implement stop-loss and take-profit orders
- [ ] Add more technical indicators to neural input
- [ ] Deploy to production with authentication

---

## 📚 Architecture Summary

### Components

| Component | Purpose | Location |
|-----------|---------|----------|
| **48-Node Ecosystem** | Data providers | `server/ecosystem.js` |
| **SmartRouter** | Node discovery | `agent/smart_router.py` |
| **DataPipeline** | Data aggregation | `agent/data_pipeline.py` |
| **RLAgent** | Neural network | `agent/brain.py` |
| **TradingEngine** | Trade orchestration | `agent/trading_engine.py` |
| **API** | REST endpoints | `agent/api.py` |
| **LightweightAgent** | Main controller | `agent/lightweight_agent.py` |
| **Trading Dashboard** | UI for trading | `frontend/components/trading-dashboard.tsx` |
| **Simulation View** | Analytics UI | `frontend/components/simulation-view.tsx` |

---

## ✅ Integration Complete!

The agent is now fully connected to the 48-node ecosystem with:
- ✅ Real-time data from all nodes
- ✅ Neural network predictions
- ✅ Live trade simulations
- ✅ Performance tracking
- ✅ Rich UI visualization

**Ready to trade!** 🚀
