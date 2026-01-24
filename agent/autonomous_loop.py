import time
import threading

from .data_consumer import fetch_node_data
from .trading_engine import TradingEngine
from .wallet_manager import get_daily_spend, can_spend

# ...existing code...



import asyncio
from .predictive_agent import PredictiveAgent

def run_autonomous_loop(agent, interval_sec=10):
    """
    Background thread that runs the predictive cycle.
    """
    print(f"[AlphaLoop] Starting background loop (Interval: {interval_sec}s)")
    # Wait for startup
    time.sleep(5)
    while True:
        try:
            # Check if trader is initialized
            if not hasattr(agent, 'trader') or agent.trader is None:
                print("[AlphaLoop] ⚠️ Agent trader not ready yet. Retrying...")
                time.sleep(5)
                continue

            print(f"[AlphaLoop] Starting unified cycle...")

            # Initialize PredictiveAgent with the Trader
            predictive_agent = PredictiveAgent(
                market_manager=agent.market,
                trading_engine=agent.trader,
                simulation_mode=False
            )

            # Run the async cycle
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(predictive_agent.run_cycle())
            loop.close()

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
