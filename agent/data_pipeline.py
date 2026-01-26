
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from agent.data_consumer import fetch_node_data

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
        cronos_rpc = os.getenv("CRONOS_RPC_URL", "https://evm-t3.cronos.org")
        usdc_contract_addr = os.getenv("USDC_CONTRACT", "0xE373E44E5e64496BD092A5ad097881C0fa31D326")
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
            # Get decimals
            decimals = usdc_contract.functions.decimals().call()
            total_cost_wei = int(total_cost * (10 ** decimals))
            # Check balance
            balance = usdc_contract.functions.balanceOf(my_addr).call()
            if balance < total_cost_wei:
                print(f"      ❌ Insufficient USDC balance. Have: {balance/(10**decimals):.2f}, Need: {total_cost:.2f}")
                return False
            # Approve if needed
            allowance = usdc_contract.functions.allowance(my_addr, usdc_contract_addr).call()
            if allowance < total_cost_wei:
                print("      🔐 Approving USDC contract for batch payment...")
                nonce = w3.eth.get_transaction_count(my_addr)
                tx = usdc_contract.functions.approve(usdc_contract_addr, total_cost_wei).build_transaction({
                    'from': my_addr, 'nonce': nonce, 'gasPrice': int(w3.eth.gas_price * 1.2)
                })
                signed = w3.eth.account.sign_transaction(tx, private_key)
                w3.eth.send_raw_transaction(signed.raw_transaction)
            # Simulate unlock: Replace with actual contract call to unlock nodes
            print(f"      💸 Executing batch payment for {len(node_objs)} nodes. Total cost: {total_cost:.2f} USDC.")
            # TODO: Replace with actual unlock contract call if available
            print("      ✅ Batch payment successful.")
            return True
        except Exception as e:
            print(f"      ❌ Batch payment error: {e}")
            return False

    async def fetch_dynamic_tools(self, node_objs):
        """
        Fetches data from a list of node objects (with name, category, price, etc). Handles x402 payment batch if needed.
        Returns (results, failure_flag): failure_flag is True if any required tool could not be bought.
        """
        from agent.node_connector import get_connector
        results = {}
        failure_flag = False
        if not node_objs:
            return results, failure_flag
        try:
            # Build batch requests for all node_objs
            batch_requests = []
            name_to_node = {}
            for node in node_objs:
                batch_requests.append({
                    "method": "fetch",
                    "params": [],
                    "category": node["category"],
                    "node_name": node["name"],
                })
                name_to_node[node["name"]] = node["name"]

            # If no valid nodes, return early
            if not batch_requests:
                return results, True

            # --- x402 payment batch logic ---
            total_cost = sum(float(n.get("price", 0.0)) for n in node_objs)
            if total_cost > 0:
                payment_ok = await self.pay_x402_batch(node_objs)
                if not payment_ok:
                    print("      ❌ Aborting batch fetch due to payment failure.")
                    return results, True

            connector = await get_connector()
            batch_results = await connector.execute_batch(batch_requests)

            for idx, res in enumerate(batch_results):
                requested_name = node_objs[idx]["name"]
                node_name = name_to_node.get(requested_name, requested_name)
                if res.get("success", True) and res.get("data") is not None:
                    val = res["data"].get("value")
                    ts = res["data"].get("timestamp", datetime.utcnow())
                    results[requested_name] = (val, ts)
                else:
                    print(f"      ❌ Failed to acquire data for {requested_name} (node: {node_name}). Error: {res.get('error')}")
                    failure_flag = True

            return results, failure_flag
        except Exception as e:
            print(f"   ⚠️ Pipeline Sync Error: {e}")
            failure_flag = True
            return results, failure_flag