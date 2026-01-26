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
    # Add more situations and their category weights as needed
}
