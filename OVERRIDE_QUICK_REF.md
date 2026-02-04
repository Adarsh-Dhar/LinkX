# 🎛️ Trading Agent Override Quick Reference

## Control Scripts

| Script | Risk | Bias | Use Case |
|--------|------|------|----------|
| `./force_aggressive.sh` | 0.1 | NONE | High-frequency trading, execute on weak signals |
| `./force_short_only.sh` | 0.85 | SHORT | Bearish market, hedging mode |
| `./force_conservative.sh` | 0.75 | NONE | Risk-off, uncertain conditions |
| `./emergency_stop.sh` | - | NEUTRAL | Freeze all trading immediately |
| `./reset_overrides.sh` | 0.15 | NONE | Return to autonomous defaults |
| `./check_override_status.sh` | - | - | Query current configuration |

## API Endpoint

```bash
curl -X POST http://localhost:8000/agent/control/override \
     -H "Content-Type: application/json" \
     -d '{"risk": 0.5, "bias": "LONG"}'
```

## Parameters

**risk** (float, 0.0-1.0):
- `0.05-0.15`: Aggressive (trades on weak signals)
- `0.15-0.50`: Balanced (default institutional)
- `0.50-0.85`: Conservative (high conviction only)
- `0.85-1.00`: Ultra-conservative (near-certainty required)

**bias** (string):
- `"LONG"`: Only buy signals (shorts forbidden)
- `"SHORT"`: Only sell signals (longs forbidden)
- `"NEUTRAL"`: Freeze all trading (monitoring only)
- `"NONE"`: AI uses market signals (autonomous)

## Common Scenarios

### 📈 Bull Market Confirmation
```bash
curl -X POST http://localhost:8000/agent/control/override \
     -d '{"risk": 0.3, "bias": "LONG"}'
```

### 📉 Bear Market Defense
```bash
curl -X POST http://localhost:8000/agent/control/override \
     -d '{"risk": 0.4, "bias": "SHORT"}'
```

### 🔥 Flash Crash Response
```bash
./emergency_stop.sh  # Immediate halt
```

### 🌙 After-Hours Low Liquidity
```bash
./force_conservative.sh  # Raise threshold
```

### ⚡ High Volatility Scalping
```bash
./force_aggressive.sh  # Lower threshold
```

## Verification

Check agent logs for confirmation:
```
🎯 [Human Override] Threshold: 0.10 | Bias: SHORT
🧭 [Instance Override] Forcing SHORT bias
```

## Implementation Files

- [agent/predictive_agent.py](agent/predictive_agent.py) — State variables
- [agent/tools.py](agent/tools.py) — LLM prompt injection
- [agent/api.py](agent/api.py) — `/agent/control/override` endpoint
- [REAL_TIME_OVERRIDE_SYSTEM.md](REAL_TIME_OVERRIDE_SYSTEM.md) — Full documentation
