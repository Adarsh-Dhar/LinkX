import express from "express";
import cors from "cors";
import "dotenv/config";
import categories from "./market_categories.js";

const BASE_PORT = 4000;
const SELLER_WALLET = process.env.WALLET_ADDRESS || "0xYourWallet";

const args = process.argv.slice(2);
if (args.length < 2) {
    console.error("Usage: node provider.js <categoryIndex> <competitorIndex>");
    process.exit(1);
}
const categoryIndex = parseInt(args[0], 10);
const competitorIndex = parseInt(args[1], 10);
const cat = categories[categoryIndex];
const competitors = [
    { suffix: "A", type: "Premium", price: "0.2", reliability: 0.99 },
    { suffix: "B", type: "Budget",  price: "0.05", reliability: 0.85 }
];
const comp = competitors[competitorIndex];
const app = express();
const port = BASE_PORT + (categoryIndex * 2) + competitorIndex;
const nodeId = `${cat.id}_${comp.suffix}`;

app.use(cors());
app.use(express.json());

app.get('/data', (req, res) => {
    res.status(402).json({
        error: "Payment Required",
        provider: `${cat.name} Node ${comp.suffix}`,
        tier: comp.type,
        invoice: {
            amount: comp.price,
            currency: "USDC",
            to: SELLER_WALLET,
            chainId: 338,
            service_id: nodeId
        }
    });
});

app.post('/data/payment', (req, res) => {
    const data = { ...cat.template };
    // Add noise to all numeric fields except 'rank'
    Object.keys(data).forEach(key => {
        if (typeof data[key] === 'number' && key !== 'rank') {
            data[key] = data[key] * (1 + (Math.random() * 0.15 - 0.075));
        }
    });
    // Always include a 'value' field for agent compatibility
    if (typeof data.value !== 'number') {
        // Find the first numeric field to use as 'value'
        const firstNumeric = Object.keys(data).find(k => typeof data[k] === 'number');
        if (firstNumeric) {
            data.value = data[firstNumeric];
        } else {
            data.value = 0;
        }
    }
    res.json({
        success: true,
        provider: nodeId,
        data: data,
        timestamp: new Date().toISOString()
    });
});

app.listen(port, () => {
    console.log(`🟢 ${cat.name} [${comp.type}] running on :${port}`);
});
