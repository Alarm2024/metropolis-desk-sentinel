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
