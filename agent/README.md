# Alpha Agent Docker Kit

Use this guide to package and run the agent in Docker so users can plug in their own keys and start trading without installing Python locally.

## 🚀 How to Run Your Own Alpha Agent

1. **Download the Agent Kit**
   ```bash
git clone https://github.com/your-repo/alpha-consumer.git
cd alpha-consumer/agent
   ```

2. **Configure Your Wallet**
   Create a `.env` file in `agent/` and add your credentials:
   ```bash
# agent/.env
WALLET_PRIVATE_KEY=0xYourPrivateKeyHere...
OPENROUTER_API_KEY=sk-or-v1-...
   ```

3. **Start the Agent (Docker)**
   ```bash
docker-compose up --build
   ```

You should see logs similar to:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
✅ Agent initialized successfully
```

The agent listens on port `8000`. Point your frontend at `http://localhost:8000` (or keep using your existing server URL for trading signals).

## Testing Locally

1. Stop any locally running Python agent (`Ctrl+C`).
2. Ensure your trading signal server is running.
3. From `agent/`, run `docker-compose up --build` and watch for the Uvicorn startup log.
4. Open your frontend (e.g., `http://localhost:3600`) and try "Buy alpha data" to confirm end-to-end flow.

## Files Added

- `Dockerfile`: Builds the agent image.
- `docker-compose.yml`: One-command startup for the agent with environment overrides.
