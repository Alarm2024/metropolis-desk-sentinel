"""Agent unit tests — mock metrics + SAFE HOLD paths."""

from agent.desk_agent import evaluate_desk, AGENT_VERSION
from agent.metrics import DeskMetrics, generate_mock_metrics


def test_mock_metrics_deterministic_per_minute():
    a = generate_mock_metrics("TEST")
    b = generate_mock_metrics("TEST")
    assert a.seed == b.seed
    assert a.order_flow_imbalance == b.order_flow_imbalance


def test_signal_card_schema():
    m = generate_mock_metrics()
    card = evaluate_desk(m)
    d = card.to_dict()
    assert d["signal"] in ("CLEAR", "SHORT", "HOLD")
    assert isinstance(d["safe_hold"], bool)
    assert 0.0 <= d["confidence"] <= 1.0
    assert len(d["provenance_hash"]) == 64
    assert d["agent_version"] == AGENT_VERSION


def test_safe_hold_on_thin_liquidity():
    m = DeskMetrics(
        symbol="TEST",
        bid_ask_bps=15.0,
        volume_delta_pct=2.0,
        order_flow_imbalance=0.05,
        volatility_1h_pct=1.0,
        liquidity_score=0.1,
        spread_stability=0.2,
        timestamp_ms=1,
        seed="test",
    )
    card = evaluate_desk(m)
    assert card.signal == "HOLD"
    assert card.safe_hold is True


def test_provenance_hash_stable():
    m = generate_mock_metrics("STABLE")
    c1 = evaluate_desk(m)
    c2 = evaluate_desk(m)
    assert c1.provenance_hash == c2.provenance_hash
