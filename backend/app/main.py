from fastapi import FastAPI, Form
from pydantic import BaseModel
import json
from pathlib import Path
from uuid import uuid4

from . import blockchain
from . import mcp_manager

app = FastAPI()
DB_PATH = Path(__file__).resolve().parent / "db.json"

class MCPRegisterRequest(BaseModel):
    local_url: str
    service_name: str
    price: float = 0.0  # Optional for now
    duration: int = 30  # Optional default to 30 days

@app.post("/register_mcp")
async def register_mcp(payload: MCPRegisterRequest):
    uid = str(uuid4())
    service_name = payload.service_name
    local_url = payload.local_url
    price = payload.price
    duration = payload.duration

    # Start cloudflared tunnel to expose the local MCP
    https_uri = mcp_manager.create_cloudflared_tunnel(local_url, service_name)

    # Register on blockchain
    tx_hash = blockchain.register_mcp_on_chain(service_name, https_uri, int(price * 1e18), duration)

    # Save metadata
    record = {
        "id": uid,
        "name": service_name,
        "local_url": local_url,
        "https_uri": https_uri,
        "tx_hash": tx_hash
    }
    db = json.load(open(DB_PATH)) if DB_PATH.exists() else []
    db.append(record)
    with open(DB_PATH, "w") as f:
        json.dump(db, f, indent=2)

    return {
        "status": "registered",
        "https_uri": https_uri,
        "tx_hash": tx_hash,
        "message": "MCP successfully registered to the smart contract and stored locally."
    }