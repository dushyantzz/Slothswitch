"""Unit tests for the SlothSwitch CLI executed in-process for coverage."""

import sys
import pytest

from slothswitch.cli import main


def test_cli_inprocess_route(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["slothswitch", "route", "I need my invoice"])
    main()
    captured = capsys.readouterr()
    assert "Routing Result" in captured.out
    assert "Route:" in captured.out


def test_cli_inprocess_route_json(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["slothswitch", "route", "I need my invoice", "--json"])
    main()
    captured = capsys.readouterr()
    assert '"chosen_route":' in captured.out


def test_cli_inprocess_health(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["slothswitch", "health"])
    main()
    captured = capsys.readouterr()
    assert "Health Check" in captured.out


def test_cli_inprocess_demo(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["slothswitch", "demo"])
    main()
    captured = capsys.readouterr()
    assert "SlothSwitch Demo" in captured.out
    assert "Telemetry Summary" in captured.out


def test_cli_inprocess_eval(monkeypatch, capsys):
    monkeypatch.setattr(
        sys,
        "argv",
        ["slothswitch", "eval", "--dataset", "datasets/customer_support_routing.json"],
    )
    main()
    captured = capsys.readouterr()
    assert "Benchmark Evaluation" in captured.out
    assert "Routing Accuracy:" in captured.out


def test_cli_inprocess_no_args_exits(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["slothswitch"])
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1
