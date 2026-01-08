import express from "express";
import cors from "cors";
import { ethers } from "ethers";
import "dotenv/config";
import fetch from "node-fetch";

const app = express();
const PORT = process.env.PORT || 3050;

// --- CONFIGURATION ---
const SELLER_WALLET = process.env.WALLET_ADDRESS || "0xYourWalletAddressHere";
// Use a free CoinGecko Demo Key if you have one, or leave blank for public rate limits
const COINGECKO_API_KEY = process.env.COINGECKO_API_KEY || ""; 

app.use(cors());
app.use(express.json());

// --- IN-MEMORY CACHE (Prevents Rate Limiting) ---
let priceCache = {
    CRO: { value: 0.10, lastUpdated: 0, history: [] },
    VVS: { value: 0.000003, lastUpdated: 0, history: [] },
    USDC: { value: 1.00, lastUpdated: 0, history: [] }
};


// 1. HELPER: Fetch Real Price from CoinGecko
async function fetchRealPrice(ticker) {
    const idMap = { 'CRO': 'crypto-com-chain', 'VVS': 'vvs-finance', 'USDC': 'usd-coin' };
    const coinId = idMap[ticker];
    if (!coinId) return null;

    try {
        // Free tier endpoint
        const url = `https://api.coingecko.com/api/v3/simple/price?ids=${coinId}&vs_currencies=usd`;
        const response = await fetch(url, {
            headers: COINGECKO_API_KEY ? { "x-cg-demo-api-key": COINGECKO_API_KEY } : {}
        });
        const data = await response.json();
        return data[coinId]?.usd;
    } catch (error) {
        console.error("❌ CoinGecko Error:", error.message);
        return null;
    }
}

// 2. ENDPOINT: Get Live Price (With Caching)
app.get('/market/price/:ticker', async (req, res) => {
    const ticker = req.params.ticker.toUpperCase();
    const now = Date.now();
    
    // Check Cache (Valid for 10 seconds)
    if (priceCache[ticker] && (now - priceCache[ticker].lastUpdated < 10000)) {
        return res.json({
            ticker,
            price: priceCache[ticker].value,
            source: "cache",
            timestamp: new Date().toISOString()
        });
    }

    // Fetch New Data
    const realPrice = await fetchRealPrice(ticker);
    if (realPrice) {
        priceCache[ticker].value = realPrice;
        priceCache[ticker].lastUpdated = now;
        // Keep a mini-history for new clients
        priceCache[ticker].history.push({ time: new Date().toLocaleTimeString(), price: realPrice });
        if (priceCache[ticker].history.length > 20) priceCache[ticker].history.shift();
    }

    res.json({
        ticker,
        price: priceCache[ticker]?.value || 0,
        source: "live",
        timestamp: new Date().toISOString()
    });
});

// 3. ENDPOINT: The "Alpha" Signal (Paid Data)
// For the demo, we simply simulate the alpha response:
app.get('/alpha/insight/:ticker', (req, res) => {
    // 402 Paywall Logic (Simulated for brevity in this step)
    res.status(402).json({
        error: "Payment Required",
        invoice: {
            amount: "0.1",
            currency: "USDC",
            to: SELLER_WALLET,
            chainId: 338
        }
    });
});

app.post('/alpha/insight/:ticker/payment', (req, res) => {
    // Payment Verification Logic
    // In a real demo, verify signature here. 
    // For now, we return the "Future Prediction" data.
    res.json({
        success: true,
        data: {
            sentiment: "bullish",
            recommended_action: "BUY",
            // SIMULATED FUTURE DATA FOR THE CHART
            prediction: [
                { time: "Now", price: priceCache['CRO'].value },
                { time: "+1m", price: priceCache['CRO'].value * 1.02 },
                { time: "+2m", price: priceCache['CRO'].value * 1.05 },
                { time: "+3m", price: priceCache['CRO'].value * 1.08 } // 8% gain predicted
            ]
        }
    });
});

// Health check
app.get('/health', (req, res) => {
    res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

app.listen(PORT, () => {
    console.log(`\n${'='.repeat(60)}`);
    console.log(`🚀 Data Server with Real Price Feed`);
    console.log(`${'='.repeat(60)}`);
    console.log(`\n📡 Server: http://localhost:${PORT}`);
    console.log(`\n📊 Market Endpoints:`);
    console.log(`   GET  /market/price/:ticker       - Get live price (CRO, VVS, USDC)`);
    console.log(`\n💰 Alpha Endpoints:`);
    console.log(`   GET  /alpha/insight/:ticker      - Premium insight (402 paywall)`);
    console.log(`   POST /alpha/insight/:ticker/payment - Submit payment proof`);
    console.log(`\n🏥 Health:`);
    console.log(`   GET  /health                     - Server health check`);
    console.log(`\n📌 Examples:`);
    console.log(`   curl http://localhost:${PORT}/market/price/CRO`);
    console.log(`   curl http://localhost:${PORT}/market/price/VVS`);
    console.log(`\n${'='.repeat(60)}\n`);
});
