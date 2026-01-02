# Analyst Node Server

Node.js + Express paywalled endpoint using **x402 protocol** with EIP-712 payment signatures to gate alpha insights for your agent.

## Setup

1) Install dependencies:

```bash
cd server
npm install
```

2) Configure environment:

```bash
cp .env.example .env
# Edit .env:
# - Set WALLET_ADDRESS (Cronos address to receive USDC)
# - Set USDC_CONTRACT (Cronos USDC token address)
# - Set CHAIN_ID (338 for testnet, 25 for mainnet)
# - Adjust PAYMENT_AMOUNT (base units, e.g., 100000 = 0.10 USDC)
```

3) Run the server:

```bash
npm start
```

The API listens on http://localhost:3050 by default.

## Endpoints

- `GET /health` — liveness check.
- `GET /alpha/insight/:ticker` — returns 402 with full x402 invoice including EIP-712 domain/types for TransferWithAuthorization when missing payment.
- `POST /alpha/insight/:ticker/payment` — accepts EIP-712 signature and typedData, verifies payment, and returns insight data.

## x402 Payment Flow (EIP-3009)

1. Client probes `GET /alpha/insight/CRO`.
2. Server replies `402 Payment Required` with `instruction` containing:
   - `token`, `recipient`, `amount` (base units)
   - `eip712Domain`, `eip712Types` for TransferWithAuthorization
   - `validAfter`, `validBefore` (unix timestamps)
3. Client builds EIP-712 typed data message with `from`, `to`, `value`, `validAfter`, `validBefore`, `nonce`.
4. Client signs the typed data with their wallet's private key.
5. Client POSTs to `/alpha/insight/CRO/payment` with JSON body:
   ```json
   {
     "signature": "0x...",
     "typedData": { "domain": {...}, "types": {...}, "message": {...} }
   }
   ```
6. Server verifies signature matches `from` address, validates amount/recipient/expiry, then returns protected data.

## Notes

- Replace `verifyPayment` with real on-chain settlement if you need guarantees that funds arrive before serving data.
- Use Cronos x402 Facilitator API to submit the signed authorization for on-chain execution and confirmation.
- Keep the price and currency in sync with your agent's `access_paid_api` tool configuration.
