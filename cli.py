#!/usr/bin/env python3
"""CLI — emit typed CLEAR / SHORT / HOLD JSON from mock desk metrics."""

from __future__ import annotations

import argparse
import json
import sys

from agent.decision_log import append_decision
from agent.desk_agent import evaluate_desk
from agent.fixtures import list_scenarios, load_fixture
from agent.metrics import generate_mock_metrics
from agent.provenance import verify_card_provenance


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Morning Light Desk Sentinel — SAFE HOLD honesty CLI",
    )
    parser.add_argument("--seed", help="Deterministic demo seed (repeatable output)")
    parser.add_argument("--symbol", default="MLDS-MOCK", help="Mock symbol label")
    parser.add_argument("--scenario", choices=list_scenarios(), help="Run named golden scenario")
    parser.add_argument("--no-log", action="store_true", help="Skip appending to decision log")
    parser.add_argument("--verify", action="store_true", help="Print provenance verification result")
    args = parser.parse_args()

    if args.scenario:
        metrics = load_fixture(args.scenario)
    else:
        metrics = generate_mock_metrics(symbol=args.symbol, seed=args.seed)

    card = evaluate_desk(metrics)
    card_dict = card.to_dict()

    if args.verify:
        valid = verify_card_provenance(card_dict)
        print(f"provenance_valid={valid}", file=sys.stderr)

    if not args.no_log:
        append_decision(card_dict)

    json.dump(card_dict, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
