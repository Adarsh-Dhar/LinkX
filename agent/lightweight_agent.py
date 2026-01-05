#!/usr/bin/env python3
"""
Lightweight trading agent - bypasses heavy SDK to avoid token limits
Uses OpenRouter directly with minimal context
"""

import os
import json
import requests
from dotenv import load_dotenv
from tools import get_token_balance, execute_vvs_swap

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
    
    def interact(self, user_input: str):
        """Process user input with minimal context"""
        
        # Build minimal tool descriptions
        tool_desc = "Available commands:\n"
        tool_desc += "- 'cro balance' or 'check balance' → calls get_token_balance(token_address='cro')\n"
        tool_desc += "- 'usdc balance' → calls get_token_balance(token_address='usdc')\n"
        tool_desc += "- 'swap X usdc to vvs' → calls execute_vvs_swap\n"
        
        # Detect intent and call tools directly (rule-based to avoid token overhead)
        user_lower = user_input.lower()
        
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
    
    print("\n" + "="*60)
    print("🤖 Lightweight Trading Agent (No Token Limit Issues!)")
    print("="*60)
    print("\nCommands:")
    print("  - 'cro balance' or 'check balance' - Check balances")
    print("  - 'swap 1 usdc to vvs' - Execute swap")
    print("  - 'exit' - Quit")
    print("\n" + "="*60 + "\n")
    
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
