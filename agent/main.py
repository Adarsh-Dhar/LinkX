#!/usr/bin/env python3
"""
Lightweight Trading Agent - No Token Limit Issues
Direct API calls without heavy SDK overhead
"""

import os
import sys
import io
import requests
from dotenv import load_dotenv
from tools import (
    get_token_balance, 
    execute_vvs_swap,
    estimate_swap_output,
    get_trading_signals,
    get_portfolio_value
)

load_dotenv()


class LightweightAgent:
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
        self.max_tokens = int(os.getenv("OPENROUTER_MAX_TOKENS", "150"))
    
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
        
        user_lower = user_input.lower()
        
        # Suppress tool output for cleaner agent responses
        old_stdout = sys.stdout
        
        try:
            sys.stdout = io.StringIO()
            
            # Balance queries
            if "cro" in user_lower and "balance" in user_lower:
                result = get_token_balance.invoke({"token_address": "cro"})
                sys.stdout = old_stdout
                if isinstance(result, dict) and "balance_readable" in result:
                    return f"CRO Balance: {result['balance_readable']:.6f} CRO"
                else:
                    return f"Error: {result}"
            
            elif "usdc" in user_lower and "balance" in user_lower:
                result = get_token_balance.invoke({"token_address": "usdc"})
                sys.stdout = old_stdout
                if isinstance(result, dict) and "balance_readable" in result:
                    return f"USDC Balance: {result['balance_readable']:.6f} USDC"
                else:
                    return f"Error: {result}"
            
            elif "balance" in user_lower:
                cro_result = get_token_balance.invoke({"token_address": "cro"})
                usdc_result = get_token_balance.invoke({"token_address": "usdc"})
                sys.stdout = old_stdout
                
                response = "💰 Wallet Balances:\n"
                if isinstance(cro_result, dict) and "balance_readable" in cro_result:
                    response += f"  CRO: {cro_result['balance_readable']:.6f}\n"
                if isinstance(usdc_result, dict) and "balance_readable" in usdc_result:
                    response += f"  USDC: {usdc_result['balance_readable']:.6f}\n"
                
                return response
            
            elif "signal" in user_lower:
                result = get_trading_signals.invoke({})
                sys.stdout = old_stdout
                if isinstance(result, dict):
                    signals = result.get("signals", [])
                    count = result.get("count", 0)
                    
                    if count > 0 and isinstance(signals, list) and len(signals) > 0:
                        response = f"📊 Trading Signals ({count} active):\n"
                        for signal in signals:
                            response += f"  • {signal}\n"
                        return response
                    else:
                        return "📊 No active trading signals currently. To enable live signals, start the signals server: bash /Users/adarsh/Documents/alpha-consumer/start_signals_server.sh"
                else:
                    return str(result)
            
            elif "portfolio" in user_lower:
                result = get_portfolio_value.invoke({})
                sys.stdout = old_stdout
                if isinstance(result, dict) and "error" not in result:
                    total = result.get("total_value_usd", result.get("total_value", 0))
                    
                    response = f"📈 Portfolio Value: ${total:.2f}\n"
                    
                    for key in ["usdc", "vvs", "cro", "wcro"]:
                        if key in result:
                            amount = result[key]
                            response += f"  {key.upper()}: {amount:.2f}\n"
                    
                    return response
                else:
                    return f"Error: {result.get('error', 'Unknown error')}"
            
            elif "swap" in user_lower or "exchange" in user_lower:
                parts = user_input.split()
                
                amount = None
                amount_idx = None
                for i, part in enumerate(parts):
                    try:
                        amount = float(part)
                        amount_idx = i
                        break
                    except ValueError:
                        continue
                
                if amount is None or amount_idx is None:
                    sys.stdout = old_stdout
                    return "❓ How much would you like to swap? (e.g., 'swap 10 usdc to vvs')"
                
                # Find "to" separator
                to_idx = -1
                if "to" in parts:
                    to_idx = parts.index("to")
                
                # Extract token_in (should be between amount and "to", or after amount)
                token_in = None
                search_start = amount_idx + 1
                search_end = to_idx if to_idx != -1 else len(parts)
                
                for i in range(search_start, search_end):
                    if parts[i].lower() not in ["to", "for", "into", "a", "an", "the"]:
                        token_in = parts[i].lower()
                        break
                
                if token_in is None:
                    sys.stdout = old_stdout
                    return f"❓ What token are you trading? (e.g., 'swap {amount} usdc to vvs')"
                
                # Extract token_out (should be after "to")
                token_out = None
                if to_idx != -1 and to_idx + 1 < len(parts):
                    token_out = parts[to_idx + 1].lower()
                
                if token_out is None or token_out in ["to", "for", "into"]:
                    sys.stdout = old_stdout
                    return f"❓ What token do you want to get? (e.g., 'swap {amount} {token_in} to vvs')"
                
                # Check if this is an estimate or actual swap
                is_estimate = "estimate" in user_lower or "price" in user_lower or "how much" in user_lower
                
                if is_estimate:
                    # Estimate the swap
                    result = estimate_swap_output.invoke({
                        "token_in": token_in,
                        "token_out": token_out,
                        "amount_in": amount
                    })
                    sys.stdout = old_stdout
                    
                    if isinstance(result, dict) and "error" not in result:
                        amount_out = result.get("amount_out_estimated", 0)
                        min_out = result.get("amount_out_min_with_slippage", 0)
                        fee = result.get("fee_percent", 0.3)
                        return f"📊 Swap Estimate: {amount} {token_in} → {amount_out:.2f} {token_out}\n   Min (with 1% slippage): {min_out:.2f} {token_out}\n   Fee: {fee}%"
                    else:
                        return f"Error estimating swap: {result.get('error', 'Unknown error')}"
                else:
                    # Execute the swap
                    result = execute_vvs_swap.invoke({
                        "token_in": token_in,
                        "token_out": token_out,
                        "amount_in": amount,
                        "max_slippage": 1.0
                    })
                    sys.stdout = old_stdout
                    
                    if isinstance(result, dict) and "status" in result and result["status"] == "success":
                        amount_out = result.get("amount_out_expected", 0)
                        tx_hash = result.get("tx_hash", "")
                        return f"✅ Swap executed: {amount} {token_in} → {amount_out:.2f} {token_out}\n   TX: {tx_hash[:20]}..."
                    else:
                        return f"Error executing swap: {result}"
            
            else:
                system_msg = "You are a brief trading assistant. Answer in one sentence."
                messages = [
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_input}
                ]
                
                result = self._call_llm(messages)
                sys.stdout = old_stdout
                return result
        
        except Exception as e:
            sys.stdout = old_stdout
            return f"Error: {e}"
        finally:
            sys.stdout = old_stdout


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
