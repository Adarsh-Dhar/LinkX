const express = require('express');

// Constants for the demo
const TREASURY_WALLET = "0xFe5e03799Fe833D93e950d22406F9aD901Ff3Bb9";
const ASSET_TICKER = "WETH/USDC";

/**
 * Common middleware to handle x402 handshakes
 * Returns 402 if X-Payment-Proof header is missing
 */
const x402Middleware = (price) => (req, res, next) => {
    const paymentProof = req.headers['x-payment-proof'];

    if (!paymentProof) {
        // Example x402 challenge data (should be dynamic in production)
        const challenge = {
            protocol: "x402",
            price: price,
            currency: "0xA0b86991c6218b36c1d19d4a2e9eb0ce3606eb48", // USDC mainnet (example)
            chainId: 1, // Ethereum mainnet (example)
            recipient: TREASURY_WALLET,
            description: `Access to ${ASSET_TICKER} insight`,
            requirements: {
                type: "EIP-3009",
                minAmount: price,
                token: "0xA0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
                recipient: TREASURY_WALLET,
                chainId: 1
            },
            eip712: {
                domain: {
                    name: "USDC",
                    version: "2",
                    chainId: 1,
                    verifyingContract: "0xA0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
                },
                types: {
                    TransferWithAuthorization: [
                        { name: "from", type: "address" },
                        { name: "to", type: "address" },
                        { name: "value", type: "uint256" },
                        { name: "validAfter", type: "uint256" },
                        { name: "validBefore", type: "uint256" },
                        { name: "nonce", type: "bytes32" }
                    ]
                },
                message: {
                    from: "<user_wallet>", // to be filled by client
                    to: TREASURY_WALLET,
                    value: Math.floor(price * 1e6), // USDC has 6 decimals
                    validAfter: Math.floor(Date.now() / 1000),
                    validBefore: Math.floor(Date.now() / 1000) + 600, // 10 min window
                    nonce: "0x" + Math.random().toString(16).slice(2, 34).padEnd(64, '0')
                }
            }
        };
        console.log(`[x402] Request blocked: Payment Required (${price} USDC)`);
        return res.status(402)
            .header('X-Payment-Price', price)
            .header('X-Payment-Wallet', TREASURY_WALLET)
            .json(challenge);
    }

    console.log(`[x402] Access Granted: Proof ${paymentProof.substring(0,10)}...`);
    next();
};

// --- NODE 1: Market Microstructure (Port 4001) ---
const node1 = express();
node1.get('/api/microstructure', x402Middleware(0.25), (req, res) => {
    res.json({
        node: "Market Microstructure & Execution",
        timestamp: Date.now(),
        data: {
            order_book_depth: { bids: 450000, asks: 120000 }, // Bullish depth
            trade_velocity: "85 ticks/sec",
            vwap: 2942.50,
            iceberg_detected: false,
            latency_ms: 5,
            quality_score: 98
        }
    });
});

// --- NODE 2: Alternative Intelligence (Port 4002) ---
const node2 = express();
node2.get('/api/sentiment', x402Middleware(0.45), (req, res) => {
    res.json({
        node: "Alternative Intelligence & Sentiment",
        timestamp: Date.now(),
        data: {
            social_sentiment: 0.82, // Highly Bullish
            social_velocity_change: "+15%",
            satellite_retail_occupancy: "88%",
            web_traffic_index: 1.4,
            quality_score: 85,
            asset_coverage: [ASSET_TICKER]
        }
    });
});

// --- NODE 3: Supply Chain & Global Macro (Port 4003) ---
const node3 = express();
node3.get('/api/macro', x402Middleware(0.65), (req, res) => {
    res.json({
        node: "Supply Chain & Global Macro",
        timestamp: Date.now(),
        data: {
            port_congestion_index: 0.12, // Low congestion (good for supply)
            vessel_count_transit: 1420,
            energy_grid_stability: "Normal",
            economic_indicators: {
                cpi_expectation: "2.1%",
                central_bank_bias: "Hawkish"
            },
            quality_score: 92
        }
    });
});


// --- x402 /settle endpoint (for demo, on node1 only) ---
const { ethers } = require("ethers");
node1.use(express.json());
node1.post('/api/settle', async (req, res) => {
    try {
        const { typedData, signature } = req.body;
        if (!typedData || !signature) {
            return res.status(400).json({ error: "Missing typedData or signature" });
        }
        const { domain, types, message } = typedData;
        // Remove EIP712Domain from types if present (ethers v6 expects it separate)
        const { EIP712Domain, ...restTypes } = types;
        // Recover signer
        let recovered;
        try {
            recovered = ethers.verifyTypedData(domain, restTypes, message, signature);
        } catch (e) {
            return res.status(403).json({ error: "Invalid signature", details: e.message });
        }
        // On-chain settlement check (EIP-3009 transferWithAuthorization)
        if (recovered && recovered.toLowerCase() === message.from.toLowerCase()) {
            // Connect to Ethereum (mainnet or testnet as per chainId)
            const provider = ethers.getDefaultProvider(domain.chainId);
            // USDC ABI fragment for TransferWithAuthorization event
            const usdcAbi = [
                "event TransferWithAuthorization(address indexed from, address indexed to, uint256 value, uint256 validAfter, uint256 validBefore, bytes32 indexed nonce)"
            ];
            const usdc = new ethers.Contract(domain.verifyingContract, usdcAbi, provider);
            // Search for TransferWithAuthorization event from 'from' to 'to' with value, nonce
            const filter = usdc.filters.TransferWithAuthorization(
                message.from,
                message.to,
                null, // value (not indexed)
                null, // validAfter (not indexed)
                null, // validBefore (not indexed)
                message.nonce
            );
            const events = await usdc.queryFilter(filter, -10000); // last ~10k blocks
            // Find event with correct value
            const found = events.find(e => e.args && e.args.value.eq(message.value));
            if (found) {
                return res.status(200).json({ success: true, address: recovered, txHash: found.transactionHash });
            } else {
                return res.status(402).json({ error: "No on-chain settlement found for this authorization (EIP-3009)" });
            }
        } else {
            return res.status(403).json({ error: "Signature does not match sender" });
        }
    } catch (err) {
        return res.status(500).json({ error: "Internal error", details: err.message });
    }
});

// Start all three servers
node1.listen(4001, () => console.log("🚀 Node 1: Microstructure online on :4001"));
node2.listen(4002, () => console.log("🚀 Node 2: Sentiment online on :4002"));
node3.listen(4003, () => console.log("🚀 Node 3: Global Macro online on :4003"));