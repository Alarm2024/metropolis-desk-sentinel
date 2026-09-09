"""Append-only decision log for auditable desk evaluations."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_LOG_PATH = Path(os.environ.get("DECISION_LOG_PATH", "data/decision_log.jsonl"))


@dataclass(frozen=True)
class LogEntry:
    logged_at: str
    card: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {"logged_at": self.logged_at, "card": self.card}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def append_decision(card: dict[str, Any], log_path: Path | None = None) -> LogEntry:
    """Append one evaluated card to the JSONL decision log."""
    path = log_path or DEFAULT_LOG_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = LogEntry(logged_at=_utc_now_iso(), card=card)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry.to_dict(), sort_keys=True, separators=(",", ":")))
        fh.write("\n")
    return entry


def read_decisions(limit: int = 100, log_path: Path | None = None) -> list[LogEntry]:
    """Read the most recent decisions (newest last in returned list)."""
    path = log_path or DEFAULT_LOG_PATH
    if not path.exists():
        return []

    entries: list[LogEntry] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            raw = json.loads(line)
            entries.append(LogEntry(logged_at=raw["logged_at"], card=raw["card"]))

    if limit > 0 and len(entries) > limit:
        entries = entries[-limit:]
    return entries


def summarize_decisions(log_path: Path | None = None) -> dict[str, Any]:
    """Aggregate read-only stats from the decision log."""
    entries = read_decisions(limit=0, log_path=log_path)
    by_signal: dict[str, int] = {"CLEAR": 0, "SHORT": 0, "HOLD": 0}
    safe_hold_count = 0
    refusal_codes: dict[str, int] = {}

    for entry in entries:
        card = entry.card
        signal = card.get("signal")
        if signal in by_signal:
            by_signal[signal] += 1
        if card.get("safe_hold"):
            safe_hold_count += 1
            code = card.get("refusal_code")
            if code:
                refusal_codes[code] = refusal_codes.get(code, 0) + 1

    total = len(entries)
    return {
        "total_evaluations": total,
        "by_signal": by_signal,
        "safe_hold_count": safe_hold_count,
        "safe_hold_rate": round(safe_hold_count / total, 3) if total else 0.0,
        "refusal_codes": refusal_codes,
        "schema_version": entries[-1].card.get("schema_version") if entries else None,
    }
