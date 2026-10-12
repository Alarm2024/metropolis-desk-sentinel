#!/usr/bin/env bash
# Deploy SentinelLog to Monad Testnet (chainId 10143). Maintainer only.
#
#   read -rsp 'Testnet key: ' MONAD_TESTNET_KEY && export MONAD_TESTNET_KEY && ./scripts/deploy_testnet.sh
#
# Full runbook: docs/MONAD_DEPLOY.md. RPC_URL overrides the RPC (default: the
# public Monad Testnet RPC); the chain must still answer 10143.
#
# The key comes from the environment variable MONAD_TESTNET_KEY only. It is never
# passed on the command line (so it stays out of shell history and `ps`), never
# written to a file, and never committed. Use a fresh throwaway key funded with
# free testnet MON; never a wallet that holds anything of value.
set -euo pipefail
cd "$(dirname "$0")/.."

: "${MONAD_TESTNET_KEY:?set MONAD_TESTNET_KEY (read -rsp 'Testnet key: ' MONAD_TESTNET_KEY && export MONAD_TESTNET_KEY)}"
command -v forge >/dev/null || { echo "Foundry is not installed: https://book.getfoundry.sh/getting-started/installation" >&2; exit 69; }
[[ -f lib/forge-std/src/Script.sol ]] || git submodule update --init

RPC="${RPC_URL:-https://testnet-rpc.monad.xyz}"
chain=$(cast chain-id --rpc-url "$RPC")
if [[ "$chain" != "10143" ]]; then
  echo "refusing: the RPC answered chainId $chain, not Monad Testnet (10143)" >&2
  exit 1
fi

forge script script/Deploy.s.sol --rpc-url "$RPC" --broadcast
echo
echo "Deployed. Next: ./scripts/record_card.sh hold_thin_liquidity, then commit deployments/ and docs/deployments/."
