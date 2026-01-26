const express = require('express');

// Constants for the demo
const TREASURY_WALLET = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e";
const ASSET_TICKER = "WETH/USDC";

/**
 * Common middleware to handle x402 handshakes
 * Returns 402 if X-Payment-Proof header is missing
 */
const x402Middleware = (price) => (req, res, next) => {
    const paymentProof = req.headers['x-payment-proof'];

    if (!paymentProof) {
        console.log(`[x402] Request blocked: Payment Required (${price} USDC)`);
        return res.status(402)
            .header('X-Payment-Price', price)
            .header('X-Payment-Wallet', TREASURY_WALLET)
            .json({
                error: "Payment Required",
                protocol: "x402",
                price: price,
                destination: TREASURY_WALLET
            });
    }
    
    console.log(`[x402] Access Granted: Proof ${paymentProof.substring(0,10)}...`);
    next();
};

// --- NODE 1: Market Microstructure (Port 4001) ---
const node1 = express();
node1.get('/api/microstructure', x402Middleware(0.25), (req, res) => {
    res.json({
        node: "Market Microstructure & Execution",
        timestamp: Date.now(),
        data: {
            order_book_depth: { bids: 450000, asks: 120000 }, // Bullish depth
            trade_velocity: "85 ticks/sec",
            vwap: 2942.50,
            iceberg_detected: false,
            latency_ms: 5,
            quality_score: 98
        }
    });
});

// --- NODE 2: Alternative Intelligence (Port 4002) ---
const node2 = express();
node2.get('/api/sentiment', x402Middleware(0.45), (req, res) => {
    res.json({
        node: "Alternative Intelligence & Sentiment",
        timestamp: Date.now(),
        data: {
            social_sentiment: 0.82, // Highly Bullish
            social_velocity_change: "+15%",
            satellite_retail_occupancy: "88%",
            web_traffic_index: 1.4,
            quality_score: 85,
            asset_coverage: [ASSET_TICKER]
        }
    });
});

// --- NODE 3: Supply Chain & Global Macro (Port 4003) ---
const node3 = express();
node3.get('/api/macro', x402Middleware(0.65), (req, res) => {
    res.json({
        node: "Supply Chain & Global Macro",
        timestamp: Date.now(),
        data: {
            port_congestion_index: 0.12, // Low congestion (good for supply)
            vessel_count_transit: 1420,
            energy_grid_stability: "Normal",
            economic_indicators: {
                cpi_expectation: "2.1%",
                central_bank_bias: "Hawkish"
            },
            quality_score: 92
        }
    });
});

// Start all three servers
node1.listen(4001, () => console.log("🚀 Node 1: Microstructure online on :4001"));
node2.listen(4002, () => console.log("🚀 Node 2: Sentiment online on :4002"));
node3.listen(4003, () => console.log("🚀 Node 3: Global Macro online on :4003"));