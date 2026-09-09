"""FastAPI app — agent API + status UI for local MVP."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from agent.decision_log import append_decision, read_decisions, summarize_decisions
from agent.desk_agent import evaluate_desk
from agent.metrics import generate_mock_metrics

ROOT = Path(__file__).resolve().parent.parent
UI_DIR = ROOT / "ui"

PUBLIC_METRICS_ENABLED = os.environ.get("PUBLIC_METRICS", "").lower() in ("1", "true", "yes")

app = FastAPI(
    title="Morning Light Desk Sentinel",
    description="Trust / Identity & AI Infrastructure — mock desk signals with provenance",
    version="0.2.0",
)

_last_card: dict[str, Any] | None = None


class EvaluateRequest(BaseModel):
    seed: str | None = Field(default=None, description="Deterministic demo seed")
    symbol: str = Field(default="MLDS-MOCK", description="Mock symbol label")


def _run_evaluation(seed: str | None = None, symbol: str = "MLDS-MOCK") -> dict[str, Any]:
    global _last_card
    metrics = generate_mock_metrics(symbol=symbol, seed=seed)
    card = evaluate_desk(metrics)
    card_dict = card.to_dict()
    append_decision(card_dict)
    _last_card = card_dict
    return card_dict


@app.get("/api/health")
def health() -> dict[str, str | bool]:
    return {
        "status": "ok",
        "mode": "local-mock",
        "public_metrics": PUBLIC_METRICS_ENABLED,
        "agent_version": "0.2.0-trust",
    }


@app.get("/api/metrics")
def metrics(
    seed: str | None = Query(default=None, description="Deterministic demo seed"),
    symbol: str = Query(default="MLDS-MOCK"),
) -> dict[str, Any]:
    return generate_mock_metrics(symbol=symbol, seed=seed).to_dict()


@app.post("/api/evaluate")
def evaluate(body: EvaluateRequest | None = None, seed: str | None = Query(default=None)) -> dict[str, Any]:
    """Run desk evaluation. Pass seed via JSON body or query for deterministic demos."""
    req = body or EvaluateRequest()
    effective_seed = req.seed if req.seed is not None else seed
    return _run_evaluation(seed=effective_seed, symbol=req.symbol)


@app.get("/api/last")
def last_card() -> dict[str, Any]:
    if _last_card is None:
        return {"signal": None, "message": "No evaluation yet — POST /api/evaluate first"}
    return _last_card


@app.get("/api/decisions")
def decisions(limit: int = Query(default=20, ge=1, le=200)) -> dict[str, Any]:
    entries = read_decisions(limit=limit)
    return {
        "count": len(entries),
        "entries": [{"logged_at": e.logged_at, "card": e.card} for e in entries],
    }


if PUBLIC_METRICS_ENABLED:

    @app.get("/api/public/summary")
    def public_summary() -> dict[str, Any]:
        """Keyless read-only aggregate metrics — no secrets, no live trading claims."""
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
