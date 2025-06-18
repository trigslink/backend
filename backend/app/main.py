from fastapi import FastAPI, UploadFile,Request, File, Form, Query
from fastapi.responses import JSONResponse
from . import mcp_manager
from . import blockchain
from . import consumer_blockchain
from .AI.agents import run_agent_with_tool
import json
from pathlib import Path
from uuid import uuid4
import shutil
import cloudinary
import cloudinary.uploader
import os

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "db.json"

cloudinary.config(
    cloud_name="dgvb4ap8o",
    api_key="554578947371512",
    api_secret="hkAqofSS7beULMIujFqQwM_paM4",
    secure=True
)

@app.post("/register_mcp")
async def register_mcp(
    tx_hash: str = Form(...),
    logo: UploadFile = File(...)
):
    uid = str(uuid4())

    try:
        metadata = blockchain.get_mcp_data_by_tx(tx_hash)
        if "error" in metadata:
            return JSONResponse(status_code=400, content={"status": "error", "message": metadata["error"]})

        original_filename = logo.filename
        if not isinstance(original_filename, str):
            original_filename = f"uploaded_logo_{uid}.png"

        safe_filename = str(original_filename).replace(" ", "_")
        temp_logo_path = os.path.join("/tmp", f"{uid}_{safe_filename}")

        with open(temp_logo_path, "wb") as buffer:
            shutil.copyfileobj(logo.file, buffer)

        cloudinary_result = cloudinary.uploader.upload(temp_logo_path)
        logo_url = cloudinary_result["secure_url"]

        https_uri = mcp_manager.create_cloudflared_tunnel(9002)

        record = {
            "id": uid,
            "wallet": metadata["owner"],
            "service_name": metadata["service_name"],
            "description": metadata["description"],
            "price": metadata["price_usd"],
            "duration": metadata.get("duration", "N/A"),
            "tx_hash": tx_hash,
            "https_uri": https_uri,
            "logo_url": logo_url
        }

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

        return {
            "status": "registered",
            "https_uri": https_uri,
            "tx_hash": tx_hash,
            "message": "MCP stored and tunnel created",
            "logo_url": logo_url,
            "metadata": record
        }

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/available_mcps")
def get_available_mcps(
    service_name: str = Query(None),
    wallet: str = Query(None),
    price_lte: float = Query(None)
):
    try:
        if DB_PATH.exists():
            with open(DB_PATH, "r") as f:
                db = json.load(f)

            # Optional filters
            if service_name:
                db = [mcp for mcp in db if service_name.lower() in mcp["service_name"].lower()]
            if wallet:
                db = [mcp for mcp in db if mcp["wallet"].lower() == wallet.lower()]
            if price_lte is not None:
                db = [mcp for mcp in db if float(mcp["price"]) <= price_lte]

            return db
        return []
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/my_mcps")
def get_my_mcps(wallet: str):
    try:
        # example: contract.functions.getUserPurchases(wallet).call()
        mcps = consumer_blockchain.contract.functions.getUserMcps(wallet).call()
        return {"wallet": wallet, "mcps": mcps}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/agent_query")
async def agent_query(request: Request):
    try:
        data = await request.json()
        mcp_id = data["mcp_id"]
        prompt = data["user_prompt"]
        openai_key = data["openai_api_key"]
        env_vars = data.get("env_vars", {})

        # Locate MCP from db.json
        with open(DB_PATH, "r") as f:
            db = json.load(f)
        
        mcp = next((item for item in db if item["id"] == mcp_id), None)
        if not mcp:
            return JSONResponse(status_code=404, content={"error": "MCP not found"})

        metadata_url = f"{mcp['https_uri']}/metadata"

        result = run_agent_with_tool(openai_key, prompt, metadata_url, env_vars)
        return {"response": result}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})