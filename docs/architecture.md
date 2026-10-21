# SlothSwitch Architecture Specification

## Overview

SlothSwitch is an open-source AI decision and execution engine designed to eliminate unnecessary generative inference. Instead of dispatching every operational request to a heavy generative model, SlothSwitch routes tasks through a structured decision model (**Laya**), enforces strict deterministic safety and authorization policies (**WorkflowPolicy**), and executes safe, registered tools directly (**ToolExecutor**). When natural language generation or technical synthesis is genuinely required, SlothSwitch delegates to a local **Google Gemma** model on CPU or GPU with zero cloud API keys.

```text
Incoming Operational Request
            |
            v
+-------------------------------------------------------------+
|  1. Workflow Registry & Action Space Definition            |
|     (Typed parameters, permissions, read-only vs mutating)  |
+-------------------------------------------------------------+
            |
            v
+-------------------------------------------------------------+
|  2. Laya Neural Decision Adapter                            |
|     (Projects workflow actions into typed choice questions) |
+-------------------------------------------------------------+
            |
            v
+-------------------------------------------------------------+
|  3. Deterministic Policy Gate (Authorizer)                  |
|     - Deny-list & permitted action enforcement              |
|     - Caller authorization (least-privilege permissions)    |
|     - Read-only mode constraints                            |
|     - Mandatory approval gates for mutating operations      |
|     - Decision confidence threshold acceptance              |
+-------------------------------------------------------------+
            |
            +---> Tool Action ------------> ToolExecutor (Deterministic API)
            +---> Generative Task --------> Local Google Gemma Adapter
            +---> Mutating Operation ------> WAITING_FOR_APPROVAL Gate
            +---> Missing Parameters ------> CLARIFY
            +---> Policy Violation --------> ABSTAIN / FALLBACK
            |
            v
+-------------------------------------------------------------+
|  4. Privacy-Aware Telemetry Recorder                        |
|     (Structured events, latency & token usage, zero secrets)|
+-------------------------------------------------------------+
```

---

## Core Components

### 1. Schemas (`src/slothswitch/schemas.py`)
Single source of truth for all structured data models:
- `DecisionOutcome`: `EXECUTE_TOOL`, `USE_GENERATIVE_MODEL`, `CLARIFY`, `ABSTAIN`, `HUMAN_REVIEW`, `FALLBACK`
- `ExecutionState`: `ACCEPTED`, `VALIDATING`, `WAITING_FOR_APPROVAL`, `EXECUTING`, `SUCCEEDED`, `FAILED`, `ABSTAINED`
- `ActionDecision`: Structured action proposal with target workflow, action ID, confidence, and reasoning.
- `WorkflowExecutionResult`: Comprehensive result with execution state, output, error handling, token counts, and latency.

### 2. Workflow Registry (`src/slothswitch/registry.py` & `src/slothswitch/workflows/base.py`)
Separates workflow specifications from core execution:
- `ActionDefinition`: ID, semantic description, parameter schemas, output schemas, permissions, mutating flags, approval requirements, and timeout limits.
- `WorkflowDefinition`: Typed bundle of actions and policies.
- `WorkflowRegistry`: Thread-safe registry with duplicate action detection and dynamic discovery.

### 3. Safe Tool Execution Engine (`src/slothswitch/executor.py`)
Enforces the 9-step safe execution protocol:
1. Confirm action registration in workflow.
2. Validate parameters against schema.
3. Check caller authorization (required permissions).
4. Enforce workflow policy (read-only mode, allowed actions).
5. Check approval requirements (returns `WAITING_FOR_APPROVAL` with single-use approval token if required).
6. Enforce execution timeouts.
7. Invoke registered `ToolAdapter`.
8. Validate structured output.
9. Record privacy-aware telemetry event.

### 4. Workflows

#### A. GitHub Issue & PR Management (`src/slothswitch/workflows/github_pr_management.py`)
- **Read-Only Direct Actions**: `count_pull_requests`, `list_open_pull_requests`, `get_pull_request_details`, `count_issues`, `list_open_issues`, `get_issue_details`, `get_pull_request_checks`, `list_repository_labels`.
- **Approval-Gated Mutating Actions**: `add_issue_label`, `add_pull_request_label`, `create_issue_comment`.
- **Generative Tasks**: `summarize_pull_requests`, `summarize_issue_concerns`, `generate_repository_activity_report`.

#### B. System Operations (`src/slothswitch/workflows/system_ops.py`)
Proves non-GitHub engine reusability:
- `get_system_health`: Real host platform, OS, and CPU metrics.
- `get_disk_usage`: Real disk partition storage analysis.
- `clean_temp_cache`: Approval-gated cache cleaning.
- `summarize_system_status`: Generative sysadmin reporting.

### 5. Local Gemma Adapter (`src/slothswitch/adapters/generative/gemma_local.py`)
Runs Google Gemma (e.g., `google/gemma-2-2b-it`) locally:
- Runs via Hugging Face Transformers on CPU or GPU without external API keys.
- Enforces input bounding (max length) and prompt injection protection (`<<<UNTRUSTED_CONTENT>>>` delimiter sandboxing).
- Tracks token consumption and distinguishes real measured latency from simulated values.

### 6. Laya Decision Adapter (`src/slothswitch/adapters/decision/laya_adapter.py`)
- Uses Convai ModernBERT (`convaiinnovations/laya`) to dynamically project workflow action spaces into typed `choice` questions.
- Selects the target tool or generative delegation path with calibrated softmax confidence scores.

---

## Benchmark Baselines & Results

Evaluated over the strictly held-out test split of the GitHub Workflow Benchmark (`datasets/github_workflow_benchmark.json`):

| Metric | Baseline A (Always-Gemma) | Baseline B (Deterministic Rules) | Baseline C (SlothSwitch) |
| :--- | :--- | :--- | :--- |
| **Accuracy** | 15.2% | 69.7% | **81.8%** |
| **Gemma Model Calls** | 33 / 33 (100%) | 5 / 33 | **5 / 33** |
| **Direct Tool Executions** | 0 | 18 | **28** |
| **Avoided Generative Calls**| 0.0% | 84.85% | **84.85%** |
| **Total Tokens Consumed** | 2,310 | 500 | **350** (-84.8%) |
| **Median Latency** | High (Full Generation) | Fast | **Sub-millisecond Routing** |
