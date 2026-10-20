# SlothSwitch Datasets

This directory contains evaluation datasets for evaluating and benchmarking SlothSwitch routing strategies against baselines.

---

## Datasets

### 1. `customer_support_routing.json`

Curated benchmark dataset representing realistic customer support queries across a modern B2B SaaS platform.

- **Total examples**: 20
- **Domain**: Customer support request routing
- **Format**: JSON array of routing examples

#### Schema

Each record contains:
- `request_id` (string): Unique identifier for the query.
- `content` (string): The natural language query or support ticket text.
- `acceptable_routes` (list[string]): One or more valid target routes. In real systems, a query can often be safely answered by more than one tier (e.g. a simple FAQ can be handled by `FAST_PATH` or `SMALL_LLM`).
- `category` (string): Semantic task category (`general`, `billing`, `account`, `sales`, `technical`, `security`, `legal`, `unclear`, `malformed`).
- `notes` (string): Rationale for the acceptable routing targets.

#### Route Distribution

| Route Target | Expected Triggers | Example Categories |
|---|---|---|
| `FAST_PATH` | Deterministic FAQ, status checks, invoice lookups | general, billing |
| `SMALL_LLM` | Standard guidance, tier comparisons, UI navigation | account, sales, billing |
| `LARGE_LLM` | Distributed systems debugging, code generation, error tracebacks | technical |
| `CLARIFY` | Single-word, ambiguous, or fragmented queries | unclear |
| `FALLBACK` | Malformed, unintelligible or unroutable queries | malformed |
| `HUMAN_REVIEW` | Security vulnerabilities (CVE), legal demands, GDPR erasure, SLA financial breaches | security, legal |

#### Evaluation Protocol

1. **Splitting**: When evaluating, `slothswitch.evaluation.split_dataset` partitions the dataset deterministically (default 80% train/val, 20% held-out test) using a fixed random seed.
2. **Gold Standard Verification**: A route decision is considered accurate if the chosen route is in `acceptable_routes`.
3. **Metrics Reported**:
   - Overall Accuracy
   - Macro-averaged F1 Score
   - Per-route Precision and Recall
   - Fallback Rate
   - Average Latency (ms)
   - Simulated Inference Cost ($ USD)
