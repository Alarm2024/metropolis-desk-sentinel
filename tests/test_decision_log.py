"""Decision log — hash chain integrity and provenance gate."""

from __future__ import annotations

import json
import threading
from pathlib import Path

import pytest

from agent.decision_log import append_decision, read_decisions, summarize_decisions, verify_log_integrity
from agent.desk_agent import evaluate_desk
from agent.fixtures import load_fixture


def test_append_and_read(tmp_path: Path) -> None:
    log_path = tmp_path / "decisions.jsonl"
    card = evaluate_desk(load_fixture("clear_bullish")).to_dict()
    append_decision(card, log_path=log_path)
    append_decision(evaluate_desk(load_fixture("hold_thin_liquidity")).to_dict(), log_path=log_path)

    entries = read_decisions(log_path=log_path)
    assert len(entries) == 2
    assert entries[0].entry_id == 1
    assert entries[1].entry_id == 2
    assert entries[1].prev_hash == entries[0].entry_hash


def test_hash_chain_integrity(tmp_path: Path) -> None:
    log_path = tmp_path / "decisions.jsonl"
    for name in ("clear_bullish", "short_bearish", "hold_thin_liquidity"):
        append_decision(evaluate_desk(load_fixture(name)).to_dict(), log_path=log_path)

    ok, msg = verify_log_integrity(log_path=log_path)
    assert ok, msg


def test_tamper_detection(tmp_path: Path) -> None:
    log_path = tmp_path / "decisions.jsonl"
    append_decision(evaluate_desk(load_fixture("clear_bullish")).to_dict(), log_path=log_path)

    lines = log_path.read_text().strip().split("\n")
    tampered = json.loads(lines[0])
    tampered["card"]["signal"] = "SHORT"  # tampered without updating entry_hash or provenance
    tampered["card"]["trust_posture"] = "DIRECTIONAL"
    lines[0] = json.dumps(tampered, sort_keys=True, separators=(",", ":"))
    log_path.write_text("\n".join(lines) + "\n")

    ok, msg = verify_log_integrity(log_path=log_path)
    assert not ok


def test_malformed_line_reports_broken_chain_not_raise(tmp_path: Path) -> None:
    """A corrupt line must be reported as a broken chain, never raised (F5)."""
    log_path = tmp_path / "decisions.jsonl"
    append_decision(evaluate_desk(load_fixture("clear_bullish")).to_dict(), log_path=log_path)
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write("{not json\n")

    ok, msg = verify_log_integrity(log_path=log_path)
    assert not ok
    assert "line 2" in msg

    # read_decisions must not raise either — it should just skip the bad line.
    entries = read_decisions(log_path=log_path)
    assert len(entries) == 1


def test_refuses_invalid_provenance(tmp_path: Path) -> None:
    log_path = tmp_path / "decisions.jsonl"
    bad = evaluate_desk(load_fixture("clear_bullish")).to_dict()
    bad["provenance_hash"] = "0" * 64
    with pytest.raises(ValueError, match="invalid provenance"):
        append_decision(bad, log_path=log_path)


def test_summarize_decisions(tmp_path: Path) -> None:
    log_path = tmp_path / "decisions.jsonl"
    for name in ("clear_bullish", "short_bearish", "hold_thin_liquidity"):
        append_decision(evaluate_desk(load_fixture(name)).to_dict(), log_path=log_path)

    summary = summarize_decisions(log_path=log_path)
    assert summary["total_evaluations"] == 3
    assert summary["log_integrity"]["ok"] is True
    assert "EXEC_QUALITY" in summary["refusal_codes"]


def test_concurrent_appends_no_race(tmp_path: Path) -> None:
    """Reproduces F1: without a lock, concurrent append_decision calls race
    on read-last-then-append and produce duplicate entry_ids / a broken
    chain. With the lock in place, all entries must be unique, sequential,
    and the chain must verify."""
    log_path = tmp_path / "decisions.jsonl"
    card = evaluate_desk(load_fixture("clear_bullish")).to_dict()

    n_threads = 40
    errors: list[BaseException] = []

    def _append() -> None:
        try:
            append_decision(card, log_path=log_path)
        except BaseException as exc:  # noqa: BLE001 - surface any failure from the thread
            errors.append(exc)

    threads = [threading.Thread(target=_append) for _ in range(n_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, errors

    entries = read_decisions(limit=0, log_path=log_path)
    assert len(entries) == n_threads

    ids = sorted(e.entry_id for e in entries)
    assert ids == list(range(1, n_threads + 1))

    ok, msg = verify_log_integrity(log_path=log_path)
    assert ok, msg


def test_non_object_line_reports_broken_not_raise(tmp_path: Path) -> None:
    log_path = tmp_path / "decisions.jsonl"
    append_decision(evaluate_desk(load_fixture("clear_bullish")).to_dict(), log_path=log_path)
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write("[1, 2, 3]\n")
    ok, msg = verify_log_integrity(log_path=log_path)
    assert not ok
    assert "line 2" in msg
    assert len(read_decisions(log_path=log_path)) == 1
    with pytest.raises(ValueError, match="malformed"):
        append_decision(evaluate_desk(load_fixture("clear_bullish")).to_dict(), log_path=log_path)
