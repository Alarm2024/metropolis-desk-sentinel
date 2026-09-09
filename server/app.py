"""FastAPI app — agent API + status UI for local MVP."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from agent.desk_agent import evaluate_desk
from agent.metrics import generate_mock_metrics

ROOT = Path(__file__).resolve().parent.parent
UI_DIR = ROOT / "ui"

app = FastAPI(
    title="Morning Light Desk Sentinel",
    description="Trust / Identity & AI Infrastructure MVP — mock desk signals with provenance",
    version="0.1.0",
)

_last_card: dict | None = None


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "mode": "local-mock"}


@app.get("/api/metrics")
def metrics() -> dict:
    return generate_mock_metrics().to_dict()


@app.post("/api/evaluate")
def evaluate() -> dict:
    global _last_card
    m = generate_mock_metrics()
    card = evaluate_desk(m)
    _last_card = card.to_dict()
    return _last_card


@app.get("/api/last")
def last_card() -> dict:
    if _last_card is None:
        return {"signal": None, "message": "No evaluation yet — POST /api/evaluate first"}
    return _last_card


@app.get("/")
def index() -> FileResponse:
    return FileResponse(UI_DIR / "index.html")


app.mount("/static", StaticFiles(directory=UI_DIR), name="static")
