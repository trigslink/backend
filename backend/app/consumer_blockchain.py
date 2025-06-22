import os
from web3 import Web3
from dotenv import load_dotenv
import json
from pathlib import Path

load_dotenv()

INFURA_URL = os.getenv("INFURA_URL")
CONSUMER_CONTRACT_ADDRESS = os.getenv("CONSUMER_CONTRACT_ADDRESS")

ABI_PATH = Path(__file__).resolve().parent.parent / "contracts" / "ConsumerContract.json"
with open(ABI_PATH) as f:
    consumer_abi = json.load(f)["abi"]

w3 = Web3(Web3.HTTPProvider(INFURA_URL))
contract = w3.eth.contract(
    address=Web3.to_checksum_address(CONSUMER_CONTRACT_ADDRESS),
    abi=consumer_abi
)

def get_subscriptions(wallet_address: str):
    try:
        wallet = Web3.to_checksum_address(wallet_address)
        raw_subs = contract.functions.getConsumerMcps(wallet).call()

        status_map = {
            0: "Active",
            1: "Grace Period",
            2: "Expired",
            3: "Penalized"
        }

        subscriptions = []
        for sub in raw_subs:
            subscriptions.append({
                "provider_nonce": sub[0],
                "provider_address": sub[1],
                "amount_paid": float(Web3.from_wei(sub[2], 'ether')),
                "start_timestamp": sub[3],
                "status": status_map.get(sub[4], "Unknown"),
                "url": sub[5]
            })

        return subscriptions
    except Exception as e:
        return {"error": str(e)}