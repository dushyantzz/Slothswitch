import os

from dotenv import load_dotenv

load_dotenv()

from huggingface_hub import hf_hub_download

print("HF_TOKEN present:", bool(os.getenv("HF_TOKEN")))
token = os.getenv("HF_TOKEN")

print("Testing download of config.json...")
try:
    path = hf_hub_download(repo_id="google/gemma-2-2b-it", filename="config.json", token=token)
    print("Downloaded config.json to:", path)
except Exception as e:
    print("Failed to download config.json:", type(e), e)

print("Testing download of model-00001-of-00002.safetensors...")
try:
    path2 = hf_hub_download(repo_id="google/gemma-2-2b-it", filename="model-00001-of-00002.safetensors", token=token)
    print("Downloaded shard 1 to:", path2)
except Exception as e:
    print("Failed to download shard 1:", type(e), e)
