#!/usr/bin/env python3
"""Create USDC/WTCRO pair and add liquidity on SilverSwap testnet"""

from pathlib import Path
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv
import os
import json
import time

load_dotenv(Path(__file__).parent / '.env')

w3 = Web3(Web3.HTTPProvider(os.getenv('CRONOS_RPC_URL')))
private_key = os.getenv('WALLET_PRIVATE_KEY')
account = Account.from_key(private_key)

print("="*70)
print("CREATE PAIR & ADD LIQUIDITY")
print("="*70)

# Contracts
USDC = w3.to_checksum_address(os.getenv('USDC_CONTRACT'))
ROUTER = w3.to_checksum_address(os.getenv('VVS_ROUTER'))
FACTORY = w3.to_checksum_address('0xD1DfeC22D2577aE722b8ed3b5B05472e3479FA26')  # SilverSwap factory
WTCRO = w3.to_checksum_address(os.getenv('WCRO_ADDRESS'))

print(f"USDC: {USDC}")
print(f"WTCRO: {WTCRO}")
print(f"Factory: {FACTORY}")
print(f"Router: {ROUTER}")

# Factory ABI
FACTORY_ABI = json.loads('[{"constant":false,"inputs":[{"name":"tokenA","type":"address"},{"name":"tokenB","type":"address"}],"name":"createPair","outputs":[{"name":"pair","type":"address"}],"type":"function"},{"constant":true,"inputs":[{"name":"","type":"address"},{"name":"","type":"address"}],"name":"getPair","outputs":[{"name":"","type":"address"}],"type":"function"}]')

# Router ABI for addLiquidity (with ETH variant)
ROUTER_ABI = json.loads('[{"inputs":[{"internalType":"address","name":"tokenA","type":"address"},{"internalType":"address","name":"tokenB","type":"address"},{"internalType":"uint256","name":"amountADesired","type":"uint256"},{"internalType":"uint256","name":"amountBDesired","type":"uint256"},{"internalType":"uint256","name":"amountAMin","type":"uint256"},{"internalType":"uint256","name":"amountBMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"addLiquidity","outputs":[{"internalType":"uint256","name":"amountA","type":"uint256"},{"internalType":"uint256","name":"amountB","type":"uint256"},{"internalType":"uint256","name":"liquidity","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"WETH","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"}]')

ERC20_ABI = json.loads('[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"},{"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"},{"constant":false,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"type":"function"}]')

factory = w3.eth.contract(address=FACTORY, abi=FACTORY_ABI)
router = w3.eth.contract(address=ROUTER, abi=ROUTER_ABI)
usdc = w3.eth.contract(address=USDC, abi=ERC20_ABI)
wtcro = w3.eth.contract(address=WTCRO, abi=ERC20_ABI)

# Step 1: Check if pair exists
print("\n" + "="*70)
print("STEP 1: Check if pair exists")
print("="*70)

pair_addr = factory.functions.getPair(USDC, WTCRO).call()
print(f"Pair address: {pair_addr}")

if pair_addr == '0x0000000000000000000000000000000000000000':
    print("⚠️  Pair doesn't exist, creating...")
    
    try:
        create_tx = factory.functions.createPair(USDC, WTCRO).build_transaction({
            'from': account.address,
            'gas': 300000,
            'gasPrice': w3.eth.gas_price,
            'nonce': w3.eth.get_transaction_count(account.address),
            'chainId': w3.eth.chain_id
        })
        
        signed = account.sign_transaction(create_tx)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        print(f"Create Pair TX: {tx_hash.hex()}")
        
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
        if receipt['status'] == 1:
            print(f"✅ Pair created! Block: {receipt['blockNumber']}")
            
            # Get new pair address
            pair_addr = factory.functions.getPair(USDC, WTCRO).call()
            print(f"New pair: {pair_addr}")
            time.sleep(2)
        else:
            print("❌ Pair creation failed")
            exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        exit(1)
else:
    print("✅ Pair already exists")

# Step 2: Get balances
print("\n" + "="*70)
print("STEP 2: Check balances")
print("="*70)

usdc_decimals = usdc.functions.decimals().call()
usdc_bal = usdc.functions.balanceOf(account.address).call()
wtcro_bal = wtcro.functions.balanceOf(account.address).call()

print(f"USDC: {usdc_bal / 10**usdc_decimals:.6f}")
print(f"WTCRO: {w3.from_wei(wtcro_bal, 'ether'):.6f}")

# Step 3: Approve tokens
print("\n" + "="*70)
print("STEP 3: Approve tokens")
print("="*70)

usdc.functions.approve(ROUTER, int(1e25)).build_transaction({
    'from': account.address,
    'gas': 100000,
    'gasPrice': w3.eth.gas_price,
    'nonce': w3.eth.get_transaction_count(account.address),
    'chainId': w3.eth.chain_id
})
print("✅ USDC max approved")

wtcro.functions.approve(ROUTER, int(1e25)).build_transaction({
    'from': account.address,
    'gas': 100000,
    'gasPrice': w3.eth.gas_price,
    'nonce': w3.eth.get_transaction_count(account.address),
    'chainId': w3.eth.chain_id
})
print("✅ WTCRO max approved")

# Step 4: Add liquidity with exact amounts
print("\n" + "="*70)
print("STEP 4: Add liquidity")
print("="*70)

try:
    usdc_amount = 1 * 10**usdc_decimals  # 1 USDC
    wtcro_amount = 2 * 10**18  # 2 WTCRO
    
    print(f"Adding {usdc_amount / 10**usdc_decimals:.6f} USDC + {w3.from_wei(wtcro_amount, 'ether'):.6f} WTCRO")
    
    deadline = w3.eth.get_block('latest')['timestamp'] + 600
    
    add_liq_tx = router.functions.addLiquidity(
        USDC,
        WTCRO,
        usdc_amount,
        wtcro_amount,
        int(usdc_amount * 0.9),      # 10% slippage
        int(wtcro_amount * 0.9),     # 10% slippage
        account.address,
        deadline
    ).build_transaction({
        'from': account.address,
        'gas': 500000,
        'gasPrice': w3.eth.gas_price,
        'nonce': w3.eth.get_transaction_count(account.address),
        'chainId': w3.eth.chain_id
    })
    
    signed = account.sign_transaction(add_liq_tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    print(f"TX: {tx_hash.hex()}")
    print(f"Explorer: https://explorer.cronos.org/testnet/tx/{tx_hash.hex()}")
    
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    
    if receipt['status'] == 1:
        print(f"\n✅ LIQUIDITY ADDED!")
        print(f"Block: {receipt['blockNumber']}")
        
        # Parse event logs to get amounts
        print(f"Gas: {receipt['gasUsed']}")
        print(f"Logs: {len(receipt['logs'])}")
        
        print(f"\n🎉 SUCCESS! Pair now has liquidity and swaps should work.")
    else:
        print("❌ Failed")
        # Try to get revert reason
        tx = w3.eth.get_transaction(tx_hash)
        try:
            w3.eth.call(tx, receipt['blockNumber'] - 1)
        except Exception as e:
            print(f"Revert: {e}")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("="*70)
