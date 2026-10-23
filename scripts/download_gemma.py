import os
import sys

from dotenv import load_dotenv

load_dotenv()
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"
token = os.getenv("HF_TOKEN")

print("HF_TOKEN present:", bool(token), flush=True)

from huggingface_hub import snapshot_download

print("Starting fast snapshot download of google/gemma-2-2b-it...", flush=True)
try:
    path = snapshot_download(
        repo_id="google/gemma-2-2b-it",
        token=token,
        max_workers=8,
    )
    print("Download COMPLETE. Cached at:", path, flush=True)
except Exception as e:
    print("Download FAILED:", type(e), e, flush=True)
    sys.exit(1)
