#!/usr/bin/env python3
"""Real swap test on Cronos testnet using SilverSwap"""

from pathlib import Path
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv
import os
import json
import time

# Load environment
load_dotenv(Path(__file__).parent / '.env')

# Setup Web3
w3 = Web3(Web3.HTTPProvider(os.getenv('CRONOS_RPC_URL')))
private_key = os.getenv('WALLET_PRIVATE_KEY')
account = Account.from_key(private_key)

print("="*70)
print("EXECUTING 1 USDC → WTCRO SWAP ON SILVERSWAP TESTNET")
print("="*70)
print(f"Wallet: {account.address}")
print(f"Chain: {w3.eth.chain_id}")

# Contract addresses
USDC = w3.to_checksum_address(os.getenv('USDC_CONTRACT'))
ROUTER = w3.to_checksum_address(os.getenv('VVS_ROUTER'))  # Actually SilverSwap now
WTCRO = w3.to_checksum_address(os.getenv('WCRO_ADDRESS'))

print(f"\nContracts:")
print(f"  USDC: {USDC}")
print(f"  Router: {ROUTER}")
print(f"  WTCRO: {WTCRO}")

# ABIs
ERC20_ABI = json.loads('[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"},{"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"},{"constant":false,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"type":"function"},{"constant":true,"inputs":[{"name":"_owner","type":"address"},{"name":"_spender","type":"address"}],"name":"allowance","outputs":[{"name":"","type":"uint256"}],"type":"function"}]')

ROUTER_ABI = json.loads('[{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"}],"name":"getAmountsOut","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactTokensForTokens","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"nonpayable","type":"function"}]')

# Create contract instances
usdc = w3.eth.contract(address=USDC, abi=ERC20_ABI)
router = w3.eth.contract(address=ROUTER, abi=ROUTER_ABI)

# Check balance
decimals = usdc.functions.decimals().call()
balance = usdc.functions.balanceOf(account.address).call()
print(f"\n✅ USDC Balance: {balance / 10**decimals:.6f} USDC")

if balance < 1 * 10**decimals:
    print("❌ Insufficient USDC balance")
    exit(1)

amount_in = 1 * 10**decimals  # 1 USDC

# Check allowance
allowance = usdc.functions.allowance(account.address, ROUTER).call()
print(f"Current allowance: {allowance / 10**decimals:.6f} USDC")

# Step 1: Approve if needed
if allowance < amount_in:
    print("\n📝 Step 1: Approving USDC...")
    try:
        approve_tx = usdc.functions.approve(ROUTER, amount_in).build_transaction({
            'from': account.address,
            'gas': 100000,
            'gasPrice': w3.eth.gas_price,
            'nonce': w3.eth.get_transaction_count(account.address),
            'chainId': w3.eth.chain_id
        })
        signed = account.sign_transaction(approve_tx)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        print(f"Approval TX: {tx_hash.hex()}")
        print(f"Waiting for confirmation...")
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
        if receipt['status'] == 1:
            print(f"✅ Approved! Block: {receipt['blockNumber']}")
        else:
            print("❌ Approval failed")
            exit(1)
        time.sleep(2)  # Wait a bit before next tx
    except Exception as e:
        print(f"❌ Approval error: {e}")
        exit(1)
else:
    print("\n✅ Already approved")

# Step 2: Get expected output
print("\n📊 Step 2: Estimating swap output...")
try:
    path = [USDC, WTCRO]
    amounts_out = router.functions.getAmountsOut(amount_in, path).call()
    expected_wtcro = amounts_out[1]
    print(f"Expected output: {w3.from_wei(expected_wtcro, 'ether'):.6f} WTCRO")
    print(f"Price: 1 USDC = {w3.from_wei(expected_wtcro, 'ether'):.6f} WTCRO")
except Exception as e:
    print(f"❌ Estimation error: {e}")
    print("The USDC/WTCRO pair may not have liquidity on testnet")
    exit(1)

# Step 3: Execute swap
print("\n🔄 Step 3: Executing swap...")
try:
    min_out = int(expected_wtcro * 0.95)  # 5% slippage tolerance
    deadline = w3.eth.get_block('latest')['timestamp'] + 600  # 10 min
    
    print(f"Min output (5% slippage): {w3.from_wei(min_out, 'ether'):.6f} WTCRO")
    print(f"Deadline: {deadline}")
    
    swap_tx = router.functions.swapExactTokensForTokens(
        amount_in,
        min_out,
        path,
        account.address,
        deadline
    ).build_transaction({
        'from': account.address,
        'gas': 300000,
        'gasPrice': w3.eth.gas_price,
        'nonce': w3.eth.get_transaction_count(account.address),
        'chainId': w3.eth.chain_id
    })
    
    signed = account.sign_transaction(swap_tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    print(f"\n🚀 Swap TX: {tx_hash.hex()}")
    print(f"🔗 Explorer: https://explorer.cronos.org/testnet/tx/{tx_hash.hex()}")
    print(f"Waiting for confirmation...")
    
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    
    print(f"\n{'='*70}")
    if receipt['status'] == 1:
        print("✅ SWAP SUCCESSFUL!")
        print(f"Gas used: {receipt['gasUsed']:,}")
        print(f"Block: {receipt['blockNumber']}")
        
        # Check new balances
        time.sleep(2)
        new_usdc = usdc.functions.balanceOf(account.address).call()
        wtcro_contract = w3.eth.contract(address=WTCRO, abi=ERC20_ABI)
        wtcro_balance = wtcro_contract.functions.balanceOf(account.address).call()
        
        print(f"\n📊 Final Balances:")
        print(f"USDC: {new_usdc / 10**decimals:.6f} USDC (spent: {(balance - new_usdc) / 10**decimals:.6f})")
        print(f"WTCRO: {w3.from_wei(wtcro_balance, 'ether'):.6f} WTCRO")
        
        print(f"\n🎉 SUCCESS! You swapped 1 USDC for {w3.from_wei(wtcro_balance, 'ether'):.6f} WTCRO")
    else:
        print("❌ SWAP FAILED")
        print(f"Transaction reverted")
    print("="*70)
    
except Exception as e:
    print(f"❌ Swap error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
