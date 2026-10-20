# SlothSwitch — Decision & Implementation Log

This living log tracks technical decisions, trade-offs, architecture choices, implementation increments, and empirical verification results across the lifecycle of SlothSwitch.

---

## Task: 01-Architecture-and-Skeleton-Setup
- Status: Complete
- What was done:
  - Formulated the core architecture for SlothSwitch separating the decision model from task execution models.
  - Defined the candidate route categories: `FAST_PATH`, `SMALL_LLM`, `LARGE_LLM`, `CLARIFY`, `FALLBACK`, `HUMAN_REVIEW`.
  - Built Pydantic data schemas in `src/slothswitch/schemas.py`.
  - Created preprocessing pipeline in `src/slothswitch/preprocessing.py` with input validation, PII redaction patterns, and feature extraction.
  - Implemented the deterministic policy gate in `src/slothswitch/policy.py`.
  - Created provider-agnostic adapter interfaces in `src/slothswitch/adapters/`.
  - Implemented Mock Decision Adapter and Mock Task Model Adapter for zero-dependency execution and testing.
  - Implemented initial `LayaDecisionAdapter` wrapping `laya.Router` with typed `choice` questions and strict label validation.
  - Created the core orchestrator in `src/slothswitch/router.py`, privacy-first telemetry in `src/slothswitch/telemetry.py`, evaluation harness in `src/slothswitch/evaluation/`, factory in `src/slothswitch/api.py`, and CLI in `src/slothswitch/cli.py`.
- Why:
  - Establish a solid, testable MVP skeleton with provider neutrality, safe defaults, and clean separation of concerns before integrating heavyweight dependencies.
- Files changed:
  - `pyproject.toml`
  - `.env.example`
  - `.gitignore`
  - `config/routing.yaml`
  - `src/slothswitch/__init__.py`
  - `src/slothswitch/schemas.py`
  - `src/slothswitch/preprocessing.py`
  - `src/slothswitch/policy.py`
  - `src/slothswitch/adapters/__init__.py`
  - `src/slothswitch/adapters/decision/__init__.py`
  - `src/slothswitch/adapters/decision/laya_adapter.py`
  - `src/slothswitch/adapters/task_models/__init__.py`
  - `src/slothswitch/router.py`
  - `src/slothswitch/telemetry.py`
  - `src/slothswitch/evaluation/__init__.py`
  - `src/slothswitch/api.py`
  - `src/slothswitch/cli.py`
- Tools and technologies:
  - Python 3.10+, Pydantic v2, PyYAML, setuptools.
- How this helps:
  - Provides a runnable, mockable foundation that enables immediate unit/integration testing, CLI execution, and baseline comparison without requiring external API keys.
- Tests and results:
  - Modules syntactically verified; ready for test suite creation and automated test runs.
- Evidence/metrics:
  - Core pipeline classes instantiated and functional via mocks.
- Decisions and trade-offs:
  - Selected 6 explicit route categories rather than arbitrary free-text classification.
  - Policy gate strictly overrides model outputs if constraints or confidence thresholds are not met.
  - Laya imports isolated exclusively to `laya_adapter.py` with graceful fallback when Laya is not installed.
- Remaining work:
  - Package installation in `.venv` and test suite authoring.
  - Evaluation dataset curation.
  - Documentation creation (`docs/technology-decisions.md`, `docs/architecture.md`, `docs/evaluation.md`).
- Next task:
  - Complete `.venv` setup, author unit and integration tests, verify test passes.

---

## Task: 02-Environment-Recovery-and-Encoding-Fix
- Status: Complete
- What was done:
  - Diagnosed `UnicodeDecodeError` during `pip install -e .` caused by UTF-16LE encoding of `README.md`.
  - Re-wrote `README.md` in standard UTF-8 format with comprehensive quickstart and CLI guides.
  - Initiated editable package installation with development dependencies (`pytest`, `ruff`, `mypy`).
- Why:
  - Clean virtual environment installation is required to execute automated tests and verify package entrypoints.
- Files changed:
  - `README.md`
  - `decision.md`
- Tools and technologies:
  - Python pip, venv.
- How this helps:
  - Eliminates installation blocker and prepares the test runtime.
- Tests and results:
  - Identified 0xFF byte BOM root cause; resolved encoding mismatch.
- Evidence/metrics:
  - UTF-8 `README.md` accepted by build system.
- Decisions and trade-offs:
  - Kept package dependencies minimal (Pydantic, PyYAML) with optional extras for `laya` and `dev`.
- Remaining work:
  - Verify test suite passes once dependencies finish installing.
- Next task:
  - Write comprehensive unit tests for schemas, preprocessing, policy, adapters, router, telemetry, and evaluation.
