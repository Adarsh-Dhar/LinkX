// shared_logic.js
// Shared utilities and x402 middleware for demo microservices

/**
 * Treasury wallet and asset ticker constants
 */
const TREASURY_WALLET = "0xFe5e03799Fe833D93e950d22406F9aD901Ff3Bb9";
const ASSET_TICKER = "WETH/USDC";

/**
 * Generate a random number between min and max, with optional decimals
 */
const getRandom = (min, max, decimals = 0) => {
    const val = Math.random() * (max - min) + min;
    return decimals === 0 ? Math.floor(val) : parseFloat(val.toFixed(decimals));
};

/**
 * x402 payment middleware for Express
 * Returns 402 with challenge if X-Payment-Proof header is missing
 */
const x402Middleware = (price) => (req, res, next) => {
    const paymentProof = req.headers['x-payment-proof'];
    if (!paymentProof) {
        const challenge = {
            protocol: "x402",
            price: price,
            currency: "0xA0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
            chainId: 1,
            recipient: TREASURY_WALLET,
            description: `Access to ${ASSET_TICKER} insight`,
            message: {
                from: "<user_wallet>",
                to: TREASURY_WALLET,
                value: Math.floor(price * 1e6),
                nonce: "0x" + Math.random().toString(16).slice(2, 34).padEnd(64, '0')
            }
        };
        return res.status(402).header('X-Payment-Price', price).json(challenge);
    }
    next();
};

module.exports = { x402Middleware, getRandom, ASSET_TICKER };
