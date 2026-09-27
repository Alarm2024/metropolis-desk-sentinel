"""Append-only, hash-chained decision log for desk evaluations."""

from __future__ import annotations

import hashlib
import json
import os
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agent.provenance import verify_card_provenance

DEFAULT_LOG_PATH = Path(os.environ.get("DECISION_LOG_PATH", "data/decision_log.jsonl"))
LOG_SCHEMA_VERSION = "1.0"

# Guards appends and reads of the log file. FastAPI runs sync endpoints in a
# threadpool, so concurrent requests within one process can otherwise race:
# two callers read the same "last entry" before either has written, and both
# append with the same entry_id / prev_hash, breaking the chain. A reader
# can also observe a partial line mid-append and report that torn write as
# a broken chain. This lock makes the read+append atomic, and readers copy
# one full snapshot while holding it, within a single process.
#
# It does NOT protect against multiple processes (e.g. running uvicorn with
# --workers > 1, or multiple replicas) writing to the same log file at the
# same time. That would additionally need a file lock (e.g. fcntl.flock on
# POSIX) around the same critical section.
_LOG_LOCK = threading.Lock()


@dataclass(frozen=True)
class LogEntry:
    entry_id: int
    logged_at: str
    prev_hash: str | None
    entry_hash: str
    log_schema_version: str
    card: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "logged_at": self.logged_at,
            "prev_hash": self.prev_hash,
            "entry_hash": self.entry_hash,
            "log_schema_version": self.log_schema_version,
            "card": self.card,
        }


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _entry_hash(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def _last_entry_hash(path: Path) -> tuple[int, str | None]:
    if not path.exists():
        return 0, None
    last_line = ""
    # O(n) full-file scan; runs inside _LOG_LOCK (via append_decision), fine for demo-sized logs.
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            stripped = line.strip()
            if stripped:
                last_line = stripped
    if not last_line:
        return 0, None
    try:
        raw = json.loads(last_line)
        return int(raw["entry_id"]), raw["entry_hash"]
    except (json.JSONDecodeError, KeyError, TypeError, ValueError, AttributeError) as exc:
        # Refuse to extend a chain whose last entry can't be read, with a clear
        # error instead of a raw JSON exception.
        raise ValueError(f"decision log last entry is malformed; refusing to append ({exc})") from exc


def append_decision(card: dict[str, Any], log_path: Path | None = None) -> LogEntry:
    """Append one validated card to the hash-chained JSONL decision log.

    Thread-safe within a single process (see _LOG_LOCK above).
    """
    if not verify_card_provenance(card):
        raise ValueError("refusing to log card with invalid provenance_hash")

    path = log_path or DEFAULT_LOG_PATH

    with _LOG_LOCK:
        path.parent.mkdir(parents=True, exist_ok=True)

        prev_id, prev_hash = _last_entry_hash(path)
        entry_id = prev_id + 1
        logged_at = _utc_now_iso()

        body = {
            "entry_id": entry_id,
            "logged_at": logged_at,
            "prev_hash": prev_hash,
            "log_schema_version": LOG_SCHEMA_VERSION,
            "card": card,
        }
        entry_hash = _entry_hash(body)
        entry = LogEntry(
            entry_id=entry_id,
            logged_at=logged_at,
            prev_hash=prev_hash,
            entry_hash=entry_hash,
            log_schema_version=LOG_SCHEMA_VERSION,
            card=card,
        )

        record = entry.to_dict()
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, sort_keys=True, separators=(",", ":")))
            fh.write("\n")
        return entry


def _snapshot_text(path: Path) -> str | None:
    """Copy the whole log while holding _LOG_LOCK.

    None means the file does not exist. A string (possibly empty) is one
    consistent snapshot: callers parse that text and do not read the file again.
    """
    with _LOG_LOCK:
        if not path.exists():
            return None
        return path.read_text(encoding="utf-8")


def _entries_from_text(text: str | None, limit: int) -> list[LogEntry]:
    if not text:
        return []

    entries: list[LogEntry] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            raw = json.loads(line)
            entry = LogEntry(
                entry_id=raw["entry_id"],
                logged_at=raw["logged_at"],
                prev_hash=raw.get("prev_hash"),
                entry_hash=raw["entry_hash"],
                log_schema_version=raw.get("log_schema_version", "1.0"),
                card=raw["card"],
            )
            if not isinstance(entry.card, dict):
                continue
        except (json.JSONDecodeError, KeyError, TypeError, AttributeError):
            continue
        entries.append(entry)

    if limit > 0 and len(entries) > limit:
        entries = entries[-limit:]
    return entries


def _integrity_from_text(text: str | None) -> tuple[bool, str]:
    if text is None:
        return True, "empty log"

    prev_hash: str | None = None
    expected_id = 1

    for line_no, line in enumerate(text.splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            raw = json.loads(line)

            if raw.get("entry_id") != expected_id:
                return False, f"line {line_no}: expected entry_id {expected_id}, got {raw.get('entry_id')}"

            if raw.get("prev_hash") != prev_hash:
                return False, f"line {line_no}: prev_hash chain broken"

            body = {
                "entry_id": raw["entry_id"],
                "logged_at": raw["logged_at"],
                "prev_hash": raw.get("prev_hash"),
                "log_schema_version": raw.get("log_schema_version", "1.0"),
                "card": raw["card"],
            }
            if _entry_hash(body) != raw["entry_hash"]:
                return False, f"line {line_no}: entry_hash mismatch (tampered?)"

            if not verify_card_provenance(raw["card"]):
                return False, f"line {line_no}: card provenance invalid"
        except (json.JSONDecodeError, KeyError, TypeError, ValueError, AttributeError) as exc:
            return False, f"line {line_no}: malformed entry, chain broken ({exc})"

        prev_hash = raw["entry_hash"]
        expected_id += 1

    return True, f"verified {expected_id - 1} entries"


def read_decisions(limit: int = 100, log_path: Path | None = None) -> list[LogEntry]:
    """Read decisions from the log (newest last when limit applied).

    Holds _LOG_LOCK and parses one snapshot of the file. A line that fails
    to parse (malformed JSON, or missing a required key) is skipped rather
    than raised, so a corrupted log doesn't 500 every read. Callers that
    need to know whether the log itself is intact should check
    verify_log_integrity() rather than infer it from what this function returns.
    """
    path = log_path or DEFAULT_LOG_PATH
    return _entries_from_text(_snapshot_text(path), limit)


def verify_log_integrity(log_path: Path | None = None) -> tuple[bool, str]:
    """
    Verify hash chain and provenance for every entry.
    Holds _LOG_LOCK and checks one snapshot of the file.
    Returns (ok, message). A line that fails to parse (malformed JSON, a
    missing required key, or a card that no longer has the fields
    verify_card_provenance needs) is reported as a broken chain at that
    line rather than raised.
    """
    path = log_path or DEFAULT_LOG_PATH
    return _integrity_from_text(_snapshot_text(path))


def snapshot_decisions(
    limit: int = 100, log_path: Path | None = None
) -> tuple[list[LogEntry], bool, str]:
    """Return entries, integrity flag, and message from one locked snapshot.

    Callers that report a count together with integrity should use this so
    both values come from the same read.
    """
    path = log_path or DEFAULT_LOG_PATH
    text = _snapshot_text(path)
    ok, msg = _integrity_from_text(text)
    return _entries_from_text(text, limit), ok, msg


def summarize_decisions(log_path: Path | None = None) -> dict[str, Any]:
    """Aggregate read-only stats from the decision log."""
    entries, integrity_ok, integrity_msg = snapshot_decisions(limit=0, log_path=log_path)
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
        "log_integrity": {"ok": integrity_ok, "message": integrity_msg},
    }
