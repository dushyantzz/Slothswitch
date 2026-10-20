# SlothSwitch --- Coding Agent Master Prompt

## Mission

Build **SlothSwitch**, an open-source, developer-focused AI routing
layer that tries to reduce inference expenditure while preserving
acceptable task quality.

SlothSwitch should inspect an incoming request and select an appropriate
processing path: deterministic logic or a lightweight decision model for
bounded tasks, a smaller generative model for suitable generation tasks,
or a more capable LLM for requests that genuinely require it. It must
also be able to abstain, ask for clarification, or escalate when it
cannot make a sufficiently reliable routing decision.

The central engineering problem is **not merely calling models**. It is
implementing and evaluating a legitimate routing policy that determines
when a request should go to a decision model such as Laya, when it
should go to a generative LLM, and when the system should choose a safer
fallback.

Build a working, testable MVP first. Do not overbuild a universal
framework before demonstrating value on a bounded workload.

## Product statement

**SlothSwitch: Stop spending big-model compute on small decisions.**

A configurable routing layer that evaluates a request, selects the least
expensive eligible processing path under quality and safety constraints,
executes that path, and records enough evidence to compare the result
with a fixed-model baseline.

The product should eventually be extensible to multiple domains, but it
must not claim to be universally accurate out of the box. The first
implementation should target a clearly defined workload (recommended:
customer-support request processing) and use adapters/configuration so
other domains can be added later.

## Core principles

1.  **Measure before claiming.** Never invent or imply benchmark
    results, accuracy, savings, or latency improvements. Clearly label
    illustrative data.
2.  **Quality-constrained cost reduction.** Select the lowest-cost path
    that meets a defined quality target; do not always choose the
    cheapest model.
3.  **Decision model versus task model.** A decision model proposes a
    structured route. The chosen processing component performs the
    actual user task.
4.  **Policy authorizes; model proposes.** Model output must be
    validated against deterministic policy and configured restrictions
    before execution.
5.  **Abstention is a valid result.** Support `clarify`, `fallback`, and
    `human_review` outcomes when the router is uncertain, unsupported,
    or outside its validated scope.
6.  **No unverified confidence assumptions.** A confidence/probability
    value is not automatically a calibrated probability of correctness.
    Validate thresholds on held-out data.
7.  **Provider/model neutrality.** Use adapter interfaces and
    configuration. Do not hardwire a single proprietary provider into
    the core.
8.  **Privacy by design.** Do not log raw prompts by default. Redact
    secrets and sensitive information; allow opt-in diagnostic samples.
9.  **Safe defaults.** Never execute arbitrary tools, perform
    destructive actions, or send sensitive data to external providers
    without explicit configuration and safeguards.
10. **Small, reviewable increments.** Implement, test, document, and
    update `decision.md` after every meaningful task.

## Mandatory discovery and verification before coding

Before implementing integrations:

-   Verify the current official documentation, repository, package name,
    supported API, license, runtime requirements, and model availability
    for Laya and any proposed decision models.
-   Verify the official Tinker documentation, supported base models,
    current setup and billing requirements, and challenge prize rules
    before attempting fine-tuning.
-   Verify any selected model's Hugging Face model card, license, usage
    restrictions, hardware requirements, and inference interface.
-   Do not assume Laya and Vega are interchangeable, that either
    supports a particular schema, or that a confidence field has a
    particular meaning. Inspect the actual current APIs.
-   If an integration is unavailable, incompatible, or too costly,
    document the limitation and implement a clean adapter/mock so the
    rest of the application remains testable. Do not silently substitute
    a different model while claiming to use the intended one.
-   Keep a `docs/technology-decisions.md` (or equivalent) with source
    links, licenses, assumptions, and decisions.

## Proposed high-level architecture

``` text
Incoming Request
      |
      v
Input validation / redaction / deterministic checks
      |
      +---- exact safe cache or deterministic handler? ----> Return result
      |
      v
Routing feature extraction
      |
      v
Decision model adapter (initially Laya if verified)
      |
      v
Routing policy / validation gate
      |
      +---- accepted fast path ---------------------------> Decision/rule handler
      |
      +---- accepted small-model path --------------------> Small generative model
      |
      +---- accepted capable-model path ------------------> Capable LLM
      |
      +---- insufficient information ---------------------> Clarify
      |
      +---- uncertain / unsupported / policy restriction -> Fallback or human review
      |
      v
Output validation and response
      |
      v
Privacy-aware metrics / evaluation records
```

This is a target design, not a requirement to implement every path on
day one. Build the simplest complete path first.

## Routing logic: required behavior

The system must implement explicit, inspectable routing logic rather
than trusting a model's free-form explanation.

### Candidate route categories

Use a small configurable set, initially:

-   `FAST_PATH`: deterministic function or structured decision is
    sufficient; no generative LLM needed.
-   `SMALL_LLM`: natural-language generation or bounded processing can
    be handled by a configured smaller model.
-   `LARGE_LLM`: task appears to need capabilities only available in a
    configured stronger model.
-   `CLARIFY`: missing information prevents a reliable route or
    completion.
-   `FALLBACK`: route decision is invalid, unsupported, or fails
    validation; use configured safe behavior.
-   `HUMAN_REVIEW`: request is outside the validated scope or its risk
    requires human judgment.

Do not equate short prompts with easy tasks or long prompts with hard
tasks. Prompt length, token estimates, task category, number of
requested operations, and other metadata may be features, but they must
not be the only routing criterion.

### Decision pipeline

1.  **Validate input.** Enforce size limits, supported content types,
    and basic request schema.
2.  **Apply deterministic checks.** Handle known operations, explicit
    user/provider constraints, unsupported requests, and safe
    exact-cache hits where applicable. A cache must be opt-in and must
    account for privacy, freshness, and correctness.
3.  **Build routing context.** Extract only relevant features. Avoid
    retaining raw user content unless explicitly enabled.
4.  **Ask the decision model a bounded question.** Use a typed choice or
    schema supported by the verified model API. Include clear
    definitions of the routes and the configured workload's constraints.
5.  **Validate the result.** Check route membership, schema, policy
    permissions, model availability, and whether the request category is
    within the evaluated domain.
6.  **Apply acceptance criteria.** Use thresholds established from
    validation data. Do not choose arbitrary confidence thresholds and
    describe them as statistically justified.
7.  **Dispatch.** Invoke only the selected adapter. Record route and
    timing metrics.
8.  **Handle errors.** If a model fails, times out, returns invalid
    output, or is unavailable, follow an explicit fallback policy. Avoid
    infinite retries or repeated paid calls.
9.  **Validate output.** Enforce configured output schemas and response
    limits.
10. **Record outcome.** Track route, model/version, latency, token usage
    and cost when available, fallback, and evaluation outcome when
    known. Do not confuse route confidence with final answer quality.

### Decision acceptance and uncertainty

-   Do not trust model confidence without evaluation.
-   Support per-route and per-task acceptance policies.
-   Keep thresholds configurable and document how they were chosen.
-   If the request is outside the benchmark's domain, use a conservative
    fallback rather than extrapolating the measured accuracy.
-   For high-consequence or security-sensitive tasks, do not let a
    learned router override deterministic authorization or safety
    policy.
-   Vega may be evaluated later as a selective verifier for ambiguous
    cases, but it is **not a mandatory dependency for the MVP**. Include
    it only if its current interface is verified and experiments show a
    measurable benefit.

## Verified Laya integration guidance (based on the official Hugging Face model card)

Primary source: https://huggingface.co/convaiinnovations/laya  
Library documentation: https://nandhakishorm.github.io/laya  
Official code repository: https://github.com/NandhaKishorM/laya

**Read the current model card and relevant library documentation before coding.** The following guidance reflects the model card available when this prompt was prepared; verify it again during implementation because APIs and guidance may change.

### Installation and recommended API

The model card documents `pip install laya` and Python 3.10+. Its recommended production-style entry point is `Router`:

```python
from laya import Router

router = Router()  # lazy loading; downloads the selected checkpoint on first use

state = {
    "subject": "Duplicate charge on invoice",
    "body": "I was billed twice and would like a refund."
}

questions = {
    "department": {
        "type": "choice",
        "instructions": "Which department should handle this request?",
        "criteria": {
            "billing": "Invoices, payments, refunds",
            "technical": "Bugs, outages, system errors",
            "other": "Everything else"
        }
    }
}

result = router.predict(state, questions)
route = result["answers"]["department"]["choice"]
routing_metadata = result.get("routing", {})
```

This is an illustrative integration based on the documented API. Smoke-test the installed version and actual result schema. Keep Laya-specific details inside an adapter.

Laya supports typed questions including `choice`, `score`, and `noul`. Use `choice` for SlothSwitch's primary route selection because explicit labels and descriptions make route meanings clear. Use `score` only for a meaningful, validated ordinal scale. The model card warns that `noul` can follow option labels instead of the state in some cases; test it carefully and consider a neutral two-option `choice` formulation instead.

### Checkpoint selection is important

The model card describes these checkpoints:
- `convaiinnovations/laya` (English/root): English text and relatively small decision sets.
- `convaiinnovations/laya-multilingual`: multilingual requests; the `Router` can select it using language/script detection. Explicitly choose `model="multilingual"` when appropriate, especially for long mostly-English text where automatic routing may otherwise select the English checkpoint.
- `convaiinnovations/laya-typed-decisions`: a checkpoint fine-tuned for the documented typed-decision workflows.

Do not assume the base/root checkpoint is a strong zero-shot router. The current model card reports weak base-checkpoint results on its typed-decisions benchmark and substantially stronger results from the fine-tuned typed-decisions checkpoint. These results do not guarantee performance on SlothSwitch, but they mean we must benchmark relevant checkpoints on our own labeled routing data before choosing a default. If zero-shot performance is inadequate, investigate domain-specific fine-tuning rather than hiding weak results.

### Use Laya for bounded decisions, not generation

Laya is a non-autoregressive structured decision model; it does not generate the final natural-language answer. Use it to answer bounded questions such as which configured path is appropriate, which supported task category applies, whether essential information is missing, or whether a request is outside the supported task set. Send generation, complex debugging, summarization, and multi-step reasoning to the selected task model after the route passes the policy gate.

Use a small set of well-defined route options with distinct descriptions. Avoid overlapping labels. The model card warns that high-cardinality choices can lose accuracy when option text is squeezed into the available token budget. For large option sets, use hierarchical coarse-to-fine routing or adjust token budgets only after checking the installed API and evaluating the change.

### Confidence, calibration, and abstention

The model card warns that base checkpoints can be overconfident and that confidence is not universally reliable across domains. It reports improved calibration after fitting temperatures on labeled data and says `action.act_probability` is not a reliable gating signal in the described version.

Therefore:
- Do not gate on `action.act_probability`.
- Inspect the exact confidence field exposed by the installed version and validate it on held-out SlothSwitch examples.
- Measure calibration using ECE and/or Brier score where appropriate.
- Fit calibration temperatures on a validation split only, grouped by question type and option count when supported and justified; never fit on the held-out test set.
- Select acceptance thresholds based on measured selective risk and coverage, not a guessed universal number.
- For low-confidence, unsupported, malformed, or high-risk decisions, abstain, clarify, or use the configured safe fallback.
- Log checkpoint/version, question schema version, confidence, chosen route, and acceptance status without logging sensitive raw request text by default.

The model card gives an example of the English checkpoint being confidently wrong on non-Latin text. Use the documented language-aware `Router` or explicitly select the appropriate multilingual checkpoint; confidence gating cannot compensate for a wrong checkpoint.

### State length, batching, memory, and latency

The model card notes that context limits differ by checkpoint and that the multilingual checkpoint supports longer documents when configured with `max_len=8192`; the default can truncate long input. For long requests, verify the selected checkpoint's supported `max_len` and token budget, test for truncation, and measure accuracy and latency. Use a bounded relevant summary only if it preserves information needed for routing.

Laya can answer multiple typed questions in one `predict(state, questions)` call. Batch related routing questions when this improves consistency without making the schema ambiguous. Benchmark batching in the target environment.

For a server/demo, preload only the checkpoints actually needed. Preloading trades startup time and memory for lower per-request latency. Do not preload all checkpoints on memory-constrained hosting without measuring resource use. If loading hangs in an environment with TensorFlow installed, the model card documents `USE_TF=0` as a potential workaround; use it only if needed and verify against current documentation.

### Required Laya integration tasks

1. Create a `LayaDecisionAdapter` with a narrow interface; do not leak Laya imports into policy/evaluation code.
2. Add a startup smoke test that loads the configured checkpoint and runs a known example.
3. Store checkpoint selection and question definitions in configuration where practical.
4. Use explicit route labels and validate every returned label.
5. Test malformed output, missing confidence, low confidence, unsupported routes, timeout/load failure, long input, and multilingual input if supported.
6. Compare feasible relevant checkpoints on the project's labeled dataset before selecting the default.
7. Add calibration analysis and threshold selection before enabling automatic routing in the demo.
8. Maintain a baseline mode that sends all requests to the same configured capable model.
9. Never claim that published model-card accuracy, speed, or calibration results apply to SlothSwitch; report only results measured on SlothSwitch data and hardware.
10. Record source links, package/checkpoint versions, license, hardware, and findings in `docs/technology-decisions.md` and `decision.md`.

## MVP scope

Build these features first:

1.  Python package and a clear public API.
2.  One bounded workload, recommended: customer-support request routing.
3.  Decision-model adapter interface, with Laya as the initial
    integration only after its current official API and license are
    verified.
4.  Deterministic baseline and policy engine.
5.  Configurable processing paths:
    -   local deterministic/decision path;
    -   optional small open-weight generative model;
    -   optional capable model/provider;
    -   fallback/clarification.
6.  Mock adapters so tests and demos can run without API keys.
7.  A reproducible evaluation harness.
8.  A command-line demo and a small web demo only after the core routing
    works.
9.  Privacy-aware structured telemetry.
10. Tests, examples, README, setup instructions, and `decision.md`.

Use a provider-neutral interface, for example:

``` python
class DecisionRouter:
    def choose_route(self, request, context) -> "RouteDecision":
        ...

class TaskModel:
    def execute(self, request, context) -> "TaskResult":
        ...
```

These signatures are illustrative. Adapt them to the actual codebase and
keep model-specific details inside adapters.

## Benchmark and evaluation --- a first-class feature

The project must prove both routing behavior and end-task usefulness. Do
not report only router accuracy.

### Dataset

-   Create or curate a small, documented dataset for the MVP workload.
-   Record each example's task type and acceptable processing path(s).
-   Use human-reviewed labels or objective task-specific checks where
    feasible.
-   Distinguish gold labels from weak labels derived from existing data.
-   Split data into development/validation and held-out test sets before
    tuning policy thresholds.
-   Avoid near-duplicate leakage across splits.
-   Document data provenance, licenses, and privacy considerations.
-   Do not include secrets, private tickets, or personal data without
    authorization.

A request may have multiple acceptable routes. Define acceptability
using the task's quality requirement and actual evaluation, not
intuition alone.

### Baselines to compare

At minimum:

1.  **Fixed capable-model baseline:** every request uses the same
    capable configured model.
2.  **Deterministic baseline:** simple rules/features only, where
    appropriate.
3.  **SlothSwitch:** decision model plus policy-based routing.
4.  **Optional selective verification:** Laya plus Vega only if
    implemented and tested.

Run strategies on the same held-out examples and comparable
configurations.

### Metrics

Report, where applicable:

-   Route accuracy and macro-F1.
-   Per-route precision and recall and confusion matrix.
-   Accepted-decision error rate (selective risk).
-   Coverage/automation rate and abstention/escalation rate.
-   End-task quality using task-specific metrics or blinded human
    evaluation.
-   Cost per request and total estimated/API-reported inference cost.
-   Router overhead and end-to-end median/p95 latency.
-   Calls and tokens per model/path.
-   Fallback/error rate.
-   Quality-cost trade-off at different acceptance thresholds.

Clearly distinguish: - routing confidence; - routing correctness; -
final task quality; - API charges; - estimated local compute cost.

Do not claim savings merely because a small model was selected. Include
the router's own overhead and all downstream calls. If using mocked
costs, label them simulated. If comparing models with different output
quality, show the quality trade-off.

## Optional Tinker experiment

Tinker is an optional extension and potential partner-prize route, not a
prerequisite for a functional MVP.

If pursued:

1.  Verify current official Tinker documentation, supported model
    families, account/billing requirements, and the exact contest
    eligibility rules.
2.  Define a specific supervised task, such as routing classification,
    with labeled examples.
3.  Fine-tune a supported open-weight language model using Tinker; do
    not claim this fine-tunes Laya unless the supported workflow
    explicitly does so.
4.  Compare the fine-tuned model against the same base model on a
    held-out set.
5.  Report improvements or regressions honestly, including latency/cost
    implications.
6.  Keep the Tinker experiment isolated so the core product works
    without it.

Do not add TabPFN to the core router by default. It may be explored
later for tabular routing features only after checking current model
version, licensing, and suitability. Do not pursue Arduino hardware
integration unless it directly improves the product. Render can be used
for a hosted demo, but model inference may need to run separately.

## Security, reliability, and privacy

-   Keep secrets in environment variables or the deployment platform's
    secret manager; never commit `.env` or API keys.
-   Provide `.env.example` containing placeholders only.
-   Add request timeouts, bounded retries, concurrency limits, and
    graceful provider failure handling.
-   Validate all model outputs before using them.
-   Never execute arbitrary code or tools based solely on a
    model-generated route.
-   Avoid logging raw request text by default; document retention and
    redaction.
-   Make external model calls explicit in configuration.
-   Show which provider/model will receive a request where practical.
-   Avoid hidden or unexpected paid calls.
-   Add dependency/license documentation.
-   Include rate limiting if a public demo is deployed.

## Suggested repository layout

Adapt as needed, but keep responsibilities separated:

``` text
slothswitch/
  README.md
  decision.md
  pyproject.toml
  .env.example
  .gitignore
  config/
    routing.yaml
  src/slothswitch/
    api.py
    router.py
    policy.py
    schemas.py
    preprocessing.py
    telemetry.py
    evaluation/
    adapters/
      decision/
      task_models/
  tests/
    unit/
    integration/
  datasets/
    README.md
  examples/
  docs/
    architecture.md
    evaluation.md
    technology-decisions.md
  demo/
```

Do not commit private datasets, model weights, secrets, or generated
artifacts unnecessarily.

## Required `decision.md` living log

Create `decision.md` at the repository root before or during the first
implementation task. **After every meaningful task, update it before
declaring the task complete.** This is mandatory.

For each task, record:

-   Date/time or task identifier.
-   What was done.
-   Why it was done.
-   Files/components changed.
-   Tools, libraries, models, and technologies used.
-   How the work helps the product or validates a hypothesis.
-   Tests/commands run and their outcomes.
-   Evidence/results, including measured values when available.
-   Decisions made, assumptions, trade-offs, and alternatives rejected.
-   Blockers, limitations, and next steps.

Use this format:

``` markdown
## Task: <short title>
- Status: Complete / Partial / Blocked
- What was done:
- Why:
- Files changed:
- Tools and technologies:
- How this helps:
- Tests and results:
- Evidence/metrics:
- Decisions and trade-offs:
- Remaining work:
- Next task:
```

Do not fabricate completed work, test results, citations, metrics, or
tool usage. Mark incomplete work as partial or blocked. Keep earlier
entries; append new entries rather than silently rewriting history. Also
update relevant architecture/evaluation docs when decisions materially
change.

## Development workflow for the coding agent

For every task:

1.  Inspect the repository and current state before changing files.
2.  State a concise plan.
3.  Implement one coherent increment.
4.  Run relevant tests, linting, and type checks where configured.
5.  Inspect the diff for mistakes, secrets, and unrelated changes.
6.  Update `decision.md` with what was done, why, tools used, tests,
    evidence, and next steps.
7.  Report what is complete, what is unverified, and what is next.

Do not claim the product is universal or production-ready unless
evidence supports that claim. Do not implement speculative features
before the core evaluation works.

## Definition of done for the MVP

The MVP is complete when:

-   A developer can run the project from documented instructions.
-   The system accepts a request and returns an inspectable route
    decision.
-   The route is validated by a policy layer before dispatch.
-   At least one real decision-model adapter works, or any blocked
    integration is clearly documented and a mock allows the rest to be
    tested.
-   At least two processing paths can be compared, with a safe fallback.
-   Unit tests cover valid routes, invalid outputs, uncertainty,
    provider failure, and fallback behavior.
-   A reproducible benchmark compares SlothSwitch with a baseline.
-   The report includes route quality, final-task quality where
    measurable, cost accounting, and latency.
-   No fabricated benchmark claims appear in the README or demo.
-   `decision.md` contains a truthful implementation log.
-   A new developer can understand the architecture and run the demo.

## Initial task for the coding agent

Start by inspecting the repository and verifying the current official
documentation and licensing for Laya and the proposed model/runtime
integrations. Then create `decision.md`, a concise architecture plan, a
technology-decision record, and a minimal runnable skeleton with mock
adapters and tests. Do not begin with a large frontend or fine-tuning
run. First establish the route schema, policy boundary, baseline, and
evaluation plan. After each task, update `decision.md` as specified
above.
