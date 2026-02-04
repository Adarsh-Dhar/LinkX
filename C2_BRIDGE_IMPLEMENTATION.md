# Real-Time Chat-to-Agent Command & Control (C2) System

## Overview

This C2 bridge allows the Next.js chat interface to parse user "intents" (e.g., "be more aggressive") and transmit them as structured state overrides to the Python agent in real-time.

## Architecture

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│  Next.js Chat   │────────>│  Intent Extractor │────────>│  Agent API      │
│  (Frontend)     │         │  (OpenRouter LLM) │         │  (FastAPI)      │
└─────────────────┘         └──────────────────┘         └─────────────────┘
                                                                    │
                                                                    ▼
                                                          ┌─────────────────┐
                                                          │ PredictiveAgent │
                                                          │ (Live Instance) │
                                                          └─────────────────┘
```

## Components Modified

### 1. Agent State Layer (`agent/predictive_agent.py`)

**State Variables:**
- `self.risk_threshold` (float 0.0-1.0): Minimum confidence required to execute trades
- `self.forced_bias` (str | None): "LONG", "SHORT", "NEUTRAL", or None for AI discretion

**New Method:**
```python
def apply_human_interference(self, risk: float = None, bias: str = None):
    """Inject human overrides into the agent's state in real time."""
```

**Integration:**
- `run_cycle()` now bundles `human_rules = {"risk_threshold": ..., "forced_bias": ...}`
- These rules are passed to the strategist LLM on every decision cycle
- Overrides persist across cycles until explicitly changed

### 2. Cognitive Strategist (`agent/tools.py`)

**Prompt Enhancement:**
```
## FUND MANAGER OVERRIDES (HIGHEST PRIORITY)
- If 'forced_bias' is set to SHORT, you are FORBIDDEN from choosing LONG
- If 'forced_bias' is set to LONG, you are FORBIDDEN from choosing SHORT
- If 'forced_bias' is set to NEUTRAL, you must NOT execute any trades
- If 'forced_bias' is None, use your own logic
- The Fund Manager's overrides supersede all other logic
```

**Method Signature:**
```python
def rethink_strategy(self, market_snapshot, working_memory, human_rules=None, max_retries=2)
```

### 3. Backend Control Plane (`agent/api.py`)

**New Endpoint:**
```
POST /agent/control/override
Content-Type: application/json

{
  "risk": 0.1,        # Optional: 0.0-1.0 confidence threshold
  "bias": "SHORT"     # Optional: "LONG", "SHORT", "NEUTRAL", "NONE"
}
```

**Response:**
```json
{
  "status": "Override Applied Successfully",
  "current_config": {
    "risk_threshold": 0.1,
    "forced_bias": "SHORT",
    "paused": false
  }
}
```

### 4. Chat Interface (`frontend/app/api/chat/route.ts`)

**Intent Extraction:**
Uses OpenRouter's `gpt-4o-mini` with function-calling to map natural language to actions:

| User Message | Intent | API Call |
|-------------|--------|----------|
| "be more aggressive" | `SET_RISK` | `{"risk": 0.1}` |
| "be conservative" | `SET_RISK` | `{"risk": 0.85}` |
| "go short only" | `SET_BIAS` | `{"bias": "SHORT"}` |
| "AI discretion" | `SET_BIAS` | `{"bias": "NONE"}` |
| "pause trading" | `PAUSE` | Forwards to `/chat` |

**UI Feedback:**
```
✅ Maneuver accepted:
• Risk Threshold: 0.1
• Bias: SHORT
• Status: Active
```

## Usage Workflow

### 1. Start the Stack
```bash
# Terminal 1: Agent
cd agent && python -m agent.main

# Terminal 2: Frontend
cd frontend && npm run dev

# Terminal 3: Providers (if using real x402)
./start_demo_providers.sh
```

### 2. Issue Commands via Chat
Open `http://localhost:3600` and type:
- **"Be extremely aggressive"** → Sets `risk_threshold = 0.1`
- **"Fire the short"** → Sets `forced_bias = "SHORT"`
- **"Give AI control back"** → Sets `forced_bias = None`

### 3. Verify Override Status
```bash
./check_override_status.sh
```

Expected output:
```json
{
  "status": "Override Applied Successfully",
  "current_config": {
    "risk_threshold": 0.1,
    "forced_bias": "SHORT",
    "paused": false
  }
}
```

### 4. Trigger Action
```bash
./test_buy.sh  # Or wait for next agent cycle (15s)
```

### 5. Confirm Obedience
Check the agent logs for:
```
🎯 [Human Override] Threshold: 0.10 | Bias: SHORT
🚀 [EXECUTION] Action: SHORT | Confidence: 1.00 | Threshold: 0.10
```

## Override Examples

### Example 1: Force Aggressive Short
```typescript
// Chat input: "Lower the floor and go short"
await fetch('http://localhost:8000/agent/control/override', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ risk: 0.1, bias: "SHORT" })
});
```

### Example 2: Reset to Conservative AI
```typescript
// Chat input: "Be conservative and let AI decide"
await fetch('http://localhost:8000/agent/control/override', {
  method: 'POST',
  body: JSON.stringify({ risk: 0.85, bias: "NONE" })
});
```

### Example 3: Emergency Neutral
```typescript
// Chat input: "Neutral stance immediately"
await fetch('http://localhost:8000/agent/control/override', {
  method: 'POST',
  body: JSON.stringify({ bias: "NEUTRAL" })
});
```

## Testing Checklist

- [ ] Start agent, frontend, and providers
- [ ] Open chat at `http://localhost:3600`
- [ ] Say "be aggressive" → Verify `risk_threshold = 0.1`
- [ ] Run `./check_override_status.sh` → Confirm override state
- [ ] Run `./test_buy.sh` → Verify agent executes immediately
- [ ] Say "give control back" → Verify `forced_bias = None`
- [ ] Check agent logs for LLM prompt containing override section
- [ ] Confirm trades skip high-confidence filter when overridden

## Security Considerations

### Production Deployment
1. **Authentication**: Add JWT/API key to `/agent/control/override`
2. **Rate Limiting**: Prevent override spam
3. **Audit Log**: Record all override commands with timestamps
4. **Role-Based Access**: Only fund managers can set overrides
5. **Confirmation Dialog**: Require explicit confirmation for aggressive settings

### Example Auth Middleware
```python
@app.post("/agent/control/override")
async def apply_override(data: dict, api_key: str = Header(...)):
    if api_key != os.getenv("FUND_MANAGER_API_KEY"):
        raise HTTPException(status_code=403, detail="Unauthorized")
    # ... rest of implementation
```

## Troubleshooting

### Override Not Applying
- Check agent is running: `curl http://localhost:8000/health`
- Verify instance exists: Look for `current_predictive_instance` in logs
- Restart agent if stale: `pkill -f agent.main && python -m agent.main`

### Chat Not Extracting Intent
- Check OpenRouter API key in `.env`: `OPENROUTER_API_KEY`
- Test intent extraction directly:
  ```bash
  curl http://localhost:3600/api/chat \
    -X POST \
    -H "Content-Type: application/json" \
    -d '{"message": "be aggressive"}'
  ```

### Agent Ignoring Overrides
- Verify LLM prompt includes `FUND MANAGER OVERRIDES` section
- Check logs for: `🎯 [Human Override] Threshold: X.XX | Bias: Y`
- Confirm `human_rules` is passed to `rethink_strategy()`

## Future Enhancements

1. **Persistent State**: Store overrides in Redis for agent restarts
2. **Node Blacklisting**: Add `POST /agent/control/blacklist` to disable specific nodes
3. **Position Sizing**: Allow "risk 50 USDC on this trade" commands
4. **Time-Bounded Overrides**: Auto-expire aggressive settings after N cycles
5. **Voice Commands**: Integrate speech-to-text for verbal control
6. **Multi-Agent**: Broadcast overrides to agent fleet

## References

- [Force Aggressive Script](force_aggressive.sh) - Example shell-based override
- [Production API Providers](PRODUCTION_API_PROVIDERS.md) - x402 integration guide
- [Real-Time Override System](REAL_TIME_OVERRIDE_SYSTEM.md) - Original design doc
