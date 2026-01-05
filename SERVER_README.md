# Trading Signals Server - Quick Start

## Problem
The agent was failing with connection errors when trying to fetch trading signals:
```
Connection refused to http://localhost:3050
```

## Solution
The trading signals server needs to be running before using the agent.

## Quick Start

### Option 1: Use the startup script (Recommended)
```bash
./start_signals_server.sh
```

### Option 2: Manual start
```bash
cd server
pnpm start
```

## Verify Server is Running
```bash
curl http://localhost:3050/trading/signals
```

Expected response:
```json
{
  "timestamp": "2026-01-04T...",
  "count": 2,
  "signals": [
    {"ticker": "CRO", "signal": "BUY", ...},
    {"ticker": "VVS", "signal": "BUY", ...}
  ]
}
```

## Stop Server
```bash
# Find the process
lsof -i :3050

# Kill it
kill $(lsof -t -i :3050)
```

## Available Endpoints

- **GET** `/trading/signals` - Get active trading signals
- **GET** `/portfolio/value?address=0x...` - Get portfolio value
- **GET** `/buy-alpha` - Get BUY-only signals
- **POST** `/alpha/premium` - Premium alpha insights (402 payment required)

## Server Configuration

Server runs on port 3050 (configurable via `server/.env`):
```
PORT=3050
CRONOS_RPC_URL=https://evm-t3.cronos.org
USDC_CONTRACT=0x908059CF02cbb643Bc96C55e14Fb3699e632479f
...
```

## Integration with Agent

The agent automatically connects to `http://localhost:3050` (configured in `agent/.env`):
```
TRADING_SIGNALS_URL=http://localhost:3050
```

Make sure to start the server before running the agent!
