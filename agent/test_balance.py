#!/usr/bin/env python3
"""Quick test script to check if the token limit fix works"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Monkey-patch to limit max_tokens
_original_max_tokens = int(os.getenv("OPENROUTER_MAX_TOKENS", "150"))
os.environ["MAX_TOKENS"] = str(_original_max_tokens)

from tools import get_token_balance

def test_cro_balance_direct():
    """Test CRO balance directly without agent (to avoid token limits)"""
    
    print("🔧 Testing CRO balance directly (without agent overhead)...\n")
    
    try:
        print("💬 Query: Check my CRO balance")
        result = get_token_balance.invoke({"token_address": "cro"})
        
        if isinstance(result, dict) and "error" not in result:
            print(f"\n✅ Success!")
            print(f"   Token: {result.get('token', 'CRO')}")
            print(f"   Balance: {result.get('balance_readable', 0):.6f}")
            print(f"   Address: {result.get('address', 'N/A')}")
            return True
        else:
            print(f"\n❌ Error: {result}")
            return False
        
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_cro_balance_direct()
    sys.exit(0 if success else 1)
