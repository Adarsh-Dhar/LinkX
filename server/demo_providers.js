const express = require('express');
const app = express();

const TREASURY = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e";

const nodes = {
  "macro-news": { price: "0.15", category: "News", data: () => ({ value: 0.88, logic: "Bullish Fed comments detected." }) },
  "neural-oracle": { price: "0.45", category: "Sentiment", data: () => ({ value: 0.75, logic: "Social volume spike on Cronos." }) },
  "chain-watcher": { price: "0.65", category: "On-Chain", data: () => ({ value: 0.92, logic: "Whale accumulation at $2900." }) }
};

app.get('/api/node/:slug', (req, res) => {
  const node = nodes[req.params.slug];
  const paymentProof = req.headers['x-payment-proof'];

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

app.listen(4000, () => console.log("📡 Demo Node Providers online on port 4000"));
