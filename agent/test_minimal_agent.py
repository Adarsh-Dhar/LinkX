#!/usr/bin/env python3
"""Minimal agent test with strict token limits"""

import os
import sys
import time
from dotenv import load_dotenv

load_dotenv()

# Set ultra-low token limits
os.environ["OPENROUTER_MAX_TOKENS"] = "150"
os.environ["OPENROUTER_MAX_HISTORY"] = "1"

from crypto_com_agent_client import Agent, SQLitePlugin
from tools import get_token_balance, execute_vvs_swap

def test_agent():
    """Test agent with minimal token usage"""
    
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
    
    # Set OpenAI-compatible env vars
    os.environ["OPENAI_API_KEY"] = openrouter_api_key
    os.environ["OPENAI_BASE_URL"] = "https://openrouter.ai/api/v1"
    
    llm_config = {
        "provider": "OpenAI",
        "model": "openai/gpt-4o-mini",
        "provider-api-key": openrouter_api_key,
        "temperature": 0.0,
        "max_tokens": 150,
        "timeout": 20,
    }
    
    blockchain_config = {
        "api-key": os.getenv("CRYPTO_COM_API_KEY"),
        "private-key": os.getenv("WALLET_PRIVATE_KEY"),
    }
    
    print("🔧 Testing agent with minimal token config...")
    print("   Max tokens: 150")
    print("   Max history: 1")
    print("   Timeout: 20s\n")
    
    try:
        agent = Agent.init(
            llm_config=llm_config,
            blockchain_config=blockchain_config,
            plugins={
                "instructions": "Trading agent. Be brief.",
                "tools": [get_token_balance],
                "storage": SQLitePlugin(db_path="minimal_test.db"),
                "max_history": 1,
            },
        )
        print("✅ Agent initialized\n")
        
        # Test query
        print("💬 Query: Check CRO balance")
        start = time.time()
        response = agent.interact("Check CRO balance")
        elapsed = time.time() - start
        
        print(f"\n🤖 Response ({elapsed:.1f}s): {response}\n")
        print("✅ SUCCESS - No 402 error!")
        return True
        
    except Exception as e:
        error_str = str(e)
        print(f"\n❌ Error: {error_str}\n")
        
        if "402" in error_str:
            print("⚠️  Still getting 402 error - need to reduce tokens further")
        elif "timeout" in error_str.lower():
            print("⚠️  Timeout - try increasing timeout or reducing complexity")
        
        return False

if __name__ == "__main__":
    success = test_agent()
    sys.exit(0 if success else 1)
