from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from . import mcp_manager
from . import blockchain  
import json
from pathlib import Path
from uuid import uuid4
import shutil
import cloudinary
import cloudinary.uploader

app = FastAPI()

# Directories
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "db.json"

# Cloudinary config
cloudinary.config( 
    cloud_name = "dgvb4ap8o", 
    api_key = "554578947371512", 
    api_secret = "hkAqofSS7beULMIujFqQwM_paM4",  
    secure = True
)

@app.post("/register_mcp")
async def register_mcp(
    tx_hash: str = Form(...),
    logo: UploadFile = File(...)
):
    uid = str(uuid4())

    try:
        # Get MCP metadata from blockchain using tx_hash
        metadata = blockchain.get_mcp_data_by_tx(tx_hash)
        if "error" in metadata:
            return JSONResponse(status_code=400, content={"status": "error", "message": metadata["error"]})

        # Safely handle the uploaded image file
        filename = str(logo.filename) if logo.filename else "uploaded_logo.png"
        filename = filename.replace(" ", "_").strip()
        temp_logo_path = f"/tmp/{uid}_{filename}"

        with open(temp_logo_path, "wb") as buffer:
            shutil.copyfileobj(logo.file, buffer)

        # Upload to Cloudinary
        cloudinary_result = cloudinary.uploader.upload(temp_logo_path)
        logo_url = cloudinary_result["secure_url"]

        # Create tunnel via Cloudflared
        local_port = 9002
        https_uri = mcp_manager.create_cloudflared_tunnel(local_port)

        # Build and save record
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

        # Load or initialize local database
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

        # Return successful response
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