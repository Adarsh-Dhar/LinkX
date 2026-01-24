
import os
import sys
import threading
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from .wallet_manager import WalletManager
from .trading_engine import TradingEngine
from .autonomous_loop import run_autonomous_loop

class MarketManager:
    def get_market_state(self):
        import requests
        try:
            resp = requests.get("http://localhost:3000/api/market/nodes", timeout=2)
            if resp.status_code == 200:
                return {"nodes": resp.json()}
        except:
            pass
        return {"nodes": []}

class IntelligentAgent:
    def __init__(self):
        load_dotenv()
        print("🤖 [Main] Initializing Intelligent Agent...")
        # 1. Wallet
        private_key = os.getenv("WALLET_PRIVATE_KEY")
        rpc_url = os.getenv("CRONOS_RPC_URL", os.getenv("RPC_URL", "https://evm-t3.cronos.org"))
        self.wallet = WalletManager(private_key, rpc_url)
        print(f"   ✅ Wallet: {self.wallet.address}")
        # 2. Market
        self.market = MarketManager()
        # 3. Trader (CRITICAL STEP)
        self.trader = TradingEngine(self.wallet)
        print(f"   ✅ TradingEngine: Ready")

    def start(self):
        print("🚀 [Main] Agent Manual Start")
        loop_thread = threading.Thread(target=run_autonomous_loop, args=(self,), daemon=True)
        loop_thread.start()
        return self

if __name__ == "__main__":
    agent = IntelligentAgent()
    agent.start()
    import time
    while True: time.sleep(1)