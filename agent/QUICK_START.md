# Quick Start - Lightweight Trading Agent

## The Problem (FIXED!)
The original agent was hitting token limits:
```
Error code: 402 - Prompt tokens limit exceeded
```

## The Solution ✅
Use the **lightweight agent** that bypasses SDK overhead:

```bash
./run_agent.sh
```

Or:

```bash
python lightweight_agent.py
```

## Your Balance
```
CRO: 41.515864
```

## Available Commands

### Check Balances
```
cro balance
usdc balance  
check balance  (checks all)
```

### Execute Swaps
```
swap 1 usdc to vvs
swap 5 usdc to vvs
```

### Exit
```
exit
quit
q
```

## What Changed?

1. ✅ Created lightweight agent (no SDK overhead)
2. ✅ Reduced OPENROUTER_MAX_TOKENS: 256 → 150
3. ✅ Added OPENROUTER_MAX_HISTORY: unlimited → 1
4. ✅ Shortened all tool descriptions
5. ✅ Changed model to openai/gpt-4o-mini

## Files

- `lightweight_agent.py` - Main agent (use this!)
- `run_agent.sh` - Quick launcher
- `TOKEN_LIMIT_FIX.md` - Detailed explanation
- `main.py` - Original SDK agent (still has issues)

## Need More?

For advanced AI features, upgrade at:
https://openrouter.ai/settings/credits

The lightweight agent handles all essential trading operations without token limits!
