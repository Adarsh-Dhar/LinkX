import express from "express";
import cors from "cors";
import categories from "./market_categories.js";

const BASE_PORT = 4000;
const REGISTRY = [];

categories.forEach((cat, index) => {
    [0, 1].forEach((compIndex) => {
        const competitors = [
            { suffix: "A", type: "Premium", price: "0.2" },
            { suffix: "B", type: "Budget", price: "0.05" }
        ];
        const comp = competitors[compIndex];
        const port = BASE_PORT + (index * 2) + compIndex;
        const nodeId = `${cat.id}_${comp.suffix}`;
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

const directoryApp = express();
directoryApp.use(cors());
directoryApp.get('/directory', (req, res) => res.json(REGISTRY));
directoryApp.listen(3999, () => {
    console.log(`\n📘 Registry/Discovery Node running on :3999`);
    console.log(`✨ Total Autonomous Nodes: ${REGISTRY.length}`);
    console.log(`🏷️  Categories: ${categories.length}`);
    console.log(`📊 Competitors per Category: 2 (Premium/Budget)\n`);
});
