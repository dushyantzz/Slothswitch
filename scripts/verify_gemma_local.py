"""Verify google/gemma-2-2b-it local inference using Hugging Face cache/auth."""

import os
import time
from dotenv import load_dotenv

load_dotenv()

from slothswitch.adapters.generative.gemma_local import LocalGemmaAdapter

print("=" * 60)
print("VERIFYING GOOGLE GEMMA 2-2B-IT LOCAL INFERENCE")
print("=" * 60)

start_init = time.perf_counter()
adapter = LocalGemmaAdapter(model_id="google/gemma-2-2b-it", lazy_load=False)
init_latency_s = time.perf_counter() - start_init
print(f"Model successfully loaded in {init_latency_s:.2f} s on device: {adapter.device}")

# Health check
assert adapter.health_check() is True, "Health check failed!"
print("Health check: PASSED")

# Run actual inference
test_prompt = "Explain in one concise sentence what a Git pull request is."
print(f"\nSending test prompt: '{test_prompt}'")

start_gen = time.perf_counter()
res = adapter.generate(prompt=test_prompt, max_new_tokens=60, temperature=0.1)
gen_latency_s = time.perf_counter() - start_gen

print("\n--- Model Output ---")
print(res.output)
print("--------------------")
print(f"Latency: {res.latency_ms:.1f} ms ({gen_latency_s:.2f} s)")
print(f"Tokens: {res.token_usage}")
print(f"Model Used: {res.model_used}")
print(f"Simulated Latency: {res.latency_is_simulated}")
print(f"Simulated Cost: {res.cost_is_simulated}")

assert res.output and len(res.output) > 10, "Inference output was empty or invalid!"
assert res.token_usage.get("completion_tokens", 0) > 0, "No completion tokens generated!"
print("\nGEMMA 2-2B-IT VERIFICATION SUCCESSFUL!")
