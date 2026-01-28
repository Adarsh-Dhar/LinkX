import time
import threading

from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path(__file__).parent.parent / '.env')

from agent.data_consumer import fetch_node_data
from agent.trading_engine import TradingEngine
from agent.wallet_manager import get_daily_spend, can_spend

# ...existing code...



import asyncio
from agent.predictive_agent import PredictiveAgent

def run_autonomous_loop(agent, interval_sec=10):

    """
    Background thread that runs the predictive cycle with persistent PredictiveAgent instance.
    """
    print(f"[AlphaLoop] Starting background loop (Interval: {interval_sec}s)")
    # Wait for startup
    time.sleep(5)

    # --- Persistent PredictiveAgent instance ---
    if not hasattr(agent, 'current_predictive_instance') or agent.current_predictive_instance is None:
        agent.current_predictive_instance = PredictiveAgent(
            market_manager=agent.market,
            trading_engine=agent.trader,
            simulation_mode=False
        )

    predictive_instance = agent.current_predictive_instance

    # Create a single asyncio event loop for the thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    while True:
        try:
            # Check if trader is initialized
            if not hasattr(agent, 'trader') or agent.trader is None:
                print("[AlphaLoop] ⚠️ Agent trader not ready yet. Retrying...")
                time.sleep(5)
                continue

            print(f"[AlphaLoop] Checking state: Paused={predictive_instance.paused}")
            loop.run_until_complete(predictive_instance.run_cycle())
            print(f"[AlphaLoop] Cycle complete. Sleeping...")

        except Exception as e:
            print(f"[AlphaLoop] ❌ Error in cycle: {e}")
            import traceback
            traceback.print_exc()

        time.sleep(interval_sec)

def start_background_loop(agent):
    t = threading.Thread(target=run_autonomous_loop, args=(agent,), daemon=True)
    t.start()

# ...existing code...
