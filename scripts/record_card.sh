#!/usr/bin/env bash
# Record one desk card on the SentinelLog contract (Monad Testnet by default).
#
#   export MONAD_TESTNET_KEY=0x...            # throwaway testnet key that deployed SentinelLog
#   ./scripts/record_card.sh hold_thin_liquidity
#   ./scripts/record_card.sh --seed metropolis-judge-001
#
# Runs the local agent (no decision-log write), takes the card's provenance_hash,
# maps safe_hold -> verdict (0 = SAFE_HOLD, 1 = OK), builds a short reason, then
# calls script/Record.s.sol. Env overrides: RPC_URL (default monad_testnet) and
# SENTINEL_LOG (default: address in deployments/monad-testnet.json).
set -euo pipefail
cd "$(dirname "$0")/.."

if [[ $# -eq 0 ]]; then
  echo "usage: $0 <scenario> | --seed <seed>" >&2
  exit 64
fi
: "${MONAD_TESTNET_KEY:?set MONAD_TESTNET_KEY to your throwaway testnet key (never commit it)}"

PY=python3
[[ -x .venv/bin/python ]] && PY=.venv/bin/python

if [[ "$1" == "--seed" ]]; then
  CARD_JSON=$("$PY" cli.py --no-log --seed "${2:?missing seed}")
else
  CARD_JSON=$("$PY" cli.py --no-log --scenario "$1")
fi

eval "$(CARD_JSON="$CARD_JSON" "$PY" - <<'PY'
import json, os, shlex
card = json.loads(os.environ["CARD_JSON"])
verdict = 0 if card["safe_hold"] else 1
if card["safe_hold"]:
    reason = f'{card["refusal_code"]}: {card["refusal_reason"]}'
else:
    reason = f'{card["signal"]}: {card["summary"]}'
reason = reason.encode()[:280].decode(errors="ignore")
print(f'CARD_HASH=0x{card["provenance_hash"]}')
print(f"VERDICT={verdict}")
print(f"REASON={shlex.quote(reason)}")
PY
)"

if [[ -z "${SENTINEL_LOG:-}" ]]; then
  SENTINEL_LOG=$("$PY" -c 'import json; print(json.load(open("deployments/monad-testnet.json"))["address"] or "")')
fi
: "${SENTINEL_LOG:?no address: deploy first (script/Deploy.s.sol) or set SENTINEL_LOG}"

echo "Recording $CARD_HASH (verdict $VERDICT) on $SENTINEL_LOG" >&2
SENTINEL_LOG="$SENTINEL_LOG" CARD_HASH="$CARD_HASH" VERDICT="$VERDICT" REASON="$REASON" \
  forge script script/Record.s.sol --rpc-url "${RPC_URL:-monad_testnet}" --broadcast
