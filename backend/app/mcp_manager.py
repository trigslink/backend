import uuid
import os
import shutil
import subprocess
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
MCP_DIR = BASE_DIR / "registered_mcps"
LOG_DIR = BASE_DIR / "tunnel_logs"

def save_and_extract(uploaded_file, save_dir: Path):
    os.makedirs(save_dir, exist_ok=True)
    file_path = save_dir / uploaded_file.filename

    with open(file_path, "wb") as f:
        f.write(uploaded_file.file.read())

    shutil.unpack_archive(str(file_path), extract_dir=str(save_dir))
    os.remove(file_path)

def build_and_run_docker(mcp_path: Path, exposed_port: int = 9002) -> int:
    image_tag = f"mcp-{uuid.uuid4()}"
    subprocess.run(["docker", "build", "-t", image_tag, "."], cwd=str(mcp_path), check=True)
    subprocess.Popen(["docker", "run", "-d", "-p", f"{exposed_port}:{exposed_port}", image_tag])
    return exposed_port

def create_cloudflared_tunnel(port: int) -> str:
    os.makedirs(LOG_DIR, exist_ok=True)
    log_file = LOG_DIR / f"{uuid.uuid4()}.log"

    proc = subprocess.Popen(
        ["cloudflared", "tunnel", "--url", f"http://localhost:{port}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    with open(log_file, "w") as log:
        if not proc.stdout:
            raise RuntimeError("cloudflared failed to start properly")

        for line in proc.stdout:
            log.write(line)
            if "trycloudflare.com" in line:
                for word in line.strip().split():
                    if word.startswith("https://") and "trycloudflare.com" in word:
                        return word

    raise RuntimeError("Failed to detect tunnel URL from cloudflared.")