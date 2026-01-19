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
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Optional: PoA middleware for EVM compatibility (not required for Cronos)
try:
    from web3.middleware import geth_poa_middleware
    HAS_POA_MIDDLEWARE = True
except ImportError:
    HAS_POA_MIDDLEWARE = False

from crypto_com_agent_client import tool

# ===================================
# CONFIGURATION FROM .env
# ===================================
CRONOS_RPC_URL = os.getenv("CRONOS_RPC_URL", "https://evm-t3.cronos.org")
TRADING_SIGNALS_URL = os.getenv("TRADING_SIGNALS_URL", "http://localhost:3050")
USDC_CONTRACT = os.getenv("USDC_CONTRACT", "0x908059CF02cbb643Bc96C55e14Fb3699e632479f")
VVS_CONTRACT = os.getenv("VVS_CONTRACT", "0xea59AC2CcEfe907e7F77B502e2C87aC929832bfF")
VVS_ROUTER = os.getenv("VVS_ROUTER", "0x3bc8a2c283751Adf1E3FAc823B6Cb0056f9f86C8")
WCRO_ADDRESS = os.getenv("WCRO_ADDRESS", "0x9005E37cDfc4361491996aD7d546fC15AC9aAD9A")

# Token symbol to address mapping
TOKEN_MAP = {
    "usdc": USDC_CONTRACT,
    "vvs": VVS_CONTRACT,
    "cro": "cro",  # Special case for native token
    "wcro": WCRO_ADDRESS
}

def resolve_token_address(token: str):
    """Convert token symbol or address to checksum address"""
    token_lower = token.lower().strip()
    
    # Check if it's a known symbol
    if token_lower in TOKEN_MAP:
        addr = TOKEN_MAP[token_lower]
        if addr == "cro":
            return "cro"
        return Web3.to_checksum_address(addr)
    
    # If it's already an address, return as checksum
    if token_lower.startswith("0x") and len(token_lower) == 42:
        try:
            return Web3.to_checksum_address(token_lower)
        except:
            return None
    
    return None

# --- VVS FINANCE ROUTER ABI (Uniswap V2 compatible) ---
ROUTER_ABI = [
    {
        "inputs": [
            {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
            {"internalType": "address[]", "name": "path", "type": "address[]"}
        ],
        "name": "getAmountsOut",
        "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
            {"internalType": "uint256", "name": "amountOutMin", "type": "uint256"},
            {"internalType": "address[]", "name": "path", "type": "address[]"},
            {"internalType": "address", "name": "to", "type": "address"},
            {"internalType": "uint256", "name": "deadline", "type": "uint256"}
        ],
        "name": "swapExactTokensForTokens",
        "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "amountOutMin", "type": "uint256"},
            {"internalType": "address[]", "name": "path", "type": "address[]"},
            {"internalType": "address", "name": "to", "type": "address"},
            {"internalType": "uint256", "name": "deadline", "type": "uint256"}
        ],
        "name": "swapExactETHForTokens",
        "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
            {"internalType": "uint256", "name": "amountOutMin", "type": "uint256"},
            {"internalType": "address[]", "name": "path", "type": "address[]"},
            {"internalType": "address", "name": "to", "type": "address"},
            {"internalType": "uint256", "name": "deadline", "type": "uint256"}
        ],
        "name": "swapExactTokensForETH",
        "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

# --- ERC20 ABI (minimal for approval and balance checks) ---
ERC20_ABI = [
    {
        "constant": False,
        "inputs": [
            {"name": "_spender", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [
            {"name": "_owner", "type": "address"},
            {"name": "_spender", "type": "address"}
        ],
        "name": "allowance",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    }
]


@tool
def access_paid_api(url: str):
    """Access URL with x402 payment handling."""
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
    Get CRO price and 24h change.
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

@tool
def get_token_balance(token_address: str, chain: str = "cronos_mainnet"):
    """Get wallet balance. Use 'cro' for native token."""
    print(f"\n💰 Checking balance of {token_address[:10]}...")
    
    try:
        rpc_url = os.getenv("CRONOS_RPC_URL", "https://evm.cronos.org")
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        if not w3.is_connected():
            return {"error": "Could not connect to RPC"}
        
        private_key = os.getenv("WALLET_PRIVATE_KEY")
        if not private_key:
            return {"error": "WALLET_PRIVATE_KEY not set"}
        
        account = w3.eth.account.from_key(private_key)
        wallet_address = account.address
        
        # Check native CRO balance
        if token_address.lower() == "cro" or token_address.lower() == "0xnative":
            balance_wei = w3.eth.get_balance(wallet_address)
            balance_readable = w3.from_wei(balance_wei, 'ether')
            
            return {
                "token": "CRO",
                "address": wallet_address,
                "balance_wei": str(balance_wei),
                "balance_readable": float(balance_readable),
                "decimals": 18
            }
        
        # Check ERC20 token balance
        token_contract = w3.eth.contract(address=token_address, abi=ERC20_ABI)
        decimals = token_contract.functions.decimals().call()
        balance_raw = token_contract.functions.balanceOf(wallet_address).call()
        balance_readable = balance_raw / (10 ** decimals)
        
        result = {
            "token": token_address[:10] + "...",
            "address": wallet_address,
            "balance_raw": str(balance_raw),
            "balance_readable": balance_readable,
            "decimals": decimals
        }
        
        print(f"   ✅ Balance: {balance_readable:.6f}")
        return result
        
    except Exception as e:
        return {"error": str(e)}


@tool
def estimate_swap_output(token_in: str, token_out: str, amount_in: float, chain: str = "cronos_mainnet"):
    """Estimate swap output without executing."""
    print(f"\n📊 Estimating swap: {amount_in} {token_in}... → {token_out}...")
    
    try:
        # Resolve token addresses
        token_in_addr = resolve_token_address(token_in)
        token_out_addr = resolve_token_address(token_out)
        
        if not token_in_addr or not token_out_addr:
            return {"error": f"Cannot resolve token addresses: {token_in} or {token_out}"}
        
        rpc_url = CRONOS_RPC_URL
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        if not w3.is_connected():
            return {"error": "Could not connect to RPC"}
        
        # Check if on testnet without VVS contracts
        is_testnet = w3.eth.chain_id == 338
        
        if is_testnet:
            # Fetch real mainnet pricing for testnet (mock transaction)
            print(f"   ℹ️  Running on testnet - fetching real mainnet pricing")
            
            try:
                # Connect to mainnet to get real prices
                mainnet_rpc = "https://rpc.cronos.org"
                mainnet_w3 = Web3(Web3.HTTPProvider(mainnet_rpc))
                
                if mainnet_w3.is_connected():
                    # Try to get real mainnet pricing
                    mainnet_router = mainnet_w3.eth.contract(
                        address=Web3.to_checksum_address("0x145677FC4d9b8F19B4172A2b88f7fb1f02fdf220"),
                        abi=ROUTER_ABI
                    )
                    
                    # Standard token addresses on mainnet
                    mainnet_token_map = {
                        "usdc": "0xc21223249CA28397B4B6541dfFaEcC539BfF0c59",
                        "vvs": "0x2D03bECE6747ADC00E1a131BBA1469C15fD11e03",
                        "wcro": "0x5C7F8A570d578ED84E63fdFA7b1eE72dEae1AE23",
                    }
                    
                    token_in_addr = mainnet_token_map.get(token_in.lower(), token_in)
                    token_out_addr = mainnet_token_map.get(token_out.lower(), token_out)
                    
                    if token_in_addr and token_out_addr:
                        try:
                            # Get real mainnet pricing via router
                            amounts_out = mainnet_router.functions.getAmountsOut(
                                int(amount_in * 10**6),  # USDC has 6 decimals
                                [Web3.to_checksum_address(token_in_addr), 
                                 Web3.to_checksum_address(token_out_addr)]
                            ).call()
                            
                            amount_out_wei = amounts_out[-1]
                            # Most tokens have 18 decimals
                            amount_out_readable = amount_out_wei / (10**18)
                            rate = amount_out_readable / amount_in
                            
                            result = {
                                "amount_in": amount_in,
                                "amount_out_estimated": amount_out_readable,
                                "amount_out_min_with_slippage": amount_out_readable * 0.99,
                                "fee_percent": 0.3,
                                "exchange_rate": rate,
                                "note": "Real mainnet pricing (mock transaction - testnet)"
                            }
                            
                            print(f"   ✅ Real mainnet price: {amount_out_readable:.2f}")
                            return result
                        except Exception as e:
                            print(f"   ⚠️  Mainnet price fetch failed: {e}")
                
                # Fallback to estimated rates if mainnet lookup fails
                print(f"   ℹ️  Using hardcoded testnet rates (Mock DEX)")
                # HARDCODED RATES FROM MOCK DEX: 1 USDC = 55 VVS
                estimated_rates = {
                    ("usdc", "vvs"): 55.0,   # Mock DEX hardcoded rate
                    ("vvs", "usdc"): 1/55.0,
                    ("cro", "usdc"): 0.12,
                    ("usdc", "cro"): 8.33,
                    ("wcro", "usdc"): 0.15,
                    ("usdc", "wcro"): 6.67,
                }
                
                key = (token_in.lower(), token_out.lower())
                rate = estimated_rates.get(key, 1.0)
                amount_out_readable = amount_in * rate
                
                result = {
                    "amount_in": amount_in,
                    "amount_out_estimated": amount_out_readable,
                    "amount_out_min_with_slippage": amount_out_readable * 0.99,
                    "fee_percent": 0.3,
                    "exchange_rate": rate,
                    "note": "Estimated mainnet pricing (mock transaction - testnet)"
                }
                
                print(f"   ✅ Estimated mainnet price: {amount_out_readable:.2f}")
                return result
                
            except Exception as e:
                print(f"   ❌ Pricing error: {e}")
                return {"error": f"Could not estimate price: {e}"}
        
        # Real mainnet swap estimation
        router = w3.eth.contract(address=Web3.to_checksum_address(VVS_ROUTER), abi=ROUTER_ABI)
        
        # Get token decimals
        if token_in_addr.lower() == "cro":
            decimals_in = 18
            amount_in_wei = int(amount_in * (10 ** decimals_in))
        else:
            token_contract = w3.eth.contract(address=token_in_addr, abi=ERC20_ABI)
            decimals_in = token_contract.functions.decimals().call()
            amount_in_wei = int(amount_in * (10 ** decimals_in))
        
        if token_out_addr.lower() == "cro":
            decimals_out = 18
        else:
            token_contract = w3.eth.contract(address=token_out_addr, abi=ERC20_ABI)
            decimals_out = token_contract.functions.decimals().call()
        
        # Build path (use WCRO as intermediary if needed)
        if token_in_addr.lower() == "cro":
            path = [WCRO_ADDRESS, token_out_addr]
        elif token_out_addr.lower() == "cro":
            path = [token_in_addr, WCRO_ADDRESS]
        else:
            path = [token_in_addr, token_out_addr]
        
        # Call getAmountsOut
        amounts = router.functions.getAmountsOut(amount_in_wei, path).call()
        amount_out_wei = amounts[-1]
        amount_out_readable = amount_out_wei / (10 ** decimals_out)
        
        # Calculate price impact (simplified)
        price_impact = 0.3  # VVS standard 0.3% fee
        
        result = {
            "amount_in": amount_in,
            "amount_out_estimated": amount_out_readable,
            "amount_out_min_with_slippage": amount_out_readable * 0.99,  # 1% slippage
            "fee_percent": price_impact,
            "exchange_rate": amount_out_readable / amount_in,
            "note": "1% slippage buffer applied for safety"
        }
        
        print(f"   ✅ Estimated output: {amount_out_readable:.6f}")
        return result
        
    except Exception as e:
        error_msg = str(e)
        print(f"   ❌ Error: {error_msg}")
        return {"error": error_msg}


@tool
def execute_vvs_swap(token_in: str, token_out: str, amount_in: float, max_slippage: float = 1.0, chain: str = "cronos_testnet"):
    """Execute token swap on VVS Finance."""
    print(f"\n🔄 Initiating VVS Swap: {amount_in} {token_in}... → {token_out}...")
    
    try:
        # 1. Resolve Addresses
        token_in_addr = resolve_token_address(token_in)
        token_out_addr = resolve_token_address(token_out)
        
        if not token_in_addr or not token_out_addr:
            return {"error": f"Cannot resolve token addresses: {token_in} or {token_out}"}
        
        # Load WCRO Address (Required for path routing)
        WCRO_ACTUAL = Web3.to_checksum_address(WCRO_ADDRESS)
        
        # 2. Setup Web3
        rpc_url = CRONOS_RPC_URL
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        if not w3.is_connected():
            return {"error": "Could not connect to RPC"}
        
        private_key = os.getenv("WALLET_PRIVATE_KEY")
        if not private_key:
            return {"error": "WALLET_PRIVATE_KEY not set"}
        
        account = w3.eth.account.from_key(private_key)
        my_address = account.address
        
        print(f"   👤 Wallet: {my_address}")
        
        ROUTER_ADDRESS = Web3.to_checksum_address(VVS_ROUTER)
        
        # 3. Only check allowance, do not approve yet
        if token_in_addr != "cro":
            token_contract = w3.eth.contract(address=token_in_addr, abi=ERC20_ABI)
            decimals = token_contract.functions.decimals().call()
            amount_in_wei = int(amount_in * (10 ** decimals))
            allowance = token_contract.functions.allowance(my_address, ROUTER_ADDRESS).call()
            if allowance < amount_in_wei:
                print(f"   ⚠️  Insufficient allowance. Please approve after swap confirmation.")
                return {"error": "Insufficient allowance. Approve after swap confirmation."}
        else:
            amount_in_wei = w3.to_wei(amount_in, 'ether')

        # 4. Prepare Swap Path
        # CRITICAL FIX: The router 'path' must strictly contain ADDRESSES.
        # If input/output is 'cro', use WCRO address in the path.
        path_in = WCRO_ACTUAL if token_in_addr == "cro" else token_in_addr
        path_out = WCRO_ACTUAL if token_out_addr == "cro" else token_out_addr
        
        path = [path_in, path_out]
        path_display = [token_in[:10], token_out[:10]]
        
        # 5. Get current gas price and nonce
        try:
            gas_price = w3.eth.gas_price
        except:
            gas_price = w3.to_wei(5, 'gwei')
        
        try:
            nonce = w3.eth.get_transaction_count(my_address)
        except:
            nonce = 0
        
        # 6. Execute Swap
        router = w3.eth.contract(address=ROUTER_ADDRESS, abi=ROUTER_ABI)
        deadline = int(time.time()) + 900
        
        print(f"   📊 Path: {' → '.join(path_display)}")

        # IMPORTANT: Mock router only supports swapExactTokensForTokens
        # All paths must use token addresses (WCRO for native CRO)
        amounts = router.functions.getAmountsOut(amount_in_wei, path).call()
        amount_out_min = int(amounts[-1] * (1 - max_slippage/100))
        
        # Get decimals for output display
        if token_out_addr == "cro":
            decimals_out = 18
            token_display = "WCRO (wraps to CRO)"
        else:
            try:
                token_out_contract = w3.eth.contract(address=path_out, abi=ERC20_ABI)
                decimals_out = token_out_contract.functions.decimals().call()
            except:
                decimals_out = 6
            token_display = token_out
        
        print(f"   💹 Expected: {amounts[-1] / (10 ** decimals_out):.6f} {token_display}")
        print(f"   🛡️  Minimum ({max_slippage}% slippage): {amount_out_min / (10 ** decimals_out):.6f} {token_display}")
        
        # Always use swapExactTokensForTokens (mock router only supports this)
        swap_tx = router.functions.swapExactTokensForTokens(
            amount_in_wei,
            amount_out_min,
            path,
            my_address,
            deadline
        ).build_transaction({
            'from': my_address,
            'gas': 300000,
            'gasPrice': gas_price,
            'nonce': nonce
        })

        # Sign & Send
        print(f"   🚀 Sending swap transaction on Cronos Testnet...")
        signed_swap = w3.eth.account.sign_transaction(swap_tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_swap.raw_transaction)
        tx_hash_hex = tx_hash.hex()
        
        print(f"   ✅ Swap submitted!")
        print(f"      Hash: {tx_hash_hex[:30]}...")
        print(f"      ⏳ Waiting for confirmation...")
        
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
        
        if receipt['status'] == 1:
            tx_info = w3.eth.get_transaction(tx_hash)
            gas_cost = receipt['gasUsed'] * tx_info['gasPrice'] / (10 ** 18)
            print(f"   ✅ Swap confirmed!")
            print(f"      Block: {receipt['blockNumber']}")
            print(f"      Gas cost: {gas_cost:.6f} CRO")
            # Now, if approval is needed, do it after swap confirmation
            if token_in_addr != "cro":
                try:
                    print(f"   🔐 Approving Router after swap confirmation...")
                    approve_nonce = w3.eth.get_transaction_count(my_address)
                    approve_tx = token_contract.functions.approve(ROUTER_ADDRESS, 2**256 - 1).build_transaction({
                        'from': my_address,
                        'nonce': approve_nonce,
                        'gas': 100000,
                        'gasPrice': gas_price
                    })
                    signed_approve = w3.eth.account.sign_transaction(approve_tx, private_key)
                    approve_hash = w3.eth.send_raw_transaction(signed_approve.raw_transaction)
                    print(f"   ⏳ Approval tx: {approve_hash.hex()[:20]}...")
                    approve_receipt = w3.eth.wait_for_transaction_receipt(approve_hash, timeout=120)
                    if approve_receipt['status'] == 1:
                        print("   ✅ Approved after swap.")
                    else:
                        print("   ❌ Approval failed after swap.")
                except Exception as e:
                    print(f"   ⚠️  Approval after swap failed: {str(e)}")
            return {
                "status": "success",
                "mode": "cronos_testnet_mock_router",
                "tx_hash": tx_hash_hex,
                "block_number": receipt['blockNumber'],
                "amount_in": amount_in,
                "path": path_display,
                "explorer": f"https://testnet.cronoscan.com/tx/{tx_hash_hex}"
            }
        else:
            return {"error": "Swap transaction failed on-chain", "tx_hash": tx_hash_hex}
        
    except Exception as e:
        import traceback
        error_msg = str(e)
        print(f"   ❌ Error: {error_msg}")
        traceback.print_exc()
        return {"error": error_msg}


@tool
def get_trading_signals(server_url: str = None):
    """
    Fetch trading signals (BUY/SELL) from server.
    """
    if server_url is None:
        server_url = TRADING_SIGNALS_URL
    
    print(f"\n📊 Fetching trading signals from {server_url}...")
    
    try:
        response = requests.get(f"{server_url}/trading/signals", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Found {data.get('count', 0)} active signals")
            return data
        else:
            print(f"   ⚠️  Signal server returned HTTP {response.status_code}, using fallback")
            return {
                "count": 0,
                "signals": [],
                "note": "Fallback: signal server unavailable"
            }
    
    except Exception as e:
        print(f"   ⚠️  Signal fetch error: {e}, using fallback")
        return {
            "count": 0,
            "signals": [],
            "note": "Fallback: signal server unreachable"
        }


@tool
def get_buy_alpha(server_url: str = None):
    """
    Get actionable BUY signals from /buy-alpha endpoint.
    """
    if server_url is None:
        server_url = TRADING_SIGNALS_URL
    
    print(f"\n💰 Checking for BUY opportunities...")
    
    try:
        response = requests.get(f"{server_url}/buy-alpha", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'signals' in data and len(data['signals']) > 0:
                print(f"   ✅ Found {len(data['signals'])} BUY signals!")
                for signal in data['signals']:
                    print(f"      • {signal['ticker']}: {signal.get('amount_usdc', 'N/A')} USDC ({signal.get('confidence', 0)*100:.0f}% confidence)")
            else:
                print(f"   ℹ️  No BUY signals at this time")
            
            return data
        else:
            print(f"   ⚠️  BUY alpha server returned HTTP {response.status_code}, using fallback")
            return {
                "signals": [],
                "note": "Fallback: buy-alpha server unavailable"
            }
    
    except Exception as e:
        print(f"   ⚠️  BUY alpha fetch error: {e}, using fallback")
        return {
            "signals": [],
            "note": "Fallback: buy-alpha server unreachable"
        }


@tool
def record_trade(ticker: str, action: str, amount: float, tx_hash: str = None, status: str = "success", server_url: str = None):
    """
    Record a completed trade to server.
    """
    if server_url is None:
        server_url = TRADING_SIGNALS_URL
    
    print(f"\n📝 Recording trade: {action} {amount} {ticker}...")
    
    try:
        payload = {
            "ticker": ticker.upper(),
            "action": action.upper(),
            "amount": amount,
            "tx_hash": tx_hash,
            "status": status
        }
        
        response = requests.post(
            f"{server_url}/portfolio/trade",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"   ✅ Trade recorded successfully")
            return response.json()
        else:
            return {"error": f"Failed to record trade: HTTP {response.status_code}"}
    
    except Exception as e:
        return {"error": str(e)}


@tool
def get_trade_history(limit: int = 10, server_url: str = None):
    """
    Get recent trade history.
    """
    if server_url is None:
        server_url = TRADING_SIGNALS_URL
    
    print(f"\n📜 Fetching last {limit} trades...")
    
    try:
        response = requests.get(
            f"{server_url}/portfolio/trades?limit={limit}",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Retrieved {len(data.get('trades', []))} trades")
            return data
        else:
            return {"error": f"Failed to fetch trade history: HTTP {response.status_code}"}
    
    except Exception as e:
        return {"error": str(e)}


@tool
def get_portfolio_value(wallet_address: str = None, server_url: str = None):
    """
    Get current portfolio value.
    """
    if server_url is None:
        server_url = TRADING_SIGNALS_URL
    
    print(f"\n💼 Fetching portfolio value...")
    
    try:
        # Validate and use agent's wallet if not provided or invalid
        if not wallet_address or not wallet_address.startswith('0x') or len(wallet_address) != 42 or wallet_address == '0x123...':
            private_key = os.getenv("WALLET_PRIVATE_KEY")
            if private_key:
                account = Account.from_key(private_key)
                wallet_address = account.address
            else:
                return {"error": "No wallet address provided and WALLET_PRIVATE_KEY not set"}
        
        response = requests.get(
            f"{server_url}/portfolio/value?address={wallet_address}",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            total_value = data.get('total_value_usd', 0)
            print(f"   ✅ Portfolio value: ${total_value:.2f}")
            return data
        else:
            print(f"   ⚠️  Portfolio server returned HTTP {response.status_code}, using fallback")
            # Fallback: compute rough value from on-chain balances with fixed prices
            return _fallback_portfolio(wallet_address)
    
    except Exception as e:
        print(f"   ⚠️  Portfolio fetch error: {e}, using fallback")
        return _fallback_portfolio(wallet_address)


def _fallback_portfolio(wallet_address: str):
    """Fallback portfolio estimation using on-chain balances and fixed prices."""
    try:
        rpc_url = os.getenv("CRONOS_RPC_URL", "https://evm-t3.cronos.org")
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not w3.is_connected():
            return {"error": "RPC unavailable for fallback"}
        # Prices (mock): USDC=$1, VVS=$0.018, CRO=$0.09
        price_usdc = 1.0
        price_vvs = 0.018
        price_cro = 0.09
        # CRO balance
        cro_wei = w3.eth.get_balance(wallet_address)
        cro = w3.from_wei(cro_wei, 'ether')
        cro_usd = float(cro) * price_cro
        # USDC balance
        usdc_addr = Web3.to_checksum_address(os.getenv("USDC_CONTRACT", USDC_CONTRACT))
        usdc_contract = w3.eth.contract(address=usdc_addr, abi=ERC20_ABI)
        usdc_raw = usdc_contract.functions.balanceOf(wallet_address).call()
        usdc = usdc_raw / (10 ** usdc_contract.functions.decimals().call())
        usdc_usd = usdc * price_usdc
        # VVS balance
        vvs_addr = Web3.to_checksum_address(os.getenv("VVS_CONTRACT", VVS_CONTRACT))
        vvs_contract = w3.eth.contract(address=vvs_addr, abi=ERC20_ABI)
        vvs_raw = vvs_contract.functions.balanceOf(wallet_address).call()
        vvs = vvs_raw / (10 ** vvs_contract.functions.decimals().call())
        vvs_usd = vvs * price_vvs
        total = cro_usd + usdc_usd + vvs_usd
        print(f"   ℹ️  Fallback portfolio: CRO ${cro_usd:.2f}, USDC ${usdc_usd:.2f}, VVS ${vvs_usd:.2f}")
        return {
            "address": wallet_address,
            "total_value_usd": total,
            "positions": {
                "CRO": {"amount": float(cro), "value_usd": cro_usd},
                "USDC": {"amount": usdc, "value_usd": usdc_usd},
                "VVS": {"amount": vvs, "value_usd": vvs_usd},
            },
            "note": "Fallback: portfolio service unavailable"
        }
    except Exception as e:
        return {"error": f"Fallback portfolio failed: {e}"}
