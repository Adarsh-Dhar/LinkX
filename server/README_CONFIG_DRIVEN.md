# 📚 Config-Driven Multi-Provider Architecture - Documentation Index

## 🎯 Quick Navigation

### 🚀 Getting Started (Start Here!)
- **[MULTI_PROVIDER_GUIDE.md](MULTI_PROVIDER_GUIDE.md)** - Complete overview and quick start guide
- **[QUICK_START_MULTI_PROVIDER.sh](QUICK_START_MULTI_PROVIDER.sh)** - Copy-paste commands to start all providers

### 📊 Understanding the Architecture
- **[CONFIG_DRIVEN_README.md](CONFIG_DRIVEN_README.md)** - Full technical documentation
- **[BEFORE_AFTER_COMPARISON.md](BEFORE_AFTER_COMPARISON.md)** - Why this architecture is better
- **[CONFIG_DRIVEN_COMPLETE.md](CONFIG_DRIVEN_COMPLETE.md)** - Implementation summary

### 🤖 Demonstrations
- **[demo_agent_provider_selection.sh](demo_agent_provider_selection.sh)** - Shows how an agent chooses between providers

### 🛠️ Core Files
- **[providers.json](providers.json)** - Configuration database for all providers
- **[index.js](index.js)** - Refactored server (loads from config)
- **[start_provider.sh](start_provider.sh)** - Helper script to launch providers

---

## 📖 Reading Order (Recommended)

### For Non-Technical Understanding
1. [MULTI_PROVIDER_GUIDE.md](MULTI_PROVIDER_GUIDE.md) - Overview section
2. [BEFORE_AFTER_COMPARISON.md](BEFORE_AFTER_COMPARISON.md) - Problem/Solution section

### For Quick Implementation
1. [QUICK_START_MULTI_PROVIDER.sh](QUICK_START_MULTI_PROVIDER.sh)
2. [demo_agent_provider_selection.sh](demo_agent_provider_selection.sh)

### For Technical Deep Dive
1. [CONFIG_DRIVEN_README.md](CONFIG_DRIVEN_README.md)
2. [BEFORE_AFTER_COMPARISON.md](BEFORE_AFTER_COMPARISON.md) - Technical sections
3. Review [providers.json](providers.json)
4. Review [index.js](index.js)

---

## 🎯 Key Concepts

### What is "Config-Driven"?
Instead of hardcoding values like `price = "0.1"` in code, store all configuration in `providers.json` and load it at startup. This allows one codebase to serve unlimited "personalities."

### The Three Providers Included

| Name | Port | Price | Bias | Use Case |
|------|------|-------|------|----------|
| **default** | 3050 | 0.1 USDC | Bullish | Standard signals |
| **premium** | 3051 | 1.0 USDC | Bullish | Conservative/expensive |
| **scam** | 3052 | 0.01 USDC | Bearish | Aggressive/cheap |

### How to Add Your Own Provider
Just add an entry to `providers.json`:
```json
{
  "your_provider": {
    "name": "Your Provider Name",
    "port": 3053,
    "wallet": "0xYourWallet",
    "price": "0.5",
    "bias": "bullish"
  }
}
```

Then start it:
```bash
PROVIDER_ID=your_provider node index.js
```

---

## 🚀 Running Everything

### Start All Three Providers

**Terminal 1:**
```bash
cd server && node index.js
```

**Terminal 2:**
```bash
cd server && PROVIDER_ID=premium node index.js
```

**Terminal 3:**
```bash
cd server && PROVIDER_ID=scam node index.js
```

### Test One Provider
```bash
curl http://localhost:3050/health
curl http://localhost:3050/market/price/CRO
curl http://localhost:3050/alpha/insight/CRO
```

### Run the Demo
```bash
./demo_agent_provider_selection.sh
```

---

## 📊 File Sizes

```
  473B  providers.json                ← All configuration
  6.2K  index.js                       ← Entire server
  8.7K  MULTI_PROVIDER_GUIDE.md        ← Complete guide
  8.2K  BEFORE_AFTER_COMPARISON.md    ← Why this is better
  6.2K  CONFIG_DRIVEN_README.md        ← Technical details
  5.7K  CONFIG_DRIVEN_COMPLETE.md     ← Implementation summary
  5.2K  demo_agent_provider_selection.sh ← Agent demo
  2.4K  QUICK_START_MULTI_PROVIDER.sh ← Quick reference
  1.7K  start_provider.sh              ← Launcher script
```

---

## ✨ Key Benefits

✅ **One Codebase** - Serve unlimited providers  
✅ **No Duplication** - Add providers in JSON  
✅ **Easy Demo** - Run multiple ports simultaneously  
✅ **Production Ready** - Deploy different brands on different servers  
✅ **Scalable** - Add 100th provider as easily as 2nd  
✅ **Maintainable** - Fix bugs once, benefits all providers  

---

## 🎯 Common Tasks

### "I want to change the premium price"
Edit `providers.json`, change `"price": "1.0"` to your new price, restart server.

### "I want to add a bearish premium provider"
Add to `providers.json`:
```json
{
  "premium_bear": {
    "name": "Premium Bearish",
    "port": 3053,
    "wallet": "0xWallet",
    "price": "1.0",
    "bias": "bearish"
  }
}
```

### "I want a different wallet per provider"
Each provider already has its own `wallet` field in `providers.json`!

### "I want to test this with my agent"
1. Start all three providers
2. Have agent query different ports
3. Compare 402 responses to see pricing
4. Agent chooses one and pays

---

## 🔍 Understanding the Server Response

When you query `/alpha/insight/CRO`, you get a 402 response:

```json
{
  "error": "Payment Required",
  "provider": "Standard Node",
  "invoice": {
    "amount": "0.1",
    "currency": "USDC",
    "to": "0xYourWallet",
    "chainId": 338
  }
}
```

**All these values come from `providers.json`!**
- `provider` → `config.name`
- `amount` → `config.price`
- `to` → `config.wallet`

When the agent pays and calls `/payment`, it gets predictions based on:
- `config.bias` (bullish or bearish)
- `config.price` (expensive providers are more conservative)

---

## 💡 Pro Tips

### Tip 1: Run Multiple Providers in One Terminal
```bash
for provider in default premium scam; do
  PROVIDER_ID=$provider node index.js &
done
```

### Tip 2: Test All Providers at Once
```bash
for port in 3050 3051 3052; do
  echo "Testing port $port:"
  curl http://localhost:$port/health
done
```

### Tip 3: Customize for Your Use Case
Edit `providers.json` to match your exact needs:
- Different prices
- Different biases
- Different wallets
- Different names

### Tip 4: Production Deployment
Each provider gets its own server/docker container:
```bash
# Server 1
PROVIDER_ID=default WALLET_ADDRESS=0xWallet1 node index.js

# Server 2
PROVIDER_ID=premium WALLET_ADDRESS=0xWallet2 node index.js
```

---

## 🆘 Troubleshooting

### "Port already in use"
Different provider trying to use same port. Check `providers.json` ports are unique, or kill existing process:
```bash
lsof -i :3050
kill -9 <PID>
```

### "Provider ID not found"
Typo in PROVIDER_ID or not in `providers.json`. Check spelling:
```bash
grep "\"default\"" providers.json  # Verify it exists
```

### "Server not responding"
Make sure to start server in correct directory:
```bash
cd server
node index.js
```

---

## 📚 Next Steps

1. ✅ Read [MULTI_PROVIDER_GUIDE.md](MULTI_PROVIDER_GUIDE.md)
2. ✅ Start all three providers
3. ✅ Run the demo: `./demo_agent_provider_selection.sh`
4. ✅ Query different providers and compare responses
5. ✅ Add your own custom provider to `providers.json`
6. ✅ Integrate with your agent

---

## 🎉 You're All Set!

You now have a **production-ready, config-driven multi-provider architecture** that can scale to hundreds of providers without code duplication.

**This is enterprise-grade architecture.** Use it proudly! 🚀

---

*Last Updated: January 9, 2026*  
*Made with ❤️ for Cronos Chain*
