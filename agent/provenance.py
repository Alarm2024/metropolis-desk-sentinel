"""Provenance hashing and verification — reproducible provenance trail."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from agent.schema import (
    AGENT_VERSION,
    CARD_SCHEMA_VERSION,
    DeskMetricsSchema,
    SignalCardSchema,
)


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
) -> dict[str, Any]:
    return {
        "agent_version": AGENT_VERSION,
        "schema_version": CARD_SCHEMA_VERSION,
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
    )
    return compute_provenance_hash(payload)


def verify_card_provenance(card: dict[str, Any] | SignalCardSchema) -> bool:
    """Return True if provenance_hash matches the hash recomputed from card fields.

    This only shows that the hashed fields (metrics, signal, safe_hold,
    trust_posture, refusal_code, reason_codes, summary, reasons, confidence,
    and refusal_reason) have not been edited since the hash was computed.

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
    expected = data["provenance_hash"]
    actual = build_provenance_hash(
        metrics=data["metrics"],
        signal=data["signal"],
        safe_hold=data["safe_hold"],
        refusal_code=data.get("refusal_code"),
        trust_posture=data["trust_posture"],
        reason_codes=data["reason_codes"],
        summary=data["summary"],
        reasons=data["reasons"],
        confidence=data["confidence"],
        refusal_reason=data.get("refusal_reason"),
    )
    return expected == actual
