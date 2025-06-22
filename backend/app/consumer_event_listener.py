import os
import json
import time
import traceback
from pathlib import Path
from dotenv import load_dotenv
from web3 import Web3

load_dotenv()

CONSUMER_ABI_PATH = Path(__file__).resolve().parent.parent / "contracts" / "ConsumerContract.json"
with open(CONSUMER_ABI_PATH) as f:
    abi = json.load(f)["abi"]

w3 = Web3(Web3.HTTPProvider(os.getenv("INFURA_URL")))
contract = w3.eth.contract(
    address=Web3.to_checksum_address(os.getenv("CONSUMER_CONTRACT_ADDRESS")),
    abi=abi
)

DB_PATH = Path(__file__).parent / "subscriptions.json"

def save_to_db(record):
    print("🔵 Saving consumer subscription to subscriptions.json...")
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
    try:
        consumer = event["args"]["consumer"]
        sub_id = event["args"]["subId"]

        sub_data = contract.functions.userSubscriptions(consumer, sub_id).call()
        provider_nonce = sub_data[0]
        provider_address = sub_data[1]
        amount_paid = Web3.from_wei(sub_data[2], 'ether')
        start_timestamp = sub_data[3]
        status_enum = sub_data[4]
        uri = sub_data[5]

        status_map = {
            0: "Active",
            1: "Grace Period",
            2: "Expired",
            3: "Penalized"
        }

        record = {
            "wallet": consumer,
            "mcp_id": f"{provider_address.lower()}_{provider_nonce}",
            "sub_id": sub_id,
            "provider_nonce": provider_nonce,
            "avax_paid": float(amount_paid),
            "status": status_map.get(status_enum, "Unknown"),
            "url": uri,
            "start_timestamp": start_timestamp,
            "timestamp": time.time()
        }

        print("🟢 New Subscription Event:", record)
        save_to_db(record)

    except Exception:
        print("🔴 Error in handle_event:")
        traceback.print_exc()

def log_loop(event_filter, poll_interval=5):
    while True:
        for event in event_filter.get_new_entries():
            handle_event(event)
        time.sleep(poll_interval)

def main():
    print("🟠 Starting Consumer Event Listener...")
    try:
        start_block = max(w3.eth.block_number - 100, 0)
        event_filter = contract.events.Subscribed.create_filter(from_block=start_block)

        past_events = event_filter.get_all_entries()
        for event in past_events:
            handle_event(event)

        log_loop(event_filter)

    except Exception:
        print("🔴 Consumer Event Listener crashed:")
        traceback.print_exc()

if __name__ == "__main__":
    main()