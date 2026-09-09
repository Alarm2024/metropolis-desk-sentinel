"""FastAPI integration tests."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Isolate decision log per test module run
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
    assert body["mode"] == "local-mock"


def test_evaluate_deterministic_seed() -> None:
    res1 = client.post("/api/evaluate", json={"seed": "demo-deterministic"})
    res2 = client.post("/api/evaluate", json={"seed": "demo-deterministic"})
    assert res1.status_code == 200
    assert res2.status_code == 200
    c1 = res1.json()
    c2 = res2.json()
    assert c1["provenance_hash"] == c2["provenance_hash"]
    assert c1["metrics"]["seed"] == "demo-deterministic"


def test_evaluate_appends_decision_log() -> None:
    client.post("/api/evaluate", json={"seed": "log-test"})
    res = client.get("/api/decisions?limit=5")
    assert res.status_code == 200
    assert res.json()["count"] >= 1


def test_last_card_after_evaluate() -> None:
    client.post("/api/evaluate", json={"seed": "last-test"})
    res = client.get("/api/last")
    assert res.status_code == 200
    assert res.json()["signal"] in ("CLEAR", "SHORT", "HOLD")


def test_metrics_with_seed_query() -> None:
    res = client.get("/api/metrics?seed=fixed-seed")
    assert res.status_code == 200
    assert res.json()["seed"] == "fixed-seed"
