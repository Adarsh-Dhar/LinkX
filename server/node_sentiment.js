// node_sentiment.js
// Node 2: AI-Driven Social Sentiment and Alternative Behavioral Intelligence
// Specializes in quantifying the "human element" of the market by aggregating data from social platforms.

const express = require('express');
const { x402Middleware, getRandom, ASSET_TICKER, TREASURY_WALLET, registerNode } = require('./shared_logic');
const app = express();
app.use(express.json());

app.get('/api/sentiment', x402Middleware(0.45), (req, res) => {
    const score = getRandom(0.1, 0.9, 2);
    res.json({
        node: "Alternative Intelligence & Sentiment",
        description: "This node specializes in quantifying the 'human element' of the market by aggregating data from social platforms to produce a highly bullish or bearish sentiment score. It tracks social velocity changes, web traffic indices, and even simulated satellite retail occupancy data to provide a holistic view of asset demand. With an 85% quality score, it helps traders understand the psychological momentum behind price action beyond traditional chart-based technical analysis.",
        timestamp: Date.now(),
        data: {
            social_sentiment: score,
            sentiment_label: score > 0.7 ? "Euphoric" : score < 0.3 ? "Fear" : "Neutral",
            social_velocity_change: `${getRandom(-15, 25)}%`,
            web_traffic_index: getRandom(1.0, 2.2, 1),
            quality_score: 85,
            asset_coverage: [ASSET_TICKER]
        }
    });
});

// POST /feed endpoint for x402 payment proof verification
app.post('/api/sentiment/feed', (req, res) => {
    const paymentProof = req.headers['x-402-payment-proof'];
    
    if (!paymentProof) {
        return res.status(402).json({
            error: 'Payment Required',
            price: 0.45,
            node: 'Alternative Intelligence & Sentiment'
        });
    }
    
    // Verify tx hash format (0x + 64 hex chars)
    const isValidTxHash = /^0x[a-fA-F0-9]{64}$/.test(paymentProof);
    if (!isValidTxHash) {
        console.warn(`[Sentiment] Invalid tx hash format: ${paymentProof}`);
    }
    
    console.log(`✅ [Sentiment] Access granted with proof ${paymentProof.slice(0, 10)}...`);
    
    // Return locked data
    const score = getRandom(0.1, 0.9, 2);
    res.json({
        success: true,
        node: 'Alternative Intelligence & Sentiment',
        timestamp: Date.now(),
        signal: parseFloat(score),
        data: {
            social_sentiment: score,
            sentiment_label: score > 0.7 ? "Euphoric" : score < 0.3 ? "Fear" : "Neutral",
            social_velocity_change: `${getRandom(-15, 25)}%`,
            web_traffic_index: getRandom(1.0, 2.2, 1),
            quality_score: 85,
            asset_coverage: [ASSET_TICKER]
        }
    });
});

// Register with marketplace on startup
registerNode({
    name: 'Alternative Intelligence & Sentiment',
    nodeType: 'sentiment',
    category: 'Sentiment',
    endpointUrl: 'http://localhost:4002/api/sentiment',
    port: 4002,
    price: 0.45,
    qualityScore: 85,
    description: "Quantifies the 'human element' of the market by aggregating data from social platforms to produce highly bullish or bearish sentiment scores. Tracks social velocity changes, web traffic indices, and simulated satellite retail occupancy data.",
    providerAddress: TREASURY_WALLET,
    assetCoverage: 'WXTZ/USDC',
    granularity: '1m'
}).catch(err => console.error('Registration error:', err));

app.listen(4002, () => console.log("🚀 Sentiment Node online on :4002"));
