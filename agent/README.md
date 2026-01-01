# Alpha-Consumer Agent 🤖

An autonomous AI agent powered by Google Gemini that automatically handles HTTP 402 Payment Required transactions using EIP-3009 on Cronos Testnet.

## 🌟 Features

- **AI-Powered Decision Making**: Uses Google Gemini 1.5 Flash for intelligent responses
- **Automatic Payment Handling**: Detects HTTP 402 errors and negotiates payments
- **EIP-3009 Support**: Signs payment authorizations using gasless transfers
- **Market Analysis**: Evaluates market conditions before making purchases
- **Interactive & Autonomous Modes**: Chat with the agent or let it run autonomously
- **Mock Payment Server**: Includes a Node.js server demonstrating the x402 protocol

## 📋 Prerequisites

- **Python 3.9+** (tested with Python 3.12)
- **Node.js 18+** (tested with Node.js 24)
- **npm** (comes with Node.js)

## 🚀 Quick Start

### 1. Run the Setup Script

```bash
./quickstart.sh
```

This will:
- Check prerequisites
- Create Python virtual environment
- Install all Python dependencies
- Install all Node.js dependencies
- Create `.env` file from template

### 2. Configure Environment

Edit the `.env` file with your credentials:

```bash
# Get Gemini API key from: https://makersuite.google.com/app/apikey
GEMINI_API_KEY=your_api_key_here

# Generate a wallet (see below)
WALLET_PRIVATE_KEY=0x...

# Server configuration
SELLER_WALLET=0x...  # Different address to receive payments
USDC_CONTRACT=0x...  # Testnet USDC address
```

### 3. Generate a Wallet

```bash
source venv/bin/activate
python wallet_manager.py
```

This will output:
- Wallet address
- Private key (add to `.env`)

**Important**: 
- Fund your address with TCRO from: https://cronos.org/faucet
- Get devUSDC from hackathon resources or deploy your own

### 4. Start the System

**Terminal 1 - Start the Mock Server:**
```bash
./start_server.sh
```

**Terminal 2 - Start the Agent:**
```bash
./start_agent.sh
```

## 📖 Usage

### Interactive Mode

```bash
./start_agent.sh
```

Example commands:
```
🧑 You: Find me some premium trading alpha

🧑 You: Check if CRO price justifies buying premium data

🧑 You: Access the alpha endpoint and pay if necessary

🧑 You: balance

🧑 You: market

🧑 You: exit
```

### Autonomous Mode

```bash
./start_agent.sh autonomous
```

The agent will automatically:
- Check market conditions every 5 minutes
- Access premium endpoints if conditions are favorable
- Handle payments automatically

## 🏗️ Project Structure

```
agent/
├── main.py                # Main agent entry point
├── tools.py               # Payment tools & EIP-3009 signing
├── wallet_manager.py      # Wallet operations
├── server.js              # Mock HTTP 402 server
├── requirements.txt       # Python dependencies
├── package.json           # Node.js dependencies
├── .env                   # Configuration (create from .env.example)
├── .env.example           # Environment template
├── addresses.json         # Contract addresses
├── usdc_abi.json          # USDC contract ABI
├── start_agent.sh         # Start agent script
├── start_server.sh        # Start server script
└── quickstart.sh          # One-command setup
```

## 🔧 Manual Installation

If the quickstart script doesn't work, follow these steps:

### Python Setup

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Node.js Setup

```bash
npm install
```

### Configuration

```bash
cp .env.example .env
# Edit .env with your credentials
```

## 🛠️ Key Components

### Main Agent (main.py)

- Initializes Gemini LLM
- Configures blockchain connection
- Manages wallet
- Handles user interactions

### Payment Tools (tools.py)

- `access_paid_api()`: Handles HTTP 402 workflow
- `create_eip3009_message()`: Creates payment authorization
- `sign_eip3009_message()`: Signs with wallet
- `check_market_conditions()`: Fetches CRO price

### Wallet Manager (wallet_manager.py)

- Balance checks (TCRO, USDC)
- ERC20 token operations
- Message signing
- Wallet generation

### Mock Server (server.js)

- Demonstrates x402 protocol
- Returns 402 on GET requests
- Verifies payments on POST
- Delivers premium data

## 🌐 API Endpoints

### Mock Server (`http://localhost:3000`)

- `GET /` - Server info
- `GET /health` - Health check
- `GET /info` - Payment details
- `GET /buy-alpha` - Returns 402 Payment Required
- `POST /buy-alpha` - Submit payment and get data
- `GET /free-data` - Free endpoint (no payment)

## 🔐 Security Notes

- **Never commit `.env` file** to version control
- **Keep private keys secure** - use test wallets only
- **Verify contract addresses** on block explorer
- **Test with small amounts** first
- **Use testnet only** for development

## 🐛 Troubleshooting

### "Module not found: cryptocom_agent_client"

```bash
source venv/bin/activate
pip install cryptocom-agent-client
```

### "Failed to connect to RPC"

Check your `CRONOS_RPC_URL` in `.env`:
```
CRONOS_RPC_URL=https://evm-t3.cronos.org
```

### "Low TCRO balance"

Get testnet funds: https://cronos.org/faucet

### "USDC contract not configured"

Deploy or get a testnet USDC address with EIP-3009 support.

### "Payment rejected"

Ensure:
- Sufficient USDC balance
- Correct SELLER_WALLET address
- Valid payment signature

## 📚 Resources

- **Cronos Docs**: https://docs.cronos.org
- **Cronos Faucet**: https://cronos.org/faucet
- **Cronos Explorer**: https://explorer.cronos.org/testnet
- **Gemini API**: https://makersuite.google.com/app/apikey
- **EIP-3009 Spec**: https://eips.ethereum.org/EIPS/eip-3009

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

MIT License - See LICENSE file for details

## 🎯 Use Cases

- **Autonomous Trading Bots**: Pay for premium market data automatically
- **Content Monetization**: Access paywalled APIs programmatically
- **Data Marketplace**: Agent-to-agent commerce
- **Research Tools**: Automatically purchase research reports
- **API Gateways**: Micropayment-enabled API access

## 🔄 Development Workflow

1. **Edit Code**: Make changes to Python or Node files
2. **Restart Services**: Ctrl+C and re-run start scripts
3. **Test**: Use interactive mode to test features
4. **Monitor**: Check terminal logs for errors
5. **Iterate**: Refine and improve

## 📊 Monitoring

### Check Balances

```bash
source venv/bin/activate
python wallet_manager.py
```

### View Server Logs

Server logs show:
- Incoming requests
- Payment verification
- Signature validation
- Data delivery

### View Agent Logs

Agent logs show:
- LLM responses
- Tool calls
- Payment decisions
- Transaction status

---

**Built with ❤️ for the Cronos Hackathon**

For questions or issues, please check the documentation or open an issue on GitHub.
