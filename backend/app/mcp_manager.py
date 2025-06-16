import uuid
import os
import shutil
import subprocess
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
MCP_DIR = BASE_DIR / "registered_mcps"
LOG_DIR = BASE_DIR / "tunnel_logs"

def save_and_extract(uploaded_file, save_dir):
    os.makedirs(save_dir, exist_ok=True)
    file_path = save_dir / uploaded_file.filename
    with open(file_path, "wb") as f:
        f.write(uploaded_file.file.read())
    shutil.unpack_archive(str(file_path), extract_dir=save_dir)
    os.remove(file_path)

def build_and_run_docker(mcp_path, exposed_port=9002):
    image_tag = f"mcp-{uuid.uuid4()}"
    subprocess.run(["docker", "build", "-t", image_tag, "."], cwd=mcp_path, check=True)
    subprocess.Popen(["docker", "run", "-d", "-p", f"{exposed_port}:{exposed_port}", image_tag])
    return exposed_port

def create_cloudflared_tunnel(local_url: str):
    os.makedirs(LOG_DIR, exist_ok=True)
    log_file = LOG_DIR / f"{uuid.uuid4()}.log"

    proc = subprocess.Popen(
        ["cloudflared", "tunnel", "--url", local_url],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    with open(log_file, "w") as log:
        for line in proc.stdout:
            log.write(line)
            if "trycloudflare.com" in line:
                parts = line.strip().split()
                for part in parts:
                    if part.startswith("https://") and "trycloudflare.com" in part:
                        return part

    raise RuntimeError("Failed to detect tunnel URL from cloudflared.")