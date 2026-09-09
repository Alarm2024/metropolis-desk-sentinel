"""Market scenario fixtures for deterministic golden tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agent.metrics import DeskMetrics

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "tests" / "fixtures"


def load_fixture(name: str) -> DeskMetrics:
    """Load a named scenario fixture (without .json extension)."""
    path = FIXTURES_DIR / f"{name}.json"
    with path.open(encoding="utf-8") as fh:
        data: dict[str, Any] = json.load(fh)
    return DeskMetrics(**data["metrics"])


def load_golden(name: str) -> dict[str, Any]:
    """Load expected golden output for a scenario."""
    path = FIXTURES_DIR / f"{name}.golden.json"
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def list_scenarios() -> list[str]:
    return sorted(p.stem for p in FIXTURES_DIR.glob("*.json") if not p.name.endswith(".golden.json"))
