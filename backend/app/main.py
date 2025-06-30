import json
import os
import shutil
from pathlib import Path

import cloudinary  # type: ignore
import cloudinary.uploader  # type: ignore
from fastapi import FastAPI, File, Form, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from . import blockchain, mcp_manager
from .AI.agents import run_agent_with_tool
from .consumer_blockchain import get_subscriptions

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specify ["http://localhost:5500"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    try:
        metadata = blockchain.get_mcp_data_by_tx(tx_hash)
        if "error" in metadata:
            return JSONResponse(status_code=400, content={"status": "error", "message": metadata["error"]})

        mcp_id = f"{metadata['owner'].lower()}_{metadata['providerNonce']}"

        original_filename = logo.filename or f"uploaded_logo_{mcp_id}.png"
        safe_filename = original_filename.replace(" ", "_")
        temp_logo_path = os.path.join("/tmp", f"{mcp_id}_{safe_filename}")

        with open(temp_logo_path, "wb") as buffer:
            shutil.copyfileobj(logo.file, buffer)

        cloudinary_result = cloudinary.uploader.upload(temp_logo_path)
        logo_url = cloudinary_result["secure_url"]

        https_uri = metadata.get("https_uri")

        record = {
            "mcp_id": mcp_id,
            "wallet": metadata["owner"],
            "service_name": metadata["serviceName"],   
            "description": metadata["serviceDescription"],  
            "price": metadata["usdPriceForConsumerMonth"], 
            "duration": "N/A",
            "tx_hash": tx_hash,
            "https_uri": metadata.get("url"),  
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
    mcps = get_subscriptions(wallet)
    if isinstance(mcps, dict) and "error" in mcps:
        return JSONResponse(status_code=500, content=mcps)
    return {"wallet": wallet, "mcps": mcps}


@app.post("/agent_query")
async def agent_query(request: Request):
    try:
        data = await request.json()
        mcp_id = data["mcp_id"]
        prompt = data["user_prompt"]
        openai_key = data["openai_api_key"]
        env_vars = data.get("env_vars", {})

        with open(DB_PATH, "r") as f:
            db = json.load(f)

        mcp = next((item for item in db if item["mcp_id"] == mcp_id), None)
        if not mcp:
            return JSONResponse(status_code=404, content={"error": "MCP not found"})

        metadata_url = f"{mcp['https_uri']}/metadata"
        result = run_agent_with_tool(openai_key, prompt, metadata_url, env_vars)

        return {"response": result}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/my_subscriptions")
def my_subscriptions(wallet: str):
    try:
        subs_path = BASE_DIR / "subscriptions.json"
        if subs_path.exists():
            with open(subs_path, "r") as f:
                db = json.load(f)
            return [sub for sub in db if sub["wallet"].lower() == wallet.lower()]
        return []
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})