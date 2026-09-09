"""Trust invariant tests — never fake CLEAR, every HOLD refuses honestly."""

from __future__ import annotations

import hashlib

import pytest

from agent.desk_agent import MIN_EXEC_QUALITY, evaluate_desk
from agent.metrics import DeskMetrics, generate_mock_metrics
from agent.provenance import verify_card_provenance


DETERMINISTIC_SEEDS = [
    "metropolis-judge-001",
    "metropolis-judge-002",
    "demo-honesty-a",
    "demo-honesty-b",
    "wyndham-seed-fixed",
    "trust-layer-alpha",
    "trust-layer-beta",
    "refusal-path-1",
    "refusal-path-2",
    "clear-path-1",
]


@pytest.mark.parametrize("seed", DETERMINISTIC_SEEDS)
def test_deterministic_seed_replay(seed: str) -> None:
    m1 = generate_mock_metrics(seed=seed)
    m2 = generate_mock_metrics(seed=seed)
    c1 = evaluate_desk(m1)
    c2 = evaluate_desk(m2)
    assert c1.to_dict() == c2.to_dict()
    assert verify_card_provenance(c1)


@pytest.mark.parametrize("seed", DETERMINISTIC_SEEDS)
def test_never_clear_without_exec_quality(seed: str) -> None:
    metrics = generate_mock_metrics(seed=seed)
    card = evaluate_desk(metrics)
    exec_quality = metrics.liquidity_score * metrics.spread_stability
    if exec_quality < MIN_EXEC_QUALITY:
        assert card.signal == "HOLD"
        assert card.safe_hold is True
    if card.signal == "CLEAR":
        assert exec_quality >= MIN_EXEC_QUALITY
        assert card.trust_posture.value == "DIRECTIONAL"


@pytest.mark.parametrize("seed", DETERMINISTIC_SEEDS)
def test_hold_always_has_refusal(seed: str) -> None:
    card = evaluate_desk(generate_mock_metrics(seed=seed))
    if card.signal == "HOLD":
        assert card.safe_hold is True
        assert card.trust_posture.value == "REFUSAL"
        assert card.refusal_code is not None
        assert card.refusal_reason is not None
        assert len(card.reasons) >= 1
        assert len(card.reason_codes) >= 1


def test_sweep_random_seeds_never_fake_clear() -> None:
    """100 synthetic metric combos — CLEAR only when exec quality passes."""
    for i in range(100):
        seed = hashlib.sha256(f"sweep-{i}".encode()).hexdigest()[:12]
        metrics = generate_mock_metrics(seed=seed)
        card = evaluate_desk(metrics)
        exec_quality = metrics.liquidity_score * metrics.spread_stability
        assert verify_card_provenance(card)
        if card.signal in ("CLEAR", "SHORT"):
            assert exec_quality >= MIN_EXEC_QUALITY
            assert card.safe_hold is False
        if card.signal == "HOLD":
            assert card.refusal_code is not None
