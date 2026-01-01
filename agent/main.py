"""
Alpha-Consumer Agent - Main Entry Point
Uses Google Gemini API for AI intelligence and Crypto.com SDK for blockchain operations
"""

import os
import sys
import time
from dotenv import load_dotenv
from crypto_com_agent_client import Agent
from tools import access_paid_api, check_market_conditions
from wallet_manager import WalletManager

# Load environment variables
load_dotenv()

class AlphaConsumerAgent:
    def __init__(self):
        """Initialize the agent with Gemini and blockchain configuration"""
        
        # Validate environment variables
        self._validate_env()
        
        # Gemini LLM Configuration
        self.llm_config = {
            "provider": "GoogleGenAI",
            "model": "gemini-1.5-flash",  # Fast, free-tier eligible
            "provider-api-key": os.getenv("GEMINI_API_KEY"),
            "temperature": 0.0,  # Deterministic for financial decisions
            "max_tokens": 8192,
        }
        
        # Blockchain Configuration (Cronos Testnet)
        self.blockchain_config = {
            "chain_id": int(os.getenv("CHAIN_ID", "338")),
            "rpc_url": os.getenv("CRONOS_RPC_URL"),
            "private_key": os.getenv("WALLET_PRIVATE_KEY"),
        }
        
        # Initialize wallet manager
        self.wallet = WalletManager(
            private_key=os.getenv("WALLET_PRIVATE_KEY"),
            rpc_url=os.getenv("CRONOS_RPC_URL")
        )
        
        print("🔧 Initializing Alpha-Consumer Agent...")
        print(f"💰 Wallet Address: {self.wallet.address}")
        print(f"🌐 Network: Cronos Testnet (Chain ID: {self.blockchain_config['chain_id']})")
        
        # Check wallet balance
        self._check_wallet_balance()
        
        # Initialize the agent with custom tools
        try:
            self.agent = Agent.init(
                llm_config=self.llm_config,
                blockchain_config=self.blockchain_config
            )
            print("✅ Agent initialized successfully!")
        except Exception as e:
            print(f"❌ Failed to initialize agent: {e}")
            sys.exit(1)
            
        # System prompt for the agent
        self.system_prompt = """
You are the Alpha-Consumer Agent, an autonomous AI agent specialized in:
1. Discovering premium APIs and data sources
2. Automatically handling payment negotiations (HTTP 402 errors)
3. Making economic decisions based on market conditions
4. Managing blockchain transactions using EIP-3009

When you encounter a URL that requires payment:
1. Use the access_paid_api tool to handle the payment automatically
2. The tool will detect 402 errors, sign payment messages, and retry

When making investment decisions:
1. Check current market conditions first
2. Evaluate if the premium data is worth the cost
3. Only proceed with payment if conditions are favorable

Always be transparent about costs and ask for confirmation on large purchases.
"""
    
    def _validate_env(self):
        """Validate required environment variables"""
        required_vars = [
            "GEMINI_API_KEY",
            "WALLET_PRIVATE_KEY",
            "CRONOS_RPC_URL",
        ]
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            print("❌ Missing required environment variables:")
            for var in missing_vars:
                print(f"   - {var}")
            print("\n💡 Please copy .env.example to .env and fill in your credentials")
            sys.exit(1)
    
    def _check_wallet_balance(self):
        """Check wallet balances for TCRO and USDC"""
        print("\n💰 Checking wallet balances...")
        
        tcro_balance = self.wallet.get_tcro_balance()
        usdc_balance = self.wallet.get_usdc_balance()
        
        print(f"   TCRO: {tcro_balance:.4f}")
        print(f"   USDC: {usdc_balance:.2f}")
        
        if tcro_balance < 0.1:
            print("⚠️  Low TCRO balance! Get more from: https://cronos.org/faucet")
        
        if usdc_balance < 1:
            print("⚠️  Low USDC balance! You may not be able to pay for premium APIs")
    
    def run_interactive(self):
        """Run the agent in interactive mode"""
        print("\n" + "="*60)
        print("🤖 Alpha-Consumer Agent Online (Powered by Gemini)")
        print("="*60)
        print("\nCommands:")
        print("  - Type your request naturally")
        print("  - 'balance' - Check wallet balance")
        print("  - 'market' - Check market conditions")
        print("  - 'exit' or 'quit' - Exit the agent")
        print("\nExample requests:")
        print("  - Find me some premium trading alpha")
        print("  - Check if CRO price justifies buying premium data")
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
                if user_input.lower() == "balance":
                    self._check_wallet_balance()
                    continue
                    
                if user_input.lower() == "market":
                    conditions = check_market_conditions()
                    print(f"\n📊 Market Conditions: {conditions}")
                    continue
                
                # Process with Gemini
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
            # Combine system prompt with user input
            full_prompt = f"{self.system_prompt}\n\nUser Request: {user_input}"
            
            # Run the agent
            response = self.agent.run(full_prompt)
            
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