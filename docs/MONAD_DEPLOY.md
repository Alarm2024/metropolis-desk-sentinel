# Monad Deploy Notes (Stub)

✝️🧿🪬

3️⃣🧿5️⃣

**Status:** Not deployed. This document is a placeholder for future Trust / Identity work.  
**MVP scope:** local mock agent + SHA-256 provenance + hash-chained decision log — **no mainnet or testnet claims**.

---

## Intent

Morning Light Desk Sentinel produces auditable signal cards with a `provenance_hash` and appends them to a hash-chained decision log. A future Monad deployment could anchor those hashes on-chain for immutable audit trails and bind agent identity to a deployer address.

---

## Local agent identity (ERC-8004-inspired, already in cards)

[ERC-8004](https://eips.ethereum.org/EIPS/eip-8004) proposes on-chain **Identity**, **Reputation**, and **Validation** registries for agents. This MVP implements the *local, off-chain* identity and validation primitives that map cleanly to a future anchor:

| ERC-8004 concept | Local field(s) in `SignalCardSchema` v2.0 | Notes |
|------------------|-------------------------------------------|-------|
| Agent identity | `agent_version` (`1.0.0-metropolis`) | Semver pin; future: registry URI or contract address |
| Output contract | `schema_version` (`2.0`) | Versioned card shape — breaking changes bump schema |
| Validation / honesty posture | `trust_posture` (`REFUSAL` \| `DIRECTIONAL`) | REFUSAL = agent refused to fake conviction |
| Validation evidence | `refusal_code`, `refusal_reason`, `reason_codes` | Machine + human audit trail for refusals |
| Integrity digest | `provenance_hash` (SHA-256) | Replayable hash over identity + metrics + signal + posture |
| Temporal anchor | `timestamp_ms` | Wall-clock ms at emission (local); on-chain: block time |
| Decision history | `decision_log.jsonl` hash chain | `prev_hash` → `entry_hash` per append; tamper-evident |

**Provenance payload** (what gets hashed today):

```json
{
  "agent_version": "1.0.0-metropolis",
  "schema_version": "2.0",
  "metrics": { "...": "mock snapshot" },
  "signal": "HOLD",
  "safe_hold": true,
  "trust_posture": "REFUSAL",
  "refusal_code": "EXEC_QUALITY",
  "reason_codes": ["THIN_LIQUIDITY", "REFUSAL_EXEC_QUALITY"]
}
```

Judges can verify any card with `verify_card_provenance()` or `POST /api/verify` without trusting the API operator.

---

## Proposed on-chain flow (future)

```
Mock/Live Metrics → Desk Agent → SignalCardSchema
                                      ↓
                            provenance_hash (bytes32)
                                      ↓
              SignalAnchor.anchor(hash, agentVersion, schemaVersion, timestampMs)
                                      ↓
                    UI shows tx reference + local hash match
```

See `contracts/` for a minimal `ISignalAnchor` interface stub (no deploy in MVP).

---

## Monad hash-anchor checklist (do not run in MVP)

Complete every item before claiming testnet or mainnet deployment:

### Phase 0 — Prerequisites

- [ ] Read [Monad documentation](https://docs.monad.xyz/) for current testnet RPC, faucet, and deploy tooling
- [ ] Confirm `SignalAnchor` interface matches local `provenance_hash` format (64-char hex → `bytes32`)
- [ ] Document honest UI copy: `anchored: false` until a verified tx exists

### Phase 1 — Contract (stub in repo)

- [ ] Review `contracts/ISignalAnchor.sol` — minimal anchor + lookup
- [ ] Choose toolchain (Foundry or Hardhat) locally — **not required in CI**
- [ ] Write deploy script — **no secrets in repo**
- [ ] Unit test anchor/lookup on local Anvil/Hardhat node (developer machine only)

### Phase 2 — Environment (never commit)

- [ ] `MONAD_RPC_URL` — official RPC from Monad docs
- [ ] `ANCHOR_CONTRACT` — deployed `SignalAnchor` address after verified deploy
- [ ] `ANCHOR_PRIVATE_KEY` — signer for anchor txs; **local/dev only**, env or secret manager

### Phase 3 — Integration

- [ ] Optional Python adapter: after `append_decision()`, call anchor if env vars present
- [ ] Store `{ tx_hash, block_number, contract }` alongside log entry (new field — schema bump)
- [ ] UI: show explorer link only when tx is confirmed on public testnet
- [ ] Integration test against Monad testnet only (skipped in default CI)

### Phase 4 — Identity attestation (post-anchor)

- [ ] Map `agent_version` to on-chain agent registry entry (ERC-8004 Identity registry when available on Monad)
- [ ] Pin deployer address ↔ agent_version in README and `/api/health`
- [ ] Third-party verify: recompute hash locally, compare to on-chain `getAnchor(hash)`

---

## Environment variables (future)

| Variable | Purpose | Committed? |
|----------|---------|------------|
| `MONAD_RPC_URL` | RPC endpoint (official Monad docs) | No |
| `ANCHOR_CONTRACT` | Deployed anchor contract address | No (document shape only) |
| `ANCHOR_PRIVATE_KEY` | Signer for anchor txs | **Never** |
| `DECISION_LOG_PATH` | Local JSONL log path (default `data/decision_log.jsonl`) | No |

---

## Honesty policy

Until every Phase 1–3 checklist item is complete and verified on a **public** testnet:

- README, UI, and `docs/SUBMIT.md` must **not** claim Monad deployment
- Provenance remains **local SHA-256** only
- No fake transaction hashes or explorer links
- `contracts/` is documentation + interface stub — not evidence of live deployment

---

## References

- [Monad documentation](https://docs.monad.xyz/)
- [EIP-8004: Trustless Agents](https://eips.ethereum.org/EIPS/eip-8004) — identity/reputation/validation registry inspiration
- Project architecture: [../ARCHITECTURE.md](../ARCHITECTURE.md)
- Submission profile: [SUBMIT.md](./SUBMIT.md)
- Contract stub: [../contracts/README.md](../contracts/README.md)
