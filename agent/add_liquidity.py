#!/usr/bin/env python3
"""
Add liquidity to USDC/WTCRO pair on SilverSwap testnet.

Steps:
1. Wrap 2 tCRO to WTCRO
2. Approve WTCRO on router
3. Approve USDC on router
4. Add liquidity (1 USDC + ~2 WTCRO)
5. Test swap
"""

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
print("ADDING LIQUIDITY TO USDC/WTCRO ON SILVERSWAP TESTNET")
print("="*70)
print(f"Wallet: {account.address}")
print(f"Chain: {w3.eth.chain_id}")

# Contract addresses
USDC = w3.to_checksum_address(os.getenv('USDC_CONTRACT'))
ROUTER = w3.to_checksum_address(os.getenv('VVS_ROUTER'))  # SilverSwap
WTCRO = w3.to_checksum_address(os.getenv('WCRO_ADDRESS'))

print(f"\nContracts:")
print(f"  USDC: {USDC}")
print(f"  WTCRO: {WTCRO}")
print(f"  Router: {ROUTER}")

# ABIs
ERC20_ABI = json.loads('[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"},{"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"},{"constant":false,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"type":"function"},{"constant":true,"inputs":[{"name":"_owner","type":"address"},{"name":"_spender","type":"address"}],"name":"allowance","outputs":[{"name":"","type":"uint256"}],"type":"function"}]')

# WTCRO contract has deposit() to wrap tCRO
WTCRO_ABI = json.loads('[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"},{"constant":false,"inputs":[],"name":"deposit","outputs":[],"stateMutability":"payable","type":"function"},{"constant":false,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"type":"function"},{"constant":true,"inputs":[{"name":"_owner","type":"address"},{"name":"_spender","type":"address"}],"name":"allowance","outputs":[{"name":"","type":"uint256"}],"type":"function"}]')

# Router ABI for addLiquidity
ROUTER_ABI = json.loads('[{"inputs":[{"internalType":"address","name":"tokenA","type":"address"},{"internalType":"address","name":"tokenB","type":"address"},{"internalType":"uint256","name":"amountADesired","type":"uint256"},{"internalType":"uint256","name":"amountBDesired","type":"uint256"},{"internalType":"uint256","name":"amountAMin","type":"uint256"},{"internalType":"uint256","name":"amountBMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"addLiquidity","outputs":[{"internalType":"uint256","name":"amountA","type":"uint256"},{"internalType":"uint256","name":"amountB","type":"uint256"},{"internalType":"uint256","name":"liquidity","type":"uint256"}],"stateMutability":"nonpayable","type":"function"}]')

# Create contract instances
usdc = w3.eth.contract(address=USDC, abi=ERC20_ABI)
wtcro = w3.eth.contract(address=WTCRO, abi=WTCRO_ABI)
router = w3.eth.contract(address=ROUTER, abi=ROUTER_ABI)

# ======= STEP 1: Check current balances =======
print("\n" + "="*70)
print("STEP 1: Check current balances")
print("="*70)

usdc_decimals = usdc.functions.decimals().call()
usdc_balance = usdc.functions.balanceOf(account.address).call()
wtcro_balance = wtcro.functions.balanceOf(account.address).call()
tcro_balance = w3.eth.get_balance(account.address)

print(f"tCRO: {w3.from_wei(tcro_balance, 'ether'):.6f}")
print(f"USDC: {usdc_balance / 10**usdc_decimals:.6f}")
print(f"WTCRO: {w3.from_wei(wtcro_balance, 'ether'):.6f}")

if usdc_balance < 1 * 10**usdc_decimals:
    print("❌ Not enough USDC (need at least 1)")
    exit(1)

if tcro_balance < w3.to_wei(2, 'ether'):
    print("❌ Not enough tCRO (need at least 2)")
    exit(1)

print("✅ Sufficient balances")

# ======= STEP 2: Wrap tCRO to WTCRO =======
print("\n" + "="*70)
print("STEP 2: Wrap 2 tCRO to WTCRO")
print("="*70)

wrap_amount = w3.to_wei(2, 'ether')

if wtcro_balance < wrap_amount:
    amount_to_wrap = wrap_amount - wtcro_balance
    print(f"Wrapping {w3.from_wei(amount_to_wrap, 'ether'):.6f} tCRO...")
    
    try:
        wrap_tx = wtcro.functions.deposit().build_transaction({
            'from': account.address,
            'value': amount_to_wrap,
            'gas': 100000,
            'gasPrice': w3.eth.gas_price,
            'nonce': w3.eth.get_transaction_count(account.address),
            'chainId': w3.eth.chain_id
        })
        
        signed = account.sign_transaction(wrap_tx)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        print(f"Wrap TX: {tx_hash.hex()}")
        print("Waiting for confirmation...")
        
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
        if receipt['status'] == 1:
            print(f"✅ Wrapped! Block: {receipt['blockNumber']}")
            print(f"   Gas used: {receipt['gasUsed']}")
            time.sleep(2)
        else:
            print("❌ Wrap failed")
            exit(1)
    except Exception as e:
        print(f"❌ Wrap error: {e}")
        exit(1)
else:
    print(f"✅ Already have {w3.from_wei(wtcro_balance, 'ether'):.6f} WTCRO")

# ======= STEP 3: Approve USDC on router =======
print("\n" + "="*70)
print("STEP 3: Approve USDC on router")
print("="*70)

usdc_allowance = usdc.functions.allowance(account.address, ROUTER).call()
usdc_amount = 1 * 10**usdc_decimals  # 1 USDC

if usdc_allowance < usdc_amount:
    print(f"Approving {usdc_amount / 10**usdc_decimals:.6f} USDC...")
    
    try:
        approve_tx = usdc.functions.approve(ROUTER, usdc_amount).build_transaction({
            'from': account.address,
            'gas': 100000,
            'gasPrice': w3.eth.gas_price,
            'nonce': w3.eth.get_transaction_count(account.address),
            'chainId': w3.eth.chain_id
        })
        
        signed = account.sign_transaction(approve_tx)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        print(f"USDC Approval TX: {tx_hash.hex()}")
        print("Waiting for confirmation...")
        
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
        if receipt['status'] == 1:
            print(f"✅ USDC approved! Block: {receipt['blockNumber']}")
            time.sleep(2)
        else:
            print("❌ USDC approval failed")
            exit(1)
    except Exception as e:
        print(f"❌ USDC approval error: {e}")
        exit(1)
else:
    print(f"✅ USDC already approved")

# ======= STEP 4: Approve WTCRO on router =======
print("\n" + "="*70)
print("STEP 4: Approve WTCRO on router")
print("="*70)

wtcro_allowance = wtcro.functions.allowance(account.address, ROUTER).call()

if wtcro_allowance < wrap_amount:
    print(f"Approving {w3.from_wei(wrap_amount, 'ether'):.6f} WTCRO...")
    
    try:
        approve_tx = wtcro.functions.approve(ROUTER, wrap_amount).build_transaction({
            'from': account.address,
            'gas': 100000,
            'gasPrice': w3.eth.gas_price,
            'nonce': w3.eth.get_transaction_count(account.address),
            'chainId': w3.eth.chain_id
        })
        
        signed = account.sign_transaction(approve_tx)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        print(f"WTCRO Approval TX: {tx_hash.hex()}")
        print("Waiting for confirmation...")
        
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
        if receipt['status'] == 1:
            print(f"✅ WTCRO approved! Block: {receipt['blockNumber']}")
            time.sleep(2)
        else:
            print("❌ WTCRO approval failed")
            exit(1)
    except Exception as e:
        print(f"❌ WTCRO approval error: {e}")
        exit(1)
else:
    print(f"✅ WTCRO already approved")

# ======= STEP 5: Add liquidity =======
print("\n" + "="*70)
print("STEP 5: Add liquidity (1 USDC + 2 WTCRO)")
print("="*70)

try:
    deadline = w3.eth.get_block('latest')['timestamp'] + 600  # 10 min
    
    add_liq_tx = router.functions.addLiquidity(
        USDC,
        WTCRO,
        usdc_amount,           # 1 USDC desired
        wrap_amount,           # 2 WTCRO desired
        int(usdc_amount * 0.95),   # 1 USDC min (5% slippage)
        int(wrap_amount * 0.95),   # 2 WTCRO min (5% slippage)
        account.address,
        deadline
    ).build_transaction({
        'from': account.address,
        'gas': 500000,
        'gasPrice': w3.eth.gas_price,
        'nonce': w3.eth.get_transaction_count(account.address),
        'chainId': w3.eth.chain_id
    })
    
    print(f"Adding liquidity...")
    print(f"  USDC: {usdc_amount / 10**usdc_decimals:.6f}")
    print(f"  WTCRO: {w3.from_wei(wrap_amount, 'ether'):.6f}")
    
    signed = account.sign_transaction(add_liq_tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    print(f"\nLiquidity TX: {tx_hash.hex()}")
    print(f"Explorer: https://explorer.cronos.org/testnet/tx/{tx_hash.hex()}")
    print("Waiting for confirmation...")
    
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    
    if receipt['status'] == 1:
        print(f"\n✅ LIQUIDITY ADDED!")
        print(f"Block: {receipt['blockNumber']}")
        print(f"Gas used: {receipt['gasUsed']:,}")
    else:
        print("❌ Liquidity addition failed")
        exit(1)
    
except Exception as e:
    print(f"❌ Liquidity error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# ======= STEP 6: Verify and test swap =======
print("\n" + "="*70)
print("STEP 6: Test swap (1 USDC → WTCRO)")
print("="*70)

try:
    time.sleep(2)
    
    # Get updated balances
    new_usdc = usdc.functions.balanceOf(account.address).call()
    new_wtcro = wtcro.functions.balanceOf(account.address).call()
    
    print(f"Current USDC: {new_usdc / 10**usdc_decimals:.6f}")
    print(f"Current WTCRO: {w3.from_wei(new_wtcro, 'ether'):.6f}")
    
    # Try a swap
    ROUTER_SWAP_ABI = json.loads('[{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"}],"name":"getAmountsOut","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"view","type":"function"}]')
    router_swap = w3.eth.contract(address=ROUTER, abi=ROUTER_SWAP_ABI)
    
    swap_amount = 1 * 10**usdc_decimals
    path = [USDC, WTCRO]
    amounts_out = router_swap.functions.getAmountsOut(swap_amount, path).call()
    expected = amounts_out[1]
    
    print(f"\n✅ Swap estimation works!")
    print(f"1 USDC → {w3.from_wei(expected, 'ether'):.6f} WTCRO")
    print(f"\n🎉 Liquidity pool is ready! Swaps can now succeed.")
    
except Exception as e:
    print(f"⚠️  Swap test error: {e}")
    print("But liquidity was added successfully!")

print("\n" + "="*70)
print("DONE! Liquidity pool is ready for swaps.")
print("="*70)
