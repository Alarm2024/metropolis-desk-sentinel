"""FastAPI integration tests."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

os.environ["DECISION_LOG_PATH"] = str(Path(__file__).resolve().parent / "_api_test_log.jsonl")

from server.app import app  # noqa: E402

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_log() -> None:
    log_path = Path(os.environ["DECISION_LOG_PATH"])
    if log_path.exists():
        log_path.unlink()


def test_health() -> None:
    res = client.get("/api/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert body["schema_version"] == "2.0"
    assert "SAFE HOLD" in body["product"]


def test_schema_endpoint() -> None:
    res = client.get("/api/schema")
    assert res.status_code == 200
    body = res.json()
    assert body["schema_version"] == "2.0"
    assert "trust_invariants" in body
    assert "json_schema" in body


def test_evaluate_deterministic_seed() -> None:
    res1 = client.post("/api/evaluate", json={"seed": "demo-deterministic"})
    res2 = client.post("/api/evaluate", json={"seed": "demo-deterministic"})
    assert res1.status_code == 200
    assert res2.status_code == 200
    c1 = res1.json()
    c2 = res2.json()
    assert c1 == c2
    assert c1["provenance_hash"] == c2["provenance_hash"]


def test_scenarios_list_and_evaluate() -> None:
    res = client.get("/api/scenarios")
    assert res.status_code == 200
    names = [s["name"] for s in res.json()]
    assert "hold_thin_liquidity" in names

    res2 = client.post("/api/scenarios/hold_thin_liquidity/evaluate")
    assert res2.status_code == 200
    card = res2.json()
    assert card["signal"] == "HOLD"
    assert card["refusal_code"] == "EXEC_QUALITY"


def test_decisions_integrity() -> None:
    client.post("/api/evaluate", json={"seed": "log-test"})
    res = client.get("/api/decisions?limit=5")
    assert res.status_code == 200
    body = res.json()
    assert body["integrity_ok"] is True
    assert body["count"] >= 1


def test_verify_endpoint() -> None:
    card = client.post("/api/evaluate", json={"seed": "verify-test"}).json()
    res = client.post("/api/verify", json=card)
    assert res.status_code == 200
    assert res.json()["valid"] is True


def test_verify_endpoint_malformed_body_returns_400() -> None:
    res = client.post("/api/verify", json={})
    assert res.status_code == 400
    assert "malformed card" in res.json()["detail"]


def test_evaluate_int_metric_fields_do_not_break_provenance() -> None:
    """Regression: int-valued metrics must not 500 on append/verify."""
    from agent.metrics import DeskMetrics
    from agent.desk_agent import evaluate_desk
    from agent.decision_log import append_decision

    metrics = DeskMetrics(
        symbol="API-INT",
        bid_ask_bps=5,
        volume_delta_pct=14,
        order_flow_imbalance=0.72,
        volatility_1h_pct=1,
        liquidity_score=0.85,
        spread_stability=0.9,
        timestamp_ms=1725900000000,
        seed="api-int-metrics",
    )
    card_dict = evaluate_desk(metrics).to_dict()
    append_decision(card_dict)  # raises if provenance invalid

    res = client.post("/api/verify", json=card_dict)
    assert res.status_code == 200
    assert res.json()["valid"] is True
