"""Provenance verification tests."""

from agent.desk_agent import evaluate_desk
from agent.fixtures import list_scenarios, load_fixture
from agent.metrics import DeskMetrics
from agent.provenance import build_provenance_hash, verify_card_provenance


def test_all_fixtures_verify() -> None:
    for name in list_scenarios():
        card = evaluate_desk(load_fixture(name))
        assert verify_card_provenance(card), name


def test_int_metric_fields_verify_after_coercion() -> None:
    """Integer metric values must hash identically to schema-coerced floats."""
    metrics = DeskMetrics(
        symbol="INT-METRICS",
        bid_ask_bps=5,
        volume_delta_pct=14,
        order_flow_imbalance=0.72,
        volatility_1h_pct=1,
        liquidity_score=0.85,
        spread_stability=0.9,
        timestamp_ms=1725900000000,
        seed="fixture-int-metrics",
    )
    card = evaluate_desk(metrics)
    card_dict = card.to_dict()

    assert verify_card_provenance(card)
    assert verify_card_provenance(card_dict)
    assert card_dict["metrics"]["bid_ask_bps"] == 5.0
    assert card_dict["metrics"]["volume_delta_pct"] == 14.0


def test_tampered_hash_fails() -> None:
    card = evaluate_desk(load_fixture("clear_bullish")).to_dict()
    card["provenance_hash"] = "f" * 64
    assert not verify_card_provenance(card)


def test_tampered_signal_fails() -> None:
    card = evaluate_desk(load_fixture("hold_thin_liquidity")).to_dict()
    card["signal"] = "CLEAR"
    assert not verify_card_provenance(card)


def test_hash_includes_reason_codes() -> None:
    card = evaluate_desk(load_fixture("hold_neutral_band"))
    d = card.to_dict()
    recomputed = build_provenance_hash(
        metrics=d["metrics"],
        signal=d["signal"],
        safe_hold=d["safe_hold"],
        refusal_code=d["refusal_code"],
        trust_posture=d["trust_posture"],
        reason_codes=d["reason_codes"],
        summary=d["summary"],
        reasons=d["reasons"],
        confidence=d["confidence"],
        refusal_reason=d.get("refusal_reason"),
    )
    assert recomputed == d["provenance_hash"]


def test_edited_summary_or_reasons_fail() -> None:
    """summary, reasons, confidence and refusal_reason are covered by the hash."""
    base = evaluate_desk(load_fixture("hold_thin_liquidity")).to_dict()
    for field, value in (
        ("summary", "Clear — bullish desk bias within trust bounds"),
        ("reasons", ["Composite score +0.90 above clear threshold"]),
        ("confidence", 0.99),
        ("refusal_reason", "edited"),
    ):
        card = dict(base)
        card[field] = value
        assert not verify_card_provenance(card), field


def test_forged_clear_keeping_old_hash_fails() -> None:
    """Flipping a HOLD card to CLEAR (public fields + summary) without the
    original inputs to re-hash must not verify against the original hash."""
    card = evaluate_desk(load_fixture("hold_thin_liquidity")).to_dict()
    card.update(
        signal="CLEAR",
        safe_hold=False,
        trust_posture="DIRECTIONAL",
        refusal_code=None,
        refusal_reason=None,
        summary="Clear — bullish desk bias within trust bounds",
    )
    assert not verify_card_provenance(card)
