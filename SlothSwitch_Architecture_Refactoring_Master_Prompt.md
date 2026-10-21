# SlothSwitch --- Architecture Refactoring & Implementation Master Prompt

## Role

Act as a senior AI infrastructure engineer, ML systems engineer,
open-source maintainer, and production Python architect. Inspect,
refactor, implement, test, and document the existing SlothSwitch
repository. Do not merely propose an architecture.

Work incrementally. Preserve working code unless there is a documented
reason to change it. Run tests, inspect diffs, and never claim
functionality, performance, or production readiness without evidence.

## 1. Product vision

SlothSwitch is an open-source AI decision and execution engine that
avoids unnecessary generative-model inference.

-   **Laya:** Decision model that proposes a supported action from a
    workflow's defined action space.
-   **SlothSwitch policy engine:** Validates and authorizes the proposed
    decision.
-   **SlothSwitch execution engine:** Executes only explicitly
    registered tools/functions.
-   **Google Gemma running locally:** General-purpose generative model
    for tasks that genuinely require generation or synthesis.
-   **Workflow plugin:** Defines actions, schemas, permissions, and
    workflow-specific policies.

The default Gemma configuration must not require a cloud LLM API key.
Keep the generative-model interface provider-neutral so another
compatible model can be added later.

The core engine should be reusable across workflows, but do **not**
claim one Laya checkpoint automatically handles every workflow. Decision
quality must be evaluated for each workflow and action schema.

Use GitHub issue and pull-request management as the first end-to-end
example---not as a permanent limitation of the core product.

## 2. First step: audit the repository

Before changing code:

1.  Inspect repository structure, entry points, dependencies,
    configuration, API/CLI, adapters, policies, handlers, telemetry,
    datasets, benchmarks, tests, README, and `decision.md`.
2.  Run existing tests, linting, type checks, and coverage commands
    where configured.
3.  Identify which components use real model inference, real API calls,
    mocks, synthetic data, simulated costs, or artificial latency.
4.  Verify current Laya and Gemma documentation, supported APIs,
    package/runtime versions, licenses, model availability, and hardware
    requirements.
5.  Produce a concise audit and staged migration plan.
6.  Preserve existing functionality and tests. Do not rewrite the
    repository wholesale.

Historical reports mentioned 59 passing tests, 93% coverage, Ruff
success, and mypy success. These are historical claims only; rerun the
current repository to verify them. If benchmark handlers include names
such as `mock-small` or `mock-large`, determine exactly what is mocked.
Never silently use mocks in real benchmark mode.

## 3. Target architecture

``` text
User / Agent / Application
            |
            v
      SlothSwitch API
            |
            v
      Input Validation
            |
            v
      Workflow Registry
            |
            v
       Laya Decision Model
            |
            v
     Decision Validation
            |
            v
     Policy Enforcement
            |
       +----+----------------+
       |                     |
       v                     v
 Direct Tool Action     Generative Task
       |                     |
       v                     v
 Registered Tool        Local Gemma
       |                     |
       +----------+----------+
                  |
                  v
          Output Validation
                  |
                  v
          Execution Result
                  |
                  v
       Privacy-aware Telemetry
```

Enforce these boundaries:

1.  Laya proposes a structured decision.
2.  SlothSwitch validates it against the registered workflow.
3.  Policy determines whether the action is permitted.
4.  The executor invokes only registered implementations.
5.  Gemma is invoked only when generative processing is required and
    policy permits it.
6.  Invalid, unsupported, uncertain, or unsafe decisions must abstain,
    ask for clarification, fall back, or require human review.

Never let model output directly execute arbitrary Python, shell
commands, SQL, or unrestricted network operations. Never use `eval()` or
unrestricted `exec()` on model output.

## 4. Laya integration

Keep Laya as the decision model; do not replace it with Gemma.

Verify current official Laya documentation, repository, package version,
checkpoint names, supported input/output contract, license, and actual
inference behavior. Historical examples may be outdated.

Requirements:

-   Preserve the existing adapter if it works; refactor only as
    necessary.
-   Keep Laya-specific code inside its adapter.
-   Use typed, validated decision outputs.
-   Handle malformed predictions, unknown actions, missing/invalid
    parameters, timeouts, and model failures.
-   Support explicit abstention or unsupported-task outcomes.
-   Do not treat uncalibrated confidence as a guarantee.
-   Compare supported checkpoints on the project's own dataset.
-   Record checkpoint/version and evaluation results.
-   Verify whether Laya can accept runtime workflow schemas directly. If
    not, implement an adapter compatible with its real interface and
    document the limitation.
-   Do not pretend the model natively supports arbitrary schemas if it
    does not.
-   If the decision space cannot express an action reliably, abstain or
    use a documented fallback rather than guessing.

## 5. Integrate Google Gemma as a real local model

Inspect the target computer's OS, Python version, CPU, RAM, GPU/VRAM and
drivers, disk space, and installed runtimes. Do not assume a powerful
GPU.

Verify current official Gemma model options, model cards, licenses/usage
terms, memory requirements, quantization options, and local runtimes.
Choose a variant that can realistically run on the actual hardware. If
hardware details are unavailable, document assumptions and provide
configurable setup instructions rather than inventing specifications.

Evaluate runtimes such as Ollama, llama.cpp-compatible runtimes, or
Hugging Face Transformers where appropriate. Choose one primary runtime
for the first implementation.

The Gemma adapter must:

-   Implement a clear task-model interface.
-   Support configurable model/runtime settings.
-   Check runtime and model availability.
-   Perform a real local inference.
-   Support bounded generation settings and input length.
-   Handle context limits, timeouts, empty output, malformed structured
    output, and runtime failures.
-   Record model identity and generation settings.
-   Avoid transmitting prompts externally in local-only mode.
-   Never silently replace failed real inference with a mock.
-   Return an actionable error if the model is unavailable.
-   Avoid downloading large weights without explaining size and
    requirements.

Use environment variables/configuration for runtime settings. Do not
hardcode machine-specific paths, ports, model names, or hardware
assumptions. Mocks may be used in unit tests, but real-model integration
tests and benchmark mode must identify and use actual inference. Clearly
label tests requiring a local model.

## 6. Decision versus generative-task boundary

Support explicit internal outcomes, adapting existing types where
possible:

-   `EXECUTE_TOOL`
-   `USE_GENERATIVE_MODEL`
-   `CLARIFY`
-   `ABSTAIN`
-   `HUMAN_REVIEW`
-   `FALLBACK`

Do not force every task into a binary direct-execution-versus-Gemma
choice. Some tasks require clarification, multiple authorized tool
calls, or human approval.

Example A: "How many open pull requests are in this repository?" 1. Laya
selects `count_pull_requests(state="open")`. 2. SlothSwitch validates
action and parameters. 3. Registered GitHub tool calls the API. 4.
SlothSwitch returns the count. 5. Gemma is not called.

Example B: "Summarize technical concerns across these 30 pull
requests." 1. SlothSwitch retrieves authorized repository data. 2. The
workflow prepares bounded input. 3. Laya selects the registered
summarization path if it can reliably express it. 4. SlothSwitch invokes
local Gemma. 5. SlothSwitch validates and returns the summary.

These examples describe intended behavior, not proven Laya capabilities.
Test action selection on the actual dataset.

Do not add a complex autonomous agent loop merely for appearance. First
implement reliable, bounded execution.

## 7. Reusable workflow registry

The core engine must not contain GitHub-specific business logic.
Implement a reusable, typed workflow registration interface.

Illustrative API only:

``` python
workflow = WorkflowDefinition(
    name="github_pr_management",
    version="1.0",
    actions=[...],
    policies=[...],
)
registry.register(workflow)

result = slothswitch.execute(
    workflow="github_pr_management",
    request=user_request,
)
```

Adapt the real API to the existing codebase and verified Laya
capabilities.

Workflow definitions should specify:

-   Workflow name and version.
-   Supported actions and descriptions.
-   Parameter schemas and output schemas where practical.
-   Required permissions.
-   Read-only versus mutating classification.
-   Approval requirements.
-   Whether generative processing is allowed.
-   Whether direct execution is eligible.
-   Validation and policy rules.
-   Timeouts and safe error behavior.

Use typed interfaces and a supported schema system such as Pydantic or
JSON Schema where appropriate. Initial registration may use trusted
Python definitions or validated local configuration files. Do not allow
unauthenticated users to register arbitrary Python through a public API.

Provide one small non-GitHub example proving the core engine is
reusable. Do not create empty modules just to match a diagram.

## 8. Safe tool execution

Every tool should expose, as appropriate: stable ID/description,
parameter schema, output schema, permissions, read-only/mutating
classification, timeout, safe retry policy, idempotency behavior, error
mapping, and audit metadata.

Before execution:

1.  Confirm the action is registered.
2.  Validate all parameters.
3.  Check caller authorization.
4.  Enforce workflow policies.
5.  Check approval requirements.
6.  Enforce timeouts/resource limits.
7.  Invoke only the registered implementation.
8.  Validate output where possible.
9.  Record a privacy-aware execution event.

A model's assertion that an action is safe is never authorization. Use
deny-by-default behavior for sensitive operations. Retries must not
duplicate destructive operations. Support clear states such as
`ACCEPTED`, `VALIDATING`, `WAITING_FOR_APPROVAL`, `EXECUTING`,
`SUCCEEDED`, `FAILED`, and `ABSTAINED`, adapting to the existing
implementation.

## 9. First workflow: GitHub issue and PR management

Start with read-only actions:

-   `list_open_pull_requests`
-   `count_pull_requests`
-   `get_pull_request_details`
-   `list_open_issues`
-   `count_issues`
-   `get_issue_details`
-   `get_pull_request_checks`
-   `list_repository_labels`

Only after read-only actions work, consider mutating actions such as
`add_issue_label`, `add_pull_request_label`, and `create_issue_comment`.

Mutating actions require explicit permissions and configurable approval
gates. Do not automatically merge PRs, delete branches, change
repository permissions, or execute arbitrary repository code.

Use GitHub's documented API and a maintained client library where
appropriate. Handle authentication, rate limits, pagination, missing
resources, permission errors, and API failures.

Start with public repositories for read-only integration tests. For
authenticated use, accept a least-privilege token through environment
configuration. Never commit credentials or expose them in logs.

Provide a reproducible demo against a public repository. Automated tests
must not make live mutating calls unless explicitly opted in and
configured for a safe target.

## 10. Gemma tasks for the GitHub workflow

Implement a few useful generative tasks, for example:

-   Summarize several PR descriptions.
-   Produce a concise repository activity report.
-   Summarize technical concerns in issue descriptions.
-   Draft an issue comment for human review.
-   Explain CI failure messages.

Keep generation separate from direct API execution. Retrieve only
authorized data and bound input size. Handle context limits and
chunking. Treat issue bodies, PR descriptions, comments, logs, and
repository content as untrusted input that may contain prompt injection.
Retrieved content must not override system policies or authorize tools.
Do not give Gemma unrestricted access to GitHub credentials or arbitrary
tools.

## 11. Security, privacy, reliability, and observability

Implement relevant controls without overengineering.

**Input validation** - Typed request/response models. - Request-size
limits. - Validated workflow IDs. - Parameter schema enforcement. - Safe
malformed-input handling.

**Model reliability** - Timeouts and bounded retries. - Clear failure
states. - Invalid-output handling. - Model-unavailable handling. -
Explicit abstention/fallback behavior.

**Authorization** - Least-privilege credentials. - Workflow-specific
permissions. - Read-only defaults. - Approval gates for sensitive
actions. - No implicit trust in model confidence.

**Privacy** - Do not log raw prompts or repository content by default. -
Redact secrets. - Store only necessary execution metadata. - Make
detailed diagnostic logging opt-in. - In local-only mode, do not send
prompts to cloud LLM providers.

**API security, if an API exists** Assess authentication, authorization,
request limits, rate limiting, CORS where relevant, consistent errors,
safe network binding, and unauthorized tool invocation.

**Observability** Record privacy-aware events such as request ID,
workflow/version, decision model/checkpoint, selected action, validation
result, execution path, whether Gemma was called, model/tool latency,
token counts where available, measured/estimated cost, failure category,
and execution status. Do not log secrets, raw prompts, or sensitive
repository content in ordinary logs.

## 12. Real data and evaluation

Use both synthetic unit-test fixtures and real data, clearly separated.

### Unit tests

Use controlled fixtures for valid/invalid decisions, unknown actions,
invalid parameters, policy denials, tool/model failures, timeouts,
malformed Gemma output, missing credentials, and approval requirements.

### Real-world integration tests

Use documented GitHub API calls against public repositories. Verify
repository metadata, issue/PR retrieval, pagination, rate limits,
missing resources, permission failures, and API errors. If network
access is unavailable, mark integration tests blocked; do not claim they
passed.

### Workflow dataset

Create or curate a documented dataset of GitHub issue/PR requests
representative of the supported actions. Examples should include user
request, workflow ID, available actions, expected/acceptable action,
expected parameters, whether direct execution is appropriate, whether
generation is required, whether clarification/abstention is expected,
and an evaluation criterion.

Use real, appropriately licensed public data where practical. Respect
source terms, rate limits, and privacy expectations. Document source,
collection date/method, license/constraints, transformations, version,
and limitations. Do not commit data that should not be redistributed. If
data cannot be redistributed, document reproducible retrieval
instructions or use appropriately redacted examples. Never describe
synthetic fixtures as real data.

### Splits and leakage

Create development, validation, and held-out test sets. Prevent
near-duplicate leakage. Prefer splitting by repository or related
issue/PR groups when appropriate. Do not tune thresholds on the held-out
test set. Identify weakly labeled or automatically labeled examples.

## 13. Benchmark baselines

Compare the same workload under comparable permissions and task
definitions.

**Baseline A --- Always-Gemma:** Send requests requiring AI handling to
the configured local Gemma model. Use the same registered tools for
actual API operations; an LLM alone does not perform authenticated API
actions without an execution mechanism.

**Baseline B --- Deterministic rules:** Use a documented deterministic
baseline where appropriate.

**Baseline C --- SlothSwitch:** Use Laya plus policy-validated direct
execution, invoking local Gemma only when appropriate.

Record dataset/version/split, example count, model/checkpoint versions,
hardware, runtime and generation settings, execution configuration,
failures, and exclusions. Do not change task definitions, quality
requirements, tool access, or permissions between conditions.

## 14. Required metrics

**Decision quality** - Action/route accuracy. - Macro-F1 where
appropriate. - Per-action precision and recall. - Confusion matrix. -
Invalid-action rate. - Unsupported-task detection. - Abstention rate. -
False direct-execution rate.

**Execution quality** - Tool execution success rate. - Parameter
validation failures. - End-task success and result correctness. - Human
approval/escalation frequency.

**Model usage** - Number of Gemma calls. - Number of direct tool
executions. - Number of decision-model calls. - Input/output tokens when
available. - Model load and inference time.

**Performance** - End-to-end median and p95 latency. - Decision-model
overhead. - Tool latency. - Gemma generation latency. - Failure and
timeout rates.

**Cost** - Total benchmark cost. - Cost per successful task. - Cost per
1,000 requests. - Avoided Gemma calls. - Estimated local inference cost
where feasible.

Distinguish actual external API charges, measured local execution time,
estimated local compute cost, electricity/hardware assumptions, and
simulated values. Local inference is not free. Report direct provider
expenditure separately from estimated local hardware and energy costs.

The goal is to reduce unnecessary generative inference while maintaining
acceptable task quality. Do not optimize only for fewer model calls. Use
held-out data for final numbers and produce both a machine-readable
report and a readable summary. Do not claim savings if task quality is
meaningfully worse.

## 15. Incremental implementation plan

Work in small, testable increments.

1.  **Audit:** Inspect repository/tests; identify mocks and real
    integrations; document architecture; create/update `decision.md`.
2.  **Architecture:** Define typed decision outcomes, workflow registry,
    tool/task-model interfaces, policy boundary, and architecture
    decisions.
3.  **Laya:** Verify API; preserve/repair adapter; test parsing, invalid
    decisions, abstention, and failures.
4.  **Gemma:** Inspect hardware; verify model/runtime/license; implement
    local adapter; verify real inference; test failure cases; document
    setup.
5.  **Execution engine:** Implement workflow registration,
    registered-tool dispatcher, policy, authorization, approval, and
    structured results.
6.  **GitHub workflow:** Implement read-only actions; test against
    public repositories; add one or two generative tasks; add mutating
    actions only if time permits and safety is implemented.
7.  **Benchmark:** Prepare documented dataset; implement baselines; run
    real Laya/Gemma integrations; record measurements; analyze errors;
    verify no simulated costs/latency.
8.  **Hardening:** Run tests, linting, type checks; review dependencies
    and security-sensitive code; inspect diff and fix regressions.
9.  **Documentation:** Update README, architecture, local Gemma setup,
    workflow registration, GitHub integration, benchmark methodology,
    reproducible commands, limitations.

Do not implement all phases in one unreviewed rewrite. After each
increment, run tests, inspect the diff, update `decision.md`, report
evidence and remaining work, and then continue.

## 16. Required tests

**Decision model:** valid/invalid action, missing parameters, wrong
types, unknown action, unsupported request, abstention, malformed
output, unavailable model, timeout.

**Policy:** permitted read-only action, denied/unauthorized action,
mutating action requiring approval, approval denied, missing
permissions, policy failure.

**Executor:** success, tool failure, timeout, invalid result, retry
behavior, idempotency where relevant, audit event.

**Gemma:** successful local inference, runtime unavailable, model not
downloaded, invalid structured output, excessive context, timeout, empty
output, and proof local-only mode does not call cloud providers.

**Registry:** valid/duplicate registration, invalid schema, unknown
workflow, version handling, invalid configuration.

**GitHub:** pagination, API errors, rate limits, missing
repository/resource, permission errors, read-only action,
approval-required mutating action.

**Benchmark:** comparable examples, held-out evaluation, correct
metrics, explicit mock-mode detection, reproducible output, no
fabricated latency/cost values.

Do not delete failing tests merely to obtain a green test suite.

## 17. Suggested repository structure

Adapt this to the existing repository; do not create empty modules
solely to match it.

``` text
src/slothswitch/
    api.py
    config.py
    schemas.py
    registry.py
    orchestrator.py
    policy.py
    executor.py
    telemetry.py
    adapters/
        decision/base.py
        decision/laya.py
        generative/base.py
        generative/gemma_local.py
        tools/base.py
        tools/github.py
    workflows/
        base.py
        github_pr_management.py
    evaluation/
        dataset.py
        baselines.py
        metrics.py
        runner.py
        reports.py
tests/
    unit/
    integration/
    security/
examples/
    basic_workflow.py
    github_pr_management.py
config/workflows/
datasets/README.md
docs/
    architecture.md
    security.md
    local_gemma_setup.md
    workflow_authoring.md
    evaluation.md
    technology-decisions.md
decision.md
README.md
.env.example
```

## 18. Mandatory `decision.md` log

If `decision.md` exists, preserve its history. Append an entry after
every meaningful task, including:

-   Task name and status: Complete, Partial, or Blocked.
-   What changed and why.
-   Files changed.
-   Libraries/models used.
-   Tests and commands run.
-   Actual results.
-   Benchmark evidence, if available.
-   Decisions and trade-offs.
-   Known limitations.
-   Remaining work and next task.

Do not claim model integration works unless real inference succeeded. Do
not claim GitHub integration works unless the API interaction was
verified. Do not claim benchmark results are real if they use mocks.
Never rewrite history to make the project look more complete.

## 19. Acceptance criteria

Mark the implementation complete only when each criterion is verified or
explicitly marked blocked.

### Architecture

-   Laya and Gemma have separate responsibilities and interfaces.
-   Decisions are policy-validated.
-   Only registered tools can execute.
-   Workflow definitions are separate from core logic.
-   A non-GitHub example demonstrates reusability.

### Local Gemma

-   Real local Gemma inference succeeds on the target machine.
-   Hardware/memory requirements and model/runtime are documented.
-   Real-mode failures do not silently become mocks.
-   Local-only mode does not transmit prompts to cloud LLM providers.

### GitHub

-   A real public repository can be queried.
-   Read-only actions are schema-validated.
-   Pagination and API errors are handled.
-   Mutating actions are protected by permissions and approval.

### Quality and security

-   Existing functionality is preserved where appropriate.
-   Tests and configured lint/type checks pass.
-   Integration test outcomes are accurate.
-   No credentials are committed.
-   Sensitive operations fail safely.

### Evaluation

-   Dataset provenance and splits are documented.
-   Baselines are comparable.
-   Real inference is used for real benchmarks.
-   Measurements are distinguished from estimates.
-   Quality and cost are reported together.
-   No unverified savings claims appear in documentation.

### Documentation

-   A new developer can install and run the project.
-   Local Gemma setup is documented.
-   The first workflow runs end to end.
-   Workflow registration and benchmark commands/results are documented.
-   `decision.md` truthfully records progress.

If a criterion cannot be completed, document the blocker and provide the
most useful verified partial implementation. Do not falsely mark it
complete.

## 20. Start now

Begin with:

1.  Repository audit.
2.  Existing test execution.
3.  Hardware and local runtime inspection.
4.  Verification of current Laya and Gemma documentation.
5.  Architecture/migration plan.
6.  First small implementation increment.

After the audit, report the current architecture, functionality to
preserve, major gaps, recommended migration sequence, hardware
constraints, and first implementation task.

Then implement incrementally, testing and updating `decision.md` after
every meaningful task.
