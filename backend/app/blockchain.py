import os
import json
from typing import Union, Dict, Any
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

# Load environment variables
INFURA_URL = os.getenv("INFURA_URL")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")
CHAIN_ID = int(os.getenv("CHAIN_ID", "43113"))

# Load the contract ABI
with open(os.path.join(os.path.dirname(__file__), "../contracts/McpProvider.json")) as f:
    contract_json = json.load(f)

    if isinstance(contract_json, list):
        if not contract_json:
            raise ValueError("McpProvider.json is an empty list.")
        contract_json = contract_json[0]

    if "abi" not in contract_json:
        raise KeyError("The contract JSON does not contain an 'abi' key. Check the format of McpProvider.json.")

    abi = contract_json["abi"]

# Web3 connection and contract object
w3 = Web3(Web3.HTTPProvider(INFURA_URL))
contract = w3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=abi)


# Fetch metadata for a wallet from smart contract
def get_mcp_data_by_wallet(wallet_address: str) -> Union[Dict[str, Any], Dict[str, str]]:
    try:
        wallet = Web3.to_checksum_address(wallet_address)
        data = contract.functions.getMcp(wallet).call()

        # Adjust depending on your contract return values
        metadata = {
            "owner": wallet,
            "service_name": data[0],
            "price_usd": float(w3.from_wei(data[1], 'ether')),
            "description": data[2],
            "isActive": data[3],
        }

        # Add duration if available
        if len(data) > 4:
            metadata["duration"] = data[4]

        return metadata

    except Exception as e:
        return {"error": str(e)}


# Fetch metadata by looking up the event in the transaction logs
def get_metadata_from_tx(tx_hash: str) -> Dict[str, Any]:
    try:
        receipt = w3.eth.get_transaction_receipt(tx_hash)

        for log in receipt.logs:
            try:
                event_data = contract.events.McpProviderRegistered().process_log(log)
                wallet = event_data["args"]["owner"]
                return get_mcp_data_by_wallet(wallet)
            except Exception:
                continue

        raise ValueError("No McpRegistered event found in transaction logs.")

    except Exception as e:
        raise RuntimeError(f"Error fetching data from tx: {e}")