"""
Custom Tools for the Alpha-Consumer Agent
Handles HTTP 402 Payment Required errors and EIP-3009 signature generation
"""

import os
import json
import time
import secrets
import requests
from eth_account import Account
from eth_account.messages import encode_typed_data
from web3 import Web3
from crypto_com_agent_client import tool

# Initialize Web3
w3 = Web3(Web3.HTTPProvider(os.getenv("CRONOS_RPC_URL", "https://evm-t3.cronos.org")))

# Load wallet
PRIVATE_KEY = os.getenv("WALLET_PRIVATE_KEY")
if not PRIVATE_KEY:
    raise ValueError("WALLET_PRIVATE_KEY not found in environment")

account = Account.from_key(PRIVATE_KEY)
AGENT_ADDRESS = account.address


def generate_nonce():
    """Generate a random 32-byte nonce for EIP-3009"""
    return "0x" + secrets.token_hex(32)


def create_eip3009_message(token_address, recipient, amount, valid_before=None):
    """
    Create an EIP-3009 compliant typed data message for USDC transfer
    
    Args:
        token_address: USDC contract address
        recipient: Address to receive the payment
        amount: Amount in smallest unit (e.g., 1000000 for 1 USDC with 6 decimals)
        valid_before: Unix timestamp for expiration (default: 1 hour from now)
    
    Returns:
        dict: EIP-712 typed data structure
    """
    if valid_before is None:
        valid_before = int(time.time()) + 3600  # 1 hour expiry
    
    nonce = generate_nonce()
    
    # EIP-712 Domain
    domain = {
        "name": "USD Coin",
        "version": "2",
        "chainId": int(os.getenv("CHAIN_ID", "338")),
        "verifyingContract": token_address
    }
    
    # Message structure for TransferWithAuthorization
    message = {
        "from": AGENT_ADDRESS,
        "to": recipient,
        "value": int(amount),
        "validAfter": 0,
        "validBefore": valid_before,
        "nonce": nonce
    }
    
    # Type definitions
    types = {
        "EIP712Domain": [
            {"name": "name", "type": "string"},
            {"name": "version", "type": "string"},
            {"name": "chainId", "type": "uint256"},
            {"name": "verifyingContract", "type": "address"}
        ],
        "TransferWithAuthorization": [
            {"name": "from", "type": "address"},
            {"name": "to", "type": "address"},
            {"name": "value", "type": "uint256"},
            {"name": "validAfter", "type": "uint256"},
            {"name": "validBefore", "type": "uint256"},
            {"name": "nonce", "type": "bytes32"}
        ]
    }
    
    return {
        "types": types,
        "primaryType": "TransferWithAuthorization",
        "domain": domain,
        "message": message
    }


def sign_eip3009_message(typed_data):
    """
    Sign an EIP-3009 message with the agent's private key
    
    Args:
        typed_data: EIP-712 typed data structure
    
    Returns:
        str: Hex-encoded signature
    """
    # Encode the typed data
    encoded_data = encode_typed_data(full_message=typed_data)
    
    # Sign with private key
    signed_message = account.sign_message(encoded_data)
    
    return signed_message.signature.hex()


@tool
def access_paid_api(url: str):
    """
    Accesses a URL that may require payment via HTTP 402 protocol.
    
    This tool automatically handles the x402 payment flow:
    1. Makes initial request to the URL
    2. If 402 Payment Required is returned, extracts payment instructions
    3. Creates and signs an EIP-3009 payment authorization
    4. Retries the request with the payment signature
    
    Use this tool whenever you need to access premium APIs or data sources
    that may require payment.
    
    Args:
        url: The URL to access (e.g., http://localhost:3000/buy-alpha)
    
    Returns:
        dict or str: The response data if successful, error message otherwise
    """
    print(f"\n🔍 Attempting to access: {url}")
    
    try:
        # 1. Initial Request
        response = requests.get(url, timeout=10)
        
        # 2. Success Case
        if response.status_code == 200:
            print("✅ Access granted without payment!")
            try:
                return response.json()
            except:
                return response.text
        
        # 3. Handle Payment Request
        if response.status_code == 402:
            print("💳 Payment Required (HTTP 402) - Analyzing payment instructions...")
            
            try:
                payment_data = response.json()
                
                if 'instruction' not in payment_data:
                    return "Error: Invalid 402 response - missing payment instructions"
                
                instruction = payment_data['instruction']
                
                # Extract payment details
                token_address = instruction.get('token')
                recipient = instruction.get('recipient')
                amount = instruction.get('amount')
                
                if not all([token_address, recipient, amount]):
                    return "Error: Incomplete payment instructions"
                
                print(f"\n💰 Payment Details:")
                print(f"   Token: {token_address}")
                print(f"   Recipient: {recipient}")
                print(f"   Amount: {amount} (smallest units)")
                print(f"   Network: Cronos Testnet (Chain ID 338)")
                
                # Ask for confirmation (in production, you might want automatic approval for small amounts)
                amount_in_usdc = int(amount) / 1_000_000  # Assuming 6 decimals
                print(f"\n📊 This will cost approximately {amount_in_usdc:.2f} USDC")
                
                # 4. Create EIP-3009 Payment Message
                print(f"\n🔐 Creating EIP-3009 payment authorization...")
                typed_data = create_eip3009_message(
                    token_address=token_address,
                    recipient=recipient,
                    amount=amount
                )
                
                # 5. Sign the Message
                print(f"✍️  Signing payment with wallet: {AGENT_ADDRESS[:10]}...")
                signature = sign_eip3009_message(typed_data)
                print(f"✅ Signature created: {signature[:20]}...")
                
                # 6. Retry Request with Payment
                headers = {
                    "X-Payment": signature,
                    "Content-Type": "application/json"
                }
                
                # Include the full typed data for verification
                payment_payload = {
                    "signature": signature,
                    "typedData": typed_data
                }
                
                print(f"\n🚀 Resubmitting request with payment proof...")
                paid_response = requests.post(
                    url,
                    headers=headers,
                    json=payment_payload,
                    timeout=10
                )
                
                if paid_response.status_code == 200:
                    print("✅ Payment accepted! Access granted.")
                    try:
                        result = paid_response.json()
                        print(f"\n📦 Received data: {json.dumps(result, indent=2)}")
                        return result
                    except:
                        return paid_response.text
                else:
                    return f"Error: Payment rejected with status {paid_response.status_code}: {paid_response.text}"
                
            except json.JSONDecodeError:
                return "Error: Invalid JSON in 402 response"
            except Exception as e:
                return f"Error processing payment: {str(e)}"
        
        # 4. Other Status Codes
        return f"Error: Received HTTP {response.status_code}: {response.text}"
        
    except requests.exceptions.Timeout:
        return f"Error: Request to {url} timed out"
    except requests.exceptions.ConnectionError:
        return f"Error: Could not connect to {url}. Make sure the server is running."
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def check_market_conditions():
    """
    Checks current market conditions for CRO and other relevant tokens.
    
    This tool helps the agent make informed decisions about whether
    to purchase premium data based on market conditions.
    
    Returns:
        dict: Current market data including prices and trends
    """
    print("\n📊 Checking market conditions...")
    
    try:
        # In a real implementation, you would call the Crypto.com Market Data API
        # or another price feed. For demo purposes, we'll use a public API.
        
        # CoinGecko API (free, no key required)
        response = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={
                "ids": "crypto-com-chain",
                "vs_currencies": "usd",
                "include_24hr_change": "true"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            cro_data = data.get("crypto-com-chain", {})
            
            price = cro_data.get("usd", 0)
            change_24h = cro_data.get("usd_24h_change", 0)
            
            result = {
                "cro_price_usd": price,
                "change_24h_percent": change_24h,
                "trending": "up" if change_24h > 0 else "down",
                "timestamp": int(time.time())
            }
            
            print(f"   CRO Price: ${price:.4f}")
            print(f"   24h Change: {change_24h:+.2f}%")
            print(f"   Trend: {result['trending']}")
            
            return result
        else:
            return {"error": "Failed to fetch market data"}
            
    except Exception as e:
        return {"error": str(e)}


@tool
def estimate_payment_cost(amount: int, token: str = "USDC"):
    """
    Estimates the cost of a payment in human-readable terms.
    
    Args:
        amount: Amount in smallest units (e.g., 1000000 for 1 USDC)
        token: Token symbol (default: USDC)
    
    Returns:
        dict: Cost breakdown and recommendations
    """
    if token.upper() == "USDC":
        decimals = 6
    else:
        decimals = 18  # Default for most ERC20 tokens
    
    amount_readable = amount / (10 ** decimals)
    
    result = {
        "amount_raw": amount,
        "amount_readable": amount_readable,
        "token": token,
        "gas_cost_paid_by": "server/facilitator",
        "recommendation": ""
    }
    
    # Add recommendation based on amount
    if amount_readable < 1:
        result["recommendation"] = "Low cost - safe to proceed"
    elif amount_readable < 10:
        result["recommendation"] = "Moderate cost - verify value of data"
    else:
        result["recommendation"] = "High cost - carefully evaluate ROI"
    
    return result