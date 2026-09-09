"""Decision log append-only audit trail tests."""

from __future__ import annotations

from pathlib import Path

from agent.decision_log import append_decision, read_decisions, summarize_decisions
from agent.desk_agent import evaluate_desk
from agent.fixtures import load_fixture


def test_append_and_read(tmp_path: Path) -> None:
    log_path = tmp_path / "decisions.jsonl"
    card = evaluate_desk(load_fixture("clear_bullish")).to_dict()

    append_decision(card, log_path=log_path)
    append_decision(evaluate_desk(load_fixture("hold_thin_liquidity")).to_dict(), log_path=log_path)

    entries = read_decisions(log_path=log_path)
    assert len(entries) == 2
    assert entries[0].card["signal"] == "CLEAR"
    assert entries[1].card["safe_hold"] is True


def test_summarize_decisions(tmp_path: Path) -> None:
    log_path = tmp_path / "decisions.jsonl"
    for name in ("clear_bullish", "short_bearish", "hold_thin_liquidity"):
        append_decision(evaluate_desk(load_fixture(name)).to_dict(), log_path=log_path)

    summary = summarize_decisions(log_path=log_path)
    assert summary["total_evaluations"] == 3
    assert summary["by_signal"]["CLEAR"] == 1
    assert summary["by_signal"]["SHORT"] == 1
    assert summary["by_signal"]["HOLD"] == 1
    assert summary["safe_hold_count"] == 1
    assert "EXEC_QUALITY" in summary["refusal_codes"]
