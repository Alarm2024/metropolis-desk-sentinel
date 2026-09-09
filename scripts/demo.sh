#!/usr/bin/env bash
# One-shot deterministic CLI demo for Metropolis judges.
# Fixed seed → identical card + provenance_hash every run. Exit 0 on success.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

DEMO_SEED="${DEMO_SEED:-metropolis-demo-2026}"

if ! python3 -c "import pydantic" 2>/dev/null; then
  echo "Installing dependencies..."
  python3 -m pip install -q -r requirements.txt
fi

echo "=== Morning Light Desk Sentinel — deterministic demo ==="
echo "seed=${DEMO_SEED}"
echo

# Evaluate with fixed seed; verify provenance; skip persistent log for clean reruns
OUTPUT="$(python3 cli.py --seed "$DEMO_SEED" --verify --no-log 2>&1)"
VERIFY_LINE="$(echo "$OUTPUT" | grep '^provenance_valid=' || true)"
JSON_BODY="$(echo "$OUTPUT" | sed '/^provenance_valid=/d')"

if [[ "$VERIFY_LINE" != "provenance_valid=True" ]]; then
  echo "FAIL: provenance verification failed" >&2
  echo "$OUTPUT" >&2
  exit 1
fi

SIGNAL="$(echo "$JSON_BODY" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['signal'])")"
TRUST="$(echo "$JSON_BODY" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['trust_posture'])")"
REFUSAL="$(echo "$JSON_BODY" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('refusal_code') or '—')")"
HASH="$(echo "$JSON_BODY" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['provenance_hash'])")"
AGENT="$(echo "$JSON_BODY" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['agent_version'])")"

echo "signal=${SIGNAL}  trust_posture=${TRUST}  refusal_code=${REFUSAL}"
echo "agent_version=${AGENT}"
echo "provenance_hash=${HASH}"
echo
echo "provenance_valid=True"
echo "=== demo OK (exit 0) ==="

exit 0
