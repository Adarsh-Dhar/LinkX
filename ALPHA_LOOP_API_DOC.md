# Alpha Loop API Documentation

## Endpoints

### /api/agent/data-log
- **GET**: Returns recent data log entries (node, value, timestamp)

### /api/agent/decision-log
- **GET**: Returns recent trade decisions (action, token, signal, reason, timestamp)

### /api/agent/roi
- **GET**: Returns total data cost and trading profit

### /api/agent/kill-switch
- **GET**: Returns kill switch status
- **POST**: Set kill switch (action: 'kill' or 'resume')

### /api/agent/daily-limit
- **GET**: Returns current daily spend limit
- **POST**: Set new daily spend limit

### /api/health
- **GET**: Health check for backend

## Agent Logic
- The agent runs an autonomous loop: scans market, assesses confidence, buys data, ingests, updates strategy, and trades.
- All data purchases and blacklists are persisted to disk.

## Deployment
- Start backend: `pnpm dev` (frontend)
- Start agent: `python3 agent/main.py`
- Configure .env for keys and endpoints

---
For more details, see code comments and README files in each directory.
