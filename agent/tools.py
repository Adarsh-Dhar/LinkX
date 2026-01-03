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
USDC_CONTRACT = os.getenv("USDC_CONTRACT", "0xc01efAaF7C5C61bEbFAeb358E1161b537b8bC0e0")
VVS_CONTRACT = os.getenv("VVS_CONTRACT", "0x5f307095E713b3eF9D0f49e4f8b0b98A7b5b8fF0")
VVS_ROUTER = os.getenv("VVS_ROUTER", "0x145677FC4d9b8F19B4172A2b88f7fb1f02fdf220")
WCRO_ADDRESS = os.getenv("WCRO_ADDRESS", "0x5C7F8A570d578ED84E63fdFA7b1eE72dEae1AE23")

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

@tool
def get_token_balance(token_address: str, chain: str = "cronos_mainnet"):
    """
    Retrieves the token balance of the agent's wallet.
    
    Args:
        token_address: Address of the token contract (or 'CRO' for native token)
        chain: 'cronos_mainnet' or 'cronos_testnet'
    
    Returns:
        dict: Token balance information
    """
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
    """
    Estimates the expected output of a swap without executing it.
    
    This helps the agent understand slippage and fair pricing.
    
    Args:
        token_in: Symbol (USDC, VVS, CRO) or address of input token
        token_out: Symbol (USDC, VVS, CRO) or address of output token
        amount_in: Amount of token_in to swap (human readable)
        chain: 'cronos_mainnet' or 'cronos_testnet'
    
    Returns:
        dict: Estimated output amount and price impact
    """
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
def execute_vvs_swap(token_in: str, token_out: str, amount_in: float, max_slippage: float = 1.0, chain: str = "cronos_mainnet"):
    """
    Executes a token swap on VVS Finance (Uniswap V2 fork).
    Automatically handles token approval if required.
    
    Args:
        token_in: Symbol (USDC, VVS, CRO) or address of token to sell
        token_out: Symbol (USDC, VVS, CRO) or address of token to buy
        amount_in: Amount of token_in to swap (in human readable units)
        max_slippage: Maximum acceptable slippage as percentage (default 1.0%)
        chain: 'cronos_mainnet' or 'cronos_testnet'
    
    Returns:
        dict: Swap confirmation with transaction hash and final amounts
    """
    print(f"\n🔄 Initiating VVS Swap: {amount_in} {token_in}... → {token_out}...")
    
    try:
        # Resolve token addresses
        token_in_addr = resolve_token_address(token_in)
        token_out_addr = resolve_token_address(token_out)
        
        if not token_in_addr or not token_out_addr:
            return {"error": f"Cannot resolve token addresses: {token_in} or {token_out}"}
        
        # 1. Setup Web3
        rpc_url = CRONOS_RPC_URL
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        # Optional: Add PoA middleware if available (Cronos is EVM-compatible, so not required)
        if HAS_POA_MIDDLEWARE:
            w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        
        if not w3.is_connected():
            return {"error": "Could not connect to RPC"}
        
        # Load Account
        private_key = os.getenv("WALLET_PRIVATE_KEY")
        if not private_key:
            return {"error": "WALLET_PRIVATE_KEY not set"}
        
        account = w3.eth.account.from_key(private_key)
        my_address = account.address
        
        print(f"   👤 Wallet: {my_address}")
        
        # Load Router Address from .env
        ROUTER_ADDRESS = Web3.to_checksum_address(VVS_ROUTER)
        WCRO_ADDRESS_LOCAL = Web3.to_checksum_address(WCRO_ADDRESS)
        
        # 2. Handle Token Approval (If not selling CRO)
        if token_in_addr.lower() != "cro":
            token_contract = w3.eth.contract(address=token_in_addr, abi=ERC20_ABI)
            decimals = token_contract.functions.decimals().call()
            amount_in_wei = int(amount_in * (10 ** decimals))
            
            # Check Allowance
            allowance = token_contract.functions.allowance(my_address, ROUTER_ADDRESS).call()
            print(f"   ℹ️  Current Allowance: {allowance / (10 ** decimals):.6f}")
            
            if allowance < amount_in_wei:
                print(f"   🔐 Approving Router to spend tokens...")
                approve_tx = token_contract.functions.approve(ROUTER_ADDRESS, 2**256 - 1).build_transaction({
                    'from': my_address,
                    'nonce': w3.eth.get_transaction_count(my_address),
                    'gas': 100000,
                    'gasPrice': w3.eth.gas_price
                })
                signed_app = w3.eth.account.sign_transaction(approve_tx, private_key)
                tx_hash = w3.eth.send_raw_transaction(signed_app.raw_transaction)
                print(f"   ⏳ Approval tx: {tx_hash.hex()[:20]}... (waiting for confirmation)")
                
                try:
                    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
                    if receipt['status'] == 1:
                        print(f"   ✅ Token approval confirmed!")
                    else:
                        return {"error": "Token approval transaction failed"}
                except Exception as e:
                    print(f"   ⚠️  Approval confirmation timeout: {str(e)}")
        else:
            amount_in_wei = w3.to_wei(amount_in, 'ether')

        # 3. Estimate output and get slippage-protected minimum
        router = w3.eth.contract(address=ROUTER_ADDRESS, abi=ROUTER_ABI)
        
        # Determine path
        if token_in_addr.lower() == "cro":
            path = [WCRO_ADDRESS_LOCAL, token_out_addr]
            path_display = ["WCRO", token_out[:10]]
        elif token_out_addr.lower() == "cro":
            path = [token_in_addr, WCRO_ADDRESS_LOCAL]
            path_display = [token_in[:10], "WCRO"]
        else:
            path = [token_in_addr, token_out_addr]
            path_display = [token_in[:10], token_out[:10]]
        
        # Get amounts out
        amounts = router.functions.getAmountsOut(amount_in_wei, path).call()
        amount_out_min_wei = int(amounts[-1] * (1 - max_slippage / 100))
        
        # Get decimals for output
        if token_out_addr.lower() == "cro":
            decimals_out = 18
        else:
            token_out_contract = w3.eth.contract(address=token_out_addr, abi=ERC20_ABI)
            decimals_out = token_out_contract.functions.decimals().call()
        
        amount_out_expected = amounts[-1] / (10 ** decimals_out)
        amount_out_min = amount_out_min_wei / (10 ** decimals_out)
        
        print(f"   📊 Path: {' → '.join(path_display)}")
        print(f"   💹 Expected: {amount_out_expected:.6f}")
        print(f"   🛡️  Minimum ({max_slippage}% slippage): {amount_out_min:.6f}")
        
        # 4. Execute Swap
        deadline = int(time.time()) + 300  # 5 minute deadline
        
        print(f"   🚀 Sending swap transaction...")
        
        # Determine swap function based on inputs/outputs
        if token_in_addr.lower() == "cro":
            # swapExactETHForTokens
            swap_tx = router.functions.swapExactETHForTokens(
                amount_out_min_wei,
                path,
                my_address,
                deadline
            ).build_transaction({
                'from': my_address,
                'value': amount_in_wei,
                'gas': 300000,
                'gasPrice': w3.eth.gas_price,
                'nonce': w3.eth.get_transaction_count(my_address)
            })
        elif token_out_addr.lower() == "cro":
            # swapExactTokensForETH
            swap_tx = router.functions.swapExactTokensForETH(
                amount_in_wei,
                amount_out_min_wei,
                path,
                my_address,
                deadline
            ).build_transaction({
                'from': my_address,
                'gas': 300000,
                'gasPrice': w3.eth.gas_price,
                'nonce': w3.eth.get_transaction_count(my_address)
            })
        else:
            # swapExactTokensForTokens
            swap_tx = router.functions.swapExactTokensForTokens(
                amount_in_wei,
                amount_out_min_wei,
                path,
                my_address,
                deadline
            ).build_transaction({
                'from': my_address,
                'gas': 300000,
                'gasPrice': w3.eth.gas_price,
                'nonce': w3.eth.get_transaction_count(my_address)
            })

        # Sign and broadcast
        signed_swap = w3.eth.account.sign_transaction(swap_tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_swap.raw_transaction)
        tx_hash_hex = tx_hash.hex()
        
        print(f"   ✅ Swap submitted!")
        print(f"      Hash: {tx_hash_hex[:30]}...")
        print(f"      ⏳ Waiting for confirmation...")
        
        # Wait for confirmation
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
        
        if receipt['status'] == 1:
            gas_cost = receipt['gasUsed'] * receipt['gasPrice'] / (10 ** 18)
            print(f"   ✅ Swap confirmed!")
            print(f"      Block: {receipt['blockNumber']}")
            print(f"      Gas cost: {gas_cost:.6f} CRO")
            
            return {
                "status": "success",
                "tx_hash": tx_hash_hex,
                "block_number": receipt['blockNumber'],
                "amount_in": amount_in,
                "amount_out_expected": amount_out_expected,
                "amount_out_minimum": amount_out_min,
                "gas_cost_cro": gas_cost,
                "path": path_display,
                "explorer": f"https://cronoscan.com/tx/{tx_hash_hex}"
            }
        else:
            return {"error": "Swap transaction failed on-chain", "tx_hash": tx_hash_hex}
        
    except Exception as e:
        error_msg = str(e)
        print(f"   ❌ Error: {error_msg}")
        return {"error": error_msg}


@tool
def get_trading_signals(server_url: str = None):
    """
    Fetches active trading signals from the analyst server.
    
    Returns BUY/SELL signals with confidence levels and reasoning.
    
    Args:
        server_url: Base URL of the analyst server (uses TRADING_SIGNALS_URL from .env if not provided)
    
    Returns:
        dict: Trading signals with recommendations
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
            return {"error": f"Failed to fetch signals: HTTP {response.status_code}"}
    
    except Exception as e:
        return {"error": str(e)}


@tool
def get_buy_alpha(server_url: str = None):
    """
    Gets actionable BUY signals from the free /buy-alpha endpoint.
    
    This is a convenience tool for quickly checking if there are any
    tokens to buy right now without needing to pay.
    
    Args:
        server_url: Base URL of the analyst server (uses TRADING_SIGNALS_URL from .env if not provided)
    
    Returns:
        dict: BUY signals ready for execution
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
            return {"error": f"Failed to fetch BUY signals: HTTP {response.status_code}"}
    
    except Exception as e:
        return {"error": str(e)}


@tool
def record_trade(ticker: str, action: str, amount: float, tx_hash: str = None, status: str = "success", server_url: str = None):
    """
    Records a completed trade to the server for tracking and analytics.
    
    Args:
        ticker: Token symbol (e.g., "VVS", "CRO")
        action: Trade action ("BUY" or "SELL")
        amount: Amount traded (in USDC or token units)
        tx_hash: Transaction hash (optional)
        status: Trade status ("success", "failed", "pending")
        server_url: Base URL of the analyst server (uses TRADING_SIGNALS_URL from .env if not provided)
    
    Returns:
        dict: Confirmation of recorded trade
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
    Retrieves recent trade history from the server.
    
    Args:
        limit: Number of recent trades to fetch (default: 10)
        server_url: Base URL of the analyst server (uses TRADING_SIGNALS_URL from .env if not provided)
    
    Returns:
        dict: Recent trades with details
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
    Gets the current portfolio value for the agent's wallet.
    
    Args:
        wallet_address: Leave empty to use agent's wallet (recommended). Do not provide placeholder addresses.
        server_url: Base URL of the analyst server (uses TRADING_SIGNALS_URL from .env if not provided)
    
    Returns:
        dict: Portfolio balances and total value
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
            return {"error": f"Failed to fetch portfolio value: HTTP {response.status_code}"}
    
    except Exception as e:
        return {"error": str(e)}
