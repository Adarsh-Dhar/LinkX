import express from "express";
import cors from "cors";
import "dotenv/config";
import categories from "./market_categories.js";

// --- CONFIGURATION ---
const BASE_PORT = 4000;
const SELLER_WALLET = process.env.WALLET_ADDRESS || "0xYourWallet";

// We create a registry to help the agent find these 48 ports
const REGISTRY = [];

// --- LAUNCH LOOP ---
categories.forEach((cat, index) => {
    // We launch 2 Competitors for each category
    // Competitor A: "Premium" (High Price, High Data)
    // Competitor B: "Budget" (Low Price, Basic Data)
    const competitors = [
        { suffix: "A", type: "Premium", price: "0.2", reliability: 0.99 },
        { suffix: "B", type: "Budget",  price: "0.05", reliability: 0.85 }
    ];

    competitors.forEach((comp, i) => {
        const app = express();
        const port = BASE_PORT + (index * 2) + i; // Unique port for every node
        const nodeId = `${cat.id}_${comp.suffix}`;

        app.use(cors());
        app.use(express.json());

        // 1. DATA ENDPOINT (PAYWALLED)
        app.get('/data', (req, res) => {
            // Paywall Simulation
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

        // 2. PAYMENT VERIFICATION (SIMULATED)
        app.post('/data/payment', (req, res) => {
            // In a real hackathon demo, you verify signature here.
            // We simulate generating "Fresh" data based on the template
            const data = { ...cat.template };
            
            // Add some randomness to make A and B different
            if (typeof data.value === 'number') {
                data.value = data.value * (1 + (Math.random() * 0.1 - 0.05));
            }
            
            // Add slight variations to numeric values
            Object.keys(data).forEach(key => {
                if (typeof data[key] === 'number' && key !== 'rank') {
                    data[key] = data[key] * (1 + (Math.random() * 0.15 - 0.075));
                }
            });
            
            res.json({
                success: true,
                provider: nodeId,
                data: data,
                timestamp: new Date().toISOString()
            });
        });

        // Start Listener
        app.listen(port, () => {
            console.log(`🟢 ${cat.name} [${comp.type}] running on :${port}`);
        });

        // Add to Registry for the Agent
        REGISTRY.push({
            id: nodeId,
            category: cat.id,
            name: `${cat.name} (${comp.type})`,
            port: port,
            url: `http://localhost:${port}/data`,
            price: parseFloat(comp.price),
            tier: comp.type
        });
    });
});

// --- DISCOVERY SERVER (Port 3999) ---
// The Agent hits this to get the "Phone Book" of 48 servers
const directoryApp = express();
directoryApp.use(cors());
directoryApp.get('/directory', (req, res) => res.json(REGISTRY));
directoryApp.listen(3999, () => {
    console.log(`\n📘 Registry/Discovery Node running on :3999`);
    console.log(`✨ Total Autonomous Nodes: ${REGISTRY.length}`);
    console.log(`🏷️  Categories: ${categories.length}`);
    console.log(`📊 Competitors per Category: 2 (Premium/Budget)\n`);
});
