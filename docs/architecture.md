# SlothSwitch Architecture Specification

## Overview

SlothSwitch is an open-source, configurable AI routing layer that reduces inference expenditure while preserving task quality. It operates between client applications and AI model providers.

```text
Incoming Request
      |
      v
+-------------------------------------------------------------+
|  1. Input Validation & Privacy Redaction                    |
|     (Size bounds, content type, PII scrubber)               |
+-------------------------------------------------------------+
      |
      v
+-------------------------------------------------------------+
|  2. Routing Feature Extraction                              |
|     (Word/char counts, code blocks, keyword categories)     |
+-------------------------------------------------------------+
      |
      v
+-------------------------------------------------------------+
|  3. Decision Model Adapter                                  |
|     (Laya Router / Mock Heuristic Proposer)                 |
+-------------------------------------------------------------+
      |
      v
+-------------------------------------------------------------+
|  4. Deterministic Policy Gate (Authorizer)                  |
|     - Route membership & enabled status                     |
|     - Caller cost tier & allowed routes                     |
|     - High-risk category escalation (Security/Legal)        |
|     - Confidence threshold acceptance                       |
+-------------------------------------------------------------+
      |
      +---> Accepted FAST_PATH -------> Deterministic Handler
      +---> Accepted SMALL_LLM -------> Efficient Generative Model
      +---> Accepted LARGE_LLM -------> Capable LLM Provider
      +---> Missing Information ------> Clarification Generator
      +---> Policy Violation / Unsure -> Safe Fallback
      +---> High Risk Escalation -----> Human Review Queue
      |
      v
+-------------------------------------------------------------+
|  5. Privacy-Aware Telemetry Recorder                        |
|     (JSONL logs without raw prompts, latency & cost metrics)|
+-------------------------------------------------------------+
```

---

## Core Components

### 1. Schemas (`src/slothswitch/schemas.py`)
Single source of truth for all data models across the routing lifecycle:
- `RouteCategory`: `FAST_PATH`, `SMALL_LLM`, `LARGE_LLM`, `CLARIFY`, `FALLBACK`, `HUMAN_REVIEW`
- `RoutingRequest`: Typed input payload with optional caller constraints (`allowed_routes`, `max_cost_tier`)
- `RouteDecision`: Output of the decision phase containing proposed route, confidence, and policy acceptance status
- `TaskResult`: Execution outcome containing generated text, model identifier, token counts, latency, and estimated cost
- `RoutingRecord`: Unified record combining the request, routing decision, and task result

### 2. Preprocessing & Privacy (`src/slothswitch/preprocessing.py`)
- **Validation**: Enforces strict size bounds (default 10,000 characters) and MIME content types (`text/plain`).
- **PII Redaction**: Regex-based redaction of emails, telephone numbers, credit cards, and secret tokens before features or state summaries are passed to decision models.
- **Feature Extraction**: Computes length, syntax cues (code blocks, questions), and category hints without retaining raw text.

### 3. Policy Engine (`src/slothswitch/policy.py`)
The deterministic gatekeeper. The decision model *proposes*; the policy layer *authorizes*.
- If the decision model returns an invalid or disabled route, policy forces `FALLBACK`.
- If caller limits cost tier below the chosen model, policy forces `FALLBACK`.
- If keywords or metadata indicate `security`, `legal`, or `financial` risks, policy forces escalation to `HUMAN_REVIEW` or `LARGE_LLM`.
- If confidence is below `acceptance_threshold`, policy diverts to `FALLBACK`.

### 4. Adapters (`src/slothswitch/adapters/`)
Clean abstract interfaces isolate provider and framework dependencies:
- `DecisionAdapter`: Interface for route proposers (`MockDecisionAdapter`, `LayaDecisionAdapter`).
- `TaskModelAdapter`: Interface for execution providers (`MockSmallLLMAdapter`, `MockLargeLLMAdapter`, `StaticResponseAdapter`).

### 5. Router Orchestrator (`src/slothswitch/router.py`)
Ties together preprocessing, decision model, policy gate, task dispatch, and telemetry. Also supports **baseline mode** (`baseline_mode=True`), routing all requests to a fixed capable model for comparative benchmarking.

### 6. Telemetry & Evaluation (`src/slothswitch/telemetry.py`, `src/slothswitch/evaluation/`)
- Telemetry outputs structured JSONL without logging raw customer content.
- Evaluation harness computes multi-label accuracy, macro-F1, per-route confusion metrics, latency, and cost savings.
