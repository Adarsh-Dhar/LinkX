// node_macro.js
// Node 3: Global Macroeconomic Indicators and Supply Chain Logistics
// Monitors large-scale economic and physical world data that impacts long-term asset valuations.

const express = require('express');
const { x402Middleware, getRandom } = require('./shared_logic');
const app = express();

app.get('/api/macro', x402Middleware(0.65), (req, res) => {
    res.json({
        node: "Supply Chain & Global Macro",
        description: "This node monitors large-scale economic and physical world data that impacts long-term asset valuations. It tracks supply chain health through port congestion indices and vessel transit counts, alongside critical infrastructure metrics like energy grid stability. Furthermore, it provides high-level economic indicators, including Consumer Price Index (CPI) expectations and Central Bank biases (Hawkish vs. Dovish), maintaining a 92% quality score for fundamental research.",
        timestamp: Date.now(),
        data: {
            port_congestion_index: getRandom(0.05, 0.35, 2),
            vessel_count_transit: getRandom(1300, 1500),
            energy_grid_stability: Math.random() > 0.9 ? "Fluctuating" : "Stable",
            economic_indicators: {
                cpi_expectation: `${getRandom(1.9, 2.6, 1)}%`,
                central_bank_bias: Math.random() > 0.5 ? "Hawkish" : "Dovish"
            },
            quality_score: 92
        }
    });
});

app.listen(4003, () => console.log("🚀 Global Macro Node online on :4003"));
