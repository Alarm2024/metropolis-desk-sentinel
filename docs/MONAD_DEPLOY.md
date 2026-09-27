# Monad Deploy Notes (Stub)

✝️🧿🪬

3️⃣🧿5️⃣

**Status:** Not deployed. This document is a placeholder for future Trust / Identity work.  
**MVP scope:** local mock agent + SHA-256 provenance + hash-chained decision log — **no mainnet or testnet claims**.

---

## Intent

Morning Light Desk Sentinel produces reviewable signal cards with a `provenance_hash` and appends them to a hash-chained decision log. A future Monad deployment could anchor those hashes on-chain for an external, timestamped record and bind agent identity to a deployer address.

---

## Local agent identity (ERC-8004-inspired, already in cards)

[ERC-8004](https://eips.ethereum.org/EIPS/eip-8004) proposes on-chain **Identity**, **Reputation**, and **Validation** registries for agents. This MVP implements the *local, off-chain* identity and validation primitives that map cleanly to a future anchor:

| ERC-8004 concept | Local field(s) in `SignalCardSchema` v2.0 | Notes |
|------------------|-------------------------------------------|-------|
| Agent identity | `agent_version` (`1.0.0-metropolis`) | Semver pin; future: registry URI or contract address |
| Output contract | `schema_version` (`2.0`) | Versioned card shape — breaking changes bump schema |
| Validation / honesty posture | `trust_posture` (`REFUSAL` \| `DIRECTIONAL`) | REFUSAL = agent refused to fake conviction |
| Validation evidence | `refusal_code`, `refusal_reason`, `reason_codes` | Machine + human record of each refusal |
| Integrity digest | `provenance_hash` (SHA-256) | Replayable hash over identity + metrics + signal + posture + reasons/summary/confidence/refusal fields |
| Temporal anchor | `timestamp_ms` | Seeded demos: seed-derived ms for deterministic hashes; unseeded local runs: wall-clock ms. On-chain: block time |
| Decision history | `decision_log.jsonl` hash chain | `prev_hash` → `entry_hash` per append; flags an edited entry, but not a deleted tail or a full rewrite with recomputed hashes |

**Provenance payload** (what gets hashed today):

```json
{
  "agent_version": "1.0.0-metropolis",
  "schema_version": "2.0",
  "timestamp_ms": 1725900000000,
  "metrics": { "...": "mock snapshot" },
  "signal": "HOLD",
  "safe_hold": true,
  "trust_posture": "REFUSAL",
  "refusal_code": "EXEC_QUALITY",
  "reason_codes": ["THIN_LIQUIDITY", "REFUSAL_EXEC_QUALITY"],
  "summary": "Hold — conditions untrusted for directional action",
  "reasons": ["...", "SAFE HOLD: insufficient execution quality"],
  "confidence": 0.01,
  "refusal_reason": "Refused directional action: execution quality below trust threshold"
}
```

Judges can recompute any card's hash with `verify_card_provenance()` or `POST /api/verify`. A match only shows the hashed fields were not edited after hashing. It does **not** prove origin: there is no key, so anyone can build a card and compute a matching plain SHA-256 over all fields. Proving origin needs a signature or an external anchor (the future work below).

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
