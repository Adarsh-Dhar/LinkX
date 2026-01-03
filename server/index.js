require('dotenv').config();
const express = require('express');
const cors = require('cors');
const { ethers } = require('ethers');
const crypto = require('crypto');

const app = express();
const PORT = process.env.PORT || 3050;

app.use(cors());
app.use(express.json());

// Payment and network configuration
const PAYMENT_NETWORK = process.env.PAYMENT_NETWORK || 'cronos_testnet';
const CHAIN_ID = Number(process.env.CHAIN_ID || '338');
const USDC_CONTRACT = process.env.USDC_CONTRACT || '0x0000000000000000000000000000000000000000';
const PAYMENT_DECIMALS = Number(process.env.PAYMENT_DECIMALS || '6');
const PAYMENT_AMOUNT_RAW = process.env.PAYMENT_AMOUNT || '100000'; // 0.10 USDC with 6 decimals
const PAYMENT_SYMBOL = process.env.PAYMENT_SYMBOL || 'USDC';
const PAYMENT_TTL_SECONDS = Number(process.env.PAYMENT_TTL_SECONDS || '900');
const SELLER_WALLET = (process.env.WALLET_ADDRESS || '').toLowerCase();
const CRONOS_RPC_URL = process.env.CRONOS_RPC_URL || 'https://evm-t3.cronos.org';

// Initialize blockchain provider for on-chain verification
const provider = new ethers.JsonRpcProvider(CRONOS_RPC_URL);

// Mocked alpha data store; replace with your own source as needed
const MARKET_INSIGHTS = {
  CRO: {
    sentiment: 'bullish',
    whale_activity: 'high_inflow',
    support_level: 0.145,
    resistance_level: 0.162,
    recommended_action: 'ACCUMULATE',
    signal: 'BUY',
    confidence: 0.85,
    price_target: 0.18,
    stop_loss: 0.14
  },
  VVS: {
    sentiment: 'bullish',
    whale_activity: 'moderate_inflow',
    support_level: 0.000003,
    resistance_level: 0.000005,
    recommended_action: 'BUY',
    signal: 'BUY',
    confidence: 0.78,
    amount_usdc: 5,
    reason: 'Strong accumulation pattern detected. Volume surge on VVS Finance.'
  },
  USDC: {
    sentiment: 'stable',
    whale_activity: 'none',
    support_level: 0.999,
    resistance_level: 1.001,
    recommended_action: 'HOLD',
    signal: 'HOLD',
    confidence: 1.0
  }
};

// EIP-712 domain and types for USDC TransferWithAuthorization (EIP-3009)
const EIP712_DOMAIN = {
  name: 'Bridged USDC (Stargate)',
  version: '1',
  chainId: CHAIN_ID,
  verifyingContract: USDC_CONTRACT
};

const EIP712_TYPES = {
  TransferWithAuthorization: [
    { name: 'from', type: 'address' },
    { name: 'to', type: 'address' },
    { name: 'value', type: 'uint256' },
    { name: 'validAfter', type: 'uint256' },
    { name: 'validBefore', type: 'uint256' },
    { name: 'nonce', type: 'bytes32' }
  ]
};

function buildInvoice() {
  const now = Math.floor(Date.now() / 1000);
  const invoiceId = `inv_${Date.now()}`;

  return {
    error: 'Payment Required',
    message: 'x402 payment needed for premium insight',
    instruction: {
      protocol: 'x402',
      version: '1.0',
      network: PAYMENT_NETWORK,
      chainId: CHAIN_ID,
      token: USDC_CONTRACT,
      tokenSymbol: PAYMENT_SYMBOL,
      amount: PAYMENT_AMOUNT_RAW,
      amountReadable: Number(PAYMENT_AMOUNT_RAW) / 10 ** PAYMENT_DECIMALS,
      currency: PAYMENT_SYMBOL,
      recipient: SELLER_WALLET,
      ttlSeconds: PAYMENT_TTL_SECONDS,
      invoice_id: invoiceId,
      types: 'TransferWithAuthorization',
      eip712Domain: EIP712_DOMAIN,
      eip712Types: EIP712_TYPES,
      validAfter: 0,
      validBefore: now + PAYMENT_TTL_SECONDS
    }
  };
}

function validateTypedDataShape(typedData = {}) {
  if (!typedData.domain || !typedData.types || !typedData.message) return false;
  if (!typedData.types.TransferWithAuthorization) return false;

  const msg = typedData.message;
  const hasField = (field) => msg[field] !== undefined && msg[field] !== null;

  return Boolean(
    typedData.domain.verifyingContract &&
      hasField('to') &&
      hasField('value') &&
      hasField('validBefore') &&
      hasField('validAfter') &&
      hasField('nonce')
  );
}

function validatePaymentMessage(message) {
  const now = Math.floor(Date.now() / 1000);

  if (!SELLER_WALLET) {
    return { valid: false, reason: 'Seller wallet (WALLET_ADDRESS) not set' };
  }

  if (message.to.toLowerCase() !== SELLER_WALLET) {
    return { valid: false, reason: 'Incorrect recipient' };
  }

  if (message.value.toString() !== PAYMENT_AMOUNT_RAW.toString()) {
    return { valid: false, reason: 'Incorrect amount' };
  }

  if (message.validBefore < now) {
    return { valid: false, reason: 'Payment authorization expired' };
  }

  if (message.validAfter > now) {
    return { valid: false, reason: 'Payment authorization not yet valid' };
  }

  return { valid: true };
}

async function verifyPayment(signature, typedData) {
  try {
    if (!validateTypedDataShape(typedData)) {
      // Debug logging to inspect malformed payloads
      console.warn('Typed data failed shape validation', JSON.stringify({ typedData, signature }));
      return { valid: false, reason: 'Invalid typed data shape' };
    }

    // Ensure the domain matches what we expect for this service
    if (
      typedData.domain.chainId !== CHAIN_ID ||
      typedData.domain.verifyingContract.toLowerCase() !== USDC_CONTRACT.toLowerCase()
    ) {
      return { valid: false, reason: 'Typed data domain mismatch' };
    }

    const recovered = ethers.verifyTypedData(
      typedData.domain,
      { TransferWithAuthorization: EIP712_TYPES.TransferWithAuthorization },
      typedData.message,
      signature
    );

    const validation = validatePaymentMessage(typedData.message);
    if (!validation.valid) {
      return { valid: false, reason: validation.reason };
    }

    // OPTIONAL: Verify on-chain that transferWithAuthorization was executed
    // This is best-effort and will not block if RPC is unavailable
    try {
      const usdc = new ethers.Contract(USDC_CONTRACT, [
        'function authorizationState(address authorizer, bytes32 nonce) view returns (bool)'
      ], provider);

      const nonceBytes32 = typedData.message.nonce;
      const authorizer = typedData.message.from;

      const consumed = await usdc.authorizationState(authorizer, nonceBytes32);

      if (!consumed) {
        return {
          valid: false,
          reason: 'Authorization not found on-chain (transferWithAuthorization not executed)'
        };
      }
    } catch (chainErr) {
      // If chain check fails, we still allow if signature + payload are valid
      console.warn('On-chain verification skipped:', chainErr.message);
    }

    return { valid: true, payer: recovered };
  } catch (err) {
    return { valid: false, reason: err.message };
  }
}

app.get('/health', (_req, res) => {
  res.json({ ok: true, timestamp: new Date().toISOString() });
});

// Trading signals endpoint - returns all available trading signals
app.get('/trading/signals', (req, res) => {
  const signals = Object.entries(MARKET_INSIGHTS)
    .filter(([_, insight]) => insight.signal && insight.signal !== 'HOLD')
    .map(([ticker, insight]) => ({
      ticker,
      signal: insight.signal,
      confidence: insight.confidence,
      sentiment: insight.sentiment,
      recommended_action: insight.recommended_action,
      amount_usdc: insight.amount_usdc,
      reason: insight.reason
    }));
  
  res.json({
    timestamp: new Date().toISOString(),
    count: signals.length,
    signals
  });
});

// Get specific ticker trading recommendation
app.get('/trading/recommendation/:ticker', (req, res) => {
  const ticker = req.params.ticker.toUpperCase();
  const insight = MARKET_INSIGHTS[ticker];
  
  if (!insight) {
    return res.status(404).json({ error: 'Ticker not found' });
  }
  
  res.json({
    ticker,
    signal: insight.signal || 'HOLD',
    confidence: insight.confidence || 0.5,
    sentiment: insight.sentiment,
    recommended_action: insight.recommended_action,
    price_target: insight.price_target,
    stop_loss: insight.stop_loss,
    amount_usdc: insight.amount_usdc,
    reason: insight.reason,
    timestamp: new Date().toISOString()
  });
});

// BUY alpha endpoint - Free endpoint that returns actionable BUY signals
app.get('/buy-alpha', (req, res) => {
  const buySignals = Object.entries(MARKET_INSIGHTS)
    .filter(([_, insight]) => insight.signal === 'BUY')
    .map(([ticker, insight]) => ({
      ticker,
      action: 'BUY',
      amount_usdc: insight.amount_usdc || 5,
      confidence: insight.confidence,
      reason: insight.reason || `Strong ${insight.sentiment} signal detected`,
      timestamp: new Date().toISOString()
    }));
  
  if (buySignals.length === 0) {
    return res.json({
      message: 'No BUY signals at this time. Market is in HOLD mode.',
      timestamp: new Date().toISOString()
    });
  }
  
  res.json({
    signals: buySignals,
    instruction: 'Execute trades using the agent\'s execute_vvs_swap tool',
    timestamp: new Date().toISOString()
  });
});

// Portfolio value endpoint - calculates total portfolio value
app.get('/portfolio/value', async (req, res) => {
  const address = req.query.address;
  
  if (!address) {
    return res.status(400).json({ error: 'Missing wallet address parameter' });
  }
  
  try {
    // In production, fetch real balances from blockchain
    // For demo, return mock portfolio data
    const mockPortfolio = {
      address: address.toLowerCase(),
      balances: {
        CRO: { amount: 1000, value_usd: 85 },
        USDC: { amount: 500, value_usd: 500 },
        VVS: { amount: 50000000, value_usd: 180 }
      },
      total_value_usd: 765,
      last_updated: new Date().toISOString()
    };
    
    res.json(mockPortfolio);
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch portfolio value', details: err.message });
  }
});

// Trade execution status tracking (store recent trades)
const recentTrades = [];

app.post('/portfolio/trade', (req, res) => {
  const { ticker, action, amount, tx_hash, status } = req.body;
  
  if (!ticker || !action) {
    return res.status(400).json({ error: 'Missing required fields: ticker, action' });
  }
  
  const trade = {
    id: `trade_${Date.now()}`,
    ticker,
    action,
    amount,
    tx_hash,
    status: status || 'pending',
    timestamp: new Date().toISOString()
  };
  
  recentTrades.unshift(trade);
  
  // Keep only last 100 trades
  if (recentTrades.length > 100) {
    recentTrades.pop();
  }
  
  res.json({ success: true, trade });
});

app.get('/portfolio/trades', (req, res) => {
  const limit = parseInt(req.query.limit) || 10;
  res.json({
    trades: recentTrades.slice(0, limit),
    total: recentTrades.length,
    timestamp: new Date().toISOString()
  });
});

// Invoice endpoint: returns 402 with x402 instruction
app.get('/alpha/insight/:ticker', (req, res) => {
  const ticker = req.params.ticker.toUpperCase();
  if (!MARKET_INSIGHTS[ticker]) {
    return res.status(404).json({ error: 'Ticker not analyzed by this node.' });
  }

  return res.status(402).json(buildInvoice());
});

// Payment endpoint: expects EIP-712 signature + typedData
app.post('/alpha/insight/:ticker/payment', async (req, res) => {
  const ticker = req.params.ticker.toUpperCase();
  const insight = MARKET_INSIGHTS[ticker];

  if (!insight) {
    return res.status(404).json({ error: 'Ticker not analyzed by this node.' });
  }

  const signature = req.headers['x-payment'] || req.body.signature;
  const typedData = req.body.typedData;

  if (!signature) {
    return res.status(400).json({ error: 'Missing signature' });
  }

  if (!typedData) {
    return res.status(400).json({ error: 'Missing typedData' });
  }

  const result = await verifyPayment(signature, typedData);

  if (!result.valid) {
    return res.status(403).json({ error: 'Invalid payment', reason: result.reason });
  }

  return res.json({
    success: true,
    payer: result.payer,
    timestamp: new Date().toISOString(),
    data: insight
  });
});

app.listen(PORT, () => {
  console.log(`\n${'='.repeat(60)}`);
  console.log(`🚀 Analyst Node + Trading Server Running`);
  console.log(`${'='.repeat(60)}`);
  console.log(`\n📡 Server: http://localhost:${PORT}`);
  console.log(`\n📊 Trading Endpoints:`);
  console.log(`   GET  /trading/signals              - All active trading signals`);
  console.log(`   GET  /trading/recommendation/:ticker - Get ticker recommendation`);
  console.log(`   GET  /buy-alpha                   - Free BUY signals (no payment)`);
  console.log(`\n💼 Portfolio Endpoints:`);
  console.log(`   GET  /portfolio/value?address=... - Get portfolio value`);
  console.log(`   GET  /portfolio/trades?limit=10   - Recent trade history`);
  console.log(`   POST /portfolio/trade             - Record new trade`);
  console.log(`\n💰 Payment Endpoints (x402 Protocol):`);
  console.log(`   GET  /alpha/insight/:ticker       - Premium insight (402 paywall)`);
  console.log(`   POST /alpha/insight/:ticker/payment - Submit payment proof`);
  console.log(`\n🏥 Health:`);
  console.log(`   GET  /health                      - Server health check`);
  console.log(`\n${'='.repeat(60)}\n`);
});
