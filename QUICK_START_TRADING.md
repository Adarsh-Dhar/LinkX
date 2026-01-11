# Quick Start Guide - Neural Agent Trading System

## 5-Minute Setup

### Prerequisites
- Python 3.9+
- Node.js 18+
- Cronos wallet with testnet CRO/USDC

### Step 1: Install Backend (1 min)

```bash
cd agent
pip install fastapi uvicorn aiohttp python-dotenv web3 torch numpy
```

### Step 2: Configure Environment (1 min)

Create `agent/.env`:
```bash
# Blockchain
CRONOS_RPC_URL=https://evm-t3.cronos.org
WALLET_ADDRESS=your_wallet_address_here
PRIVATE_KEY=your_private_key_here  # For testnet only!

# Smart Contracts (Testnet)
USDC_CONTRACT=0x908059CF02cbb643Bc96C55e14Fb3699e632479f
VVS_ROUTER=0x3bc8a2c283751Adf1E3FAc823B6Cb0056f9f86C8
WCRO_ADDRESS=0x9005E37cDfc4361491996aD7d546fC15AC9aAD9A

# Optional: LLM (for agent chat)
OPENROUTER_API_KEY=sk_your_key_here
```

### Step 3: Start Backend (1 min)

```bash
cd agent
python -m uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 4: Start Frontend (1 min)

In a new terminal:
```bash
cd frontend
npm install
npm run dev
```

Visit: http://localhost:3000

### Step 5: Run First Simulation (1 min)

1. Click **"Simulation"** in the sidebar
2. In the right panel, select:
   - From: **CRO**
   - To: **USDC**
   - Amount: **100**
   - Check **"Simulate only"**
3. Click **"Run Simulation"**
4. Watch the results appear:
   - Neural decision (BUY/SELL/HOLD)
   - Confidence score
   - Predicted output
   - 48 nodes data sources

## What You're Seeing

### Simulation View
- **Equity Curve**: Portfolio growth over time
- **Confidence Distribution**: Network certainty levels
- **Metrics**: Win rate, Sharpe ratio, max drawdown

### Trading Panel
- **Neural Decision**: AI recommendation based on 48 data sources
- **Confidence Score**: How sure the AI is (0-100%)
- **Predicted Output**: Expected tokens you'll receive
- **Recent Trades**: History of simulations

## Understanding the Data Flow

```
┌──────────────────────────────────────────┐
│  You submit: 100 CRO → USDC             │
└──────────────────┬───────────────────────┘
                   │
          ┌────────▼────────┐
          │  48 Nodes Fetch │
          │  Real Data:     │
          │ • Prices        │
          │ • Liquidity     │
          │ • Volume        │
          │ • Gas Prices    │
          └────────┬────────┘
                   │
          ┌────────▼────────────┐
          │ Neural Brain        │
          │ Analyzes all 48     │
          │ data points and     │
          │ makes decision      │
          └────────┬────────────┘
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
    Show Results      Execute Trade
    (simulate_only)   (real blockchain)
```

## Key Features

### 1. Real Node Data (48 Sources)
- Premium + Budget providers
- Automatic fallback if node is slow
- Parallel queries for speed

### 2. Neural Network Predictions
- BUY: Confidence the price will go up
- SELL: Confidence the price will go down
- HOLD: Uncertainty, no trade

### 3. Live Metrics
- Equity curve updates in real-time
- Win rate tracks accuracy
- Sharpe ratio shows risk-adjusted returns
- Max drawdown shows worst loss

### 4. Safe by Default
- All trades start in **"simulate only"** mode
- See what WOULD happen without real money
- Only execute when confident

## Common Actions

### Run a Simulation
1. Change token pairs in Trade Panel
2. Enter amount
3. Keep "Simulate only" checked
4. Click "Run Simulation"

### View Performance
1. Click "Simulation" tab
2. Scroll down to see:
   - Total trades
   - Win rate percentage
   - Current equity
   - Risk analysis

### Check Node Status
- Backend console shows node responses
- Green = online and fast
- Yellow = online but slow
- Red = offline (uses fallback)

## Troubleshooting Quick Fixes

**Backend won't start?**
```bash
# Check Python version
python --version  # Should be 3.9+

# Install missing packages
pip install fastapi uvicorn aiohttp
```

**Frontend won't connect to API?**
- Check backend is running: `curl http://localhost:8000/health`
- Check CORS is enabled in `api.py`
- Check API_BASE in `simulation-view.tsx`

**WebSocket connection fails?**
- This is normal on first load, it retries
- Real-time updates will work once connected
- Frontend falls back to HTTP polling

**Nodes not responding?**
- Check internet connection
- Your RPC URLs might be rate limited
- Try alternative RPC endpoints in `.env`

## Next Steps

1. **Understand the Metrics**
   - Read NEURAL_AGENT_NODE_INTEGRATION.md
   - Learn what Sharpe Ratio means
   - Understand max drawdown

2. **Test Different Trade Pairs**
   - CRO ↔ USDC (most liquid)
   - VVS ↔ USDC (alternative pair)
   - Try different amounts

3. **Monitor the Neural Network**
   - Watch confidence scores improve over time
   - See how it handles volatility
   - Compare against actual market movement

4. **Configure Real Trading** (Advanced)
   - Uncheck "Simulate only"
   - Increase confidence threshold
   - Use small amounts first
   - Monitor gas prices

## File Structure

```
agent/
├── api.py                      # FastAPI server ← Start here
├── node_connector.py           # 48 node management
├── simulation_service.py       # Trade history & metrics
├── brain.py                    # Neural network
├── tools.py                    # Blockchain interactions
└── .env                        # Your config (create this)

frontend/
├── app/page.tsx               # Main app ← Access from browser
├── components/
│   ├── simulation-view.tsx    # Real metrics & charts
│   └── trading-panel.tsx      # Trade executor
└── package.json
```

## API Endpoints You Can Test

```bash
# Health check
curl http://localhost:8000/health

# Get metrics
curl http://localhost:8000/simulations/metrics

# Get equity curve
curl http://localhost:8000/simulations/equity-curve

# Get recent trades
curl http://localhost:8000/simulations/recent?limit=5

# Run simulation
curl -X POST http://localhost:8000/trade/simulate/advanced \
  -H "Content-Type: application/json" \
  -d '{
    "token_in": "CRO",
    "token_out": "USDC",
    "amount": 100,
    "simulate_only": true,
    "slippage_tolerance": 1.0
  }'
```

## Understanding Confidence Scores

| Score | Meaning | Action |
|-------|---------|--------|
| 90%+ | Very confident | Safe to execute |
| 70-90% | Confident | Reasonable to trade |
| 50-70% | Uncertain | Consider waiting |
| <50% | Not confident | HOLD or skip |

## Performance Tips

1. **More Nodes = Better Decisions**
   - 48 nodes → highly accurate
   - Fallback system ensures reliability
   - Parallel queries keep it fast

2. **Monitor During Volatility**
   - Sharpe ratio changes with market
   - Max drawdown increases in crashes
   - Win rate reflects strategy quality

3. **Check Recent Trades**
   - Successful trades shown in panel
   - P&L shows profit/loss
   - Watch for patterns

## Get Help

1. Check backend logs (terminal where you ran api.py)
2. Check frontend logs (browser DevTools → Console)
3. Read the full integration guide: `NEURAL_AGENT_NODE_INTEGRATION.md`
4. Review comments in code files

## Security Reminder ⚠️

- `.env` contains your private key
- **NEVER commit .env to git**
- Add to `.gitignore`:
  ```
  .env
  *.pth
  __pycache__/
  ```
- Use testnet keys only
- Start with small amounts
- Always simulate before executing

---

**Congratulations!** You now have a fully functional neural network trading agent with 48 blockchain data sources. Happy trading! 🚀
