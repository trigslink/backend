import json
import time
import os
import traceback
from web3 import Web3
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
ABI_PATH = Path(__file__).resolve().parent.parent / "contracts" / "McpProvider.json"

with open(ABI_PATH) as f:
    abi = json.load(f)["abi"]

w3 = Web3(Web3.HTTPProvider(os.getenv("INFURA_URL")))
contract_address = Web3.to_checksum_address(os.getenv("CONTRACT_ADDRESS"))
contract = w3.eth.contract(address=contract_address, abi=abi)

DB_PATH = Path(__file__).parent / "db.json"

def save_to_db(record):
    print("🔵 Saving as Meta-Data to the Central Database")
    db = []
    if DB_PATH.exists():
        with open(DB_PATH, "r") as f:
            try:
                db = json.load(f)
            except json.JSONDecodeError:
                db = []
    db.append(record)
    with open(DB_PATH, "w") as f:
        json.dump(db, f, indent=2)

def handle_event(event):
    provider = event["args"]["provider"]
    nonce = event["args"]["providerNonce"]
    amount_paid = event["args"]["amountPaid"]
    tx_hash = event["transactionHash"].hex()
    mcp_id = f"{provider.lower()}_{nonce}"

    record = {
        "mcp_id": mcp_id,
        "wallet": provider,
        "provider_nonce": nonce,
        "amount_paid": str(amount_paid),
        "tx_hash": tx_hash,
        "timestamp": time.time()
    }

    print("🟢 New MCP Event:", record)
    save_to_db(record)

def log_loop(event_filter, poll_interval=5):
    while True:
        for event in event_filter.get_new_entries():
            handle_event(event)
        time.sleep(poll_interval)

def main():
    print("🟠 Starting Event Listener...")
    try:
        start_block = max(w3.eth.block_number - 100, 0)
        event_filter = contract.events.McpProviderRegistered.create_filter(from_block=start_block)
        past_events = event_filter.get_all_entries()
        for event in past_events:
            handle_event(event)
        log_loop(event_filter)
    except Exception as e:
        print("🔴 Event Listener crashed:")
        traceback.print_exc()

if __name__ == "__main__":
    main()