"""Integration tests for the SlothSwitch CLI."""

import json
import subprocess
import sys


def run_cli(*args: str) -> subprocess.CompletedProcess:
    """Helper to invoke CLI in a subprocess."""
    cmd = [sys.executable, "-m", "slothswitch.cli", *args]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=15, check=False)



def test_cli_help():
    result = run_cli("--help")
    assert result.returncode == 0
    assert "SlothSwitch" in result.stdout
    assert "route" in result.stdout
    assert "eval" in result.stdout
    assert "health" in result.stdout


def test_cli_health():
    result = run_cli("health")
    assert result.returncode == 0
    assert "Health Check" in result.stdout
    assert "OK" in result.stdout


def test_cli_route_standard():
    result = run_cli("route", "Where can I find my invoice?")
    assert result.returncode == 0
    assert "Routing Result" in result.stdout
    assert "Route:" in result.stdout
    assert "Task Result" in result.stdout


def test_cli_route_json():
    result = run_cli("route", "How do I reset my password?", "--json")
    assert result.returncode == 0
    parsed = json.loads(result.stdout)
    assert "request_id" in parsed
    assert "route_decision" in parsed
    assert "chosen_route" in parsed["route_decision"]
    assert "task_result" in parsed


def test_cli_eval():
    result = run_cli("eval", "--dataset", "datasets/customer_support_routing.json")
    assert result.returncode == 0
    assert "Benchmark Evaluation" in result.stdout
    assert "Routing Accuracy:" in result.stdout
    assert "Macro F1 Score:" in result.stdout
    assert "Per-Route Metrics" in result.stdout


def test_cli_eval_baseline():
    result = run_cli("eval", "--dataset", "datasets/customer_support_routing.json", "--baseline")
    assert result.returncode == 0
    assert "BASELINE" in result.stdout
