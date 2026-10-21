# SlothSwitch ⚡

### Let decision models handle the simple work. Save generative AI for the work that needs it.

## The idea in 30 seconds

Many AI agents send almost every request to a generative Large Language
Model (LLM), even when the task is as simple as counting issues,
checking a status, retrieving a record, or choosing a known action.

That can waste inference time and resources.

**SlothSwitch adds a decision layer before generative AI.** It asks a
lightweight decision model, **Laya**, to choose from actions that a
workflow explicitly supports. SlothSwitch then validates the choice and
either executes a registered tool directly or calls a locally configured
**Gemma** model when the task genuinely needs language generation.

The goal is not to remove LLMs from every workflow. The goal is to
**avoid unnecessary LLM calls without sacrificing task quality or
safety**.

### In one sentence

**SlothSwitch helps AI agents choose the right way to do a task---direct
execution when possible, generative AI when needed, and a safe fallback
when uncertain.**

------------------------------------------------------------------------

## Why does this matter?

Imagine an agent that helps maintain an open-source repository. A
maintainer asks it to:

-   Count open pull requests.
-   List issues without labels.
-   Check whether a pull request's CI checks passed.
-   Summarize the technical concerns across 30 pull requests.
-   Draft a comment explaining a complicated bug.

These requests do not all need the same kind of processing.

  -----------------------------------------------------------------------
  Example request         A sensible path         Why
  ----------------------- ----------------------- -----------------------
  "How many open PRs are  Direct GitHub API call  The API can return the
  there?"                                         answer; text generation
                                                  is unnecessary.

  "List issues without    Direct tool execution   Retrieve the issues and
  labels."                                        apply a deterministic
                                                  check.

  "Did CI pass on PR      Direct GitHub API call  This is a structured
  #42?"                                           status lookup.

  "Summarize the main     Local Gemma, when       The task requires
  concerns in these PRs." appropriate             synthesizing
                                                  natural-language
                                                  content.

  "Should this risky      Human review or a       A consequential
  change be merged?"      carefully bounded       decision should not be
                          analysis workflow       authorized by model
                                                  confidence alone.
  -----------------------------------------------------------------------

A conventional agent may use an LLM to interpret and handle all these
requests. SlothSwitch aims to identify which tasks can be handled
through direct, validated execution and reserve generative inference for
the tasks that benefit from it.

The actual decision quality depends on the workflow, available actions,
model checkpoint, and evaluation. These examples explain the design;
they are not a claim that every request is already handled perfectly.

------------------------------------------------------------------------

## How SlothSwitch works

``` mermaid
flowchart TD
    A["User or existing AI agent"] --> B["SlothSwitch receives request"]
    B --> C["Validate input and identify workflow"]
    C --> D["Laya: choose a supported action"]
    D --> E["Validate decision against schemas and policies"]
    E --> F{"What path is allowed and appropriate?"}
    F -->|Known, permitted action| G["Run registered tool or deterministic function"]
    F -->|Needs language generation| H["Call locally configured Gemma"]
    F -->|Unclear or unsupported| I["Clarify, abstain, or use safe fallback"]
    F -->|Sensitive action| J["Require authorization or human approval"]
    G --> K["Validate result and record safe metrics"]
    H --> K
    I --> K
    J --> K
    K --> L["Return result to the user or agent"]
```

### The four main parts

#### 1. Laya --- the decision model

Laya is responsible for choosing among the actions defined for a
workflow.

For example, when the available actions include `count_pull_requests`,
`list_issues`, and `summarize_pull_requests`, Laya can be asked to
select the appropriate action for a request.

Laya does **not** execute the GitHub API call itself. It proposes a
structured decision.

A decision model is not automatically correct. SlothSwitch must validate
its output, test it on representative data, and handle uncertainty or
unsupported requests safely.

#### 2. SlothSwitch --- the policy and execution layer

SlothSwitch sits between the decision model and the real tools.

It checks questions such as:

-   Is the proposed action registered?
-   Are the parameters valid?
-   Is this action allowed for this workflow and caller?
-   Is it read-only or does it change something?
-   Does it require explicit approval?
-   Did the tool return a valid result?

Only registered, permitted tools can execute. Model output must never be
treated as permission to run arbitrary code.

#### 3. Google Gemma --- the local generative model

Some requests need more than choosing a known action. They require
summarization, explanation, drafting, or synthesis.

For those tasks, SlothSwitch can call a locally running Google Gemma
model. The user can configure the model and local runtime appropriate
for their machine.

The local-first design aims to avoid sending prompts to a cloud LLM
provider. Local inference still consumes hardware resources,
electricity, memory, and time; it is not automatically free.

The exact Gemma variant and runtime should be selected based on the
target computer's hardware and the model's current license and
requirements.

#### 4. Workflow plugins --- the actions an agent can perform

Different agents have different tools. A GitHub agent might list pull
requests; a DevOps agent might inspect deployment status.

A workflow definition describes its available actions, input/output
schemas, permissions, and policies. The core SlothSwitch engine can then
be reused without hardcoding every workflow into the core.

**Important limitation:** Reusable architecture does not mean one
decision model automatically understands every domain. Each workflow's
action set and decision quality need validation.

------------------------------------------------------------------------

## What happens internally? A worked example

Suppose a maintainer asks:

> "How many open pull requests are in `owner/repository`?"

A successful direct-execution path should look like this:

1.  **Receive:** SlothSwitch receives the request and identifies the
    GitHub workflow.
2.  **Describe the choices:** The workflow exposes registered actions
    and their parameter schemas.
3.  **Decide:** Laya proposes an action such as `count_pull_requests`
    with the relevant repository and state.
4.  **Validate:** SlothSwitch checks the action name, parameter types,
    allowed repository access, and policy.
5.  **Execute:** The registered GitHub tool calls the documented GitHub
    API.
6.  **Check the result:** SlothSwitch validates the tool result and
    handles API errors.
7.  **Return:** The count is returned to the user.
8.  **Measure:** Privacy-aware telemetry records the chosen path,
    latency, outcome, and whether Gemma was called---without logging
    secrets or raw content by default.

If this path succeeds, **Gemma is not needed for the request**.

Now consider:

> "Summarize the main technical concerns across these 30 pull requests."

The workflow may retrieve authorized PR information and prepare a
bounded input. If the request requires generative synthesis, SlothSwitch
can call local Gemma, validate its output, and return the summary.

For an ambiguous or unsupported request, SlothSwitch should ask for
clarification, abstain, or use a documented fallback instead of
inventing an action.

These are target flows. The current implementation and tests determine
which paths are actually available today.

------------------------------------------------------------------------

## Why not just call an LLM directly?

  -----------------------------------------------------------------------
  Direct LLM-centric approach         SlothSwitch approach
  ----------------------------------- -----------------------------------
  May send simple status lookups to a Aims to execute supported status
  generative model                    lookups directly

  Tool selection and execution policy Separates model proposals from
  may be mixed into an agent prompt   deterministic validation and
                                      authorization

  Can make it difficult to tell why a Records structured decisions and
  tool was invoked                    execution outcomes

  Often tied closely to one agent's   Uses workflow definitions and
  implementation                      adapters to support reuse

  May send data to a remote provider, Can use local Gemma for generative
  depending on configuration          tasks

  Performance depends on model        Still depends on model quality, but
  behavior and external calls         direct actions can avoid
                                      unnecessary generation
  -----------------------------------------------------------------------

SlothSwitch is not a replacement for every agent framework or every LLM.
It is a layer that can be integrated into an existing agent when the
agent has bounded actions that can be safely executed through tools.

------------------------------------------------------------------------

## Why this could benefit existing agentic workflows

### 1. Potentially fewer generative-model calls

If a task can be resolved by selecting a known action and executing a
deterministic function, a generative call may be unnecessary.

### 2. Potentially lower latency

A direct API call or local function can be faster than generating a
response. Actual end-to-end latency must be measured; running Laya and
checking policies also adds overhead.

### 3. More predictable action execution

Schemas, registered tools, permission checks, and output validation make
it easier to constrain what the system can execute.

### 4. Local-first generative processing

When configured for local-only operation, Gemma can handle supported
generative tasks on the user's machine instead of sending prompts to a
cloud LLM provider. This can help with data-control requirements,
subject to local machine security and configuration.

### 5. A reusable integration point

Instead of rebuilding routing and policy logic for every agent,
developers can define workflow-specific actions and reuse the core
engine.

### 6. Evidence instead of guesses

SlothSwitch is designed to measure decision quality, successful task
completion, model usage, latency, and cost. The aim is to make
trade-offs visible rather than claim that fewer LLM calls automatically
means a better system.

------------------------------------------------------------------------

## Architecture: reusable core, workflow-specific actions

``` mermaid
flowchart LR
    subgraph Workflows["Existing workflows"]
      GH["GitHub / PR agent"]
      DV["DevOps agent"]
      RS["Research agent"]
    end

    subgraph Core["Reusable SlothSwitch core"]
      REG["Workflow registry and schemas"]
      DEC["Laya decision adapter"]
      POL["Policy and authorization"]
      EXE["Registered-tool executor"]
      GEN["Generative-model interface"]
    end

    subgraph Providers["Configured capabilities"]
      TOOLS["Workflow tools and APIs"]
      GEM["Local Gemma"]
      OTHER["Other compatible LLMs (optional)"]
    end

    GH --> REG
    DV --> REG
    RS --> REG
    REG --> DEC --> POL
    POL --> EXE --> TOOLS
    POL --> GEN
    GEN --> GEM
    GEN -. "optional adapter" .-> OTHER
```

The diagram illustrates the intended architecture. It does not imply
that every workflow, provider, or adapter is already implemented.

------------------------------------------------------------------------

## Safety is part of the design

A decision model's prediction is not authorization.

SlothSwitch should enforce these principles:

-   **Registered tools only:** Model outputs cannot create arbitrary
    executable functions.
-   **Schema validation:** Parameters must match the tool's expected
    schema.
-   **Least privilege:** Credentials should have only the permissions
    the workflow needs.
-   **Read-only first:** Begin with safe queries; add mutating actions
    only with explicit safeguards.
-   **Approval for consequential actions:** Actions such as posting
    comments or modifying repository state can require approval. More
    destructive actions should be restricted further.
-   **Safe uncertainty handling:** Unsupported or ambiguous requests
    should not be forced into a guessed action.
-   **Prompt-injection awareness:** Issue descriptions, PR comments,
    logs, and other retrieved content are untrusted data, not
    instructions that can override system policy.
-   **Privacy-aware telemetry:** Do not log secrets or raw prompts by
    default.
-   **Bounded execution:** Apply timeouts, input limits, error handling,
    and safe retry rules.

A production deployment must still be reviewed for the security
requirements of its specific environment.

------------------------------------------------------------------------

## First use case: open-source PR and issue management

The initial workflow focuses on tasks that can be evaluated against real
GitHub data.

### Direct-execution candidates

-   Count open pull requests.
-   List open issues.
-   Retrieve pull-request details.
-   Check CI status.
-   List repository labels.
-   Find issues missing a required label, once the necessary data is
    retrieved.

### Generative tasks

-   Summarize several pull requests.
-   Produce a repository activity report.
-   Summarize recurring concerns across issue descriptions.
-   Draft an issue comment for human review.
-   Explain a set of CI failure messages.

### Human-controlled actions

Mutating operations---such as adding labels or creating
comments---should require explicit permissions and configurable approval
rules. The initial demonstration should prioritize read-only operations.

GitHub is the first validation workflow, not the limit of SlothSwitch's
intended use.

------------------------------------------------------------------------

## How we will prove whether it works

A useful project needs evidence, not just an architecture diagram.

SlothSwitch should be evaluated against comparable baselines using the
same task set, permissions, and quality requirements.

### Comparison conditions

1.  **Always-Gemma baseline:** Use the configured local Gemma model for
    tasks that require AI processing, while using the same tools for
    actual API operations.
2.  **Deterministic baseline:** Use documented rules for tasks they can
    handle.
3.  **SlothSwitch:** Use Laya to select supported actions, execute
    permitted direct actions, and invoke Gemma when generative
    processing is appropriate.

### Metrics

  -----------------------------------------------------------------------
  Area                                What to measure
  ----------------------------------- -----------------------------------
  Decision quality                    Action accuracy, macro-F1 where
                                      appropriate, per-action errors,
                                      abstentions

  Task outcome                        Successful execution and
                                      correctness of returned results

  Model usage                         Number of Laya and Gemma calls;
                                      tokens when available

  Latency                             End-to-end median and p95, decision
                                      overhead, tool time, Gemma
                                      inference time

  Cost                                Actual external charges and
                                      separately estimated local compute
                                      cost

  Safety                              Invalid actions, denied actions,
                                      approval frequency, failures and
                                      fallbacks
  -----------------------------------------------------------------------

The benchmark must distinguish real model inference from mocks and
synthetic fixtures. Use development and validation data for tuning, then
report final results on a held-out test set. Document data provenance,
model versions, hardware, settings, and known limitations.

### What counts as a meaningful result?

A reduction in Gemma calls is useful only if the system still completes
tasks correctly at an acceptable quality level. If quality drops
significantly, the trade-off must be reported rather than hidden.

**No cost, latency, or quality improvement should be claimed until it
has been measured with the real integrations.** Local inference also has
hardware and energy costs.

See the evaluation documentation and benchmark report for the current
verified results once those artifacts are available.

------------------------------------------------------------------------

## Getting started

> **Implementation note:** Commands and configuration below should be
> finalized against the actual repository. Do not publish commands as
> verified until they have been tested on a clean environment.

### Prerequisites

-   Python version supported by the repository.
-   Git.
-   A compatible local Gemma runtime and a model variant that fits your
    hardware for real generative inference.
-   Optional GitHub credentials for authenticated access. Start with
    public, read-only repositories where possible.

### Setup

Once the repository's package configuration and local Gemma adapter are
implemented, the intended setup flow is:

``` bash
git clone <YOUR_REPOSITORY_URL>
cd <YOUR_REPOSITORY_DIRECTORY>

# Create and activate a virtual environment using your platform's commands.
# Install the project's documented dependencies.
# Configure the local Gemma runtime and model.
# Copy .env.example to .env if the project uses environment variables.
# Follow the verified setup instructions in docs/local_gemma_setup.md.
```

Do not commit `.env`, API tokens, or model credentials.

### Run a demo

The intended first demo will query a public GitHub repository using
read-only actions and show:

-   The incoming request.
-   Laya's proposed action.
-   Policy/schema validation.
-   The execution path chosen.
-   Whether Gemma was called.
-   The returned result.
-   Latency and relevant model-usage measurements.

The exact CLI/API command should be added here after it is implemented
and tested. Consult the repository's current examples and documentation.

------------------------------------------------------------------------

## Extending SlothSwitch to another workflow

The intended extension process is:

1.  **Define the workflow:** Give it a stable name and version.
2.  **Register actions:** Describe what each action does, its
    parameters, and its output.
3.  **Add policies:** Define permissions, restrictions, and approval
    requirements.
4.  **Connect tools:** Implement registered functions or API clients.
5.  **Configure the decision model:** Ensure its actual input/output
    contract can represent the workflow's action choices.
6.  **Evaluate:** Create representative examples and a held-out test
    set.
7.  **Integrate:** Call SlothSwitch from the existing agent through the
    documented interface.

A hypothetical workflow definition might look like this:

``` python
workflow = WorkflowDefinition(
    name="my_workflow",
    version="1.0",
    actions=[
        # Register explicitly implemented and validated actions here.
    ],
    policies=[
        # Define permission and approval rules here.
    ],
)

registry.register(workflow)
```

This is illustrative pseudocode, not a promise that this exact API
exists in the current code.

The key idea is that a workflow supplies its supported actions and
policies; the reusable engine handles validation, decisions, dispatch,
and measurement. Every new workflow still needs domain-specific testing.

------------------------------------------------------------------------

## Project principles

SlothSwitch is being built around the following principles:

1.  **Decision before generation:** Do not invoke a generative model
    when a supported direct action is sufficient.
2.  **Model proposes; policy authorizes:** Never treat a model output as
    permission to execute.
3.  **Real measurements over marketing claims:** Publish only
    reproducible results.
4.  **Workflow reuse without universal-accuracy claims:** Reuse the
    engine; evaluate each domain.
5.  **Local-first where practical:** Make local generative inference a
    first-class option.
6.  **Safe failure:** Clarify, abstain, or escalate rather than guess.
7.  **Incremental open-source development:** Keep architecture
    decisions, tests, limitations, and progress visible.

------------------------------------------------------------------------

## Current status and roadmap

Update this section as features are implemented and verified.

-   [ ] Audit and preserve the existing codebase.
-   [ ] Verify the Laya adapter and supported decision schema.
-   [ ] Integrate and verify real local Gemma inference on target
    hardware.
-   [ ] Implement the reusable workflow registry.
-   [ ] Enforce policy-validated registered-tool execution.
-   [ ] Complete read-only GitHub issue/PR integration.
-   [ ] Add a safe generative GitHub task using Gemma.
-   [ ] Add unit, integration, and security tests.
-   [ ] Run a reproducible benchmark on real integrations and held-out
    data.
-   [ ] Publish measured results, setup instructions, and limitations.

Mark an item complete only when evidence supports it. Keep planned
features clearly distinguished from working features.

------------------------------------------------------------------------

## Contributing

Contributions are welcome. Useful areas include:

-   Workflow plugins and action schemas.
-   Decision-model adapters and evaluation.
-   Local Gemma runtime support.
-   Tool authorization and policy enforcement.
-   Real-world datasets and benchmark methodology.
-   Documentation, tests, and reproducible examples.

Before submitting a change:

1.  Read the contribution instructions, if present.
2.  Add or update tests.
3.  Run the repository's configured checks.
4.  Document new configuration and security implications.
5.  Update `decision.md` if it is part of the project's engineering
    process.
6.  Clearly identify anything not tested against a real model or
    service.

Never include secrets, private repository data, or unlicensed datasets
in a contribution.

## License

Add the project's actual license here after verifying the repository's
license file. Do not claim an open-source license until it has been
selected and included.

## Acknowledgements

SlothSwitch builds on open model and open-source software ecosystems.
See the project's dependency and model documentation for the specific
projects, licenses, and versions used.

------------------------------------------------------------------------

## The bigger picture

AI agents should not need a generative model for every small operation.

**SlothSwitch explores a practical alternative: let a decision model
select a known action, let deterministic software validate and execute
it, and use a generative model when the task genuinely needs one.**

The ambition is a reusable layer that helps developers build agentic
workflows with more deliberate model usage, clearer execution
boundaries, and measurable trade-offs.

The claim will be earned through working integrations, safe execution,
reproducible benchmarks, and transparent results---not by assuming that
fewer model calls automatically means a better agent.
