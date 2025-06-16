import os
import json
from typing import Union, Dict, Any
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

INFURA_URL = os.getenv("INFURA_URL")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")
CHAIN_ID = int(os.getenv("CHAIN_ID", "43113"))

try:
    abi_path = os.path.join(os.path.dirname(__file__), "../contracts/McpProvider.json")
    with open(abi_path, "r") as f:
        contract_json = json.load(f)

    if "abi" not in contract_json:
        raise KeyError("ABI key not found in McpProvider.json")
    abi = contract_json["abi"]

except Exception as e:
    raise RuntimeError(f"Error loading ABI: {e}")

w3 = Web3(Web3.HTTPProvider(INFURA_URL))
if not w3.is_connected():
    raise ConnectionError("Web3 is not connected")

contract = w3.eth.contract(
    address=Web3.to_checksum_address(CONTRACT_ADDRESS),
    abi=abi
)

def get_mcp_data_by_wallet(wallet_address: str) -> Union[Dict[str, Any], Dict[str, str]]:
    try:
        wallet = Web3.to_checksum_address(wallet_address)
        data = contract.functions.getAllMcpsByAddress(wallet).call()

        if not data:
            return {"error": "No MCP data found for this wallet."}

        latest = data[-1]  # take the latest record

        metadata = {
            "providerNonce": latest[0],
            "owner": latest[1],
            "amountPaid": float(Web3.from_wei(latest[2], 'ether')),
            "service_name": latest[3],
            "price_usd": float(latest[4]),
            "description": latest[5],
        }

        return metadata

    except Exception as e:
        return {"error": str(e)}

def get_mcp_data_by_tx(tx_hash: str) -> Dict[str, Any]:
    try:
        receipt = w3.eth.get_transaction_receipt(tx_hash)

        for log in receipt.logs:
            try:
                event_data = contract.events.McpProviderRegistered().process_log(log)
                wallet = event_data["args"]["provider"]
                print("Wallet from event:", wallet)
                return get_mcp_data_by_wallet(wallet)
            except Exception as e:
                print("Failed to parse log:", e)
                continue

        raise ValueError("No McpProviderRegistered event found in transaction logs.")

    except Exception as e:
        return {"status": "error", "message": str(e)}