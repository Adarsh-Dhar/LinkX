/**
 * Alpha-Consumer Mock Server
 * Demonstrates HTTP 402 Payment Required protocol with x402
 * Simulates a premium API that requires payment
 */

const express = require('express');
const cors = require('cors');
const { ethers } = require('ethers');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3100;

// Middleware
app.use(cors());
app.use(express.json());

// Configuration from environment
const SELLER_WALLET = process.env.SELLER_WALLET || '0x0000000000000000000000000000000000000000';
const USDC_CONTRACT = process.env.USDC_CONTRACT || '0x0000000000000000000000000000000000000000';
const PAYMENT_AMOUNT = process.env.PAYMENT_AMOUNT || '1000000'; // 1 USDC
const CHAIN_ID = parseInt(process.env.CHAIN_ID || '338');

// Initialize Web3 provider
const provider = new ethers.JsonRpcProvider(
    process.env.CRONOS_RPC_URL || 'https://evm-t3.cronos.org'
);

// EIP-712 Domain for USDC
const EIP712_DOMAIN = {
    name: 'USD Coin',
    version: '2',
    chainId: CHAIN_ID,
    verifyingContract: USDC_CONTRACT
};

// EIP-712 Types for TransferWithAuthorization
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

/**
 * Verify EIP-712 signature
 */
function verifySignature(typedData, signature) {
    try {
        const domain = typedData.domain;
        const types = { TransferWithAuthorization: EIP712_TYPES.TransferWithAuthorization };
        const value = typedData.message;

        // Recover signer from signature
        const recoveredAddress = ethers.verifyTypedData(domain, types, value, signature);
        
        // Check if recovered address matches the 'from' address in the message
        const expectedFrom = typedData.message.from;
        
        console.log(`   Expected From: ${expectedFrom}`);
        console.log(`   Recovered:     ${recoveredAddress}`);
        
        return recoveredAddress.toLowerCase() === expectedFrom.toLowerCase();
    } catch (error) {
        console.error('   ❌ Signature verification error:', error.message);
        return false;
    }
}

/**
 * Validate payment message
 */
function validatePaymentMessage(message) {
    const now = Math.floor(Date.now() / 1000);
    
    // Check if payment is to the correct recipient
    if (message.to.toLowerCase() !== SELLER_WALLET.toLowerCase()) {
        return { valid: false, reason: 'Incorrect recipient' };
    }
    
    // Check if amount is correct
    if (message.value.toString() !== PAYMENT_AMOUNT) {
        return { valid: false, reason: `Incorrect amount. Expected ${PAYMENT_AMOUNT}, got ${message.value}` };
    }
    
    // Check if payment is still valid
    if (message.validBefore < now) {
        return { valid: false, reason: 'Payment authorization expired' };
    }
    
    if (message.validAfter > now) {
        return { valid: false, reason: 'Payment authorization not yet valid' };
    }
    
    return { valid: true };
}

// ============================================
// ROUTES
// ============================================

/**
 * Root endpoint - Server info
 */
app.get('/', (req, res) => {
    res.json({
        name: 'Alpha-Consumer Mock Server',
        version: '1.0.0',
        protocol: 'x402',
        endpoints: {
            '/buy-alpha': 'Premium trading data (requires payment)',
            '/health': 'Health check',
            '/info': 'Payment information'
        }
    });
});

/**
 * Health check endpoint
 */
app.get('/health', (req, res) => {
    res.json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        network: 'Cronos Testnet',
        chainId: CHAIN_ID
    });
});

/**
 * Payment info endpoint
 */
app.get('/info', (req, res) => {
    res.json({
        seller_wallet: SELLER_WALLET,
        usdc_contract: USDC_CONTRACT,
        payment_amount: PAYMENT_AMOUNT,
        chain_id: CHAIN_ID,
        amount_in_usdc: (parseInt(PAYMENT_AMOUNT) / 1_000_000).toFixed(2)
    });
});

/**
 * Premium endpoint - Requires payment
 * GET: Returns 402 with payment instructions
 * POST: Accepts payment and returns data
 */
app.get('/buy-alpha', (req, res) => {
    console.log('\n📥 Received request for /buy-alpha (GET)');
    console.log('   No payment detected - sending 402 Payment Required');
    
    // Return 402 with payment instructions
    res.status(402).json({
        error: 'Payment Required',
        message: 'This endpoint requires payment to access premium trading data',
        instruction: {
            protocol: 'x402',
            version: '1.0',
            network: 'cronos_testnet',
            chainId: CHAIN_ID,
            token: USDC_CONTRACT,
            amount: PAYMENT_AMOUNT,
            recipient: SELLER_WALLET,
            types: 'TransferWithAuthorization',
            eip712Domain: EIP712_DOMAIN,
            eip712Types: EIP712_TYPES
        }
    });
});

/**
 * POST endpoint to submit payment
 */
app.post('/buy-alpha', async (req, res) => {
    console.log('\n📥 Received payment submission to /buy-alpha (POST)');
    
    try {
        // Get signature from header or body
        const signature = req.headers['x-payment'] || req.body.signature;
        const typedData = req.body.typedData;
        
        if (!signature) {
            console.log('   ❌ No signature provided');
            return res.status(400).json({
                error: 'Missing signature',
                message: 'Payment signature required in X-Payment header or request body'
            });
        }
        
        if (!typedData) {
            console.log('   ❌ No typed data provided');
            return res.status(400).json({
                error: 'Missing typed data',
                message: 'EIP-712 typed data required in request body'
            });
        }
        
        console.log('   🔍 Verifying signature...');
        console.log(`   Signature: ${signature.substring(0, 20)}...`);
        
        // Verify signature
        const isValidSignature = verifySignature(typedData, signature);
        
        if (!isValidSignature) {
            console.log('   ❌ Invalid signature');
            return res.status(403).json({
                error: 'Invalid signature',
                message: 'Signature verification failed'
            });
        }
        
        console.log('   ✅ Signature valid!');
        
        // Validate payment message
        const validation = validatePaymentMessage(typedData.message);
        
        if (!validation.valid) {
            console.log(`   ❌ Invalid payment: ${validation.reason}`);
            return res.status(400).json({
                error: 'Invalid payment',
                message: validation.reason
            });
        }
        
        console.log('   ✅ Payment validated!');
        console.log('   💰 Payment accepted - delivering premium data');
        
        // In production, you would:
        // 1. Store the signature
        // 2. Submit to blockchain via facilitator
        // 3. Wait for confirmation
        // 4. Deliver the data
        
        // For demo, we immediately return the data
        const premiumData = {
            success: true,
            message: 'Payment accepted',
            data: {
                secret_alpha: 'VVS Finance whale accumulation detected at block #99283',
                confidence: 0.87,
                source: 'On-chain analysis',
                timestamp: new Date().toISOString(),
                recommendation: 'Monitor VVS/USDC pool for large swaps',
                additional_intel: {
                    wallet_address: '0x742d35Cc6634C0532925a3b844Bc454e4438f44e',
                    accumulated_amount: '125,000 VVS',
                    timeframe: 'Last 24 hours',
                    unusual_activity: true
                }
            },
            payment_details: {
                amount: PAYMENT_AMOUNT,
                token: 'USDC',
                from: typedData.message.from,
                to: SELLER_WALLET,
                nonce: typedData.message.nonce
            }
        };
        
        res.json(premiumData);
        
    } catch (error) {
        console.error('   ❌ Error processing payment:', error);
        res.status(500).json({
            error: 'Internal server error',
            message: error.message
        });
    }
});

/**
 * Example: Free endpoint (no payment required)
 */
app.get('/free-data', (req, res) => {
    console.log('\n📥 Received request for /free-data');
    console.log('   ✅ No payment required - delivering free data');
    
    res.json({
        message: 'This is free public data',
        data: {
            cro_price: 0.0842,
            market_cap: '2.1B',
            volume_24h: '45M',
            timestamp: new Date().toISOString()
        }
    });
});

/**
 * Optional: Submit to facilitator
 * (For production implementation)
 */
async function submitToFacilitator(signature, typedData) {
    const facilitatorUrl = process.env.FACILITATOR_URL;
    
    if (!facilitatorUrl) {
        console.log('   ⚠️  No facilitator URL configured - skipping blockchain submission');
        return { success: true, mock: true };
    }
    
    try {
        // This would submit to the actual x402 facilitator
        // which would handle the on-chain settlement
        console.log('   📤 Submitting to facilitator...');
        
        // Implementation would go here
        // const response = await fetch(facilitatorUrl, { ... });
        
        return { success: true };
    } catch (error) {
        console.error('   ❌ Facilitator submission failed:', error);
        return { success: false, error: error.message };
    }
}

// ============================================
// GLOBAL ERROR HANDLER (always return JSON)
// ============================================
app.use((err, req, res, next) => {
    console.error('❌ Express error:', err);
    res.status(500).json({
        error: 'Internal server error',
        message: err && err.message ? err.message : 'Unknown error'
    });
});

// ============================================
// START SERVER
// ============================================

app.listen(PORT, () => {
    console.log('╔═══════════════════════════════════════════════════════════╗');
    console.log('║                                                           ║');
    console.log('║       🚀 Alpha-Consumer Mock Server Running!              ║');
    console.log('║                                                           ║');
    console.log('╠═══════════════════════════════════════════════════════════╣');
    console.log(`║  Port:         ${PORT}                                       ║`);
    console.log(`║  Network:      Cronos Testnet (Chain ID: ${CHAIN_ID})           ║`);
    console.log(`║  Protocol:     x402 (HTTP 402 Payment Required)          ║`);
    console.log('║                                                           ║');
    console.log('║  Endpoints:                                               ║');
    console.log(`║    GET  http://localhost:${PORT}/buy-alpha               ║`);
    console.log(`║    POST http://localhost:${PORT}/buy-alpha               ║`);
    console.log(`║    GET  http://localhost:${PORT}/free-data               ║`);
    console.log(`║    GET  http://localhost:${PORT}/info                    ║`);
    console.log('║                                                           ║');
    console.log('║  Payment Details:                                         ║');
    console.log(`║    Seller:     ${SELLER_WALLET.substring(0, 15)}...        ║`);
    console.log(`║    Amount:     ${(parseInt(PAYMENT_AMOUNT) / 1_000_000).toFixed(2)} USDC                                     ║`);
    console.log('║                                                           ║');
    console.log('╚═══════════════════════════════════════════════════════════╝');
    console.log('\n💡 Tip: Run the agent in another terminal to test the payment flow');
    console.log('📝 Logs will appear below as requests are processed\n');
});

// Error handling
process.on('uncaughtException', (error) => {
    console.error('❌ Uncaught Exception:', error);
});

process.on('unhandledRejection', (error) => {
    console.error('❌ Unhandled Rejection:', error);
});