import time
import threading
from data_consumer import fetch_node_data
from trading_engine import TradingEngine
from wallet_manager import get_daily_spend, can_spend

# ...existing code...

def run_autonomous_loop(agent, interval_sec=300):
    """
    Unified autonomous loop: ensure data access, fetch/pay for data, run prediction, and execute trades.
    Runs in a background thread.
    """
    import asyncio
    from predictive_agent import PredictiveAgent
    predictive_agent = PredictiveAgent(simulation_mode=False)
    while True:
        print("[AlphaLoop] Starting unified cycle...")
        # 1. Ensure required data nodes are active (buy if needed)
        market_state = agent.market.get_market_state()
        if not market_state:
            print("[AlphaLoop] Market offline. Retrying...")
            time.sleep(interval_sec)
            continue
        for node in market_state.get('missing', []):
            if can_spend(node['price']):
                buy_log = agent.market.buy_node(node['name'])
                print(buy_log)
        # 2. Fetch/pay for fresh data (x402 logic is in fetch_node_data)
        # 3. Pass data to PredictiveAgent (Brain) to get a decision
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(predictive_agent.run_cycle())
        except Exception as e:
            print(f"[AlphaLoop] Error in PredictiveAgent cycle: {e}")
        # 4. (Inside PredictiveAgent) Execute the trade using TradingEngine
        print("[AlphaLoop] Cycle complete. Sleeping...")
        time.sleep(interval_sec)

def start_background_loop(agent):
    t = threading.Thread(target=run_autonomous_loop, args=(agent,), daemon=True)
    t.start()

# ...existing code...
