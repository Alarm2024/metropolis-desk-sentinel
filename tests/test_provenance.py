"""Provenance verification tests."""

from agent.desk_agent import evaluate_desk
from agent.fixtures import list_scenarios, load_fixture
from agent.provenance import build_provenance_hash, verify_card_provenance


def test_all_fixtures_verify() -> None:
    for name in list_scenarios():
        card = evaluate_desk(load_fixture(name))
        assert verify_card_provenance(card), name


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
    )
    assert recomputed == d["provenance_hash"]
