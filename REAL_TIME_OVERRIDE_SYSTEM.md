# Real-Time Human Override System

## Overview

This system transforms the trading agent from a static script into a **Dynamic State Machine** that obeys human commands without requiring restarts. Fund managers can now control risk tolerance and directional bias in real-time via API or CLI.

## Architecture Changes

### 1. PredictiveAgent State Variables ([agent/predictive_agent.py](agent/predictive_agent.py))

Added two new instance attributes:
- **`risk_threshold`** (float, default: 0.15) — Minimum confidence required for trade execution
- **`forced_bias`** (str|None) — Mandated direction: "LONG", "SHORT", "NEUTRAL", or None for AI discretion

These override existing environment-based `FORCE_ACTION` logic while maintaining backward compatibility.

### 2. LLM Prompt Engineering ([agent/tools.py](agent/tools.py))

The `rethink_strategy()` method now accepts an optional `human_rules` dictionary that injects "FUND MANAGER COMMANDS" into the system prompt:

```python
def rethink_strategy(self, market_snapshot, working_memory, human_rules=None, max_retries=2):
    rules = human_rules or {"risk_threshold": 0.15, "forced_bias": None}
    # Prompt includes:
    # - MANDATED DIRECTIONAL BIAS: {forced_bias}
    # - CONFIDENCE FLOOR REQUIREMENT: {risk_threshold}
```

The LLM is instructed that these commands are **non-negotiable** and override all market signals.

### 3. API Control Endpoint ([agent/api.py](agent/api.py))

New endpoint: **`POST /agent/control/override`**

**Request Body:**
```json
{
  "risk": 0.5,    // Optional: 0.0-1.0 confidence threshold
  "bias": "SHORT" // Optional: "LONG" | "SHORT" | "NEUTRAL" | "NONE"
}
```

**Response:**
```json
{
  "status": "Override Applied Successfully",
  "current_config": {
    "risk_threshold": 0.5,
    "forced_bias": "SHORT",
    "paused": false
  }
}
```

## CLI Control Scripts

### 1. **`./force_aggressive.sh`** — High-Frequency Trading Mode
- Sets risk threshold to **0.1** (10% confidence)
- Clears directional bias (AI discretion)
- **Use case:** Execute on weak signals during high volatility

```bash
./force_aggressive.sh
```

### 2. **`./force_short_only.sh`** — Bearish Market Override
- Mandates **SHORT** bias (forbids LONG trades)
- Maintains institutional-grade **0.85** threshold
- **Use case:** Downtrend confirmation, hedging positions

```bash
./force_short_only.sh
```

### 3. **`./reset_overrides.sh`** — Return to Defaults
- Risk threshold: **0.15** (institutional standard)
- Bias: **NONE** (AI uses market signals)
- **Use case:** End of trading session, resume autonomous mode

```bash
./reset_overrides.sh
```

### 4. **`./check_override_status.sh`** — Query Current Config
- Returns active risk threshold and forced bias
- **Use case:** Verify override state before market open

```bash
./check_override_status.sh
```

## Execution Flow

### Before (Static Environment Variables)
```
1. Set FORCE_ACTION=LONG in .env
2. Restart agent container
3. Agent reads env on startup
4. Change requires full restart
```

### After (Dynamic State Machine)
```
1. Agent running with default config
2. Curl /agent/control/override with new params
3. Next cycle (10 sec) uses new rules
4. No restart, no downtime
```

## How the AI Responds to Overrides

### Example 1: Aggressive Mode (risk=0.1)
**Market Signal:** Weak bullish divergence (0.12 confidence)

**Without Override:**
```
🛡️ [Risk Management] Decision confidence (0.12) below 0.15 threshold. Holding.
```

**With Override (risk=0.1):**
```
🎯 [Human Override] Threshold: 0.10 | Bias: AI Discretion
✅ [Execution] Confidence (0.12) meets 0.10 floor. Executing LONG trade.
```

### Example 2: Short-Only Mode (bias=SHORT)
**Market Signal:** Strong bullish breakout (0.92 confidence, suggests LONG)

**LLM Reasoning (with override):**
```json
{
  "thought": "Fund Manager mandated SHORT-only. Despite bullish technicals, I am FORBIDDEN from suggesting LONG. Searching for counter-trend short opportunities or recommending ABORT.",
  "execution_bias": "SHORT",
  "risk_confidence": 0.35,
  "verdict": "ABORT"
}
```

**Output:**
```
🧭 [Instance Override] Forcing SHORT bias
🛡️ [Risk Management] No valid SHORT setup. Holding per mandate.
```

## Production Scenarios

### Scenario 1: Flash Crash Recovery
```bash
# Market drops 15% in 2 minutes - disable all trading immediately
curl -X POST http://localhost:8000/agent/control/override \
     -d '{"bias": "NEUTRAL"}'
# Agent stops executing, continues monitoring
```

### Scenario 2: News-Driven Directional Play
```bash
# Fed announces rate cut - force bullish positioning
curl -X POST http://localhost:8000/agent/control/override \
     -d '{"risk": 0.3, "bias": "LONG"}'
# Agent only looks for long entries, ignores short signals
```

### Scenario 3: End-of-Day Risk Reduction
```bash
# 30 minutes before market close - raise threshold to avoid late-day noise
curl -X POST http://localhost:8000/agent/control/override \
     -d '{"risk": 0.75}'
# Only institutional-grade setups execute
```

## Integration with Existing `/chat` Endpoint

The override system complements the natural language `/chat` interface:

**Chat Command:** `"be more aggressive"`
- Interpreted by LLM in `/chat` endpoint
- Could be extended to auto-trigger `/agent/control/override`

**Override API:** Direct parameter control
- Bypasses NLP interpretation layer
- Guaranteed precise state changes

## Backward Compatibility

The system maintains support for `FORCE_ACTION` environment variable:

```python
# Priority order:
1. Instance variable (self.forced_bias) — highest
2. Environment variable (FORCE_ACTION) — fallback
3. AI discretion — default
```

## State Persistence (Future Enhancement)

Currently, overrides are in-memory only. To survive agent restarts, extend [agent/agent_state_db.py](agent/agent_state_db.py):

```python
# In AgentStateDB
def save_override_config(self, risk_threshold, forced_bias):
    self._state["override_config"] = {
        "risk_threshold": risk_threshold,
        "forced_bias": forced_bias,
        "updated_at": datetime.utcnow().isoformat()
    }
    self.save()
```

## Testing the Implementation

### Step 1: Start the agent
```bash
cd /Users/adarsh/Documents/alpha-consumer/agent
python main.py
```

### Step 2: Verify default behavior
```bash
./check_override_status.sh
# Should show: risk_threshold=0.15, forced_bias="AI Discretion"
```

### Step 3: Apply aggressive override
```bash
./force_aggressive.sh
# Watch agent logs - next cycle should show lower threshold
```

### Step 4: Force directional bias
```bash
./force_short_only.sh
# Agent should reject any LONG signals in next cycle
```

### Step 5: Reset to autonomous mode
```bash
./reset_overrides.sh
```

## Monitoring Override Activity

All override applications are visible in agent logs:

```
🧠 [Reasoning] Consulting AlphaStrategist with 12 nodes...
🎯 [Human Override] Threshold: 0.10 | Bias: SHORT
🧭 [Instance Override] Forcing SHORT bias
```

Activity is also logged to the frontend dashboard via:
```
POST http://localhost:3600/api/agent/activity
```

## Security Considerations

1. **No Authentication** — Current implementation has no auth layer. In production:
   - Add JWT tokens to `/agent/control/override`
   - Implement role-based access (only fund managers can override)
   - Audit log all override requests with user attribution

2. **Validation** — Current implementation validates:
   - `risk`: Must be 0.0-1.0 float
   - `bias`: Must be LONG/SHORT/NEUTRAL/NONE
   - Invalid requests return error without changing state

3. **Concurrent Access** — Uses global `agent_instance` singleton:
   - No race conditions (Python GIL protects instance attribute writes)
   - Multiple override requests are processed sequentially

## Why This Approach is Production-Level

1. **Human-in-the-Loop Design** — Mimics institutional HFT fund operations where traders override algorithms based on macro events

2. **Zero Downtime** — State changes in memory, no container restarts required

3. **Prompt-First Logic** — Instead of complex Python conditionals, uses LLM's reasoning capabilities to interpret and apply rules contextually

4. **Auditability** — All decisions logged with override state for post-trade analysis

5. **Graceful Degradation** — If override API is unavailable, falls back to environment variables and autonomous mode

## API Reference

### POST /agent/control/override

**Description:** Apply real-time risk and bias overrides to running agent

**Authentication:** None (add JWT in production)

**Request Headers:**
```
Content-Type: application/json
```

**Request Body Schema:**
```typescript
{
  risk?: number;     // 0.0 - 1.0, minimum confidence for execution
  bias?: string;     // "LONG" | "SHORT" | "NEUTRAL" | "NONE"
}
```

**Response Schema:**
```typescript
{
  status: string;           // "Override Applied Successfully" | "error"
  current_config?: {
    risk_threshold: number;
    forced_bias: string;    // "LONG" | "SHORT" | "NEUTRAL" | "AI Discretion"
    paused: boolean;
  },
  message?: string;         // Error message if status is "error"
}
```

**Error Codes:**
- **400**: Invalid risk value (not 0.0-1.0) or invalid bias value
- **503**: Agent not initialized yet

**Example Requests:**

```bash
# Lower risk threshold only
curl -X POST http://localhost:8000/agent/control/override \
     -H "Content-Type: application/json" \
     -d '{"risk": 0.05}'

# Change bias only
curl -X POST http://localhost:8000/agent/control/override \
     -H "Content-Type: application/json" \
     -d '{"bias": "LONG"}'

# Change both
curl -X POST http://localhost:8000/agent/control/override \
     -H "Content-Type: application/json" \
     -d '{"risk": 0.25, "bias": "SHORT"}'

# Clear bias, keep current risk threshold
curl -X POST http://localhost:8000/agent/control/override \
     -H "Content-Type: application/json" \
     -d '{"bias": "NONE"}'
```

## Troubleshooting

### Issue: "Agent not initialized yet"
**Cause:** Override called before autonomous loop started  
**Solution:** Wait 5-10 seconds after agent startup

### Issue: Overrides not taking effect
**Cause:** Agent cycle hasn't run yet (10-second interval)  
**Solution:** Wait for next cycle, check logs for confirmation

### Issue: LLM still suggests opposite bias
**Cause:** Prompt injection may be ignored by weak models  
**Solution:** Current implementation uses `gpt-4o-mini`. For stronger compliance, upgrade to `claude-3.5-sonnet` or `deepseek-reasoner`

### Issue: Overrides lost after restart
**Cause:** State is in-memory only  
**Solution:** Implement state persistence via `agent_state_db.py` (see "State Persistence" section above)

---

**Implementation Complete** — The agent now operates as a fully controllable state machine with institutional-grade override capabilities.
