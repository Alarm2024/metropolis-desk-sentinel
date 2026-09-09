"""FastAPI app — Morning Light Desk Sentinel API + demo UI."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, ValidationError

from agent.decision_log import append_decision, read_decisions, summarize_decisions, verify_log_integrity
from agent.desk_agent import evaluate_desk
from agent.fixtures import list_scenarios, load_fixture
from agent.metrics import generate_mock_metrics
from agent.provenance import verify_card_provenance
from agent.schema import AGENT_VERSION, CARD_SCHEMA_VERSION, SignalCardSchema

ROOT = Path(__file__).resolve().parent.parent
UI_DIR = ROOT / "ui"

PUBLIC_METRICS_ENABLED = os.environ.get("PUBLIC_METRICS", "").lower() in ("1", "true", "yes")

app = FastAPI(
    title="Morning Light Desk Sentinel",
    description=(
        "Trust / Identity & AI Infrastructure for Metropolis Monad. "
        "Mock desk signals with SAFE HOLD honesty, provenance hashing, and append-only audit log. "
        "No live trading. No secrets."
    ),
    version=AGENT_VERSION,
    openapi_tags=[
        {"name": "health", "description": "Liveness and mode flags"},
        {"name": "evaluate", "description": "Run desk agent on mock or fixture metrics"},
        {"name": "audit", "description": "Decision log and provenance verification"},
        {"name": "schema", "description": "Typed card schema for judges"},
        {"name": "public", "description": "Optional keyless read-only aggregates"},
    ],
)

_last_card: dict[str, Any] | None = None


class EvaluateRequest(BaseModel):
    seed: str | None = Field(default=None, description="Deterministic demo seed — same seed, same hash")
    symbol: str = Field(default="MLDS-MOCK", description="Mock symbol label")


class HealthResponse(BaseModel):
    status: str
    mode: str
    agent_version: str
    schema_version: str
    public_metrics: bool
    product: str = "SAFE HOLD honesty — agents that refuse soft lies"


class DecisionsResponse(BaseModel):
    count: int
    integrity_ok: bool
    integrity_message: str
    entries: list[dict[str, Any]]


class ScenarioInfo(BaseModel):
    name: str
    description: str


def _card_dict(card: SignalCardSchema) -> dict[str, Any]:
    return card.to_dict()


def _run_evaluation(seed: str | None = None, symbol: str = "MLDS-MOCK") -> dict[str, Any]:
    global _last_card
    metrics = generate_mock_metrics(symbol=symbol, seed=seed)
    card = evaluate_desk(metrics)
    card_dict = _card_dict(card)
    append_decision(card_dict)
    _last_card = card_dict
    return card_dict


def _run_scenario(name: str) -> dict[str, Any]:
    global _last_card
    metrics = load_fixture(name)
    card = evaluate_desk(metrics)
    card_dict = _card_dict(card)
    append_decision(card_dict)
    _last_card = card_dict
    return card_dict


@app.get("/api/health", response_model=HealthResponse, tags=["health"])
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        mode="local-mock",
        agent_version=AGENT_VERSION,
        schema_version=CARD_SCHEMA_VERSION,
        public_metrics=PUBLIC_METRICS_ENABLED,
    )


@app.get("/api/schema", tags=["schema"])
def card_schema() -> dict[str, Any]:
    """Return JSON Schema for the typed signal card — for judges and integrators."""
    return {
        "title": "Morning Light Signal Card",
        "schema_version": CARD_SCHEMA_VERSION,
        "agent_version": AGENT_VERSION,
        "json_schema": SignalCardSchema.model_json_schema(),
        "trust_invariants": [
            "HOLD => safe_hold=true, trust_posture=REFUSAL, refusal_code required",
            "CLEAR/SHORT => safe_hold=false, trust_posture=DIRECTIONAL, no refusal fields",
            "provenance_hash must verify against metrics + signal + reason_codes",
            "decision log entries are hash-chained and provenance-checked on append",
        ],
    }


@app.get("/api/metrics", tags=["evaluate"])
def metrics(
    seed: str | None = Query(default=None, description="Deterministic demo seed"),
    symbol: str = Query(default="MLDS-MOCK"),
) -> dict[str, Any]:
    return generate_mock_metrics(symbol=symbol, seed=seed).to_dict()


@app.post("/api/evaluate", response_model=SignalCardSchema, tags=["evaluate"])
def evaluate(body: EvaluateRequest | None = None, seed: str | None = Query(default=None)) -> dict[str, Any]:
    req = body or EvaluateRequest()
    effective_seed = req.seed if req.seed is not None else seed
    return _run_evaluation(seed=effective_seed, symbol=req.symbol)


@app.get("/api/scenarios", response_model=list[ScenarioInfo], tags=["evaluate"])
def scenarios() -> list[ScenarioInfo]:
    """Named market fixtures for judge demos — deterministic golden scenarios."""
    import json
    from agent.fixtures import FIXTURES_DIR

    out: list[ScenarioInfo] = []
    for name in list_scenarios():
        path = FIXTURES_DIR / f"{name}.json"
        with path.open(encoding="utf-8") as fh:
            desc = json.load(fh).get("description", name)
        out.append(ScenarioInfo(name=name, description=desc))
    return out


@app.post("/api/scenarios/{name}/evaluate", response_model=SignalCardSchema, tags=["evaluate"])
def evaluate_scenario(name: str) -> dict[str, Any]:
    if name not in list_scenarios():
        raise HTTPException(status_code=404, detail=f"Unknown scenario: {name}")
    return _run_scenario(name)


@app.get("/api/last", tags=["evaluate"])
def last_card() -> dict[str, Any]:
    if _last_card is None:
        return {"signal": None, "message": "No evaluation yet — POST /api/evaluate first"}
    return _last_card


@app.get("/api/decisions", response_model=DecisionsResponse, tags=["audit"])
def decisions(limit: int = Query(default=20, ge=1, le=200)) -> DecisionsResponse:
    entries = read_decisions(limit=limit)
    ok, msg = verify_log_integrity()
    return DecisionsResponse(
        count=len(entries),
        integrity_ok=ok,
        integrity_message=msg,
        entries=[e.to_dict() for e in entries],
    )


@app.post("/api/verify", tags=["audit"])
def verify_card(card: dict[str, Any]) -> dict[str, Any]:
    """Verify provenance_hash for a submitted card JSON."""
    required = ("provenance_hash", "metrics", "signal", "safe_hold", "trust_posture", "reason_codes")
    missing = [field for field in required if field not in card]
    if missing:
        raise HTTPException(status_code=400, detail=f"malformed card: missing fields {missing}")
    try:
        ok = verify_card_provenance(card)
    except (KeyError, TypeError, ValidationError) as exc:
        raise HTTPException(status_code=400, detail=f"malformed card: {exc}") from exc
    return {"valid": ok, "provenance_hash": card["provenance_hash"]}


if PUBLIC_METRICS_ENABLED:

    @app.get("/api/public/summary", tags=["public"])
    def public_summary() -> dict[str, Any]:
        return {
            "mode": "local-mock",
            "read_only": True,
            "claims": "none — synthetic desk evaluations only",
            **summarize_decisions(),
        }


@app.get("/")
def index() -> FileResponse:
    return FileResponse(UI_DIR / "index.html")


app.mount("/static", StaticFiles(directory=UI_DIR), name="static")
