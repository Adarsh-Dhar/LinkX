"""
Alpha-Consumer Agent - Main Entry Point
Uses Crypto.com AI Agent SDK with OpenRouter (OpenAI-compatible) for LLM access
and Crypto.com Developer Platform for blockchain operations
"""

import os
import sys
import time
from dotenv import load_dotenv
from crypto_com_agent_client import Agent, SQLitePlugin, tool
from tools import (
    access_paid_api, 
    check_market_conditions, 
    execute_vvs_swap, 
    get_token_balance, 
    estimate_swap_output,
    get_trading_signals,
    get_buy_alpha,
    record_trade,
    get_trade_history,
    get_portfolio_value
)

# Load environment variables
load_dotenv()

class AlphaConsumerAgent:
    def __init__(self):
        """Initialize the agent with OpenRouter LLM and blockchain configuration"""
        
        # Validate environment variables
        self._validate_env()

        # Configure OpenRouter (OpenAI-compatible) for LangChain's ChatOpenAI
        openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        openrouter_base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

        # LangChain reads OpenAI-compatible environment variables for ChatOpenAI
        os.environ["OPENAI_API_KEY"] = openrouter_api_key
        os.environ["OPENAI_API_BASE"] = openrouter_base_url
        os.environ["OPENAI_BASE_URL"] = openrouter_base_url

        # Optional OpenRouter ranking metadata
        if os.getenv("OPENROUTER_HTTP_REFERER"):
            os.environ["HTTP-Referer"] = os.getenv("OPENROUTER_HTTP_REFERER")
        if os.getenv("OPENROUTER_SITE_NAME"):
            os.environ["X-Title"] = os.getenv("OPENROUTER_SITE_NAME")
        
        # LLM Configuration (OpenRouter over OpenAI-compatible API)
        # Using openai/gpt-4o-mini instead of free Gemini to avoid rate limiting
        self.llm_config = {
            "provider": "OpenAI",
            "model": os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
            "provider-api-key": openrouter_api_key,
            "temperature": 0.0,  # Deterministic for financial decisions
        }
        
        # Blockchain Configuration (Cronos Testnet via Crypto.com Developer Platform)
        self.blockchain_config = {
            "api-key": os.getenv("CRYPTO_COM_API_KEY"),
            "private-key": os.getenv("WALLET_PRIVATE_KEY"),
        }
        
        print("🔧 Initializing Alpha-Consumer Agent...")
        print(f"🌐 Network: Cronos EVM")
        print(f"🤖 Model: {self.llm_config['model']}")
        
        # Initialize storage for agent state persistence
        custom_storage = SQLitePlugin(db_path="agent_state.db")
        
        # Agent personality and instructions
        personality = {
            "tone": "helpful and professional",
            "language": "English",
            "verbosity": "concise",
        }
        
        instructions = """
You are the Alpha-Consumer Agent, an autonomous AI agent specialized in:
1. Discovering premium APIs and data sources
2. Automatically handling payment negotiations (HTTP 402 errors)
3. Making economic decisions based on market conditions
4. Executing token swaps on VVS Finance when receiving BUY signals
5. Managing blockchain transactions and monitoring portfolio
6. Tracking trading history and portfolio performance

When you encounter a URL that requires payment:
1. Use the access_paid_api tool to handle the payment automatically
2. The tool will detect 402 errors and manage payment signing

When making investment decisions:
1. Check current market conditions first using check_market_conditions
2. Get trading signals using get_trading_signals or get_buy_alpha
3. Evaluate if the premium data is worth the cost
4. Only proceed with payment if conditions are favorable

When you receive BUY signals (e.g., "BUY VVS", "BUY VVS at market"):
1. Use get_token_balance to confirm you have sufficient funds
2. Use estimate_swap_output to preview the trade without executing
3. Use execute_vvs_swap to execute the trade when confident
4. Use record_trade to log the trade for tracking
5. Always report the transaction hash and outcome

For portfolio management:
1. Use get_portfolio_value to check total portfolio value
2. Use get_trade_history to review past trades
3. Use get_trading_signals to find new opportunities

Always be transparent about costs and confirm before making transactions.
"""
        
        # Initialize the agent with Crypto.com AI Agent SDK
        try:
            self.agent = Agent.init(
                llm_config=self.llm_config,
                blockchain_config=self.blockchain_config,
                plugins={
                    "personality": personality,
                    "instructions": instructions,
                    "tools": [
                        access_paid_api, 
                        check_market_conditions, 
                        execute_vvs_swap, 
                        get_token_balance, 
                        estimate_swap_output,
                        get_trading_signals,
                        get_buy_alpha,
                        record_trade,
                        get_trade_history,
                        get_portfolio_value
                    ],
                    "storage": custom_storage,
                },
            )
            print("✅ Agent initialized successfully!")
        except Exception as e:
            print(f"❌ Failed to initialize agent: {e}")
            sys.exit(1)
    
    def _validate_env(self):
        """Validate required environment variables"""
        required_vars = [
            "OPENROUTER_API_KEY",
            "WALLET_PRIVATE_KEY",
            "CRYPTO_COM_API_KEY",
        ]
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            print("❌ Missing required environment variables:")
            for var in missing_vars:
                print(f"   - {var}")
            print("\n💡 Please copy .env.example to .env and fill in your credentials")
            sys.exit(1)
    
    def run_interactive(self):
        """Run the agent in interactive mode"""
        print("\n" + "="*60)
        print("🤖 Alpha-Consumer Agent Online (Powered by GPT-4o Mini)")
        print("="*60)
        print("\nCommands:")
        print("  - Type your request naturally")
        print("  - 'market' - Check market conditions")
        print("  - 'exit' or 'quit' - Exit the agent")
        print("\nExample requests:")
        print("  - What are the current trading signals?")
        print("  - Check for BUY opportunities")
        print("  - What's my portfolio value?")
        print("  - Show me my recent trades")
        print("  - Estimate a 5 USDC to VVS swap")
        print("  - Execute: Swap 1 USDC for VVS")
        print("  - Access the alpha endpoint and pay if necessary")
        print("\n" + "="*60 + "\n")
        
        while True:
            try:
                user_input = input("\n🧑 You: ").strip()
                
                if not user_input:
                    continue
                    
                if user_input.lower() in ["exit", "quit", "q"]:
                    print("\n👋 Shutting down agent... Goodbye!")
                    break
                    
                # Handle special commands
                if user_input.lower() == "market":
                    conditions = check_market_conditions()
                    print(f"\n📊 Market Conditions: {conditions}")
                    continue
                
                # Process with Agent
                print("\n🤖 Agent: ", end="", flush=True)
                response = self._process_request(user_input)
                print(response)
                
                # Rate limiting for free tier
                time.sleep(1)
                
            except KeyboardInterrupt:
                print("\n\n👋 Shutting down agent... Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                print("Please try again or type 'exit' to quit.")
    
    def _process_request(self, user_input: str):
        """Process user request with the agent"""
        try:
            # Use agent.interact() method from Crypto.com AI Agent SDK
            response = self.agent.interact(user_input)
            return response
            
        except Exception as e:
            return f"Error processing request: {str(e)}"
    
    def run_autonomous(self, task_description: str, interval_seconds: int = 300):
        """
        Run the agent autonomously on a repeating task
        
        Args:
            task_description: The task to perform repeatedly
            interval_seconds: How often to run the task (default 5 minutes)
        """
        print(f"\n🔄 Starting autonomous mode...")
        print(f"📋 Task: {task_description}")
        print(f"⏱️  Interval: {interval_seconds} seconds")
        print(f"⚠️  Press Ctrl+C to stop\n")
        
        iteration = 0
        while True:
            try:
                iteration += 1
                print(f"\n{'='*60}")
                print(f"🔄 Iteration {iteration} at {time.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"{'='*60}\n")
                
                response = self._process_request(task_description)
                print(f"🤖 Agent: {response}\n")
                
                print(f"⏸️  Waiting {interval_seconds} seconds until next check...")
                time.sleep(interval_seconds)
                
            except KeyboardInterrupt:
                print("\n\n⏹️  Stopping autonomous mode...")
                break
            except Exception as e:
                print(f"\n❌ Error in autonomous mode: {e}")
                print(f"⏸️  Waiting {interval_seconds} seconds before retry...")
                time.sleep(interval_seconds)


def main():
    """Main entry point"""
    
    # Check command line arguments for mode
    if len(sys.argv) > 1 and sys.argv[1] == "autonomous":
        # Autonomous mode
        agent = AlphaConsumerAgent()
        
        task = "Check http://localhost:3100/buy-alpha for premium trading data. If CRO price is above $0.08, pay for the data."
        
        # Run every 5 minutes
        agent.run_autonomous(task, interval_seconds=300)
    else:
        # Interactive mode (default)
        agent = AlphaConsumerAgent()
        agent.run_interactive()


if __name__ == "__main__":
    main()