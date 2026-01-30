from web3 import Web3
import os

# Load environment variables
USDC_CONTRACT = os.getenv("USDC_CONTRACT", "0x466930303420B7a4Fb2DEB7e15111222ED1363fe")
RPC_URL = os.getenv("RPC_URL", "https://node.shadownet.etherlink.com")
PRIVATE_KEY = os.getenv("WALLET_PRIVATE_KEY", "276c1780d486387b7f4cad347a60c2e3c41fe757688c4e2c2cbc50d315dbb9fe")

# Minimal ERC20 ABI
ERC20_ABI = [
    {"constant":True,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"},
    {"constant":True,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"},
    {"constant":False,"inputs":[{"name":"_to","type":"address"},{"name":"_value","type":"uint256"}],"name":"transfer","outputs":[{"name":"","type":"bool"}],"type":"function"}
]

# Setup web3
w3 = Web3(Web3.HTTPProvider(RPC_URL))
account = w3.eth.account.from_key(PRIVATE_KEY)
address = account.address

# Test transfer
recipient = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"  # Example recipient
usdc = w3.eth.contract(address=USDC_CONTRACT, abi=ERC20_ABI)
decimals = usdc.functions.decimals().call()
amount = int(0.45 * (10 ** decimals))
nonce = w3.eth.get_transaction_count(address)
gas_estimate = usdc.functions.transfer(recipient, amount).estimate_gas({'from': address})
tx = usdc.functions.transfer(recipient, amount).build_transaction({
    'from': address,
    'nonce': nonce,
    'gas': gas_estimate,
    'gasPrice': int(w3.eth.gas_price * 1.2),
    'chainId': w3.eth.chain_id
})
signed = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
print(f"Sent 0.45 USDC to {recipient}. Tx hash: {tx_hash.hex()}")
receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=30)
print(f"Transaction receipt: {receipt}")
