import os
import json
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

INFURA_URL = os.getenv("INFURA_URL")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
WALLET_ADDRESS = os.getenv("WALLET_ADDRESS")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")
CHAIN_ID = int(os.getenv("CHAIN_ID", "43113"))

# Load ABI
with open(os.path.join(os.path.dirname(__file__), "../contracts/McpProvider.json")) as f:
    contract_json = json.load(f)

    # Handle case where the JSON is a list
    if isinstance(contract_json, list):
        if not contract_json:
            raise ValueError("McpProvider.json is an empty list.")
        contract_json = contract_json[0]

    # Ensure 'abi' exists
    if "abi" not in contract_json:
        raise KeyError("The contract JSON does not contain an 'abi' key. Check the format of McpProvider.json.")

    abi = contract_json["abi"]

# Setup Web3
w3 = Web3(Web3.HTTPProvider(INFURA_URL))
wallet_address = Web3.to_checksum_address(WALLET_ADDRESS)
contract = w3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=abi)

# Register function
def register_on_chain(https_uri: str) -> str:
    nonce = w3.eth.get_transaction_count(wallet_address)

    txn = contract.functions.registerProvider(https_uri).build_transaction({
        'chainId': CHAIN_ID,
        'gas': 250000,
        'gasPrice': w3.eth.gas_price,
        'nonce': nonce,
        'from': wallet_address
    })

    signed_txn = w3.eth.account.sign_transaction(txn, private_key=PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
    return tx_hash.hex()