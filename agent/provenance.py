"""Provenance hashing and verification — reproducible provenance trail."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from pydantic import ValidationError

from agent.schema import DeskMetricsSchema, SignalCardSchema


# Card fields that must be present for verify_card_provenance to recompute
# the hash. refusal_code and refusal_reason are optional (None for
# directional cards) and are read with .get().
_REQUIRED_CARD_FIELDS = (
    "provenance_hash",
    "metrics",
    "signal",
    "safe_hold",
    "trust_posture",
    "reason_codes",
    "summary",
    "reasons",
    "confidence",
    "agent_version",
    "schema_version",
    "timestamp_ms",
)

# Keys the hash understands. Anything else on the card or inside metrics
# fails verification instead of being silently dropped.
_ALLOWED_TOP_LEVEL_KEYS = frozenset(SignalCardSchema.model_fields)
_ALLOWED_METRIC_KEYS = frozenset(DeskMetricsSchema.model_fields)


def canonicalize_metrics(metrics: dict[str, Any]) -> dict[str, Any]:
    """Normalize metrics to the same JSON form used in stored cards (float coercion)."""
    return DeskMetricsSchema.model_validate(metrics).model_dump(mode="json")


def provenance_payload(
    metrics: dict[str, Any],
    signal: str,
    safe_hold: bool,
    refusal_code: str | None,
    trust_posture: str,
    reason_codes: list[str],
    summary: str,
    reasons: list[str],
    confidence: float,
    refusal_reason: str | None,
    agent_version: str,
    schema_version: str,
    timestamp_ms: int,
) -> dict[str, Any]:
    """Hash inputs taken from the card itself, not from module constants."""
    return {
        "agent_version": agent_version,
        "schema_version": schema_version,
        "timestamp_ms": timestamp_ms,
        "metrics": metrics,
        "signal": signal,
        "safe_hold": safe_hold,
        "trust_posture": trust_posture,
        "refusal_code": refusal_code,
        "reason_codes": reason_codes,
        "summary": summary,
        "reasons": reasons,
        "confidence": confidence,
        "refusal_reason": refusal_reason,
    }


def compute_provenance_hash(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def build_provenance_hash(
    metrics: dict[str, Any],
    signal: str,
    safe_hold: bool,
    refusal_code: str | None,
    trust_posture: str,
    reason_codes: list[str],
    summary: str,
    reasons: list[str],
    confidence: float,
    refusal_reason: str | None,
    agent_version: str,
    schema_version: str,
    timestamp_ms: int,
) -> str:
    payload = provenance_payload(
        canonicalize_metrics(metrics),
        signal,
        safe_hold,
        refusal_code,
        trust_posture,
        reason_codes,
        summary,
        reasons,
        confidence,
        refusal_reason,
        agent_version,
        schema_version,
        timestamp_ms,
    )
    return compute_provenance_hash(payload)


def verify_card_provenance(card: dict[str, Any] | SignalCardSchema) -> bool:
    """Return True if provenance_hash matches the hash recomputed from card fields.

    This only shows that the hashed fields (the card's own agent_version,
    schema_version, and top-level timestamp_ms, plus metrics, signal,
    safe_hold, trust_posture, refusal_code, reason_codes, summary, reasons,
    confidence, and refusal_reason) have not been edited since the hash was
    computed. Unknown keys on the card or inside metrics fail this check.

    It does NOT prove who produced the card — there is no key involved, so
    anyone can build a card and compute a matching hash for it. It also does
    NOT prove the signal correctly follows from the metrics (this function
    never re-runs evaluate_desk). And because it is a hash over the current
    values with no external anchor, a full rewrite of a record with a
    freshly recomputed hash, or truncation of a stored record, is not
    detected by this check alone.
    """
    if isinstance(card, SignalCardSchema):
        data = card.model_dump(mode="json")
    else:
        data = card
    if not isinstance(data, dict):
        return False
    missing = [field for field in _REQUIRED_CARD_FIELDS if field not in data]
    if missing:
        # A card without the hashed fields cannot verify; report failure
        # instead of raising KeyError.
        return False
    if set(data) - _ALLOWED_TOP_LEVEL_KEYS:
        return False
    metrics = data["metrics"]
    if not isinstance(metrics, dict) or set(metrics) - _ALLOWED_METRIC_KEYS:
        return False
    expected = data["provenance_hash"]
    try:
        actual = build_provenance_hash(
            metrics=metrics,
            signal=data["signal"],
            safe_hold=data["safe_hold"],
            refusal_code=data.get("refusal_code"),
            trust_posture=data["trust_posture"],
            reason_codes=data["reason_codes"],
            summary=data["summary"],
            reasons=data["reasons"],
            confidence=data["confidence"],
            refusal_reason=data.get("refusal_reason"),
            agent_version=data["agent_version"],
            schema_version=data["schema_version"],
            timestamp_ms=data["timestamp_ms"],
        )
    except (TypeError, ValueError, ValidationError):
        # Wrong-typed fields (e.g. metrics not a mapping, or failing schema
        # validation) are also a verification failure, not a crash.
        return False
    return expected == actual
