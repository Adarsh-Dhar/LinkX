# Agent Activity Logging Integration Guide

This guide explains how to integrate the Python agent with the activity logging system to capture node purchases, utility scores, trade decisions, and risk management actions.

## Overview

The agent can log its decisions and activities to the database via the `/api/agent/activity` endpoint. These activities will appear in the "Recent Activity" feed on the dashboard.

## API Endpoint

**POST** `/api/agent/activity`

### Request Body

```json
{
  "type": "node_purchase|trade_decision|utility_score|signal_received|risk_skip|cycle_start|cycle_end",
  "title": "Human-readable title",
  "description": "Detailed description",
  "nodeId": "node-uuid (optional)",
  "nodePrice": 0.25,
  "nodeQuality": 98,
  "utilityScore": 0.7404,
  "alphaPerUsdcRatio": 2.9616,
  "signalValue": 0.61,
  "signalSource": "market_microstructure",
  "tradeBias": "BUY|SELL|NEUTRAL",
  "tradeConfidence": 0.85,
  "tradeReason": "Positive signal from microstructure",
  "riskAction": "SKIP|EXECUTE|HOLD",
  "riskReason": "Bias neutral, holding for confirmation",
  "agentThought": "Full strategist thought process",
  "metadata": { "custom": "data" }
}
```

## Implementation in Python Agent

Add this to your agent's activity logging:

```python
import requests
import json

ACTIVITY_LOG_URL = "http://localhost:3600/api/agent/activity"

def log_activity(activity_type, title, **kwargs):
    """Log an agent activity to the database"""
    try:
        payload = {
            "type": activity_type,
            "title": title,
            **kwargs
        }
        response = requests.post(ACTIVITY_LOG_URL, json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Failed to log activity: {e}")

# Example: Log node purchase
log_activity(
    "node_purchase",
    "Purchased Market Microstructure & Execution",
    description="Quality: 98/100 | Utility Score: 0.7404",
    nodePrice=0.25,
    nodeQuality=98,
    utilityScore=0.7404,
    alphaPerUsdcRatio=2.9616
)

# Example: Log utility score
log_activity(
    "utility_score",
    "Computed Utility Scores",
    description="Utility: 0.7404 | Alpha/USDC: 2.9616",
    utilityScore=0.7404,
    alphaPerUsdcRatio=2.9616,
    agentThought="Volatility is moderate (3.11 > 0.05), favoring microstructure nodes"
)

# Example: Log trade decision
log_activity(
    "trade_decision",
    "Initiated Trade",
    description="BUY signal from microstructure",
    tradeBias="BUY",
    tradeConfidence=0.85,
    tradeReason="Positive signal from market_microstructure node"
)

# Example: Log risk management skip
log_activity(
    "risk_skip",
    "Skipped Trade Execution",
    description="Risk management: bias NEUTRAL, confidence 0.85",
    riskAction="SKIP",
    riskReason="Bias is neutral - waiting for confirmation"
)

# Example: Log cycle start/end
log_activity("cycle_start", "Predictive Agent Cycle Started")
log_activity("cycle_end", "Predictive Agent Cycle Completed")
```

## Integration Points

### In `autonomous_loop.py`

```python
# After computing utility scores
log_activity(
    "utility_score",
    f"Computed {len(nodes)} Node Utility Scores",
    description=f"Top utility: {max_utility:.4f}",
    utilityScore=max_utility,
    alphaPerUsdcRatio=best_ratio,
    agentThought=strategist_thought
)

# After node purchase decision
if should_purchase_node:
    log_activity(
        "node_purchase",
        f"Purchased {selected_node.name}",
        description=f"Quality: {selected_node.quality}% | Price: {selected_node.price} USDC",
        nodeId=selected_node.id,
        nodePrice=selected_node.price,
        nodeQuality=selected_node.quality,
        utilityScore=node_utility,
        alphaPerUsdcRatio=alpha_ratio
    )

# After receiving signal
if signal_received:
    log_activity(
        "signal_received",
        f"Signal from {node_name}",
        description=f"Value: {signal_value:.2f}",
        signalValue=signal_value,
        signalSource=node_name
    )

# After risk decision
log_activity(
    "risk_skip" if should_skip else "trade_decision",
    f"{'Skipped' if should_skip else 'Executed'} Trade",
    description=f"{trade_reason}",
    tradeBias=bias,
    tradeConfidence=confidence,
    riskAction="SKIP" if should_skip else "EXECUTE",
    riskReason=risk_reason
)
```

## Database Schema

Activities are stored in the `AgentActivity` table with fields:
- `id`: Unique identifier
- `type`: Activity type (node_purchase, trade_decision, etc.)
- `title`: Display title
- `description`: Detailed message
- `utilityScore`: 0.0-1.0
- `nodePrice`, `nodeQuality`: Node purchase details
- `tradeBias`, `tradeConfidence`: Trade details
- `riskAction`, `riskReason`: Risk management details
- `agentThought`: Full reasoning
- `timestamp`: Auto-generated

## Activity Types

| Type | Use Case |
|------|----------|
| `node_purchase` | When agent purchases an alpha node |
| `trade_decision` | When agent executes a trade |
| `utility_score` | When agent computes node utility scores |
| `signal_received` | When agent receives a signal from a node |
| `risk_skip` | When risk management skips execution |
| `cycle_start` | Start of agent cycle |
| `cycle_end` | End of agent cycle |

## Frontend Display

Activities appear in the Recent Activity feed with:
- Icon based on activity type
- Color-coded for positive/negative impact
- Timestamp
- Title and description
- Key metrics (utility score, price, confidence, etc.)

The feed updates every 10 seconds and shows up to 12 most recent activities from the last 30 minutes.
