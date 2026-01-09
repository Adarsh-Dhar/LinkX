import express from "express";
import cors from "cors";
import { ethers } from "ethers";
import "dotenv/config";
import fetch from "node-fetch";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// 1. LOAD CONFIGURATION FROM providers.json
const providersPath = path.join(__dirname, 'providers.json');
const providers = JSON.parse(fs.readFileSync(providersPath, 'utf8'));

// Check which provider identity to load (from Environment Variable)
// Default to 'default' if not specified
const PROVIDER_ID = process.env.PROVIDER_ID || 'default';
const CONFIG = providers[PROVIDER_ID];

if (!CONFIG) {
    console.error(`❌ Error: Provider ID '${PROVIDER_ID}' not found in providers.json`);
    process.exit(1);
}

const app = express();
const PORT = CONFIG.port;
const SELLER_WALLET = CONFIG.wallet || process.env.WALLET_ADDRESS;
const PRICE_COST = CONFIG.price;
const PROVIDER_NAME = CONFIG.name;
const PROVIDER_BIAS = CONFIG.bias;

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
    // 402 Paywall Logic with Dynamic Pricing
    res.status(402).json({
        error: "Payment Required",
        provider: PROVIDER_NAME,
        invoice: {
            amount: PRICE_COST,
            currency: "USDC",
            to: SELLER_WALLET,
            chainId: 338
        }
    });
});

app.post('/alpha/insight/:ticker/payment', (req, res) => {
    // Payment Verification Logic
    // In a real demo, verify signature here. 
    // For now, we return the "Future Prediction" data with bias-based direction.
    
    // Simulate Prediction logic based on Provider Bias
    const currentPrice = priceCache['CRO'].value;
    const direction = PROVIDER_BIAS === 'bullish' ? 1 : -1;
    const volatility = PRICE_COST > 0.5 ? 0.03 : 0.08; // Premium providers are more conservative
    
    res.json({
        success: true,
        data: {
            source: PROVIDER_NAME,
            sentiment: PROVIDER_BIAS,
            recommended_action: PROVIDER_BIAS === 'bullish' ? "BUY" : "SELL",
            // SIMULATED FUTURE DATA FOR THE CHART
            prediction: [
                { time: "Now", price: currentPrice },
                { time: "+1m", price: currentPrice * (1 + (volatility * 0.25 * direction)) },
                { time: "+2m", price: currentPrice * (1 + (volatility * 0.60 * direction)) },
                { time: "+3m", price: currentPrice * (1 + (volatility * 1.0 * direction)) }
            ]
        }
    });
});

// Health check
app.get('/health', (req, res) => {
    res.json({ 
        status: 'ok',
        provider: PROVIDER_ID,
        providerName: PROVIDER_NAME,
        timestamp: new Date().toISOString()
    });
});

app.listen(PORT, () => {
    console.log(`\n${'='.repeat(70)}`);
    console.log(`⚙️  PROVIDER IDENTITY LOADED: ${PROVIDER_ID.toUpperCase()}`);
    console.log(`${'='.repeat(70)}`);
    console.log(`\n🎯 Provider Configuration:`);
    console.log(`   Name:     ${PROVIDER_NAME}`);
    console.log(`   Bias:     ${PROVIDER_BIAS.toUpperCase()}`);
    console.log(`   Price:    ${PRICE_COST} USDC per signal`);
    console.log(`   Wallet:   ${SELLER_WALLET}`);
    console.log(`\n🚀 Data Server with Real Price Feed`);
    console.log(`${'='.repeat(70)}`);
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
    console.log(`\n${'='.repeat(70)}\n`);
});
