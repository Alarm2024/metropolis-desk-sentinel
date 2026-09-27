#!/usr/bin/env python3
"""Recompute provenance_hash in every tests/fixtures/*.golden.json.

Use this after an intentional change to the provenance hash formula
(agent/provenance.py) or to the card fields that feed it
(agent/desk_agent.py), so the stored golden hashes match the new formula.

How to run, from the repo root with dependencies installed:

    python3 -m venv .venv && . .venv/bin/activate
    pip install -r requirements.txt
    python3 tools/regen_golden_hashes.py

For each scenario it prints "<name>: <hash> (changed|unchanged)". Only
provenance_hash is overwritten; every other field in each *.golden.json is
left as-is. If nothing in the formula changed, every line should say
"unchanged" and `git diff tests/fixtures` should be empty. Review any diff
before committing, then run `pytest` (tests/test_scenarios.py compares the
stored hashes against freshly computed cards).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Allow `python3 tools/regen_golden_hashes.py` from the repo root without
# setting PYTHONPATH (the script's own directory is tools/, not the root).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent.desk_agent import evaluate_desk
from agent.fixtures import FIXTURES_DIR, list_scenarios, load_fixture


def main() -> None:
    for name in list_scenarios():
        golden_path = FIXTURES_DIR / f"{name}.golden.json"
        if not golden_path.exists():
            print(f"skip {name}: no golden file")
            continue

        golden = json.loads(golden_path.read_text(encoding="utf-8"))
        card = evaluate_desk(load_fixture(name)).to_dict()

        old_hash = golden.get("provenance_hash")
        new_hash = card["provenance_hash"]
        golden["provenance_hash"] = new_hash

        golden_path.write_text(json.dumps(golden, indent=2) + "\n", encoding="utf-8")
        changed = " (changed)" if old_hash != new_hash else " (unchanged)"
        print(f"{name}: {new_hash}{changed}")


if __name__ == "__main__":
    main()
