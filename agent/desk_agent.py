"""Desk sentinel agent — CLEAR / SHORT / HOLD with SAFE HOLD honesty."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Literal

from agent.metrics import DeskMetrics

AGENT_VERSION = "0.2.0-trust"
CARD_SCHEMA_VERSION = "1.1"


class Signal(str, Enum):
    CLEAR = "CLEAR"
    SHORT = "SHORT"
    HOLD = "HOLD"


class RefusalCode(str, Enum):
    """Explicit refusal codes when SAFE HOLD fires — auditable, never silent."""

    EXEC_QUALITY = "EXEC_QUALITY"
    NO_EDGE = "NO_EDGE"
    NEUTRAL_BAND = "NEUTRAL_BAND"


REFUSAL_MESSAGES: dict[RefusalCode, str] = {
    RefusalCode.EXEC_QUALITY: "Refused directional action: execution quality below trust threshold",
    RefusalCode.NO_EDGE: "Refused directional action: composite score too weak to trust",
    RefusalCode.NEUTRAL_BAND: "Refused directional action: score inside neutral band — no fake conviction",
}


@dataclass(frozen=True)
class SignalCard:
    signal: Literal["CLEAR", "SHORT", "HOLD"]
    summary: str
    safe_hold: bool
    confidence: float
    reasons: list[str]
    metrics: dict[str, Any]
    provenance_hash: str
    agent_version: str
    schema_version: str
    timestamp_ms: int
    refusal_code: str | None = None
    refusal_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "signal": self.signal,
            "summary": self.summary,
            "safe_hold": self.safe_hold,
            "confidence": self.confidence,
            "reasons": self.reasons,
            "metrics": self.metrics,
            "provenance_hash": self.provenance_hash,
            "agent_version": self.agent_version,
            "schema_version": self.schema_version,
            "timestamp_ms": self.timestamp_ms,
        }
        if self.refusal_code is not None:
            out["refusal_code"] = self.refusal_code
        if self.refusal_reason is not None:
            out["refusal_reason"] = self.refusal_reason
        return out


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def _score_metrics(m: DeskMetrics) -> tuple[float, list[str]]:
    """Return directional score (-1 bearish .. +1 bullish) and reason strings."""
    reasons: list[str] = []
    score = 0.0
    weight_sum = 0.0

    w = 0.35
    score += m.order_flow_imbalance * w
    weight_sum += w
    if abs(m.order_flow_imbalance) < 0.15:
        reasons.append("Order flow near neutral")
    elif m.order_flow_imbalance > 0.35:
        reasons.append("Buy-side order flow dominant")
    elif m.order_flow_imbalance < -0.35:
        reasons.append("Sell-side order flow dominant")

    w = 0.25
    vol_norm = _clamp(m.volume_delta_pct / 20.0, -1.0, 1.0)
    score += vol_norm * w
    weight_sum += w
    if abs(m.volume_delta_pct) < 4:
        reasons.append("Volume delta flat")
    elif m.volume_delta_pct > 8:
        reasons.append("Volume expanding on uptick")
    elif m.volume_delta_pct < -8:
        reasons.append("Volume expanding on downtick")

    w = 0.2
    exec_quality = _clamp(m.liquidity_score * m.spread_stability)
    if exec_quality < 0.35:
        reasons.append("Thin liquidity — execution risk elevated")
        score -= 0.15 * w
    elif exec_quality > 0.7:
        reasons.append("Liquidity and spread stability acceptable")
    weight_sum += w

    w = 0.2
    if m.volatility_1h_pct > 3.0:
        reasons.append("Elevated 1h volatility")
        damp = _clamp((m.volatility_1h_pct - 3.0) / 2.0)
        score *= 1.0 - 0.5 * damp
    weight_sum += w

    if m.bid_ask_bps > 8:
        reasons.append("Wide bid-ask spread")

    normalized = score / weight_sum if weight_sum else 0.0
    return normalized, reasons


def _provenance_hash(
    metrics: DeskMetrics,
    signal: str,
    safe_hold: bool,
    refusal_code: str | None,
) -> str:
    payload = {
        "agent_version": AGENT_VERSION,
        "schema_version": CARD_SCHEMA_VERSION,
        "metrics": metrics.to_dict(),
        "signal": signal,
        "safe_hold": safe_hold,
        "refusal_code": refusal_code,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def evaluate_desk(metrics: DeskMetrics) -> SignalCard:
    """
    Evaluate mock desk metrics and emit a CLEAR / SHORT / HOLD card.

    SAFE HOLD honesty: ambiguous or low-trust conditions default to HOLD with
    safe_hold=True and an explicit refusal_code rather than overstating conviction.
    """
    score, reasons = _score_metrics(metrics)
    abs_score = abs(score)

    clear_threshold = 0.42
    short_threshold = -0.42
    min_confidence = 0.55
    min_exec_quality = 0.4

    exec_quality = metrics.liquidity_score * metrics.spread_stability
    safe_hold = False
    refusal_code: RefusalCode | None = None
    confidence = _clamp(abs_score + exec_quality * 0.25)

    if exec_quality < min_exec_quality or abs_score < 0.18:
        signal = Signal.HOLD
        safe_hold = True
        confidence = _clamp(confidence * 0.6)
        if exec_quality < min_exec_quality:
            refusal_code = RefusalCode.EXEC_QUALITY
            reasons.append("SAFE HOLD: insufficient execution quality")
        else:
            refusal_code = RefusalCode.NO_EDGE
            reasons.append("SAFE HOLD: no actionable edge detected")
        summary = "Hold — conditions ambiguous or untrusted for directional action"
    elif score >= clear_threshold and confidence >= min_confidence:
        signal = Signal.CLEAR
        safe_hold = False
        summary = "Clear — bullish desk bias within trust bounds"
        reasons.append(f"Composite score {score:+.2f} above clear threshold")
    elif score <= short_threshold and confidence >= min_confidence:
        signal = Signal.SHORT
        safe_hold = False
        summary = "Short — bearish desk bias within trust bounds"
        reasons.append(f"Composite score {score:+.2f} below short threshold")
    else:
        signal = Signal.HOLD
        safe_hold = True
        refusal_code = RefusalCode.NEUTRAL_BAND
        confidence = _clamp(confidence * 0.75)
        reasons.append("SAFE HOLD: score inside neutral band")
        summary = "Hold — edge too weak to act; staying honest"

    refusal_code_str = refusal_code.value if refusal_code else None
    refusal_reason = REFUSAL_MESSAGES.get(refusal_code) if refusal_code else None
    prov = _provenance_hash(metrics, signal.value, safe_hold, refusal_code_str)

    return SignalCard(
        signal=signal.value,
        summary=summary,
        safe_hold=safe_hold,
        confidence=round(confidence, 3),
        reasons=reasons[:6],
        metrics=metrics.to_dict(),
        provenance_hash=prov,
        agent_version=AGENT_VERSION,
        schema_version=CARD_SCHEMA_VERSION,
        timestamp_ms=metrics.timestamp_ms,
        refusal_code=refusal_code_str,
        refusal_reason=refusal_reason,
    )
