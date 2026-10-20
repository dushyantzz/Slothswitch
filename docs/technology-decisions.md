# Technology Decisions & Model Integration Record

This document records the official documentation, licensing, hardware requirements, APIs, and verified assumptions for all technologies and models integrated into SlothSwitch.

---

## 1. Decision Model: Laya

### Verification & Provenance
- **Model Card / Hub Repository**: [https://huggingface.co/convaiinnovations/laya](https://huggingface.co/convaiinnovations/laya)
- **Official Documentation**: [https://nandhakishorm.github.io/laya](https://nandhakishorm.github.io/laya)
- **Source Code Repository**: [https://github.com/NandhaKishorM/laya](https://github.com/NandhaKishorM/laya)
- **Package Name**: `laya` (Verified installed version: `0.4.12`)
- **License**: Apache 2.0 / MIT compatible open release
- **Runtime Environment**: Python 3.10+, PyTorch >= 2.0.0, Transformers >= 4.48.0

### Architectural Role in SlothSwitch
Laya is a non-autoregressive structured decision model designed specifically for bounded categorization tasks rather than free-form natural language generation. In SlothSwitch, Laya functions strictly as a **decision model**, proposing a route category (`FAST_PATH`, `SMALL_LLM`, `LARGE_LLM`, `CLARIFY`, `HUMAN_REVIEW`) from a small, clearly described candidate set. It does *not* generate user-facing task responses.

### Official API Usage
SlothSwitch integrates with Laya using the production-recommended entrypoint:
```python
from laya import Router

router = Router()
state = {
    "subject": redacted_subject,
    "body": redacted_summary,
    "word_count": str(word_count),
    "has_code": str(has_code),
    "category_hints": category_hints,
}
questions = {
    "route": {
        "type": "choice",
        "instructions": "Which processing path is most appropriate for this request?",
        "criteria": {
            "FAST_PATH": "Simple factual lookup, status check, or rule-based task...",
            "SMALL_LLM": "Standard text generation or routine customer support response...",
            "LARGE_LLM": "Complex reasoning, multi-step analysis, code debugging...",
            "CLARIFY": "Request is ambiguous or missing essential information...",
            "HUMAN_REVIEW": "Sensitive, risky, or compliance-critical topics...",
        }
    }
}
result = router.predict(state, questions)
chosen_route = result["answers"]["route"]["choice"]
confidence = result["answers"]["route"].get("confidence")
```

### Critical Verified Constraints & Guardrails
1. **Never gate on `action.act_probability`**: The model card explicitly warns that `act_probability` is uncalibrated in the current release. SlothSwitch relies strictly on verified `confidence` scores and policy bounds.
2. **Untrusted Confidence without Verification**: Confidence scores from non-autoregressive decision models are not true probabilities of task success. SlothSwitch places a deterministic policy gate in front of all route proposals.
3. **Checkpoints**:
   - `convaiinnovations/laya`: Default English/root checkpoint for small decision sets.
   - `convaiinnovations/laya-multilingual`: Multilingual variant with `max_len=8192` support.
   - `convaiinnovations/laya-typed-decisions`: Checkpoint fine-tuned for typed decision benchmarks.
4. **Environment Isolation**: All direct imports of `laya` are isolated within `src/slothswitch/adapters/decision/laya_adapter.py`. If Laya is not installed, or if offline operation is desired, SlothSwitch falls back cleanly to the heuristic `MockDecisionAdapter`.

---

## 2. Policy Engine: Deterministic Authorizer

### Principle: Policy Authorizes; Model Proposes
No machine-learning model is permitted to execute requests directly or bypass security and cost invariants. The `RoutingPolicy` enforces:
1. **Route Membership**: Proposed route must belong to `RouteCategory`.
2. **Route Enabled**: Disabled paths in `routing.yaml` trigger immediate fallback.
3. **Caller Constraints**: User-specified `allowed_routes` and `max_cost_tier` are enforced deterministically.
4. **High-Risk Escalation**: Sensitive categories (`security`, `legal`, `financial`) bypass low-cost paths and escalate to `HUMAN_REVIEW` or `LARGE_LLM`.
5. **Confidence Gating**: Requests below `acceptance_threshold` (default 0.7) fall back to safe handlers.

---

## 3. Privacy & Telemetry Architecture

### Redaction and Non-Retention
- Incoming text is scrubbed for sensitive patterns (RFC 5322 emails, E.164 phone numbers, credit card sequences, API keys).
- Raw prompts are **never written to disk or telemetry logs** unless `log_raw_prompts=True` is explicitly activated.
- Telemetry records request IDs, timestamp, chosen route, latency, token consumption, and cost estimates as append-only JSONL.

---

## 4. Evaluation Methodology & Baselines

### Baselines Compared
1. **Fixed Capable-Model Baseline (`LARGE_LLM`)**: Dispatches 100% of incoming requests to the highest-capability (and highest-cost) generative model.
2. **Deterministic Baseline**: Pure regex/keyword feature extraction.
3. **SlothSwitch Hybrid Router**: Decision model proposal + deterministic policy validation.

### Evaluation Metrics
- **Routing Accuracy**: Fraction of predictions matching `acceptable_routes`.
- **Macro-Averaged F1**: Unweighted mean of per-route F1 scores.
- **Fallback Rate**: Proportion of requests redirected to fallback due to policy rejection or uncertainty.
- **End-to-End Latency & Cost**: Router decision overhead vs. total downstream execution cost.
