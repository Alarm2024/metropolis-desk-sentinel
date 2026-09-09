"""Agent unit tests — typed schema and provenance."""

from agent.desk_agent import evaluate_desk
from agent.metrics import DeskMetrics, generate_mock_metrics
from agent.provenance import verify_card_provenance
from agent.schema import AGENT_VERSION, CARD_SCHEMA_VERSION


def test_mock_metrics_deterministic_per_minute():
    a = generate_mock_metrics("TEST")
    b = generate_mock_metrics("TEST")
    assert a.seed == b.seed
    assert a.order_flow_imbalance == b.order_flow_imbalance


def test_mock_metrics_explicit_seed():
    a = generate_mock_metrics("TEST", seed="demo-seed-001")
    b = generate_mock_metrics("TEST", seed="demo-seed-001")
    assert a.order_flow_imbalance == b.order_flow_imbalance
    assert a.seed == "demo-seed-001"


def test_signal_card_schema():
    m = generate_mock_metrics(seed="schema-test")
    card = evaluate_desk(m)
    d = card.to_dict()
    assert d["signal"] in ("CLEAR", "SHORT", "HOLD")
    assert d["trust_posture"] in ("DIRECTIONAL", "REFUSAL")
    assert 0.0 <= d["confidence"] <= 1.0
    assert len(d["provenance_hash"]) == 64
    assert d["agent_version"] == AGENT_VERSION
    assert d["schema_version"] == CARD_SCHEMA_VERSION
    assert verify_card_provenance(card)


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
    assert card.refusal_code.value == "EXEC_QUALITY"
    assert card.trust_posture.value == "REFUSAL"


def test_provenance_hash_stable():
    m = generate_mock_metrics("STABLE", seed="stable-demo")
    c1 = evaluate_desk(m)
    c2 = evaluate_desk(m)
    assert c1.provenance_hash == c2.provenance_hash


def test_directional_has_no_refusal_fields():
    from agent.fixtures import load_fixture

    card = evaluate_desk(load_fixture("clear_bullish"))
    d = card.to_dict()
    assert "refusal_code" not in d
    assert "refusal_reason" not in d
    assert d["trust_posture"] == "DIRECTIONAL"
