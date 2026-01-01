require('dotenv').config();
const express = require('express');
const cors = require('cors');

const app = express();
const PORT = process.env.PORT || 3050;

app.use(cors());
app.use(express.json());

// Mocked alpha data store; replace with your own source as needed
const MARKET_INSIGHTS = {
  CRO: {
    sentiment: 'bullish',
    whale_activity: 'high_inflow',
    support_level: 0.145,
    resistance_level: 0.162,
    recommended_action: 'ACCUMULATE'
  },
  VVS: {
    sentiment: 'neutral',
    whale_activity: 'stagnant',
    support_level: 0.000003,
    resistance_level: 0.000004,
    recommended_action: 'HOLD'
  }
};

// x402-style middleware to enforce payment before data access
const x402Middleware = async (req, res, next) => {
  const paymentProof = req.headers['x-payment-token'];

  // If no proof, request payment with invoice metadata
  if (!paymentProof) {
    return res.status(402).json({
      error: 'Payment Required',
      detail: 'Alpha insights cost $0.10 per request.',
      payment_context: {
        network: 'cronos',
        recipient: process.env.WALLET_ADDRESS,
        amount: '0.10',
        currency: 'USDC',
        invoice_id: `inv_${Date.now()}`
      }
    });
  }

  // Verify payment; replace with chain lookup (Cronos) in production
  const isValidPayment = await verifyOnChainPayment(paymentProof);

  if (!isValidPayment) {
    return res.status(403).json({ error: 'Invalid or expired payment token.' });
  }

  return next();
};

async function verifyOnChainPayment(token) {
  // TODO: Replace with actual on-chain verification against Cronos RPC.
  // This placeholder only checks shape of a tx hash.
  return typeof token === 'string' && token.startsWith('0x');
}

app.get('/health', (_req, res) => {
  res.json({ ok: true, timestamp: new Date().toISOString() });
});

app.get('/alpha/insight/:ticker', x402Middleware, (req, res) => {
  const ticker = req.params.ticker.toUpperCase();
  const data = MARKET_INSIGHTS[ticker];

  if (!data) {
    return res.status(404).json({ error: 'Ticker not analyzed by this node.' });
  }

  return res.json({
    success: true,
    timestamp: new Date().toISOString(),
    data
  });
});

app.listen(PORT, () => {
  console.log(`Analyst Node running on port ${PORT}`);
  console.log(`Endpoint: http://localhost:${PORT}/alpha/insight/:ticker`);
});
