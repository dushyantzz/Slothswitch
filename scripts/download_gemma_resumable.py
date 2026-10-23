import os
import sys
import time
import urllib.request
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()
token = os.getenv("HF_TOKEN")
if not token:
    print("ERROR: No HF_TOKEN found in environment", flush=True)
    sys.exit(1)

cache_dir = Path(os.path.expanduser("~/.cache/huggingface/hub/models--google--gemma-2-2b-it/snapshots/299a8560bedf22ed1c72a8a11e7dce4a7f9f51f8"))
cache_dir.mkdir(parents=True, exist_ok=True)

files = [
    ("model-00002-of-00002.safetensors", 240691728),
    ("model-00001-of-00002.safetensors", 4988025760),
]

for filename, expected_size in files:
    dest = cache_dir / filename
    part = cache_dir / f"{filename}.part"
    
    if dest.exists() and dest.stat().st_size == expected_size:
        print(f"File {filename} already complete ({dest.stat().st_size} bytes).", flush=True)
        continue
    
    downloaded = part.stat().st_size if part.exists() else 0
    if downloaded >= expected_size:
        part.rename(dest)
        print(f"File {filename} finished and renamed.", flush=True)
        continue

    print(f"Downloading {filename}: {downloaded}/{expected_size} bytes ({downloaded/expected_size*100:.1f}%)", flush=True)
    url = f"https://huggingface.co/google/gemma-2-2b-it/resolve/main/{filename}"
    
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {token}",
        "Range": f"bytes={downloaded}-"
    })
    
    t0 = time.time()
    last_log = t0
    bytes_since_log = 0
    
    try:
        with urllib.request.urlopen(req) as response:
            with open(part, "ab") as f:
                while True:
                    chunk = response.read(1024 * 1024)  # 1MB chunks
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    bytes_since_log += len(chunk)
                    
                    now = time.time()
                    if now - last_log >= 10.0:  # log every 10 seconds
                        speed_mb = (bytes_since_log / (1024 * 1024)) / (now - last_log)
                        pct = downloaded / expected_size * 100
                        print(f"[{filename}] {downloaded / 1024**2:.1f}/{expected_size / 1024**2:.1f} MB ({pct:.1f}%) at {speed_mb:.2f} MB/s", flush=True)
                        last_log = now
                        bytes_since_log = 0
                        
        if part.stat().st_size == expected_size:
            part.rename(dest)
            print(f"SUCCESS: {filename} downloaded and verified.", flush=True)
        else:
            print(f"WARNING: Size mismatch for {filename}: {part.stat().st_size} vs {expected_size}", flush=True)
    except Exception as e:
        print(f"Download error on {filename}: {e}", flush=True)
        sys.exit(1)

print("ALL GEMMA WEIGHTS READY!", flush=True)
