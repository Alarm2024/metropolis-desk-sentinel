#!/usr/bin/env python3
"""CLI — emit CLEAR / SHORT / HOLD JSON from mock desk metrics."""

from __future__ import annotations

import argparse
import json
import sys

from agent.decision_log import append_decision
from agent.desk_agent import evaluate_desk
from agent.metrics import generate_mock_metrics


def main() -> int:
    parser = argparse.ArgumentParser(description="Morning Light Desk Sentinel CLI")
    parser.add_argument("--seed", help="Deterministic demo seed (repeatable output)")
    parser.add_argument("--symbol", default="MLDS-MOCK", help="Mock symbol label")
    parser.add_argument("--no-log", action="store_true", help="Skip appending to decision log")
    args = parser.parse_args()

    metrics = generate_mock_metrics(symbol=args.symbol, seed=args.seed)
    card = evaluate_desk(metrics)
    card_dict = card.to_dict()
    if not args.no_log:
        append_decision(card_dict)
    json.dump(card_dict, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
