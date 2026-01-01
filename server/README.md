# Analyst Node Server

Node.js + Express paywalled endpoint that uses an x402-style payment handshake to gate alpha insights for your agent.

## Setup

1) Install dependencies:

```bash
cd server
npm install
```

2) Configure environment:

```bash
cp .env.example .env
# set WALLET_ADDRESS (Cronos USDC recipient); PORT defaults to 3050
```

3) Run the server:

```bash
npm start
```

The API listens on http://localhost:3050 by default.

## Endpoints

- `GET /health` — liveness check.
- `GET /alpha/insight/:ticker` — protected endpoint; returns 402 with invoice when missing `x-payment-token`, otherwise returns insight JSON.

## Payment Flow

1. Client probes `GET /alpha/insight/CRO`.
2. Server replies `402 Payment Required` with `payment_context` (network `cronos`, currency `USDC`, amount `0.10`).
3. Client pays and retries with header `x-payment-token: <tx_hash>`.
4. Server verifies the token (replace the mock in `verifyOnChainPayment` with a Cronos on-chain check) and returns data.

## Notes

- Replace `verifyOnChainPayment` with real Cronos RPC/indexer verification to confirm funds arrived at `WALLET_ADDRESS`.
- Keep the price and currency in sync with your agent's `Paid API Access` tool configuration.
