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
  console.log(`Analyst Node running on port ${PORT}`);
  console.log(`Invoice:  http://localhost:${PORT}/alpha/insight/:ticker`);
  console.log(`Payment:  http://localhost:${PORT}/alpha/insight/:ticker/payment`);
});
