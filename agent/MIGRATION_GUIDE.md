# AI Agent SDK Migration Guide

## Overview

The Alpha-Consumer Agent has been migrated from using the raw Crypto.com CDP API to use the **Crypto.com AI Agent SDK**. This simplification removes the need for manual wallet management, blockchain interaction code, and direct RPC calls.

## Key Changes

### 1. **Removed CDP API Dependency**
- **Before**: Required `CDP_API_KEY` for Crypto.com Developer Platform
- **After**: Uses Crypto.com AI Agent SDK which handles blockchain interactions internally
- **Benefit**: SDK abstracts away low-level blockchain complexity

### 2. **Simplified Environment Variables**

**Before** (.env.example):
```
GEMINI_API_KEY=...
CHAIN_ID=338
CRONOS_RPC_URL=https://evm-t3.cronos.org
WALLET_PRIVATE_KEY=...
USDC_CONTRACT=...
CDP_API_KEY=...
```

**After** (.env.example):
```
GEMINI_API_KEY=...
WALLET_PRIVATE_KEY=...
CRYPTO_COM_API_KEY=...
```

**Why**: 
- The AI Agent SDK handles RPC endpoints automatically
- No need to manually specify CHAIN_ID (defaults to Cronos EVM)
- USDC contract address is managed by the SDK

### 3. **Updated Main Agent Class**

**Before**:
```python
from crypto_com_agent_client import Agent
from wallet_manager import WalletManager

# Manual wallet initialization
self.wallet = WalletManager(...)
agent = Agent.init(
    llm_config=self.llm_config,
    blockchain_config=self.blockchain_config
)
```

**After**:
```python
from crypto_com_agent_client import Agent, SQLitePlugin, tool

# SDK handles everything
custom_storage = SQLitePlugin(db_path="agent_state.db")

agent = Agent.init(
    llm_config=self.llm_config,
    blockchain_config=self.blockchain_config,
    plugins={
        "personality": personality,
        "instructions": instructions,
        "tools": [access_paid_api, check_market_conditions],
        "storage": custom_storage,
    },
)
```

**Benefits**:
- No separate `WalletManager` class needed
- Built-in storage with SQLitePlugin
- Personality and instructions integrated directly
- Cleaner initialization

### 4. **Simplified Tools**

**Before** (`tools.py`):
- Manual EIP-3009 message creation
- Manual wallet signing with `encode_typed_data`
- Direct Web3 interactions
- Complex signature generation logic

**After** (`tools.py`):
- HTTP 402 payment handling via tools decorator
- Crypto.com AI Agent SDK coordinates payment signing
- No manual EIP-712 or signature code
- Cleaner, more maintainable tool definitions

### 5. **Agent Interaction Method**

**Before**:
```python
response = self.agent.run(full_prompt)
```

**After**:
```python
response = self.agent.interact(user_input)
```

The `interact()` method is the standard interface for the Crypto.com AI Agent SDK.

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

This now includes:
- `cryptocom-agent-client>=1.3.6` (already includes Gemini support)
- `google-generativeai>=0.3.0` (Gemini API)
- `web3>=7.0.0` (blockchain utilities)
- `eth-account>=0.13.0` (wallet signing)

### 2. Get API Keys

1. **Gemini API Key**
   - Visit: https://makersuite.google.com/app/apikey
   - Create a new API key
   - Copy to `.env` as `GEMINI_API_KEY`

2. **Crypto.com Developer Platform API Key** (NEW)
   - Visit: https://developers.crypto.com/console
   - Sign up or log in
   - Create a new project/API key
   - Copy to `.env` as `CRYPTO_COM_API_KEY`
   - This replaces the old `CDP_API_KEY`

3. **Wallet Private Key**
   - Generate a new Ethereum wallet:
     ```python
     from eth_account import Account
     account = Account.create()
     print(account.key)  # This is your WALLET_PRIVATE_KEY
     ```
   - Copy to `.env` as `WALLET_PRIVATE_KEY`

### 3. Create .env File
```bash
cp .env.example .env
# Edit .env and fill in your API keys and wallet private key
```

### 4. Run the Agent
```bash
python main.py              # Interactive mode
python main.py autonomous   # Autonomous mode
```

## Migration Checklist

- [x] Remove CDP API dependency
- [x] Simplify environment variables
- [x] Update main.py to use Agent.init() with plugins
- [x] Simplify tools.py (remove manual signing)
- [x] Remove wallet_manager.py (handled by SDK)
- [x] Update requirements.txt
- [x] Update .env.example

## Breaking Changes

1. **Removed `WalletManager` class**: The AI Agent SDK handles wallet operations
2. **Removed manual blockchain config**: Use `CRYPTO_COM_API_KEY` instead of `CDP_API_KEY`
3. **Removed RPC URL requirement**: SDK manages RPC endpoints automatically
4. **Changed interaction method**: Use `agent.interact()` instead of `agent.run()`
5. **Removed `_check_wallet_balance()` method**: The SDK provides balance queries through tools

## Testing

To verify the migration:

```bash
# 1. Ensure all dependencies are installed
pip install -r requirements.txt

# 2. Test environment variables
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('CRYPTO_COM_API_KEY'))"

# 3. Run interactive agent
python main.py
```

## Benefits of the Migration

1. **Simplified Codebase**: Removed 100+ lines of manual blockchain code
2. **Better Abstraction**: SDK handles complex blockchain details
3. **Improved Maintainability**: Fewer dependencies and fewer potential issues
4. **Easier to Extend**: Built-in plugin system for storage and tools
5. **Production-Ready**: Uses official Crypto.com SDK instead of manual implementations

## Troubleshooting

### Error: "CRYPTO_COM_API_KEY not found"
- Run `cp .env.example .env` and fill in your API key from https://developers.crypto.com/console

### Error: "Failed to initialize agent"
- Ensure all environment variables are properly set
- Check that your API keys are valid
- Verify your wallet private key format (should start with 0x)

### Error: "Module not found: crypto_com_agent_client"
- Run `pip install -r requirements.txt`

## References

- [Crypto.com AI Agent SDK Docs](https://ai-agent-sdk-docs.crypto.com/)
- [Quick Start Guide](https://ai-agent-sdk-docs.crypto.com/crypto.com-ai-agent-sdk/quick-start-guide-simulation-entry-point)
- [Crypto.com Developer Platform](https://developers.crypto.com/)
