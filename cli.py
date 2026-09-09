#!/usr/bin/env python3
"""CLI — emit CLEAR / SHORT / HOLD JSON from mock desk metrics."""

from __future__ import annotations

import json
import sys

from agent.desk_agent import evaluate_desk
from agent.metrics import generate_mock_metrics


def main() -> int:
    metrics = generate_mock_metrics()
    card = evaluate_desk(metrics)
    json.dump(card.to_dict(), sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
