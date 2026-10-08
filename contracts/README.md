# SignalAnchor — Contract Stub (Not Deployed)

✝️🧿🪬

3️⃣🧿5️⃣

**Status:** `ISignalAnchor.sol` is an interface + documentation only. No deployment and no keys.

The deployable demo contract in this folder is [`SentinelLog.sol`](./SentinelLog.sol), the Monad Testnet log described in the main README's "On Monad Testnet" section.

This folder holds a minimal **SignalAnchor** interface for future Monad hash-anchoring of desk sentinel `provenance_hash` values. The Python MVP already computes SHA-256 digests locally; on-chain anchoring is a post-hackathon extension documented in [docs/MONAD_DEPLOY.md](../docs/MONAD_DEPLOY.md).

---

## Interface

See [ISignalAnchor.sol](./ISignalAnchor.sol):

- `anchor(bytes32 hash, string agentVersion, string schemaVersion, uint64 timestampMs)` — store one provenance digest
- `getAnchor(bytes32 hash)` — read back anchor metadata for third-party hash checks

`provenance_hash` from signal cards is 64-char lowercase hex; convert to `bytes32` before calling `anchor`.

---

## Toolchain (optional, local only)

Pick one when implementing — **not required for `pytest` or `./scripts/demo.sh`**:

| Tool | Notes |
|------|-------|
| [Foundry](https://book.getfoundry.sh/) | `forge init` in a separate branch; add `ISignalAnchor` implementation |
| [Hardhat](https://hardhat.org/) | Same interface; deploy script reads env vars |

Foundry runs in its own CI job (`.github/workflows/foundry.yml`, installed via `foundry-rs/foundry-toolchain`). The Python job does not need Solidity tooling, and `pytest` / `./scripts/demo.sh` must stay green without it.

---

## Honesty

- No `ANCHOR_PRIVATE_KEY` or RPC URLs in this repo
- No fake tx hashes in UI or docs until public testnet verification
- README and submission profile link here as **future work**, not a deployment
