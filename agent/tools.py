"""
Custom Tools for the Alpha-Consumer Agent
Works with Crypto.com AI Agent SDK for payment handling and market data
"""

import os
import json
import time
import requests
from eth_account import Account
from eth_account.messages import encode_typed_data
from web3 import Web3
from crypto_com_agent_client import tool


@tool
def access_paid_api(url: str):
    """
    Accesses a URL that may require payment via HTTP 402 protocol with x402 standard.
    
    This tool automatically handles the x402 payment flow:
    1. Makes initial request to the URL (GET)
    2. If 402 Payment Required is returned with instruction, extracts payment invoice
    3. Signs EIP-712 TransferWithAuthorization message using agent wallet
    4. Submits payment signature to payment endpoint (POST)
    5. Returns protected data on successful verification
    
    Use this tool whenever you need to access premium APIs or data sources
    that may require payment.
    
    Args:
        url: The URL to access (e.g., http://localhost:3050/alpha/insight/CRO)
    
    Returns:
        dict or str: The response data if successful, error message otherwise
    """
    print(f"\n🔍 Attempting to access: {url}")
    
    try:
        # 1. Initial Request (probe for invoice)
        response = requests.get(url, timeout=10)
        
        # 2. Success Case (no payment needed)
        if response.status_code == 200:
            print("✅ Access granted without payment!")
            try:
                return response.json()
            except:
                return response.text
        
        # 3. Handle Payment Request (HTTP 402)
        if response.status_code == 402:
            print("💳 Payment Required (HTTP 402) - Processing x402 payment...")
            
            try:
                payment_data = response.json()
                
                if 'instruction' not in payment_data:
                    return "Error: Invalid 402 response - missing payment instruction"
                
                instruction = payment_data['instruction']
                
                # Validate instruction has required fields
                required = ['token', 'recipient', 'amount', 'eip712Domain', 'eip712Types', 'validAfter', 'validBefore']
                missing = [f for f in required if f not in instruction]
                if missing:
                    return f"Error: Incomplete payment instruction (missing: {', '.join(missing)})"
                
                # Extract payment details
                token_address = instruction['token']
                recipient = instruction['recipient']
                amount_raw = str(instruction['amount'])
                amount_readable = instruction.get('amountReadable', float(amount_raw) / 1e6)
                valid_after = instruction['validAfter']
                valid_before = instruction['validBefore']
                
                print(f"\n💰 Payment Invoice:")
                print(f"   Token: {token_address}")
                print(f"   Recipient: {recipient}")
                print(f"   Amount: {amount_readable} {instruction.get('tokenSymbol', 'USDC')}")
                print(f"   Valid: {valid_after} → {valid_before}")
                
                # Load wallet for signing
                private_key = os.getenv("WALLET_PRIVATE_KEY")
                if not private_key:
                    return "Error: WALLET_PRIVATE_KEY not set in environment"
                
                account = Account.from_key(private_key)
                payer_address = account.address
                
                print(f"\n🔐 Signing with wallet: {payer_address}")
                
                # Generate unique nonce for this payment
                nonce = '0x' + os.urandom(32).hex()
                
                # Build EIP-712 TypedData for TransferWithAuthorization
                typed_data = {
                    "domain": instruction['eip712Domain'],
                    "types": instruction['eip712Types'],
                    "primaryType": "TransferWithAuthorization",
                    "message": {
                        "from": payer_address,
                        "to": recipient,
                        "value": amount_raw,
                        "validAfter": valid_after,
                        "validBefore": valid_before,
                        "nonce": nonce
                    }
                }
                
                # Sign the typed data
                encoded = encode_typed_data(full_message=typed_data)
                signed = account.sign_message(encoded)
                signature = signed.signature.hex()
                
                # Ensure signature has 0x prefix for ethers.js compatibility
                if not signature.startswith('0x'):
                    signature = '0x' + signature
                
                print(f"   ✅ Signature generated: {signature[:20]}...")
                
                # Execute on-chain transaction using transferWithAuthorization
                print(f"\n💰 Executing on-chain payment...")
                tx_hash = None
                try:
                    # Load Web3 and connect to Cronos
                    rpc_url = os.getenv("CRONOS_RPC_URL", "https://evm-t3.cronos.org")
                    w3 = Web3(Web3.HTTPProvider(rpc_url))
                    
                    if not w3.is_connected():
                        print(f"   ⚠️  Could not connect to RPC, skipping on-chain tx")
                    else:
                        # Load USDC ABI
                        abi_path = os.path.join(os.path.dirname(__file__), 'usdc_abi.json')
                        with open(abi_path, 'r') as f:
                            usdc_abi = json.load(f)
                        
                        # Get USDC contract
                        usdc_contract = w3.eth.contract(
                            address=w3.to_checksum_address(token_address),
                            abi=usdc_abi
                        )
                        
                        # Split signature into r, s, v components
                        sig_bytes = bytes.fromhex(signature[2:])  # Remove 0x
                        r = sig_bytes[:32]
                        s = sig_bytes[32:64]
                        v = sig_bytes[64]
                        
                        # Convert v to proper format (27 or 28)
                        # eth_account already returns the correct v value
                        v_int = int(v)
                        
                        # Call transferWithAuthorization on-chain
                        print(f"   📡 Submitting to blockchain...")
                        print(f"      From: {payer_address}")
                        print(f"      To: {recipient}")
                        print(f"      Amount: {amount_readable}")
                        
                        tx = usdc_contract.functions.transferWithAuthorization(
                            w3.to_checksum_address(payer_address),  # from
                            w3.to_checksum_address(recipient),      # to
                            int(amount_raw),                        # value
                            valid_after,                            # validAfter
                            valid_before,                           # validBefore
                            nonce if isinstance(nonce, bytes) else bytes.fromhex(nonce[2:] if nonce.startswith('0x') else nonce),  # nonce as bytes32
                            v_int,                                  # v as uint8
                            r,                                      # r as bytes32
                            s                                       # s as bytes32
                        ).build_transaction({
                            'from': w3.to_checksum_address(payer_address),
                            'gas': 200000,
                            'gasPrice': w3.eth.gas_price,
                            'nonce': w3.eth.get_transaction_count(w3.to_checksum_address(payer_address))
                        })
                        
                        # Sign and send transaction
                        signed_tx = account.sign_transaction(tx)
                        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
                        tx_hash_hex = tx_hash.hex()
                        
                        print(f"   ✅ Transaction submitted: {tx_hash_hex}")
                        print(f"   ⏳ Waiting for confirmation...")
                        
                        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
                        
                        if receipt['status'] == 1:
                            print(f"   ✅ Payment confirmed on-chain!")
                            print(f"      Block: {receipt['blockNumber']}")
                            print(f"      Gas used: {receipt['gasUsed']}")
                        else:
                            print(f"   ❌ Transaction failed on-chain")
                            # Try to get revert reason
                            try:
                                failed_tx = w3.eth.get_transaction(tx_hash)
                                w3.eth.call(failed_tx, block_identifier=receipt['blockNumber']-1)
                            except Exception as revert_err:
                                print(f"      Revert reason: {str(revert_err)}")
                            print(f"   ℹ️  Continuing with off-chain verification...")
                            tx_hash = None  # Don't return error, continue with off-chain
                        
                except Exception as tx_error:
                    print(f"   ⚠️  On-chain execution failed: {str(tx_error)}")
                    print(f"   ℹ️  Continuing with off-chain verification...")
                
                # Determine payment endpoint (try POST to same URL + /payment suffix first)
                payment_url = url.rstrip('/') + '/payment'
                
                print(f"\n📤 Submitting payment proof to: {payment_url}")
                
                # Submit payment with signature and typedData
                payment_payload = {
                    "signature": signature,
                    "typedData": typed_data
                }
                
                headers = {
                    "Content-Type": "application/json",
                    "X-Payment": signature
                }
                
                payment_response = requests.post(
                    payment_url,
                    json=payment_payload,
                    headers=headers,
                    timeout=10
                )
                
                if payment_response.status_code == 200:
                    print("✅ Payment accepted! Access granted.")
                    try:
                        result = payment_response.json()
                        print(f"\n📦 Received protected data successfully")
                        return result
                    except:
                        return payment_response.text
                else:
                    error_detail = ""
                    try:
                        error_detail = payment_response.json()
                    except:
                        error_detail = payment_response.text
                    
                    return f"Error: Payment rejected. Status: {payment_response.status_code}, Details: {error_detail}"
                
            except json.JSONDecodeError:
                return "Error: Invalid JSON in 402 response"
            except Exception as e:
                return f"Error processing x402 payment: {str(e)}"
        
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
        # Using CoinGecko API (free, no key required)
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
    
    This helps the agent understand the financial impact of payments.
    
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
