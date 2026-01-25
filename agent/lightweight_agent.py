#!/usr/bin/env python3
"""
Lightweight trading agent - bypasses heavy SDK to avoid token limits
Uses OpenRouter directly with minimal context
Integrated with 48-Node Ecosystem via SmartRouter
Powered by Neural Network Brain for AI-driven decisions
"""

from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path(__file__).parent.parent / '.env')

import os
import json
import requests
import numpy as np
import asyncio
from dotenv import load_dotenv
from tools import get_token_balance, execute_vvs_swap
from smart_router import SmartRouter
from brain import RLAgent
try:
    from data_pipeline import DataPipeline
except ImportError:
    # Patch: Use thriftpy2 or a stub if data_pipeline is unavailable
    import thriftpy2 as thriftpy
    class DataPipeline:
        def __init__(self, *args, **kwargs):
            # TODO: Implement or patch with actual logic as needed
            pass
        def get_market_state(self):
            # Return dummy data or raise NotImplementedError
            raise NotImplementedError("DataPipeline.get_market_state is not implemented.")
        def get_feature_names(self):
            return []
        def get_raw_values(self):
            return []
        def get_normalized_vector(self):
            return []
from .trading_engine import TradingEngine, initialize_engine

load_dotenv()

class LightweightAgent:
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
        self.max_tokens = int(os.getenv("OPENROUTER_MAX_TOKENS", "150"))
        
        # Tool registry
        self.tools = {
            "get_token_balance": get_token_balance,
            "execute_vvs_swap": execute_vvs_swap,
        }
        
        # Initialize the Smart Router for 48-node ecosystem
        print("\n🔌 Initializing Smart Router for 48-Node Ecosystem...")
        self.smart_router = SmartRouter()
        
        # Initialize the Data Pipeline for 48-node data aggregation
        print("📡 Initializing Data Pipeline...")
        self.data_pipeline = DataPipeline()
        
        # Initialize the Neural Network Brain
        print("🧠 Initializing Neural Network Brain...")
        try:
            self.brain = RLAgent(model_path="agent/brain.pth")
            print("✅ Neural Network loaded successfully")
        except Exception as e:
            print(f"⚠️  Brain initialization warning: {e}")
            print("   Continuing in non-neural mode...")
            self.brain = None
        
        # Initialize the Trading Engine for orchestrating trades
        print("⚙️  Initializing Trading Engine...")
        try:
            self.trading_engine = initialize_engine(
                smart_router=self.smart_router,
                data_pipeline=self.data_pipeline,
                neural_brain=self.brain
            )
            print("✅ Trading Engine initialized successfully")
        except Exception as e:
            print(f"⚠️  Trading Engine warning: {e}")
            self.trading_engine = None
        
        # Data accumulator for neural network (48 features)
        self.market_state = np.zeros(48, dtype=np.float32)
        self.feature_index = 0  # Track which feature slot to fill next
        
        # Minimal conversation history
        self.history = []
        self.max_history = 2
    
    def _call_llm(self, messages):
        """Call OpenRouter LLM with minimal context"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": 0.0,
        }
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=20
        )
        
        if response.status_code != 200:
            raise Exception(f"LLM Error {response.status_code}: {response.text}")
        
        return response.json()["choices"][0]["message"]["content"]
    
    def _vectorize_market_data(self, data_dict, category="market"):
        """
        Convert raw market data from providers into neural network input format.
        The brain expects a 48-dimensional vector.
        """
        try:
            # Extract numeric value from data
            if isinstance(data_dict, dict):
                # Try common keys
                value = (
                    data_dict.get('value') or 
                    data_dict.get('price') or 
                    data_dict.get('sentiment') or 
                    data_dict.get('volume') or 
                    data_dict.get('count') or 
                    data_dict.get('score') or 
                    0
                )
                
                # Handle nested data structures
                if isinstance(value, dict):
                    value = list(value.values())[0] if value else 0
                    
                value = float(value)
            else:
                value = float(data_dict)
            
            # Store in the appropriate feature slot
            if self.feature_index < 48:
                self.market_state[self.feature_index] = value
                self.feature_index = (self.feature_index + 1) % 48
            
            # Normalize based on category
            if category == "sentiment":
                value = max(0, min(1, value))  # Clamp to [0,1]
            elif category == "price":
                value = value / 100 if value > 1 else value  # Scale down large prices
            elif category == "volume":
                value = np.log1p(value) / 20  # Log scale for volumes
            
            # Fill remaining slots with derived features (prevent all zeros)
            if self.feature_index < 47:
                self.market_state[self.feature_index:self.feature_index+3] = [
                    value * 1.1,  # Slightly adjusted versions
                    value * 0.9,
                    value ** 2 if abs(value) < 10 else value
                ]
                self.feature_index = min(self.feature_index + 3, 47)
            
            return value
        except Exception as e:
            print(f"⚠️  Vectorization warning: {e}")
            return 0.0
    
    def _get_neural_prediction(self):
        """
        Get AI prediction from the neural network based on live 48-server data.
        """
        if self.brain is None:
            return None
        
        try:
            # Fetch live market state from 48 providers
            print("📡 Fetching live data from 48 providers...")
            state = asyncio.run(self.data_pipeline.get_market_state())
            
            # Get prediction from brain (state is already normalized by data_pipeline)
            action, confidence, probabilities = self.brain.get_action(state, epsilon=0.05)
            
            return {
                'action': action,
                'confidence': confidence,
                'probabilities': probabilities,
                'live_data': True
            }
        except Exception as e:
            print(f"⚠️  Neural prediction error: {e}")
            print("   Attempting fallback to accumulated state...")
            
            # Fallback to accumulated state if live fetch fails
            try:
                state = self.market_state.copy()
                state_min = state.min()
                state_max = state.max()
                if state_max - state_min > 0:
                    state = (state - state_min) / (state_max - state_min)
                
                action, confidence, probabilities = self.brain.get_action(state, epsilon=0.05)
                
                return {
                    'action': action,
                    'confidence': confidence,
                    'probabilities': probabilities,
                    'live_data': False
                }
            except Exception as fallback_error:
                print(f"❌ Fallback also failed: {fallback_error}")
                return None
    
    def interact(self, user_input: str):
        """Process user input with minimal context"""
        
        # Detect intent and call tools directly (rule-based to avoid token overhead)
        user_lower = user_input.lower()
        
        # === NEURAL PREDICTION COMMAND ===
        if any(phrase in user_lower for phrase in [
            "neural predict", "ai predict", "brain predict", 
            "run prediction", "activate neural", "neural mode",
            "what does the brain think", "ai analysis"
        ]):
            print("\n🧠 Activating Neural Network Prediction...")
            
            if self.brain is None:
                return "❌ Neural Network not available. Brain failed to initialize."
            
            # Get current market state prediction
            neural_result = self._get_neural_prediction()
            
            if neural_result:
                brain_stats = self.brain.get_stats()
                data_source = "🌐 LIVE 48-Server Data" if neural_result.get('live_data') else "📊 Cached Data"
                
                response = (
                    f"{'='*70}\n"
                    f"🧠 **NEURAL NETWORK PREDICTION**\n"
                    f"{'='*70}\n\n"
                    f"**Market State Analysis:**\n"
                    f"   • Data Source: {data_source}\n"
                    f"   • Features Analyzed: 48 data points\n"
                    f"   • Providers: 48 autonomous nodes\n\n"
                    f"**AI Decision:**\n"
                    f"   🎯 **Action:** {neural_result['action']}\n"
                    f"   📊 **Confidence:** {neural_result['confidence']*100:.1f}%\n\n"
                    f"**Probability Distribution:**\n"
                )
                
                # Visual probability bars
                for action, prob in neural_result['probabilities'].items():
                    bar_length = int(prob * 50)
                    bar = '█' * bar_length + '░' * (50 - bar_length)
                    response += f"   {action:5s} [{bar}] {prob*100:.1f}%\n"
                
                response += (
                    f"\n**Agent Intelligence Metrics:**\n"
                    f"   • Total Trades: {brain_stats['total_trades']}\n"
                    f"   • Win Rate: {brain_stats['win_rate']:.1f}%\n"
                    f"   • Performance Score: {brain_stats['cumulative_reward']:+.2f}\n"
                    f"   • Memory: {brain_stats['memory_size']}/1000 experiences\n\n"
                )
                
                # Actionable recommendation
                if neural_result['action'] == 'BUY' and neural_result['confidence'] > 0.70:
                    response += (
                        f"🚀 **RECOMMENDATION:** Strong BUY signal ({neural_result['confidence']*100:.0f}% confidence)\n"
                        f"   Suggested action: 'swap 10 usdc to cro'\n"
                    )
                elif neural_result['action'] == 'SELL' and neural_result['confidence'] > 0.70:
                    response += (
                        f"📉 **RECOMMENDATION:** Strong SELL signal ({neural_result['confidence']*100:.0f}% confidence)\n"
                        f"   Suggested action: 'swap 10 cro to usdc'\n"
                    )
                else:
                    response += (
                        f"⏸️  **RECOMMENDATION:** HOLD current positions\n"
                        f"   Confidence below threshold ({neural_result['confidence']*100:.0f}% < 70%)\n"
                    )
                
                return response
            else:
                return "❌ Could not generate neural prediction. Insufficient market data."
        
        # Check specialized data nodes (48-node ecosystem)
        if ("check" in user_lower or "analyze" in user_lower or "get" in user_lower or "find" in user_lower or "query" in user_lower) and (
            "whale" in user_lower or "sentiment" in user_lower or "rsi" in user_lower or 
            "price" in user_lower or "volume" in user_lower or "spread" in user_lower or
            "depth" in user_lower or "tvl" in user_lower or "dev" in user_lower or
            "social" in user_lower or "inflow" in user_lower or "tech" in user_lower or
            "premium" in user_lower or "data" in user_lower or "correlation" in user_lower or
            "burn" in user_lower or "active" in user_lower or "order book" in user_lower
        ):
            print(f"\n🧠 Agent analyzing intent: '{user_input}'")
            
            # A. FIND PROVIDERS (Scans the 48 nodes)
            candidates = self.router.find_providers(user_input)
            
            if not candidates:
                return "❌ No specialized data node found for that request."
            
            # B. EXECUTE COMPETITION (Selects the best one)
            # We default to 'cheap' to save money, or 'premium' if user asks
            strategy = "premium" if "premium" in user_lower else "cheap"
            chosen_node = self.router.select_best_provider(candidates, strategy)
            
            if not chosen_node:
                return "❌ Could not select a provider node."
            
            # C. BUY DATA (Simulate x402 flow with the ecosystem node)
            print(f"💰 Connecting to {chosen_node['url']}...")
            try:
                # Fetch data from the chosen node
                response = requests.get(chosen_node['url'])
                
                if response.status_code == 402:
                    # Payment required - simulate payment
                    invoice = response.json()
                    print(f"💳 Invoice: {invoice['invoice']['amount']} USDC to {invoice['invoice']['to']}")
                    
                    # Simulate payment and fetch actual data
                    payment_response = requests.post(
                        f"http://localhost:{chosen_node['port']}/data/payment",
                        json={"signature": "simulated_payment"}
                    )
                    
                    if payment_response.status_code == 200:
                        data = payment_response.json()
                        market_data = data.get('data', {})
                        
                        # === NEURAL BRAIN INTEGRATION ===
                        # 1. Vectorize the acquired data for neural network
                        category = "market"  # Default
                        if "whale" in user_lower or "transaction" in user_lower:
                            category = "onchain"
                        elif "sentiment" in user_lower or "social" in user_lower:
                            category = "sentiment"
                        elif "price" in user_lower or "volume" in user_lower:
                            category = "price"
                        
                        extracted_value = self._vectorize_market_data(market_data, category)
                        
                        # 2. Get AI prediction from the brain
                        neural_result = self._get_neural_prediction()
                        
                        # 3. Build response with both raw data AND neural analysis
                        response = (
                            f"✅ **Data Acquired from:** {chosen_node['name']}\n"
                            f"💸 **Cost:** ${chosen_node['price']} USDC\n"
                            f"🔗 **Provider:** {data['provider']}\n"
                            f"📊 **Raw Data:**\n{json.dumps(market_data, indent=2)}\n"
                        )
                        
                        # Add neural network analysis if available
                        if neural_result:
                            response += (
                                f"\n{'='*60}\n"
                                f"🧠 **NEURAL NETWORK ANALYSIS:**\n"
                                f"{'='*60}\n"
                                f"   🎯 **Decision:** {neural_result['action']}\n"
                                f"   📊 **Confidence:** {neural_result['confidence']*100:.1f}%\n"
                                f"   📈 **Probability Distribution:**\n"
                                f"      • BUY:  {neural_result['probabilities']['BUY']*100:.0f}%\n"
                                f"      • HOLD: {neural_result['probabilities']['HOLD']*100:.0f}%\n"
                                f"      • SELL: {neural_result['probabilities']['SELL']*100:.0f}%\n"
                                f"\n"
                            )
                            
                            # Add actionable recommendation
                            if neural_result['action'] == 'BUY' and neural_result['confidence'] > 0.70:
                                response += "🚀 **Recommendation:** Strong BUY signal detected. Consider entering a position.\n"
                            elif neural_result['action'] == 'SELL' and neural_result['confidence'] > 0.70:
                                response += "📉 **Recommendation:** Strong SELL signal detected. Consider exiting positions.\n"
                            else:
                                response += "⏸️  **Recommendation:** Signal is weak. HOLD current positions.\n"
                        else:
                            response += "\n⚠️  Neural analysis unavailable (brain not initialized)\n"
                        
                        response += f"\n💡 Provider selected based on '{strategy}' preference."
                        
                        return response
                    else:
                        return f"❌ Payment failed: {payment_response.text}"
                else:
                    return f"❌ Unexpected response: {response.status_code}"
                    
            except Exception as e:
                return f"❌ Error accessing data node: {str(e)}\n\nMake sure 'node ecosystem.js' is running."
        
        # Buy alpha data detection (legacy for backward compatibility)
        if ("buy" in user_lower and "alpha" in user_lower) or ("purchase" in user_lower and "alpha" in user_lower) or ("get" in user_lower and "alpha" in user_lower and "insight" in user_lower):
            # Extract ticker from user input (default to CRO)
            ticker = "CRO"  # Default
            ticker_keywords = ["cro", "vvs", "usdc"]
            for keyword in ticker_keywords:
                if keyword in user_lower:
                    ticker = keyword.upper()
                    break
            
            print("💰 Agent is buying alpha...")
            api_url = f"http://localhost:3050/alpha/insight/{ticker}"
            
            try:
                # This tool handles the x402 payment automatically
                alpha_data = access_paid_api.invoke(api_url)
                
                # Parse the data and suggest trading action
                if isinstance(alpha_data, dict):
                    # Check if we got the data directly or wrapped in a 'data' field
                    data = alpha_data.get("data", alpha_data)
                    
                    if isinstance(data, dict):
                        signal = data.get("recommended_action") or data.get("signal", "")
                        sentiment = data.get("sentiment", "")
                        confidence = data.get("confidence", 0)
                        
                        # Build response with purchased data
                        response = f"✅ **Alpha Purchased for {ticker}:**\n\n"
                        response += f"📊 Sentiment: {sentiment}\n"
                        response += f"🎯 Signal: {signal}\n"
                        if confidence > 0:
                            response += f"📈 Confidence: {confidence*100:.0f}%\n"
                        
                        # Extract additional fields if available
                        if "price_target" in data:
                            response += f"🎯 Price Target: ${data['price_target']:.4f}\n"
                        if "stop_loss" in data:
                            response += f"🛑 Stop Loss: ${data['stop_loss']:.4f}\n"
                        if "reason" in data:
                            response += f"💡 Reason: {data['reason']}\n"
                        
                        response += "\n"
                        
                        # AUTOMATIC ACTION: Parse the data and Trade
                        if signal == "ACCUMULATE" or signal == "BUY" or data.get("signal") == "BUY":
                            # Determine token to swap to (use ticker or default to VVS)
                            token = ticker if ticker != "USDC" else "VVS"
                            response += f"🚀 **Action:** The signal is BUY. I recommend swapping USDC for {token}.\n"
                            response += f"💬 Type 'swap 10 usdc to {token.lower()}' to execute."
                        else:
                            response += f"🛑 **Action:** Signal is {signal}. No trade recommended at this time."
                        
                        return response
                    else:
                        return f"✅ **Alpha Purchased:** {json.dumps(alpha_data, indent=2)}\n\n⚠️ Unexpected data format received."
                else:
                    return f"✅ **Alpha Purchased:** {alpha_data}"
            except Exception as e:
                return f"❌ Error purchasing alpha data: {str(e)}\n\nMake sure the server is running on port 3050."
        
        # Balance queries
        if "cro" in user_lower and "balance" in user_lower:
            result = get_token_balance.invoke({"token_address": "cro"})
            if isinstance(result, dict) and "balance_readable" in result:
                return f"CRO Balance: {result['balance_readable']:.6f} CRO"
            else:
                return f"Error: {result}"
        
        elif "usdc" in user_lower and "balance" in user_lower:
            result = get_token_balance.invoke({"token_address": "usdc"})
            if isinstance(result, dict) and "balance_readable" in result:
                return f"USDC Balance: {result['balance_readable']:.6f} USDC"
            else:
                return f"Error: {result}"
        
        elif "balance" in user_lower:
            # Check both
            cro_result = get_token_balance.invoke({"token_address": "cro"})
            usdc_result = get_token_balance.invoke({"token_address": "usdc"})
            
            response = "💰 Wallet Balances:\n"
            if isinstance(cro_result, dict) and "balance_readable" in cro_result:
                response += f"  CRO: {cro_result['balance_readable']:.6f}\n"
            if isinstance(usdc_result, dict) and "balance_readable" in usdc_result:
                response += f"  USDC: {usdc_result['balance_readable']:.6f}\n"
            
            return response
        
        # Swap execution
        elif "swap" in user_lower:
            # Parse swap parameters (very basic)
            # Format: "swap 1 usdc to vvs"
            try:
                parts = user_input.split()
                amount_idx = parts.index("swap") + 1 if "swap" in parts else 0
                amount = float(parts[amount_idx])
                token_in = parts[amount_idx + 1].lower()
                token_out = parts[amount_idx + 3].lower() if "to" in parts else "vvs"
                
                result = execute_vvs_swap.invoke({
                    "token_in": token_in,
                    "token_out": token_out,
                    "amount_in": amount,
                    "max_slippage": 1.0
                })
                
                return f"Swap executed: {result}"
            except Exception as e:
                return f"Error parsing swap command: {e}\nFormat: 'swap 1 usdc to vvs'"
        
        # Fallback - use LLM but with minimal context
        else:
            system_msg = "You are a brief trading assistant. Answer in one sentence."
            messages = [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_input}
            ]
            
            try:
                return self._call_llm(messages)
            except Exception as e:
                return f"Error: {e}"


def main():
    """Interactive mode"""
    agent = LightweightAgent()
    
    print("\n" + "="*70)
    print("🤖 AI-Powered Trading Agent + 48-Node Ecosystem + Neural Brain")
    print("="*70)
    print("\n🧠 **Neural Network Commands:**")
    print("    - 'neural predict' or 'ai predict' - Get AI trading decision")
    print("    - 'activate neural mode' - Run brain analysis")
    print("    - 'what does the brain think' - Neural market analysis")
    print("\n📡 **Data Queries (48-Node Ecosystem):**")
    print("    - 'check whale transactions'")
    print("    - 'check premium sentiment'")
    print("    - 'analyze rsi'")
    print("    - 'get tvl data'")
    print("    - 'find social volume'")
    print("    - 'query correlation'")
    print("\n💰 **Wallet Commands:**")
    print("    - 'cro balance' or 'check balance' - Check balances")
    print("    - 'swap 1 usdc to vvs' - Execute swap")
    print("    - 'buy alpha' - Purchase premium alpha insights")
    print("\n    - 'exit' - Quit")
    print("\n" + "="*70 + "\n")
    
    while True:
        try:
            user_input = input("\n🧑 You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ["exit", "quit", "q"]:
                print("\n👋 Goodbye!")
                break
            
            response = agent.interact(user_input)
            print(f"\n🤖 Agent: {response}")
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
