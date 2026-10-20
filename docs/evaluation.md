# SlothSwitch Benchmark & Evaluation Report

## Executive Summary

To validate the core thesis of SlothSwitch—*reducing inference expenditure while maintaining task quality without blind trust in models*—we benchmarked the routing pipeline against a fixed capable-model baseline on the curated 20-sample `customer_support_routing.json` dataset.

---

## 1. Evaluation Methodology

### Dataset
- **Workload**: B2B SaaS Customer Support Requests
- **Size**: 20 curated examples
- **Categories**: `general`, `billing`, `account`, `sales`, `technical`, `security`, `legal`, `unclear`, `malformed`
- **Gold Standard**: `acceptable_routes` array allowing multi-path acceptability (e.g., both `FAST_PATH` and `SMALL_LLM` for simple account questions).

### Evaluated Strategies
1. **Fixed Capable-Model Baseline (`LARGE_LLM`)**: All requests dispatched directly to the large model regardless of complexity or risk.
2. **SlothSwitch Intelligent Routing**: Decision adapter proposal filtered through deterministic policy checks and risk escalation.

---

## 2. Empirical Benchmark Results

Measured locally via `python -m slothswitch.cli eval --dataset datasets/customer_support_routing.json`:

| Metric | Fixed Baseline (`LARGE_LLM`) | SlothSwitch Policy Router | Delta / Improvement |
|---|---|---|---|
| **Routing Accuracy** | 25.0% | **65.0%** | **+40.0%** |
| **Macro F1 Score** | 0.0667 | **0.5194** | **+0.4527** |
| **Fallback Rate** | 0.0% | 0.0% | Parity |
| **Average Decision Latency** | 0.08 ms | 0.11 ms | +0.03 ms overhead |
| **Escalation Coverage (Security/Legal)** | 0% (unflagged) | **100% (escalated to HUMAN_REVIEW)** | Verified safety gate |
| **Compute Offload Rate** | 0.0% (100% large model) | **75.0% routed away from large model** | Massive compute savings |

### Per-Route Precision & Recall (SlothSwitch)

```text
Route           Precision    Recall      
--------------- ------------ ------------
CLARIFY         1.000        0.250       
FALLBACK        0.000        0.000       
FAST_PATH       0.600        0.500       
HUMAN_REVIEW    0.800        1.000       
LARGE_LLM       1.000        0.500       
SMALL_LLM       0.500        0.800       
```

---

## 3. Analysis & Key Takeaways

1. **Compute Waste in Fixed Baselines**: The fixed capable model wastes high-cost compute on 75% of queries (basic FAQs, simple account inquiries, clarification needs) that do not require expensive LLM weights.
2. **Policy Prevents Silent Failure**: High-risk items (such as CVE vulnerability disclosures or GDPR data deletion requests) are caught deterministically by policy and escalated to `HUMAN_REVIEW` with 100% recall.
3. **Low Decision Overhead**: SlothSwitch routing adds only ~0.1 ms of processing time per query, making the routing layer negligible compared to model generation times (which typically range from 200 ms to 2,000 ms).
