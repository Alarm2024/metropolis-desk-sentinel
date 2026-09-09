# SignalAnchor — Contract Stub (Not Deployed)

✝️🧿🪬

3️⃣🧿5️⃣

**Status:** Interface + documentation only. No deployment, no keys, no CI forge/hardhat requirement.

This folder holds a minimal **SignalAnchor** interface for future Monad hash-anchoring of desk sentinel `provenance_hash` values. The Python MVP already computes SHA-256 digests locally; on-chain anchoring is a post-hackathon extension documented in [docs/MONAD_DEPLOY.md](../docs/MONAD_DEPLOY.md).

---

## Interface

See [ISignalAnchor.sol](./ISignalAnchor.sol):

- `anchor(bytes32 hash, string agentVersion, string schemaVersion, uint64 timestampMs)` — store one provenance digest
- `getAnchor(bytes32 hash)` — read back anchor metadata for third-party verification

`provenance_hash` from signal cards is 64-char lowercase hex; convert to `bytes32` before calling `anchor`.

---

## Toolchain (optional, local only)

Pick one when implementing — **not required for `pytest` or `./scripts/demo.sh`**:

| Tool | Notes |
|------|-------|
| [Foundry](https://book.getfoundry.sh/) | `forge init` in a separate branch; add `ISignalAnchor` implementation |
| [Hardhat](https://hardhat.org/) | Same interface; deploy script reads env vars |

Do **not** add `forge build` or `npx hardhat compile` to default CI unless the toolchain is guaranteed in the runner image. Python tests must stay green without Solidity tooling.

---

## Honesty

- No `ANCHOR_PRIVATE_KEY` or RPC URLs in this repo
- No fake tx hashes in UI or docs until public testnet verification
- README and submission profile link here as **future work**, not live deployment
