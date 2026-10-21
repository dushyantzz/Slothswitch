# Local Google Gemma Setup Guide

This guide describes how to configure and run Google Gemma locally with SlothSwitch without external cloud API keys or transmission of prompts to third-party providers.

## 1. Hardware & Memory Requirements

| Variant | Precision | Parameter Count | Required RAM / VRAM | Recommended Execution Device |
| :--- | :--- | :--- | :--- | :--- |
| `google/gemma-2-2b-it` | FP16 / FP32 | 2.6B | ~3.5 GB - 5.5 GB | NVIDIA GPU (>= 4 GB VRAM) or CPU (>= 8 GB RAM) |
| `google/gemma-1.1-2b-it`| FP16 / FP32 | 2.5B | ~3.0 GB - 5.0 GB | NVIDIA GPU or CPU |
| `TinyLlama/TinyLlama-1.1B-Chat-v1.0` (Fast lightweight alternative) | FP16 / FP32 | 1.1B | ~1.5 GB - 2.5 GB | CPU / GPU |

On this host machine (Windows 11, Intel Core i5-12450H, 16 GB RAM, NVIDIA GTX 1650 4 GB VRAM), `google/gemma-2-2b-it` runs smoothly on CPU or GPU with zero cloud dependencies.

## 2. Authentication & Model Access

Google Gemma models are gated on Hugging Face Hub under the Gemma Terms of Use.
To access official Gemma weights:
1. Visit https://huggingface.co/google/gemma-2-2b-it and accept the license terms.
2. Log in using the Hugging Face CLI:
   ```bash
   huggingface-cli login
   ```
3. Alternatively, export your token in your environment:
   ```bash
   export HF_TOKEN="hf_your_token_here"  # On Linux/macOS
   $env:HF_TOKEN="hf_your_token_here"     # On Windows PowerShell
   ```

## 3. Configuration in SlothSwitch

SlothSwitch automatically discovers your local model or falls back gracefully to configurable alternatives:

```bash
# Set primary local generative model ID or local directory path
$env:SLOTHSWITCH_GEMMA_MODEL_ID="google/gemma-2-2b-it"

# Or point to a local directory containing converted weights
$env:SLOTHSWITCH_GEMMA_MODEL_ID="C:/models/gemma-2-2b-it"
```

## 4. Programmatic Usage

```python
from slothswitch.adapters.generative import LocalGemmaAdapter

# Initialize adapter (lazy loading ensures weights load on first generation call)
adapter = LocalGemmaAdapter(model_id="google/gemma-2-2b-it")

# Perform real local inference
result = adapter.generate(
    prompt="Summarize repository status",
    max_new_tokens=150,
)

print(result.output)
print(f"Latency: {result.latency_ms:.1f} ms | Simulated: {result.latency_is_simulated}")
```

## 5. Security & Prompt Injection Protections

SlothSwitch enforces prompt isolation for all generative tasks:
- **Input Bounding**: Prompts and untrusted repository descriptions are truncated to prevent context overflow or denial-of-service.
- **Delimiter Sandboxing**: Untrusted PR descriptions and issue bodies are enclosed within `<<<UNTRUSTED_CONTENT>>> ... <<<END_UNTRUSTED_CONTENT>>>` tags.
- **System Boundary Prompts**: Instructions explicitly mandate that the model must NOT execute commands or directives embedded within untrusted repository texts.
- **Zero Tool Access**: Gemma does NOT receive raw GitHub credentials or unrestricted execution access; all mutating actions are performed deterministically through approval-gated tool adapters.
