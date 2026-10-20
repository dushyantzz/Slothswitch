"""Public API — convenience factory for building a SlothSwitch router from config."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional

import yaml

from slothswitch.adapters import DecisionAdapter, TaskModelAdapter
from slothswitch.adapters.decision import MockDecisionAdapter
from slothswitch.adapters.task_models import MockTaskModelAdapter
from slothswitch.policy import RoutingPolicy
from slothswitch.router import SlothSwitchRouter
from slothswitch.schemas import RouteCategory
from slothswitch.telemetry import TelemetryRecorder

logger = logging.getLogger(__name__)


def create_router(
    config_path: str = "config/routing.yaml",
    baseline_mode: bool = False,
) -> SlothSwitchRouter:
    """Build a SlothSwitchRouter from a YAML configuration file.

    This is the recommended entry point for users and demos.
    """
    config = _load_config(config_path)
    routing_cfg = config.get("routing", {})
    telemetry_cfg = config.get("telemetry", {})

    # --- Decision adapter ---
    adapter_name = routing_cfg.get("decision_model", {}).get("adapter", "mock")
    decision_adapter = _build_decision_adapter(adapter_name, routing_cfg.get("decision_model", {}))

    # --- Task model adapters ---
    task_adapters = _build_task_adapters(routing_cfg.get("task_models", {}), routing_cfg.get("routes", {}))

    # --- Policy ---
    enabled_routes = {
        RouteCategory(name)
        for name, rcfg in routing_cfg.get("routes", {}).items()
        if rcfg.get("enabled", True)
    }
    policy_cfg = routing_cfg.get("policy", {})
    policy = RoutingPolicy(
        enabled_routes=enabled_routes,
        high_risk_categories=policy_cfg.get("high_risk_categories", []),
        acceptance_threshold=routing_cfg.get("decision_model", {}).get("acceptance_threshold", 0.7),
    )

    # --- Telemetry ---
    telemetry = TelemetryRecorder(
        output_path=telemetry_cfg.get("metrics_output"),
        enabled=telemetry_cfg.get("enabled", True),
        log_raw_prompts=telemetry_cfg.get("log_raw_prompts", False),
    )

    # --- Build router ---
    return SlothSwitchRouter(
        decision_adapter=decision_adapter,
        task_adapters=task_adapters,
        policy=policy,
        telemetry=telemetry,
        max_request_length=policy_cfg.get("max_request_length", 10_000),
        supported_content_types=policy_cfg.get("supported_content_types", ["text/plain"]),
        baseline_mode=baseline_mode,
    )


def _load_config(path: str) -> dict[str, Any]:
    """Load and parse the YAML config file."""
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _build_decision_adapter(name: str, config: dict[str, Any]) -> DecisionAdapter:
    """Instantiate the configured decision adapter."""
    if name == "mock":
        return MockDecisionAdapter()
    elif name == "laya":
        try:
            from slothswitch.adapters.decision.laya_adapter import LayaDecisionAdapter

            return LayaDecisionAdapter(
                checkpoint=config.get("checkpoint", "convaiinnovations/laya"),
            )
        except ImportError:
            logger.warning(
                "Laya is not installed; falling back to mock decision adapter. "
                "Install with: pip install laya"
            )
            return MockDecisionAdapter()
    else:
        raise ValueError(f"Unknown decision adapter: {name}")


def _build_task_adapters(
    task_config: dict[str, Any],
    routes_config: dict[str, Any],
) -> dict[RouteCategory, TaskModelAdapter]:
    """Build task model adapters for each route that needs one."""
    adapters: dict[RouteCategory, TaskModelAdapter] = {}

    # Routes that need a task adapter
    generation_routes = {
        RouteCategory.SMALL_LLM: task_config.get("small_llm", {}),
        RouteCategory.LARGE_LLM: task_config.get("large_llm", {}),
    }

    for route, cfg in generation_routes.items():
        adapter_type = cfg.get("adapter", "mock")
        model_name = cfg.get("model", f"mock-{route.value.lower()}")
        if adapter_type == "mock":
            adapters[route] = MockTaskModelAdapter(model_name=model_name)
        else:
            logger.warning("Non-mock task adapter '%s' not yet implemented; using mock", adapter_type)
            adapters[route] = MockTaskModelAdapter(model_name=f"mock-{model_name}")

    # FAST_PATH, CLARIFY, FALLBACK, HUMAN_REVIEW use a shared mock for now
    for route in [RouteCategory.FAST_PATH, RouteCategory.CLARIFY, RouteCategory.FALLBACK, RouteCategory.HUMAN_REVIEW]:
        adapters[route] = MockTaskModelAdapter(model_name=f"handler-{route.value.lower()}")

    return adapters
