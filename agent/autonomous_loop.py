import time
import threading

from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path(__file__).parent.parent / '.env')

from agent.data_consumer import fetch_node_data
from agent.trading_engine import TradingEngine
from agent.wallet_manager import get_daily_spend, can_spend

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
        # Ensure agent.pipeline exists, else create it
        pipeline = getattr(agent, 'pipeline', None)
        if pipeline is None:
            from agent.data_pipeline import DataPipeline
            pipeline = DataPipeline(agent.market)
            agent.pipeline = pipeline
        wallet = getattr(agent, 'wallet', None)
        node_connector = getattr(agent, 'node_connector', None)
        # Use pipeline as market_analyst (not agent.market)
        market_analyst = pipeline
        trading_engine = getattr(agent, 'trader', None)
        strategist = getattr(agent, 'strategist', None)
        if strategist is None:
            from agent.tools import AlphaStrategist
            strategist = AlphaStrategist()
            agent.strategist = strategist
        agent.current_predictive_instance = PredictiveAgent(wallet, node_connector, market_analyst, trading_engine, strategist)

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

            print(f"[AlphaLoop] Running predictive agent cycle...")
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
