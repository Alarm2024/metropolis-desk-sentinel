"""Desk sentinel agent — SAFE HOLD honesty is the product."""

from __future__ import annotations

from agent.metrics import DeskMetrics
from agent.provenance import build_provenance_hash
from agent.schema import (
    AGENT_VERSION,
    CARD_SCHEMA_VERSION,
    REFUSAL_MESSAGES,
    RefusalCode,
    Signal,
    SignalCardSchema,
    TrustPosture,
)

# Trust thresholds — conservative by design; judges can audit these constants.
CLEAR_THRESHOLD = 0.42
SHORT_THRESHOLD = -0.42
MIN_CONFIDENCE = 0.55
MIN_EXEC_QUALITY = 0.40
MIN_EDGE = 0.18


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def _score_metrics(m: DeskMetrics) -> tuple[float, list[str], list[str]]:
    """Return score (-1..+1), human reasons, and machine reason_codes."""
    reasons: list[str] = []
    codes: list[str] = []
    score = 0.0
    weight_sum = 0.0

    w = 0.35
    score += m.order_flow_imbalance * w
    weight_sum += w
    if abs(m.order_flow_imbalance) < 0.15:
        reasons.append("Order flow near neutral")
        codes.append("ORDER_FLOW_NEUTRAL")
    elif m.order_flow_imbalance > 0.35:
        reasons.append("Buy-side order flow dominant")
        codes.append("BUY_FLOW_DOMINANT")
    elif m.order_flow_imbalance < -0.35:
        reasons.append("Sell-side order flow dominant")
        codes.append("SELL_FLOW_DOMINANT")

    w = 0.25
    vol_norm = _clamp(m.volume_delta_pct / 20.0, -1.0, 1.0)
    score += vol_norm * w
    weight_sum += w
    if abs(m.volume_delta_pct) < 4:
        reasons.append("Volume delta flat")
        codes.append("VOLUME_FLAT")
    elif m.volume_delta_pct > 8:
        reasons.append("Volume expanding on uptick")
        codes.append("VOLUME_UPTICK")
    elif m.volume_delta_pct < -8:
        reasons.append("Volume expanding on downtick")
        codes.append("VOLUME_DOWNTICK")

    w = 0.2
    exec_quality = _clamp(m.liquidity_score * m.spread_stability)
    if exec_quality < 0.35:
        reasons.append("Thin liquidity — execution risk elevated")
        codes.append("THIN_LIQUIDITY")
        score -= 0.15 * w
    elif exec_quality > 0.7:
        reasons.append("Liquidity and spread stability acceptable")
        codes.append("EXEC_QUALITY_OK")
    weight_sum += w

    w = 0.2
    if m.volatility_1h_pct > 3.0:
        reasons.append("Elevated 1h volatility")
        codes.append("HIGH_VOLATILITY")
        damp = _clamp((m.volatility_1h_pct - 3.0) / 2.0)
        score *= 1.0 - 0.5 * damp
    weight_sum += w

    if m.bid_ask_bps > 8:
        reasons.append("Wide bid-ask spread")
        codes.append("WIDE_SPREAD")

    normalized = score / weight_sum if weight_sum else 0.0
    return normalized, reasons, codes


def evaluate_desk(metrics: DeskMetrics) -> SignalCardSchema:
    """
    Evaluate mock desk metrics and emit a validated CLEAR / SHORT / HOLD card.

    Product principle: when trust is insufficient, refuse loudly — never fake CLEAR.
    """
    score, reasons, reason_codes = _score_metrics(metrics)
    abs_score = abs(score)
    exec_quality = metrics.liquidity_score * metrics.spread_stability
    confidence = _clamp(abs_score + exec_quality * 0.25)

    refusal_code: RefusalCode | None = None

    if exec_quality < MIN_EXEC_QUALITY or abs_score < MIN_EDGE:
        signal = Signal.HOLD
        confidence = _clamp(confidence * 0.6)
        if exec_quality < MIN_EXEC_QUALITY:
            refusal_code = RefusalCode.EXEC_QUALITY
            reasons.append("SAFE HOLD: insufficient execution quality")
            reason_codes.append("REFUSAL_EXEC_QUALITY")
        else:
            refusal_code = RefusalCode.NO_EDGE
            reasons.append("SAFE HOLD: no actionable edge detected")
            reason_codes.append("REFUSAL_NO_EDGE")
        summary = "Hold — conditions untrusted for directional action"
        trust_posture = TrustPosture.REFUSAL
    elif score >= CLEAR_THRESHOLD and confidence >= MIN_CONFIDENCE:
        signal = Signal.CLEAR
        summary = "Clear — bullish desk bias within trust bounds"
        reasons.append(f"Composite score {score:+.2f} above clear threshold")
        reason_codes.append("SCORE_ABOVE_CLEAR")
        trust_posture = TrustPosture.DIRECTIONAL
    elif score <= SHORT_THRESHOLD and confidence >= MIN_CONFIDENCE:
        signal = Signal.SHORT
        summary = "Short — bearish desk bias within trust bounds"
        reasons.append(f"Composite score {score:+.2f} below short threshold")
        reason_codes.append("SCORE_BELOW_SHORT")
        trust_posture = TrustPosture.DIRECTIONAL
    else:
        signal = Signal.HOLD
        refusal_code = RefusalCode.NEUTRAL_BAND
        confidence = _clamp(confidence * 0.75)
        reasons.append("SAFE HOLD: score inside neutral band")
        reason_codes.append("REFUSAL_NEUTRAL_BAND")
        summary = "Hold — edge too weak; refusing soft conviction"
        trust_posture = TrustPosture.REFUSAL

    safe_hold = trust_posture == TrustPosture.REFUSAL
    refusal_code_str = refusal_code.value if refusal_code else None
    refusal_reason = REFUSAL_MESSAGES.get(refusal_code) if refusal_code else None

    metrics_dict = metrics.to_dict()
    prov = build_provenance_hash(
        metrics=metrics_dict,
        signal=signal.value,
        safe_hold=safe_hold,
        refusal_code=refusal_code_str,
        trust_posture=trust_posture.value,
        reason_codes=reason_codes,
    )

    return SignalCardSchema(
        signal=signal.value,
        summary=summary,
        safe_hold=safe_hold,
        trust_posture=trust_posture,
        confidence=round(confidence, 3),
        reasons=reasons[:8],
        reason_codes=reason_codes[:8],
        metrics=metrics_dict,  # type: ignore[arg-type]
        provenance_hash=prov,
        agent_version=AGENT_VERSION,
        schema_version=CARD_SCHEMA_VERSION,
        timestamp_ms=metrics.timestamp_ms,
        refusal_code=refusal_code,
        refusal_reason=refusal_reason,
    )
