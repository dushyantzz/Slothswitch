"""Unit tests for privacy-aware telemetry recording."""

import json
from pathlib import Path

from slothswitch.schemas import RouteCategory, RouteDecision, RoutingRecord, TaskResult
from slothswitch.telemetry import TelemetryRecorder


def test_telemetry_in_memory_records():
    recorder = TelemetryRecorder(enabled=True)
    dec = RouteDecision(
        request_id="t1",
        chosen_route=RouteCategory.SMALL_LLM,
        confidence=0.88,
    )
    rec = RoutingRecord(request_id="t1", route_decision=dec)
    recorder.record(rec)
    records = recorder.get_records()
    assert len(records) == 1
    assert records[0]["request_id"] == "t1"



def test_telemetry_flush_to_file(tmp_path: Path):
    log_file = tmp_path / "metrics.jsonl"
    recorder = TelemetryRecorder(enabled=True, output_path=log_file)

    dec = RouteDecision(
        request_id="t2",
        chosen_route=RouteCategory.FAST_PATH,
        confidence=0.99,
    )
    res = TaskResult(
        request_id="t2",
        route_used=RouteCategory.FAST_PATH,
        output="Result",
        latency_ms=5.0,
    )
    recorder.record(RoutingRecord(request_id="t2", route_decision=dec, task_result=res))
    recorder.flush()

    assert log_file.exists()
    content = log_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(content) == 1

    parsed = json.loads(content[0])
    assert parsed["request_id"] == "t2"
    assert parsed["route"] == "FAST_PATH"
    # Ensure no raw prompt content is logged in telemetry

    assert "prompt" not in parsed
    assert "content" not in parsed


def test_telemetry_disabled_records_nothing():
    recorder = TelemetryRecorder(enabled=False)
    dec = RouteDecision(
        request_id="t3",
        chosen_route=RouteCategory.FAST_PATH,
    )
    recorder.record(RoutingRecord(request_id="t3", route_decision=dec))
    assert len(recorder.get_records()) == 0
