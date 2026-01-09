# 🚀 Config-Driven Multi-Provider Alpha Server

This server has been refactored to support **multiple "Hedge Fund Personalities"** without code duplication. Each provider can have different pricing, bias, and wallet addresses.

## 📋 Architecture

```
server/
├── providers.json        ← Configuration for all providers
├── index.js             ← Dynamic server that reads providers.json
├── start_provider.sh    ← Helper script to launch specific providers
└── package.json
```

## ⚙️ Configuration File: `providers.json`

The `providers.json` file defines all available provider identities:

```json
{
  "default": {
    "name": "Standard Node",
    "port": 3050,
    "wallet": "0xYourWalletAddressHere",
    "price": "0.1",
    "bias": "bullish"
  },
  "premium": {
    "name": "Quant Elite (Expensive)",
    "port": 3051,
    "wallet": "0xYourWalletAddressHere",
    "price": "1.0",
    "bias": "bullish"
  },
  "scam": {
    "name": "Degen Calls (Cheap/Risky)",
    "port": 3052,
    "wallet": "0xYourWalletAddressHere",
    "price": "0.01",
    "bias": "bearish"
  }
}
```

### Configuration Fields

| Field | Description | Example |
|-------|-------------|---------|
| `name` | Display name of the provider | "Standard Node" |
| `port` | Port the server runs on | 3050 |
| `wallet` | Ethereum address to receive payments | "0x1234..." |
| `price` | Cost per signal in USDC | "0.1" |
| `bias` | Market sentiment (bullish/bearish) | "bullish" |

## 🎯 How It Works

### 1. **Load Configuration**
When the server starts, it reads `providers.json` and loads the specified provider configuration:

```javascript
const PROVIDER_ID = process.env.PROVIDER_ID || 'default';
const CONFIG = providers[PROVIDER_ID];
```

### 2. **Dynamic Pricing**
The `/alpha/insight/:ticker` endpoint returns the price from the config:

```json
{
  "error": "Payment Required",
  "provider": "Quant Elite (Expensive)",
  "invoice": {
    "amount": "1.0",          ← From config
    "currency": "USDC",
    "to": "0xYourWallet",     ← From config
    "chainId": 338
  }
}
```

### 3. **Bias-Based Predictions**
The `/alpha/insight/:ticker/payment` endpoint adjusts predictions based on provider bias:

- **Bullish**: Predicts price increases
- **Bearish**: Predicts price decreases

```javascript
const direction = PROVIDER_BIAS === 'bullish' ? 1 : -1;
// If bearish, multiplies predictions by -1
```

## 🚀 Running Multiple Providers

### Option 1: Using the Helper Script

**Terminal 1 - Standard Provider:**
```bash
cd server
./start_provider.sh
# or
./start_provider.sh default
```

**Terminal 2 - Premium Provider:**
```bash
cd server
./start_provider.sh premium
```

**Terminal 3 - Degen Provider:**
```bash
cd server
./start_provider.sh scam
```

### Option 2: Direct Node Command

**Terminal 1:**
```bash
cd server
node index.js
# Runs 'default' provider on port 3050
```

**Terminal 2:**
```bash
cd server
export PROVIDER_ID=premium
node index.js
# Runs 'premium' provider on port 3051
```

**Terminal 3:**
```bash
cd server
export PROVIDER_ID=scam
node index.js
# Runs 'scam' provider on port 3052
```

## 📊 Testing Multiple Providers

Once all three servers are running, you can query them independently:

```bash
# Get price from Standard Node
curl http://localhost:3050/market/price/CRO

# Get price from Premium Node
curl http://localhost:3051/market/price/CRO

# Get alpha from Degen Node
curl http://localhost:3052/alpha/insight/CRO
```

## 🔧 Adding a New Provider

To add a new provider, simply add an entry to `providers.json`:

```json
{
  "conservative": {
    "name": "Ultra Safe ETF Bot",
    "port": 3053,
    "wallet": "0xNewWalletHere",
    "price": "5.0",
    "bias": "bullish"
  }
}
```

Then start it:
```bash
./start_provider.sh conservative
```

## 📡 Server Startup Output

When you start a provider, you'll see:

```
══════════════════════════════════════════════
⚙️  PROVIDER IDENTITY LOADED: DEFAULT
══════════════════════════════════════════════

🎯 Provider Configuration:
   Name:     Standard Node
   Bias:     BULLISH
   Price:    0.1 USDC per signal
   Wallet:   0xYourWalletAddressHere

🚀 Data Server with Real Price Feed
══════════════════════════════════════════════

📡 Server: http://localhost:3050
...
```

## 🎨 Demo Scenario: The Agent Chooses

This architecture enables powerful demos:

1. **Frontend Agent** starts and sees 3 available providers (at different ports)
2. **Agent compares pricing**: 
   - Premium = 1.0 USDC (conservative predictions)
   - Standard = 0.1 USDC (balanced predictions)
   - Degen = 0.01 USDC (aggressive predictions)
3. **Agent chooses based on risk tolerance**
4. **Agent queries the chosen provider** and pays for insights

## 🔐 Production Considerations

Before deploying to production:

1. ✅ Validate wallet addresses in `providers.json`
2. ✅ Use environment variables for sensitive data:
   ```bash
   export PROVIDER_ID=premium
   export COINGECKO_API_KEY=your_key
   node index.js
   ```
3. ✅ Implement real payment verification (signature validation)
4. ✅ Use a real database instead of in-memory cache
5. ✅ Add authentication/rate limiting per provider

## 📝 Environment Variables

```bash
# Load a specific provider
export PROVIDER_ID=premium

# Optional: Override wallet address
export WALLET_ADDRESS=0xYourWallet

# Optional: CoinGecko API key
export COINGECKO_API_KEY=your_api_key

# Start server
node index.js
```

## 🎯 Benefits of This Architecture

| Benefit | Details |
|---------|---------|
| **Scalability** | Add new providers with just 5 lines of JSON |
| **No Code Duplication** | One codebase supports unlimited providers |
| **Easy Demos** | Show multiple personalities in different terminal windows |
| **Dynamic Pricing** | Each provider has independent pricing logic |
| **Wallet Management** | Different wallets can receive payments |
| **Testing** | Test agent behavior with different provider configurations |

---

**Made with ❤️ for Cronos Chain** 🚀
