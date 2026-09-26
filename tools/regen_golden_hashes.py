#!/usr/bin/env python3
"""Recompute provenance_hash in every tests/fixtures/*.golden.json.

Run this once after pulling in the provenance.py / desk_agent.py changes
that add summary, reasons, confidence, and refusal_reason to the hash.
I could only run this myself against tests/fixtures/hold_thin_liquidity
(the one fixture included in the uploaded review pack) since I don't have
a Python environment with fastapi/pydantic installed here, and I don't
have the other four fixtures' content at all. Run it from the repo root,
with dependencies installed:

    python3 tools/regen_golden_hashes.py

It leaves every other field in each *.golden.json untouched and only
overwrites provenance_hash. Diff the result before committing, in case any
of your golden files intentionally pin other fields.
"""

from __future__ import annotations

import json
from pathlib import Path

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
