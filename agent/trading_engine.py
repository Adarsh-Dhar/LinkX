
import time
import uuid
from agent.wallet_manager import WalletManager

class TradingEngine:
    def __init__(self, wallet=None):
        self.wallet = wallet or WalletManager()

    def trade(self, *args, **kwargs):
        # Implement trading logic here
        pass
    def _get_tx_params(self, w3, nonce, gas_limit):
        """Build transaction parameters with proper gas handling for both legacy and EIP-1559 networks"""
        tx_params = {
            'from': self.wallet.address,
            'nonce': nonce,
            'gas': gas_limit,
            'chainId': w3.eth.chain_id
        }
        # Try to get gas price - if None, Web3 will estimate it
        try:
            gas_price = w3.eth.gas_price
            if gas_price:
                tx_params['gasPrice'] = int(gas_price * 1.2)
        except:
            # If gas_price fails, don't include it and let Web3 estimate
            pass
        return tx_params


    def execute_swap(self, token_in, token_out, amount_in, max_slippage=5.0):
        try:
            print(f"[TradingEngine] Swapping {amount_in} {token_in} to {token_out}...")
            import os
            
            # Production mode: Use real DEX
            from agent.tools import VVS_ROUTER_ADDR, ROUTER_ABI, resolve_address
            from web3 import Web3
            
            vvs_available = VVS_ROUTER_ADDR and VVS_ROUTER_ADDR.strip() != ""
            
            # Production swap execution with VVS Router
            w3 = self.wallet.w3
            nonce = w3.eth.get_transaction_count(self.wallet.address)
            router_addr = Web3.to_checksum_address(VVS_ROUTER_ADDR) if vvs_available else None
            token_in_addr = resolve_address(token_in)
            token_out_addr = resolve_address(token_out)
            path = [token_in_addr, token_out_addr]
            deadline = int(time.time()) + 600
            
            # CRITICAL: Check if pair exists using factory contract
            factory_addr = os.getenv("VVS_FACTORY_ADDR")
            if factory_addr:
                factory_abi = [
                    {"type":"function","name":"getPair","inputs":[{"name":"","type":"address"},{"name":"","type":"address"}],"outputs":[{"name":"","type":"address"}],"stateMutability":"view"},
                    {"type":"function","name":"createPair","inputs":[{"name":"tokenA","type":"address"},{"name":"tokenB","type":"address"}],"outputs":[{"name":"pair","type":"address"}],"stateMutability":"nonpayable"}
                ]
                factory = w3.eth.contract(address=Web3.to_checksum_address(factory_addr), abi=factory_abi)
                pair_address = factory.functions.getPair(token_in_addr, token_out_addr).call()
                
                if pair_address == "0x0000000000000000000000000000000000000000":
                    print(f"   ⚠️  No liquidity pool exists between {token_in} and {token_out}")
                    print(f"   💡 Skipping swap - pool needs to be created and funded first")
                    print(f"   📝 Run: python check_and_add_liquidity.py to set up the pool")
                    return None
                else:
                    print(f"   ✅ Pair exists at: {pair_address}")
            
            # Get token decimals and convert amount
            if token_in.lower() in ['cro', 'tcro', 'native', 'xtz', 'tez']:
                amount_in_wei = w3.to_wei(amount_in, 'ether')
                decimals = 18
            else:
                # For ERC20 tokens, get decimals and convert to int
                erc20_abi = [
                    {"constant":True,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"},
                    {"constant":True,"inputs":[{"name":"account","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"type":"function"}
                ]
                erc20 = w3.eth.contract(address=token_in_addr, abi=erc20_abi)
                decimals = erc20.functions.decimals().call()
                amount_in_wei = int(float(amount_in) * (10 ** decimals))
                
                # CRITICAL: Check if we have enough balance
                balance = erc20.functions.balanceOf(self.wallet.address).call()
                print(f"   💰 Balance: {balance / (10 ** decimals):.2f} {token_in}")
                if balance < amount_in_wei:
                    print(f"   ❌ Insufficient {token_in} balance. Need: {amount_in}, Have: {balance / (10 ** decimals):.2f}")
                    return None
            
            # Get expected output amount from router to calculate slippage
            if vvs_available and router_addr:
                router = w3.eth.contract(address=router_addr, abi=ROUTER_ABI)
                try:
                    amounts_out = router.functions.getAmountsOut(amount_in_wei, path).call()
                    expected_out = amounts_out[-1]
                    # Calculate minimum output with slippage protection
                    amount_out_min = int(expected_out * (1 - max_slippage / 100))
                    print(f"   📊 Expected: {expected_out}, Min (with {max_slippage}% slippage): {amount_out_min}")
                    
                    # Verify minimum output is reasonable
                    if amount_out_min <= 0:
                        print(f"   ❌ Calculated amountOutMin is too low. Pool may have insufficient liquidity.")
                        return None
                except Exception as e:
                    print(f"   ⚠️ Could not get expected output from router: {e}")
                    print(f"   💡 Falling back to direct pair swap.")
                    amount_out_min = None
            else:
                amount_out_min = None

            # Fallback: direct swap via pair contract (no router)
            if amount_out_min is None:
                factory_addr = os.getenv("VVS_FACTORY_ADDR")
                if not factory_addr:
                    print("   ❌ VVS_FACTORY_ADDR not set; cannot perform direct pair swap.")
                    return None

                pair_abi = [
                    {"constant":True,"inputs":[],"name":"token0","outputs":[{"name":"","type":"address"}],"type":"function"},
                    {"constant":True,"inputs":[],"name":"token1","outputs":[{"name":"","type":"address"}],"type":"function"},
                    {"constant":True,"inputs":[],"name":"getReserves","outputs":[{"name":"reserve0","type":"uint112"},{"name":"reserve1","type":"uint112"},{"name":"blockTimestampLast","type":"uint32"}],"type":"function"},
                    {"constant":False,"inputs":[{"name":"amount0Out","type":"uint256"},{"name":"amount1Out","type":"uint256"},{"name":"to","type":"address"},{"name":"data","type":"bytes"}],"name":"swap","outputs":[],"type":"function"},
                    {"constant":False,"inputs":[],"name":"sync","outputs":[],"type":"function"}
                ]

                factory_abi = [
                    {"type":"function","name":"getPair","inputs":[{"name":"","type":"address"},{"name":"","type":"address"}],"outputs":[{"name":"","type":"address"}],"stateMutability":"view"}
                ]
                factory = w3.eth.contract(address=Web3.to_checksum_address(factory_addr), abi=factory_abi)
                pair_address = factory.functions.getPair(token_in_addr, token_out_addr).call()
                if pair_address == "0x0000000000000000000000000000000000000000":
                    print("   ❌ No pair found for direct swap.")
                    return None

                pair = w3.eth.contract(address=pair_address, abi=pair_abi)
                token0 = pair.functions.token0().call()
                token1 = pair.functions.token1().call()
                reserves = pair.functions.getReserves().call()
                reserve0, reserve1 = reserves[0], reserves[1]

                if token_in_addr == token0:
                    reserve_in, reserve_out = reserve0, reserve1
                else:
                    reserve_in, reserve_out = reserve1, reserve0

                if reserve_in == 0 or reserve_out == 0:
                    try:
                        print("   ⚠️ Reserves are zero. Syncing pair...")
                        # Build transaction params with proper gas handling
                        tx_params = {
                            'from': self.wallet.address,
                            'nonce': nonce,
                            'gas': 2000000,
                            'chainId': w3.eth.chain_id
                        }
                        # Handle gas price (legacy) vs maxFeePerGas (EIP-1559)
                        try:
                            gas_price = w3.eth.gas_price
                            if gas_price:
                                tx_params['gasPrice'] = int(gas_price * 1.2)
                        except:
                            pass
                    
                        sync_tx = pair.functions.sync().build_transaction(tx_params)
                        signed_sync = w3.eth.account.sign_transaction(sync_tx, private_key=self.wallet.private_key)
                        sync_hash = w3.eth.send_raw_transaction(signed_sync.raw_transaction)
                        w3.eth.wait_for_transaction_receipt(sync_hash, timeout=120)
                        nonce += 1
                        reserves = pair.functions.getReserves().call()
                        reserve0, reserve1 = reserves[0], reserves[1]
                        if token_in_addr == token0:
                            reserve_in, reserve_out = reserve0, reserve1
                        else:
                            reserve_in, reserve_out = reserve1, reserve0
                    except Exception as e:
                        print(f"   ❌ Sync failed: {e}")
                        return None

                if reserve_in == 0 or reserve_out == 0:
                    print("   ❌ Pool reserves are still zero; cannot swap.")
                    return None

                amount_in_with_fee = amount_in_wei * 997
                numerator = amount_in_with_fee * reserve_out
                denominator = reserve_in * 1000 + amount_in_with_fee
                expected_out = numerator // denominator
                amount_out_min = int(expected_out * (1 - max_slippage / 100))
                print(f"   📊 Expected (direct): {expected_out}, Min (with {max_slippage}% slippage): {amount_out_min}")

                if amount_out_min <= 0:
                    print("   ❌ Calculated amountOutMin is too low for direct swap.")
                    return None

                # Transfer token_in to pair
                erc20_transfer_abi = [
                    {"constant":False,"inputs":[{"name":"to","type":"address"},{"name":"value","type":"uint256"}],"name":"transfer","outputs":[{"name":"","type":"bool"}],"type":"function"}
                ]
                erc20_transfer = w3.eth.contract(address=token_in_addr, abi=erc20_transfer_abi)
                # Build transaction params with proper gas handling
                tx_params = {
                    'from': self.wallet.address,
                    'nonce': nonce,
                    'gas': 2000000,
                    'chainId': w3.eth.chain_id
                }
                try:
                    gas_price = w3.eth.gas_price
                    if gas_price:
                        tx_params['gasPrice'] = int(gas_price * 1.2)
                except:
                    pass
                
                transfer_tx = erc20_transfer.functions.transfer(pair_address, amount_in_wei).build_transaction(tx_params)
                signed_transfer = w3.eth.account.sign_transaction(transfer_tx, private_key=self.wallet.private_key)
                transfer_hash = w3.eth.send_raw_transaction(signed_transfer.raw_transaction)
                print(f"   ⏳ Waiting for transfer confirmation (Hash: {transfer_hash.hex()})...")
                w3.eth.wait_for_transaction_receipt(transfer_hash, timeout=120)
                nonce += 1

                amount0_out = amount_out_min if token_out_addr == token0 else 0
                amount1_out = amount_out_min if token_out_addr == token1 else 0
                # Build transaction params with proper gas handling
                tx_params = {
                    'from': self.wallet.address,
                    'nonce': nonce,
                    'gas': 5000000,
                    'chainId': w3.eth.chain_id
                }
                try:
                    gas_price = w3.eth.gas_price
                    if gas_price:
                        tx_params['gasPrice'] = int(gas_price * 1.2)
                except:
                    pass
                
                swap_tx = pair.functions.swap(amount0_out, amount1_out, self.wallet.address, b'').build_transaction(tx_params)
                signed_swap = w3.eth.account.sign_transaction(swap_tx, private_key=self.wallet.private_key)
                tx_hash = w3.eth.send_raw_transaction(signed_swap.raw_transaction)
                print(f"   ⏳ Waiting for Swap confirmation (Hash: {tx_hash.hex()})...")
                receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
                if receipt['status'] == 1:
                    print("   ✅ Swap Confirmed (direct pair)!")
                    return tx_hash.hex()
                print("   ❌ Swap Failed (direct pair).")
                return None
            
            # CRITICAL: Approve router to spend token_in before swapping
            print(f"   🔐 Approving router to spend {token_in}...")
            erc20_approve_abi = [
                {"constant":False,"inputs":[{"name":"spender","type":"address"},{"name":"value","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"type":"function"},
                {"constant":True,"inputs":[{"name":"_owner","type":"address"},{"name":"_spender","type":"address"}],"name":"allowance","outputs":[{"name":"","type":"uint256"}],"type":"function"}
            ]
            erc20_contract = w3.eth.contract(address=token_in_addr, abi=erc20_approve_abi)
            
            # Check current allowance
            current_allowance = erc20_contract.functions.allowance(self.wallet.address, router_addr).call()
            if current_allowance < amount_in_wei:
                print(f"   Current allowance: {current_allowance}, Approving: {amount_in_wei}")
                # Approve with unlimited amount for future swaps
                # Build transaction params with proper gas handling
                tx_params = {
                    'from': self.wallet.address,
                    'nonce': nonce,
                    'gas': 2000000,
                    'chainId': w3.eth.chain_id
                }
                try:
                    gas_price = w3.eth.gas_price
                    if gas_price:
                        tx_params['gasPrice'] = int(gas_price * 1.2)
                except:
                    pass
                
                approve_tx = erc20_contract.functions.approve(router_addr, Web3.to_wei(10000000, 'ether')).build_transaction(tx_params)
                
                signed_approve = w3.eth.account.sign_transaction(approve_tx, private_key=self.wallet.private_key)
                approve_hash = w3.eth.send_raw_transaction(signed_approve.raw_transaction)
                print(f"   ⏳ Waiting for approval (Hash: {approve_hash.hex()})...")
                w3.eth.wait_for_transaction_receipt(approve_hash, timeout=60)
                print(f"   ✅ Approval confirmed!")
                
                # Increment nonce for next transaction
                nonce += 1
            else:
                print(f"   ✅ Sufficient allowance already exists: {current_allowance}")
            
            # Execute swap with calculated minimum output
            swap_tx = router.functions.swapExactTokensForTokens(
                amount_in_wei, amount_out_min, path, self.wallet.address, deadline
            ).build_transaction(self._get_tx_params(w3, nonce, 5000000))
            
            signed_tx = w3.eth.account.sign_transaction(swap_tx, private_key=self.wallet.private_key)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            print(f"   ⏳ Waiting for Swap confirmation (Hash: {tx_hash.hex()})...")
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            
            # Verify transaction actually succeeded
            if receipt['status'] == 1:
                print(f"   ✅ Swap Confirmed!")
                return tx_hash.hex()
            else:
                print(f"   ❌ Swap Failed! Transaction reverted.")
                print(f"   🔍 Check transaction: {tx_hash.hex()}")
                return None
        except Exception as e:
            error_str = str(e).lower()
            if "invalid sequence" in error_str or "nonce" in error_str:
                print("   ⚠️ Nonce mismatch detected. Retrying with incremented nonce...")
            elif "deployed" in error_str or "no code" in error_str:
                print(f"   ❌ [TradingEngine] DEX contract not found at configured address")
                print(f"   💡 [Fix] Set VVS_ROUTER_ADDR in .env to a deployed DEX")
            elif "insufficient" in error_str:
                print(f"   ❌ [TradingEngine] Insufficient balance or liquidity")
                print(f"   💡 Check your {token_in} balance and pool liquidity")
            elif "transfer amount exceeds balance" in error_str:
                print(f"   ❌ [TradingEngine] Not enough {token_in} in wallet")
            elif "k" in error_str or "pancake" in error_str or "uniswap" in error_str:
                print(f"   ❌ [TradingEngine] Swap would exceed slippage tolerance")
                print(f"   💡 Try increasing max_slippage or reducing amount")
            else:
                print(f"❌ [TradingEngine] Production Swap Failed: {e}")
            return None
