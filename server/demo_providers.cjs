const express = require('express');
const app = express();

const TREASURY = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e";

const nodes = {
  "macro-news": {
    price: "0.15",
    category: "News",
    data: () => ({
      value: 0.88,
      logic: "Bullish Fed comments detected. Rate hike pause likely.",
      headline: "Fed signals dovish stance after inflation cools.",
      source: "Reuters, Bloomberg"
    })
  },
  "neural-oracle": {
    price: "0.45",
    category: "Sentiment",
    data: () => ({
      value: 0.61,
      logic: "Social sentiment spike: #CRO trending. Early pump signals detected.",
      trending: ["#CRO", "#DeFi", "#BullRun"],
      score: 92
    })
  },
  "chain-watcher": {
    price: "0.65",
    category: "On-Chain",
    data: () => ({
      value: 0.97,
      logic: "Whale accumulation at $2900. Large wallet inflows detected.",
      whales: 3,
      inflowUSD: 1200000
    })
  }
};

app.get('/api/node/:slug', (req, res) => {
  const node = nodes[req.params.slug];
  // Accept both header variants for compatibility
  const paymentProof = req.headers['x-payment-proof'] || req.headers['x402-payment-proof'];

  if (!node) {
    return res.status(404).json({ error: "Node not found" });
  }

  if (!paymentProof) {
    return res.status(402)
      .header('X-Payment-Price', node.price)
      .header('X-Payment-Wallet', TREASURY)
      .json({ error: "Payment Required via x402" });
  }

  // Realistic randomized data for demo
  const result = node.data();
  console.log(`✅ Paid Access: ${req.params.slug} unlocked by ${paymentProof}`);
  res.json({ ...result, timestamp: Date.now() });
});

// Generic /data endpoint for compatibility with agent/curl tests
app.get('/data', (req, res) => {
  console.log('--- Incoming /data request ---');
  console.log('Headers:', req.headers);
  // Accept both header variants for compatibility
  const paymentProof = req.headers['x-payment-proof'] || req.headers['x402-payment-proof'];
  if (!paymentProof) {
    return res.status(402)
      .header('X-Payment-Price', '0.45')
      .header('X-Payment-Wallet', TREASURY)
      .json({ error: "Payment Required via x402" });
  }

  // Determine node from apiKey or nodeName (query or header)
  const apiKey = req.query.apiKey || req.headers['x-api-key'];
  const nodeName = req.query.nodeName || req.headers['x-node-name'];
  let nodeKey = null;
  if (apiKey === 'demo-macro-news' || nodeName === 'Macro News AI') nodeKey = 'macro-news';
  if (apiKey === 'demo-neural-oracle' || nodeName === 'Neural Oracle') nodeKey = 'neural-oracle';
  if (apiKey === 'demo-chain-watcher' || nodeName === 'On-Chain Watcher') nodeKey = 'chain-watcher';

  let result;
  if (nodeKey && nodes[nodeKey]) {
    result = nodes[nodeKey].data();
    result.category = nodes[nodeKey].category;
    result.node = nodeKey;
  } else {
    result = { value: null, logic: "Unknown node or apiKey." };
  }
  console.log(`✅ Paid Access: /data unlocked by ${paymentProof} for node ${nodeKey}`);
  res.json({ ...result, timestamp: Date.now() });
});

app.listen(4100, () => console.log("📡 Demo Node Providers online on port 4100"));
