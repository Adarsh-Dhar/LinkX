
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from .data_consumer import fetch_node_data

class DataPipeline:
    def __init__(self, market_manager):
        self.market = market_manager
        self.chart_api_url = "http://localhost:3600/api/dashboard/chart"
        self.nodes_api_url = "http://localhost:3600/api/market/nodes"
        # TOOL_CATEGORIES will be dynamically populated
        self.TOOL_CATEGORIES = {}
    async def refresh_market_knowledge(self):
        """Fetches all nodes to map names to categories dynamically."""
        try:
            res = requests.get(self.nodes_api_url, timeout=2)
            if res.status_code == 200:
                all_nodes = res.json()
                # Dynamically build the map from the DB
                self.TOOL_CATEGORIES = {n['name']: n['category'] for n in all_nodes}
                return all_nodes
        except Exception as e:
            print(f"   ⚠️ Market Sync Error: {e}")
        return []


    def fetch_candles(self):
        try:
            response = requests.get(self.chart_api_url, timeout=2)
            if response.status_code == 200:
                data = response.json()
                if not data or len(data) < 20:
                    print(f"      ⚠️ API returned only {len(data) if data else 0} records.")
                    return None
                df = pd.DataFrame(data)
                cols = ['open', 'high', 'low', 'close', 'volume']
                for c in cols: df[c] = pd.to_numeric(df[c])
                df = df.sort_values('timestamp').reset_index(drop=True)
                df = df.tail(20)
                print(f"      ✅ Tape Synced: Using {len(df)} most recent data points.")
                return df
        except Exception as e:
            print(f"   ⚠️ Fetch Error: {e}")
        return None

    async def pay_x402_batch(self, node_objs):
        """
        Executes a single batch payment for all nodes in node_objs.
        Returns True if payment succeeded, False otherwise.
        """
        from web3 import Web3
        import os, json
        # Load USDC ABI
        abi_path = os.path.join(os.path.dirname(__file__), "usdc_abi.json")
        with open(abi_path, "r") as f:
            usdc_abi = json.load(f)
        # Load batch unlock contract ABI (replace with actual ABI file as needed)
        unlock_abi_path = os.path.join(os.path.dirname(__file__), "../abi/vvsrouter.json")
        with open(unlock_abi_path, "r") as f:
            unlock_abi = json.load(f)
        cronos_rpc = os.getenv("RPC_URL", "https://node.ghostnet.etherlink.com")
        usdc_contract_addr = os.getenv("USDC_CONTRACT", "0xE373E44E5e64496BD092A5ad097881C0fa31D326")
        unlock_contract_addr = "0x1234567890abcdef1234567890abcdef12345678"  # Placeholder address
        unlock_contract_addr = Web3.to_checksum_address(unlock_contract_addr)
        private_key = os.getenv("WALLET_PRIVATE_KEY")
        if not private_key:
            print("      ❌ Missing wallet private key for payment.")
            return False
        w3 = Web3(Web3.HTTPProvider(cronos_rpc))
        account = w3.eth.account.from_key(private_key)
        my_addr = account.address
        usdc_contract = w3.eth.contract(address=usdc_contract_addr, abi=usdc_abi)
        # Calculate total cost in USDC
        total_cost = sum(float(n.get("price", 0.0)) for n in node_objs)
        if total_cost <= 0:
            print("      ⚠️ No payment required for batch (total cost is zero).")
            return True
        try:
            decimals = usdc_contract.functions.decimals().call()
            total_cost_wei = int(total_cost * (10 ** decimals))
            balance = usdc_contract.functions.balanceOf(my_addr).call()
            if balance < total_cost_wei:
                print(f"      ❌ Insufficient USDC balance. Have: {balance/(10**decimals):.2f}, Need: {total_cost:.2f}")
                return False
            allowance = usdc_contract.functions.allowance(my_addr, unlock_contract_addr).call()
            if allowance < total_cost_wei:
                print("      🔐 Approving unlock contract for batch payment...")
                nonce = w3.eth.get_transaction_count(my_addr)
                tx = usdc_contract.functions.approve(unlock_contract_addr, total_cost_wei).build_transaction({
                    'from': my_addr, 'nonce': nonce, 'gasPrice': int(w3.eth.gas_price * 1.2)
                })
                signed = w3.eth.account.sign_transaction(tx, private_key)
                w3.eth.send_raw_transaction(signed.raw_transaction)
            # Call the VVS Router's swapExactTokensForTokens as a placeholder for payment logic
            unlock_contract = w3.eth.contract(address=unlock_contract_addr, abi=unlock_abi)
            # Example: swap USDC for WCRO (or another token) as a payment simulation
            # You must replace these addresses with real token addresses for your use case
            usdc_token = usdc_contract_addr
            wcro_token = os.getenv("WCRO_CONTRACT", "0x8F65e9482DB43F403400C6Cb7B20E7dc132d21D2")
            path = [Web3.to_checksum_address(usdc_token), Web3.to_checksum_address(wcro_token)]
            amount_in = total_cost_wei
            amount_out_min = 1  # Accept any amount out for now
            to_addr = my_addr
            deadline = int(datetime.utcnow().timestamp()) + 600
            nonce = w3.eth.get_transaction_count(my_addr)
            tx = unlock_contract.functions.swapExactTokensForTokens(
                amount_in, amount_out_min, path, to_addr, deadline
            ).build_transaction({
                'from': my_addr,
                'nonce': nonce,
                'gasPrice': int(w3.eth.gas_price * 1.2),
                'gas': 120000  # Increased gas limit
            })
            signed = w3.eth.account.sign_transaction(tx, private_key)
            try:
                tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
                if tx_hash:
                    print(f"      💸 Executed swapExactTokensForTokens for {len(node_objs)} nodes. Tx: {tx_hash.hex()}")
                    print("      ✅ Batch payment and unlock (swap) successful.")
                    return True
                else:
                    print("      ❌ No transaction hash returned (transaction may have failed to broadcast).")
                    return False
            except Exception as e:
                print(f"      ❌ Error sending transaction: {e}")
                return False
        except Exception as e:
            print(f"      ❌ Batch payment error: {e}")
            return False

    async def fetch_dynamic_tools(self, node_objs):
        """
        Accepts a list of node objects (not just names), fetches their data, and returns results.
        Returns (results, failure_flag): failure_flag is True if any node could not be bought.
        """
        from agent.wallet_manager import WalletManager
        results = {}
        failure_flag = False
        wallet_manager = WalletManager()
        for node in node_objs:
            try:
                data = fetch_node_data(node_url=node.get("endpointUrl"), api_key=node.get("apiKey"), wallet_manager=wallet_manager)
                results[node.get("name")] = data
            except Exception as e:
                print(f"   ❌ Failed to fetch {node.get('name')}: {e}")
                failure_flag = True
        return results, failure_flag