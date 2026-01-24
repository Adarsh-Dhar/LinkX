import asyncio
import numpy as np
from datetime import datetime

try:
    from .data_pipeline import DataPipeline
except ImportError:
    from agent.data_pipeline import DataPipeline

class PredictiveAgent:
    def __init__(self, market_manager, trading_engine, simulation_mode=True):
        self.pipeline = DataPipeline(market_manager)
        self.trading_engine = trading_engine

    async def run_cycle(self):
        print("\n" + "─"*60)
        print(f"🤖 EXPERT TRADER (ALPHA-CONSUMER) - {datetime.now().strftime('%H:%M:%S')}")

        # ---------------------------------------------------------
        # PHASE 1: MARKET STRUCTURE ANALYSIS (The "Eyes")
        # ---------------------------------------------------------
        prices = self.pipeline.fetch_chart_history()
        
        if len(prices) < 20:
            print("   ⏳ [Market] Insufficient liquidity/data. Waiting for candle close...")
            return

        current_price = prices[-1]
        
        # Calculate Advanced Metrics
        # 1. Short Trend (Last 10 mins)
        short_trend_pct = ((current_price - prices[-10]) / prices[-10]) * 100
        # 2. Medium Trend (Last 50 mins)
        medium_trend_pct = ((current_price - prices[0]) / prices[0]) * 100
        # 3. Volatility (Standard Deviation normalized)
        volatility = np.std(prices[-20:]) / np.mean(prices[-20:]) * 100
        
        # Determine Market Phase
        market_phase = "UNDEFINED"
        if volatility < 0.05:
            market_phase = "ACCUMULATION (Ranging)"
        elif short_trend_pct > 0.1 and medium_trend_pct > 0.2:
            market_phase = "BULLISH EXPANSION"
        elif short_trend_pct < -0.1 and medium_trend_pct < -0.2:
            market_phase = "BEARISH CORRECTION"
        elif volatility > 0.2:
            market_phase = "HIGH VOLATILITY (Choppy)"
        else:
            market_phase = "CONSOLIDATION"

        print(f"   📊 [Chart] Price: ${current_price:.2f} | Vol: {volatility:.3f}%")
        print(f"   📐 [Structure] Phase: {market_phase}")

        # ---------------------------------------------------------
        # PHASE 2: STRATEGIC PLANNING (The "Brain")
        # ---------------------------------------------------------
        # The agent decides WHAT data it needs based on the Phase
        
        shopping_list = []
        hypothesis = ""

        if market_phase == "BULLISH EXPANSION":
            hypothesis = "Momentum is strong. Is this retail FOMO or real volume?"
            shopping_list = ["ON_CHAIN", "SENTIMENT"] # Check Volume & Hype
            
        elif market_phase == "BEARISH CORRECTION":
            hypothesis = "Price falling. Looking for support or panic selling."
            shopping_list = ["TECHNICAL", "SENTIMENT"] # Check Support Levels & Panic
            
        elif market_phase == "ACCUMULATION (Ranging)":
            hypothesis = "Market is sleeping. Scanning for breakout catalysts."
            shopping_list = ["NEWS", "ON_CHAIN"] # Check for News or Whale Buys
            
        elif market_phase == "HIGH VOLATILITY (Choppy)":
            hypothesis = "Dangerous chop. checking for trend reversal signals."
            shopping_list = ["TECHNICAL", "VOLATILITY"] # Safe Technicals

        else:
            hypothesis = "No clear trend. Maintaining baseline awareness."
            shopping_list = ["NEWS"]

        print(f"   🤔 [Hypothesis] \"{hypothesis}\"")
        print(f"   🛒 [Strategy] Required Data: {', '.join(shopping_list)}")

        # ---------------------------------------------------------
        # PHASE 3: INTELLIGENCE GATHERING (The "Action")
        # ---------------------------------------------------------
        # This triggers actual blockchain payments for the selected nodes
        data_signals = await self.pipeline.fetch_specific_nodes(shopping_list)
        
        # If we paid for data but got nothing (e.g., API errors), abort
        if not data_signals and shopping_list:
            print("   ⚠️ [Alert] Failed to acquire intelligence. Aborting trade.")
            return

        # Calculate a "Confirmation Score" based on the bought data
        # 0.0 (Bearish) -> 1.0 (Bullish)
        confirmation_score = np.mean(data_signals) if data_signals else 0.5
        
        print(f"   🧠 [Intel] Data Consensus: {confirmation_score:.2f}")

        # ---------------------------------------------------------
        # PHASE 4: EXECUTION MATRIX (The "Trigger")
        # ---------------------------------------------------------
        action = "HOLD"
        reason = "Waiting for setup"

        # Trading Rules
        if market_phase == "BULLISH EXPANSION":
            if confirmation_score > 0.6:
                action = "BUY"
                reason = "Trend Up + Data Confirms Strength"
            elif confirmation_score < 0.4:
                action = "HOLD"
                reason = "Trend Up but Data is Weak (Fakeout Warning)"

        elif market_phase == "BEARISH CORRECTION":
            if confirmation_score < 0.4:
                action = "SELL"
                reason = "Trend Down + Data Confirms Weakness"
            elif confirmation_score > 0.7:
                action = "BUY"
                reason = "Oversold Bounce Detected (Contrarian)"

        elif market_phase == "ACCUMULATION (Ranging)":
            if confirmation_score > 0.8:
                action = "BUY"
                reason = "Whale Accumulation / News Catalyst in Range"

        # Execute
        print(f"   🎯 [Decision] {action} | Reason: {reason}")

        if action == "BUY":
            # Dynamic position sizing could go here
            self.trading_engine.execute_swap("USDC", "WETH", 100.0) 
        elif action == "SELL":
            self.trading_engine.execute_swap("WETH", "USDC", 0.05)