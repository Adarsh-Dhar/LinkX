# agent/situational_logic.py
# Situation-category importance weights for node selection

SITUATION_WEIGHTS = {
    "PARABOLIC_PUMP": {
        "Whale Alert": 10,
        "Social Pulse": 10,
        "Technical": 4,
        "On-chain": 6,
        "Macro": 3,
        "Sentiment": 8,
    },
    "LIQUIDATION_CASCADE": {
        "Whale Alert": 8,
        "Social Pulse": 5,
        "Technical": 7,
        "On-chain": 10,
        "Macro": 6,
        "Sentiment": 4,
    },
    "VOLATILITY_SQUEEZE": {
        "Whale Alert": 3,
        "Social Pulse": 4,
        "Technical": 10,
        "On-chain": 7,
        "Macro": 5,
        "Sentiment": 2,
    },
    "PRICE_ANOMALY": {
        "Whale Alert": 7,
        "Social Pulse": 3,
        "Technical": 8,
        "On-chain": 9,
        "Macro": 4,
        "Sentiment": 2,
    },
    "ESTABLISHED_TREND": {
        "Whale Alert": 2,
        "Social Pulse": 3,
        "Technical": 6,
        "On-chain": 5,
        "Macro": 10,
        "Sentiment": 4,
    },
    # Add more situations and their category weights as needed
}
