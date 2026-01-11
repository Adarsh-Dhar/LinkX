# Alpha-Consumer Agent: Node-Connected Trading System

## Overview

This system integrates a neural network-based trading agent with 48 blockchain data nodes for real-time trading simulations and execution on Cronos mainnet.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Next.js)                       │
│  ┌─────────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ SimulationView  │  │ TradingPanel │  │   Dashboard  │  │
│  └────────┬────────┘  └──────┬───────┘  └──────────────┘  │
│           │                  │                              │
│           └──────────────────┴──────────────────────────────┤
│                          HTTP/WebSocket                      │
└──────────────────────────────┬───────────────────────────────┘
                               │
┌──────────────────────────────┴───────────────────────────────┐
│              FastAPI Backend (Python)                        │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           Trading API Endpoints                      │  │
│  │  • POST /trade/simulate/advanced                     │  │
│  │  • POST /trade/execute/confirmed                     │  │
│  │  • GET /simulations/metrics                          │  │
│  │  • GET /simulations/equity-curve                     │  │
│  │  • WS /ws/trading (live updates)                     │  │
│  │  • WS /ws/nodes (node status)                        │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           Core Services                              │  │
│  │                                                      │  │
│  │  ┌─────────────────┐  ┌──────────────────────┐     │  │
│  │  │  Node Connector │  │ Simulation Service   │     │  │
│  │  │  (48 Nodes)     │  │ (Trade History)      │     │  │
│  │  └─────────────────┘  └──────────────────────┘     │  │
│  │         │                      │                    │  │
│  │         └──────────┬───────────┘                    │  │
│  │                    │                                │  │
│  │            ┌───────▼────────┐                       │  │
│  │            │  Neural Brain  │                       │  │
│  │            │  (RLAgent)     │                       │  │
│  │            └────────────────┘                       │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
└──────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┴────────────────────┐
          │                                        │
┌─────────▼──────────┐                 ┌──────────▼────────┐
│   48 Blockchain    │                 │   VVS Finance     │
│   Data Nodes       │                 │   Smart Contract  │
│                    │                 │   (Execute Swap)  │
│ • 12 Price nodes   │                 └───────────────────┘
│ • 12 Liquidity     │
│ • 12 Volume        │
│ • 12 Gas prices    │
└────────────────────┘
```

## Components

### 1. Node Connector (`agent/node_connector.py`)

Manages connections to 48 blockchain data providers:

- **12 Price Nodes**: Real-time token prices
- **12 Liquidity Nodes**: DEX liquidity pools
- **12 Volume Nodes**: Trading volume data
- **12 Gas Nodes**: Network gas price data

Features:
- Health checking and fallback routing
- Parallel data aggregation
- Response time monitoring
- Automatic reconnection

### 2. Simulation Service (`agent/simulation_service.py`)

Tracks all trade simulations with performance metrics:

- Trade history and active trades
- Equity curve calculation
- Performance metrics (Sharpe Ratio, Drawdown, Win Rate)
- Confidence distribution analysis
- P&L tracking

### 3. Trading API (`agent/api.py`)

FastAPI endpoints for:

```
POST   /trade/simulate/advanced          - Run neural network simulation
POST   /trade/execute/confirmed          - Execute real trade
GET    /simulations/metrics              - Get performance metrics
GET    /simulations/equity-curve         - Get equity curve
GET    /simulations/recent               - Recent completed trades
GET    /simulations/active               - Currently pending trades
WS     /ws/trading                       - Live metrics stream
WS     /ws/nodes                         - Node status stream
```

### 4. Frontend Components

#### SimulationView (`frontend/components/simulation-view.tsx`)
- Real-time equity curve visualization
- Performance metrics dashboard
- Confidence distribution charts
- Risk analysis
- WebSocket live updates

#### TradingPanel (`frontend/components/trading-panel.tsx`)
- Trade simulation interface
- Token selection
- Amount input
- Real-time results display
- Recent trades feed

## How to Use

### 1. Start the Backend

```bash
cd agent

# Install dependencies (if not already installed)
pip install fastapi uvicorn aiohttp python-dotenv

# Start the API server
python -m uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`

### 2. Start the Frontend

```bash
cd frontend

# Install dependencies (if not already installed)
npm install  # or pnpm install

# Start dev server
npm run dev  # or pnpm dev
```

The frontend will be available at `http://localhost:3000`

### 3. Navigate to Simulation

1. Click "Simulation" in the left sidebar
2. The SimulationView will load real data from the backend
3. See live performance metrics and equity curve

### 4. Execute a Trade

1. In the TradingPanel (right sidebar when on Simulation page):
   - Select `From Token` (e.g., CRO)
   - Select `To Token` (e.g., USDC)
   - Enter `Amount`
   - Check "Simulate only" for dry-run or uncheck to execute real trade

2. Click "Run Simulation"
   - Neural network analyzes data from all 48 nodes
   - Returns decision (BUY/SELL/HOLD) with confidence score
   - Shows predicted output and reasoning

3. Review Results:
   - Confidence score shows neural network certainty
   - Predicted output shows expected token amount
   - Data sources shows how many nodes were used

4. Execute Trade (if not simulate-only):
   - Click "Execute Trade"
   - Trade is sent to VVS Finance smart contract
   - Transaction hash returned upon success

## Simulation Metrics

The system tracks:

- **Total Trades**: Number of simulations
- **Successful Trades**: Profitable trades
- **Win Rate**: % of profitable trades
- **Sharpe Ratio**: Risk-adjusted returns (higher is better)
- **Max Drawdown**: Worst percentage loss from peak
- **Cumulative Return**: Total portfolio return
- **Average Confidence**: Mean neural network confidence
- **Equity Curve**: Portfolio value over time

## Data Flow

### Simulation Flow

```
1. User submits trade parameters
   ↓
2. Node Connector fetches data from 48 providers in parallel
   ↓
3. Data normalized and aggregated into 48-dimensional vector
   ↓
4. Neural Brain (RLAgent) processes vector
   ↓
5. Returns decision: BUY/SELL/HOLD with confidence
   ↓
6. Simulation Service records trade in history
   ↓
7. Frontend displays results with equity curve update
```

### Execution Flow

```
1. User approves simulated trade
   ↓
2. Check confidence > 0.6 threshold
   ↓
3. Estimate slippage using VVS Router
   ↓
4. Sign transaction with wallet
   ↓
5. Submit to VVS Finance contract
   ↓
6. Wait for blockchain confirmation
   ↓
7. Update simulation with actual output and TX hash
   ↓
8. Calculate realized P&L
   ↓
9. Update metrics and equity curve
```

## Environment Variables

Create `.env` in the `agent/` directory:

```bash
# LLM Configuration
OPENROUTER_API_KEY=sk_...
OPENROUTER_MODEL=openai/gpt-4o-mini

# Blockchain
CRONOS_RPC_URL=https://evm.cronos.org
WALLET_ADDRESS=0x...
PRIVATE_KEY=0x...

# Smart Contracts
USDC_CONTRACT=0x908059CF02cbb643Bc96C55e14Fb3699e632479f
VVS_ROUTER=0x3bc8a2c283751Adf1E3FAc823B6Cb0056f9f86C8
WCRO_ADDRESS=0x9005E37cDfc4361491996aD7d546fC15AC9aAD9A

# Trading Signals
TRADING_SIGNALS_URL=http://localhost:3050
```

## Node Types

### Premium Nodes (Higher Cost, Better Data)
- Lower latency
- Higher uptime
- More accurate pricing
- Used for confidence score boost

### Budget Nodes (Lower Cost)
- Standard latency
- Good for redundancy
- Used for fallback

The system balances cost and accuracy by:
1. Using premium nodes for high-confidence trades
2. Using budget nodes as backup
3. Aggregating multiple sources for robustness

## WebSocket Events

### Trading Updates (`/ws/trading`)

```json
{
  "type": "metrics_update",
  "metrics": {
    "total_trades": 48,
    "win_rate": 72.5,
    "sharpe_ratio": 1.8,
    "max_drawdown": -8.3
  },
  "recent_trades": [...],
  "equity_curve": {...},
  "timestamp": "2024-01-11T14:30:00"
}
```

### Node Status Updates (`/ws/nodes`)

```json
{
  "type": "nodes_update",
  "nodes": {
    "total_nodes": 48,
    "connected_nodes": 46,
    "nodes": [...]
  },
  "timestamp": "2024-01-11T14:30:00"
}
```

## Performance Optimization

1. **Parallel Node Queries**: All 48 nodes queried simultaneously
2. **Connection Pooling**: Reuse HTTP connections
3. **Caching**: 10-second cache for stable data
4. **Async I/O**: Non-blocking requests
5. **WebSocket**: Real-time updates without polling

## Troubleshooting

### API Connection Failed
- Check if backend is running: `curl http://localhost:8000/health`
- Check CORS settings in `api.py`
- Verify frontend API_BASE URL

### Nodes Not Responding
- Check internet connection
- Verify RPC URLs in `node_connector.py`
- Check node provider status

### Simulation Not Updating
- Refresh page (Ctrl+Shift+R)
- Check browser console for errors
- Verify WebSocket connection in DevTools

### Trade Execution Failed
- Check wallet has sufficient balance
- Verify token approvals
- Check slippage tolerance
- Review gas prices

## Advanced Configuration

### Adjust Confidence Threshold

Edit `api.py` line ~370:
```python
if simulation.confidence < 0.6:  # Change 0.6 to desired threshold
```

### Add More Nodes

Edit `node_connector.py` `_initialize_nodes()`:
```python
self.nodes[node_id] = NodeInfo(
    node_id=node_id,
    name=f"custom_node_{i}",
    rpc_url="https://your-custom-rpc.com",
    provider_type="premium",
    category="custom"
)
```

### Modify Neural Network

The `brain.py` RLAgent can be retrained:
```python
brain = RLAgent(model_path="custom_brain.pth")
brain.train(experiences, epochs=10)
brain.save()
```

## Security Considerations

1. **Private Keys**: Never commit `.env` with real private keys
2. **RPC Rate Limits**: Consider using dedicated RPC providers
3. **Slippage**: Always set appropriate slippage tolerance
4. **Whitelist**: Use wallet whitelisting for production
5. **Testing**: Always test with simulate_only=true first

## Future Enhancements

- [ ] Multi-chain support (Polygon, Arbitrum)
- [ ] Advanced order types (limit, stop-loss)
- [ ] Portfolio optimization
- [ ] Risk management modules
- [ ] Advanced charting (TradingView integration)
- [ ] Backtesting framework
- [ ] Paper trading mode
- [ ] Mobile app

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review logs in terminal output
3. Check browser DevTools console
4. Verify environment configuration

## License

This project is part of the Alpha-Consumer ecosystem.
