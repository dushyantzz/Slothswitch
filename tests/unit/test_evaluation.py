"""Unit tests for the evaluation harness and metrics calculation."""

import json
from pathlib import Path

import pytest

from slothswitch.evaluation import EvaluationResult, load_dataset, split_dataset


def test_evaluation_result_metrics():
    res = EvaluationResult()
    # Example 1: correct prediction
    res.add(predicted="FAST_PATH", acceptable=["FAST_PATH"], latency_ms=10.0, cost_usd=0.0)
    # Example 2: correct multi-label prediction
    res.add(predicted="SMALL_LLM", acceptable=["SMALL_LLM", "LARGE_LLM"], latency_ms=25.0, cost_usd=0.001)
    # Example 3: incorrect prediction (predicted FAST_PATH instead of LARGE_LLM)
    res.add(predicted="FAST_PATH", acceptable=["LARGE_LLM"], latency_ms=10.0, cost_usd=0.0)
    # Example 4: fallback
    res.add(predicted="FALLBACK", acceptable=["FALLBACK"], latency_ms=5.0, cost_usd=0.0)

    assert res.total == 4
    assert res.correct == 3
    assert res.accuracy == 0.75
    assert res.fallback_rate == 0.25

    summary = res.summary()
    assert summary["total_examples"] == 4
    assert summary["accuracy"] == 0.75
    assert "macro_f1" in summary
    assert "per_route_precision" in summary
    assert "per_route_recall" in summary


def test_split_dataset_deterministic():
    dataset = [{"request_id": f"id_{i}", "content": f"msg {i}", "acceptable_routes": ["FAST_PATH"]} for i in range(10)]
    dev_split, test_split = split_dataset(dataset, test_ratio=0.3, seed=42)
    assert len(dev_split) == 7
    assert len(test_split) == 3

    # Ensure deterministic reproduction
    d2, t2 = split_dataset(dataset, test_ratio=0.3, seed=42)
    assert dev_split == d2
    assert test_split == t2


def test_load_dataset_valid_and_missing(tmp_path: Path):
    data_file = tmp_path / "test_data.json"
    dummy_data = [
        {"request_id": "1", "content": "hello", "acceptable_routes": ["FAST_PATH"]}
    ]
    data_file.write_text(json.dumps(dummy_data), encoding="utf-8")

    loaded = load_dataset(str(data_file))
    assert len(loaded) == 1
    assert loaded[0]["request_id"] == "1"

    with pytest.raises(FileNotFoundError):
        load_dataset(str(tmp_path / "non_existent.json"))
