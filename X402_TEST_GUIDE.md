# x402 Integration Test Guide

## Prerequisites

1. **Server environment** ([.env](server/.env)):
   - `WALLET_ADDRESS` — your Cronos address to receive USDC
   - `USDC_CONTRACT` — Cronos USDC token address
   - `CHAIN_ID` — 338 (testnet) or 25 (mainnet)
   - `PAYMENT_AMOUNT` — e.g., 100000 (0.10 USDC with 6 decimals)

2. **Agent environment** ([agent/.env](agent/.env)):
   - `WALLET_PRIVATE_KEY` — agent wallet private key (funds for payment)
   - `GEMINI_API_KEY` — Google Gemini API key
   - `CRYPTO_COM_API_KEY` — Crypto.com Developer Platform key

## Test Flow

### 1. Start the paywalled server

```bash
cd server
./start_server.sh
```

Expected output:
```
Analyst Node running on port 3050
Invoice:  http://localhost:3050/alpha/insight/:ticker
Payment:  http://localhost:3050/alpha/insight/:ticker/payment
```

### 2. Manual test (optional)

Probe the invoice endpoint:
```bash
curl http://localhost:3050/alpha/insight/CRO
```

You should receive a **402 Payment Required** response with full x402 instruction including `eip712Domain`, `eip712Types`, `token`, `recipient`, `amount`, `validAfter`, `validBefore`.

### 3. Start the agent

```bash
cd agent
./start_agent.sh
```

### 4. Trigger payment from agent

In the agent prompt:
```
Access http://localhost:3050/alpha/insight/CRO
```

Expected agent behavior:
1. **GET** → receives 402 invoice
2. Extracts payment instruction
3. Signs EIP-712 `TransferWithAuthorization` message
4. **POST** to `/alpha/insight/CRO/payment` with signature + typedData
5. Server verifies signature, returns protected data

### 5. Verify logs

**Server log** should show:
- Invoice request (GET)
- Payment submission (POST)
- Signature verification steps
- Data delivery

**Agent log** should show:
- 402 detected
- Payment details parsed
- Signature generated
- Payment accepted
- Data received

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `Missing signature` | Agent not POSTing to `/payment` endpoint; check `access_paid_api` tool logic |
| `Invalid payment` / `Incorrect recipient` | `WALLET_ADDRESS` mismatch between server `.env` and payment message `to` field |
| `Incorrect amount` | `PAYMENT_AMOUNT` mismatch; ensure both use same base units |
| `Payment authorization expired` | System clock skew or `validBefore` too short; increase `PAYMENT_TTL_SECONDS` |
| `WALLET_PRIVATE_KEY not set` | Agent `.env` missing private key; ensure agent can sign |

## Next Steps

- **On-chain settlement**: Integrate Cronos x402 Facilitator to submit signed authorization and confirm funds arrive before serving data.
- **Facilitator URL**: Add `FACILITATOR_URL` to server config and POST the signature to it.
- **Receipt verification**: Accept facilitator-issued receipts as payment proof instead of just validating the signature.
- **Multi-ticker pricing**: Support dynamic pricing per ticker or data type.
