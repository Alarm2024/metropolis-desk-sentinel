"""Provenance hashing and verification — reproducible audit trail."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from agent.schema import AGENT_VERSION, CARD_SCHEMA_VERSION, SignalCardSchema


def provenance_payload(
    metrics: dict[str, Any],
    signal: str,
    safe_hold: bool,
    refusal_code: str | None,
    trust_posture: str,
    reason_codes: list[str],
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
) -> str:
    payload = provenance_payload(
        metrics, signal, safe_hold, refusal_code, trust_posture, reason_codes
    )
    return compute_provenance_hash(payload)


def verify_card_provenance(card: dict[str, Any] | SignalCardSchema) -> bool:
    """Return True if provenance_hash matches recomputed hash from card fields."""
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
    )
    return expected == actual
