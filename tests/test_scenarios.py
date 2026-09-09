"""Golden scenario tests — prove CLEAR / SHORT / HOLD and SAFE HOLD honesty."""

from __future__ import annotations

import pytest

from agent.desk_agent import evaluate_desk
from agent.fixtures import list_scenarios, load_fixture, load_golden


@pytest.mark.parametrize("name", list_scenarios())
def test_scenario_golden(name: str) -> None:
    metrics = load_fixture(name)
    card = evaluate_desk(metrics)
    golden = load_golden(name)
    result = card.to_dict()

    for key in (
        "signal",
        "safe_hold",
        "refusal_code",
        "refusal_reason",
        "confidence",
        "provenance_hash",
        "schema_version",
        "agent_version",
    ):
        assert result.get(key) == golden.get(key), f"{name}.{key}: {result.get(key)!r} != {golden.get(key)!r}"


def test_clear_never_safe_hold() -> None:
    card = evaluate_desk(load_fixture("clear_bullish"))
    assert card.signal == "CLEAR"
    assert card.safe_hold is False
    assert card.refusal_code is None


def test_short_never_safe_hold() -> None:
    card = evaluate_desk(load_fixture("short_bearish"))
    assert card.signal == "SHORT"
    assert card.safe_hold is False
    assert card.refusal_code is None


def test_safe_hold_always_has_refusal() -> None:
    for name in ("hold_thin_liquidity", "hold_neutral_edge", "hold_neutral_band"):
        card = evaluate_desk(load_fixture(name))
        assert card.signal == "HOLD"
        assert card.safe_hold is True
        assert card.refusal_code in ("EXEC_QUALITY", "NO_EDGE", "NEUTRAL_BAND")
        assert card.refusal_reason is not None
        assert "Refused directional action" in card.refusal_reason


def test_no_fake_conviction_on_thin_liquidity() -> None:
    """Strong bullish flow must not emit CLEAR when execution quality is poor."""
    from agent.metrics import DeskMetrics

    m = DeskMetrics(
        symbol="TRAP",
        bid_ask_bps=20.0,
        volume_delta_pct=18.0,
        order_flow_imbalance=0.9,
        volatility_1h_pct=1.0,
        liquidity_score=0.05,
        spread_stability=0.1,
        timestamp_ms=1,
        seed="trap",
    )
    card = evaluate_desk(m)
    assert card.signal == "HOLD"
    assert card.safe_hold is True
    assert card.refusal_code == "EXEC_QUALITY"
