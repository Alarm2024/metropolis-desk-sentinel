"""FastAPI integration tests."""

from __future__ import annotations

import json
import os
import socket
import threading
import time
from pathlib import Path

import httpx
import pytest
import uvicorn
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


def test_directional_api_omits_refusal_fields() -> None:
    """CLEAR/SHORT omit refusal_code — never null placeholders (F3 honesty)."""
    card = client.post("/api/scenarios/clear_bullish/evaluate").json()
    assert card["signal"] == "CLEAR"
    assert card["trust_posture"] == "DIRECTIONAL"
    assert "refusal_code" not in card
    assert "refusal_reason" not in card


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


def test_malformed_log_line_does_not_500() -> None:
    client.post("/api/evaluate", json={"seed": "malformed-log"})
    log_path = Path(os.environ["DECISION_LOG_PATH"])
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write("{not json\n")
    res = client.get("/api/decisions?limit=5")
    assert res.status_code == 200
    assert res.json()["integrity_ok"] is False
    res = client.post("/api/evaluate", json={"seed": "malformed-log-2"})
    assert res.status_code == 409
    assert res.json()["detail"] == "decision log is malformed; append refused"


def _assert_decision_snapshot(body: dict) -> None:
    """count and the integrity message must describe one response's snapshot."""
    message = body["integrity_message"]
    assert body["count"] == len(body["entries"])
    if message == "empty log":
        assert body["integrity_ok"] is True
        assert body["count"] == 0
        return
    assert body["integrity_ok"] is True, message
    assert "chain broken" not in message
    prefix = "hashes match for "
    suffix = " entries"
    assert message.startswith(prefix) and message.endswith(suffix), message
    matched = int(message[len(prefix) : -len(suffix)])
    assert matched == body["count"], message


@pytest.mark.parametrize(
    "field",
    ["agent_version", "schema_version", "timestamp_ms", "metrics.undocumented_risk"],
)
def test_verify_rejects_card_field_or_unknown_metric(field: str) -> None:
    """Changing identity, schema version, timestamp, or an unknown metric fails verify."""
    card = client.post("/api/evaluate", json={"seed": "hash-coverage"}).json()
    assert client.post("/api/verify", json=card).json()["valid"] is True

    edited = json.loads(json.dumps(card))
    if field == "agent_version":
        edited["agent_version"] = "0.0.0-edited"
    elif field == "schema_version":
        edited["schema_version"] = "0.0"
    elif field == "timestamp_ms":
        edited["timestamp_ms"] = edited["timestamp_ms"] + 1
    else:
        edited["metrics"]["undocumented_risk"] = 1

    res = client.post("/api/verify", json=edited)
    assert res.status_code == 200
    assert res.json()["valid"] is False


def test_verify_rejects_unknown_top_level_key() -> None:
    card = client.post("/api/evaluate", json={"seed": "hash-unknown-top"}).json()
    card["undocumented_claim"] = True
    res = client.post("/api/verify", json=card)
    assert res.status_code == 200
    assert res.json()["valid"] is False


def test_concurrent_decision_reads_during_writes() -> None:
    """HTTP reads during appends must not report a torn line as a broken chain.

    Each response's count and integrity message come from the same snapshot,
    so "hashes match for N entries" matches count whenever the limit covers the log.
    """
    n_writers = 4
    per_writer = 4
    errors: list[str] = []
    errors_lock = threading.Lock()
    successful_writes = 0
    writes_lock = threading.Lock()

    probe = socket.socket()
    probe.bind(("127.0.0.1", 0))
    port = probe.getsockname()[1]
    probe.close()

    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
    server_thread = threading.Thread(target=server.run, daemon=True)
    server_thread.start()
    base = f"http://127.0.0.1:{port}"
    deadline = time.time() + 5
    while time.time() < deadline:
        try:
            if httpx.get(f"{base}/api/health", timeout=0.2).status_code == 200:
                break
        except httpx.HTTPError:
            time.sleep(0.05)
    else:
        server.should_exit = True
        raise RuntimeError("decision log server did not start")

    def record(message: str) -> None:
        with errors_lock:
            errors.append(message)

    def writer(index: int) -> None:
        nonlocal successful_writes
        with httpx.Client(base_url=base, timeout=5) as local:
            for seq in range(per_writer):
                res = local.post("/api/evaluate", json={"seed": f"conc-{index}-{seq}"})
                if res.status_code != 200:
                    record(f"write {index}-{seq}: {res.status_code} {res.text}")
                    continue
                with writes_lock:
                    successful_writes += 1

    def reader(index: int) -> None:
        with httpx.Client(base_url=base, timeout=5) as local:
            for _ in range(per_writer):
                res = local.get("/api/decisions", params={"limit": 200})
                if res.status_code != 200:
                    record(f"read {index}: {res.status_code} {res.text}")
                    continue
                try:
                    _assert_decision_snapshot(res.json())
                except AssertionError as exc:
                    record(f"read {index}: {exc}")

    threads = [threading.Thread(target=writer, args=(i,)) for i in range(n_writers)]
    threads += [threading.Thread(target=reader, args=(i,)) for i in range(n_writers)]
    try:
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=30)
        assert not any(thread.is_alive() for thread in threads)
        assert not errors, errors

        final = httpx.get(f"{base}/api/decisions", params={"limit": 200}, timeout=5)
        assert final.status_code == 200
        body = final.json()
        _assert_decision_snapshot(body)
        assert body["count"] == successful_writes == n_writers * per_writer
    finally:
        server.should_exit = True
        server_thread.join(timeout=5)


def test_symbol_and_seed_length_capped() -> None:
    assert client.post("/api/evaluate", json={"symbol": "X" * 33}).status_code == 422
    assert client.post("/api/evaluate", json={"seed": "s" * 129}).status_code == 422
    assert client.get("/api/metrics", params={"symbol": "X" * 33}).status_code == 422
    assert client.post("/api/evaluate", json={"symbol": "X" * 32, "seed": "s" * 128}).status_code == 200
