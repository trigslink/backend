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
contract = w3.eth.contract(address=Web3.to_checksum_address(CONSUMER_CONTRACT_ADDRESS), abi=consumer_abi)
