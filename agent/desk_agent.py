"""Desk sentinel agent — CLEAR / SHORT / HOLD with SAFE HOLD honesty."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Literal

from agent.metrics import DeskMetrics

AGENT_VERSION = "0.1.0-mvp"


class Signal(str, Enum):
    CLEAR = "CLEAR"
    SHORT = "SHORT"
    HOLD = "HOLD"


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
    timestamp_ms: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "signal": self.signal,
            "summary": self.summary,
            "safe_hold": self.safe_hold,
            "confidence": self.confidence,
            "reasons": self.reasons,
            "metrics": self.metrics,
            "provenance_hash": self.provenance_hash,
            "agent_version": self.agent_version,
            "timestamp_ms": self.timestamp_ms,
        }


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def _score_metrics(m: DeskMetrics) -> tuple[float, list[str]]:
    """Return directional score (-1 bearish .. +1 bullish) and reason strings."""
    reasons: list[str] = []
    score = 0.0
    weight_sum = 0.0

    # Order flow — primary directional cue
    w = 0.35
    score += m.order_flow_imbalance * w
    weight_sum += w
    if abs(m.order_flow_imbalance) < 0.15:
        reasons.append("Order flow near neutral")
    elif m.order_flow_imbalance > 0.35:
        reasons.append("Buy-side order flow dominant")
    elif m.order_flow_imbalance < -0.35:
        reasons.append("Sell-side order flow dominant")

    # Volume delta
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

    # Liquidity & spread — trust / execution quality
    w = 0.2
    exec_quality = _clamp(m.liquidity_score * m.spread_stability)
    if exec_quality < 0.35:
        reasons.append("Thin liquidity — execution risk elevated")
        score -= 0.15 * w
    elif exec_quality > 0.7:
        reasons.append("Liquidity and spread stability acceptable")
    weight_sum += w

    # Volatility dampener — high vol → less conviction
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


def _provenance_hash(metrics: DeskMetrics, signal: str, safe_hold: bool) -> str:
    payload = {
        "agent_version": AGENT_VERSION,
        "metrics": metrics.to_dict(),
        "signal": signal,
        "safe_hold": safe_hold,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def evaluate_desk(metrics: DeskMetrics) -> SignalCard:
    """
    Evaluate mock desk metrics and emit a CLEAR / SHORT / HOLD card.

    SAFE HOLD honesty: ambiguous or low-trust conditions default to HOLD with
    safe_hold=True rather than overstating directional conviction.
    """
    score, reasons = _score_metrics(metrics)
    abs_score = abs(score)

    # Thresholds tuned for mock data — conservative by design
    clear_threshold = 0.42
    short_threshold = -0.42
    min_confidence = 0.55
    min_exec_quality = 0.4

    exec_quality = metrics.liquidity_score * metrics.spread_stability
    safe_hold = False
    confidence = _clamp(abs_score + exec_quality * 0.25)

    if exec_quality < min_exec_quality or abs_score < 0.18:
        signal = Signal.HOLD
        safe_hold = True
        confidence = _clamp(confidence * 0.6)
        if exec_quality < min_exec_quality:
            reasons.append("SAFE HOLD: insufficient execution quality")
        else:
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
        confidence = _clamp(confidence * 0.75)
        reasons.append("SAFE HOLD: score inside neutral band")
        summary = "Hold — edge too weak to act; staying honest"

    prov = _provenance_hash(metrics, signal.value, safe_hold)

    return SignalCard(
        signal=signal.value,
        summary=summary,
        safe_hold=safe_hold,
        confidence=round(confidence, 3),
        reasons=reasons[:5],
        metrics=metrics.to_dict(),
        provenance_hash=prov,
        agent_version=AGENT_VERSION,
        timestamp_ms=metrics.timestamp_ms,
    )
