# SlothSwitch Datasets

This directory contains evaluation datasets for evaluating and benchmarking SlothSwitch routing strategies against baselines.

---

## Datasets

### 1. `customer_support_routing.json`

Representative evaluation benchmark representing realistic customer support queries and engineering requests across a modern B2B SaaS platform.

- **Total examples**: 210
- **Domain**: Customer support and technical request routing
- **Format**: JSON array of structured routing examples

#### Task Types Covered

| Task Type | Description | Target Routes | Count |
|---|---|---|---|
| `simple_classification` | Ticket categorization, department assignment, priority tagging | `FAST_PATH`, `SMALL_LLM` | 30 |
| `information_extraction` | Extracting invoice numbers, tracking IDs, error codes, IPs | `FAST_PATH`, `SMALL_LLM` | 30 |
| `straightforward_generation` | Password reset, billing guidance, business hours, FAQ answers | `SMALL_LLM`, `FAST_PATH` | 40 |
| `complex_reasoning` | Distributed systems deadlocks, Postgres query plans, memory leaks, code debugging | `LARGE_LLM` | 40 |
| `ambiguous_requests` | Short, vague, or fragmented queries lacking context ("broken", "failed") | `CLARIFY` | 25 |
| `requests_requiring_clarification` | Actionable queries missing essential parameters (IDs, links, targets) | `CLARIFY` | 25 |
| `high_risk_escalation` | CVE exploits, GDPR erasure, SLA liquidated damages, fraud disputes | `HUMAN_REVIEW` | 15 |
| `malformed_unroutable` | Non-linguistic corrupted strings, binary/hex dumps | `FALLBACK`, `CLARIFY` | 5 |

#### Split Methodology

To ensure strict empirical validity and avoid data leakage:
- **Dev Split (`split: "dev"`)**: 147 examples (70%) used for policy threshold calibration, prompt analysis, and exploratory testing.
- **Held-Out Test Split (`split: "test"`)**: 63 examples (30%) strictly reserved for final benchmark reporting. Policy thresholds must never be tuned on this split.

#### Schema

Each record contains:
- `request_id` (string): Unique identifier (`cs-001` to `cs-210`).
- `content` (string): The natural language query or support ticket text.
- `task_type` (string): Semantic workload category.
- `category` (string): Domain topic (`billing`, `technical`, `account`, `security`, `legal`, `sales`, `general`, `malformed`).
- `split` (string): `"dev"` or `"test"`.
- `acceptable_routes` (list[string]): One or more valid target routes. In real systems, a query can often be safely answered by more than one tier.
- `expected_quality` (dict[string, float]): Expected final task quality score (0.0 to 1.0) under each processing route. Used to measure the end-task quality vs. cost trade-off.
- `notes` (string): Engineering rationale for routing targets.
