# Monad Deploy Notes (Stub)

✝️🧿🪬

3️⃣🧿5️⃣

**Status:** Not deployed. This document is a placeholder for future Trust / Identity work.  
**MVP scope:** local mock agent + SHA-256 provenance only — **no mainnet or testnet claims**.

---

## Intent

Morning Light Desk Sentinel produces auditable signal cards with a `provenance_hash`. A future Monad deployment could:

1. Anchor each hash on-chain for immutable audit trails
2. Bind agent version (`0.1.0-mvp`) to a deployer identity
3. Enable third-party verification without trusting the API operator

---

## Proposed flow (future)

```
Mock/Live Metrics → Agent → Signal Card
                              ↓
                    provenance_hash
                              ↓
              Monad contract: anchor(hash, agentVersion, timestamp)
                              ↓
                    UI shows tx reference + local hash
```

---

## Stub checklist (do not run in MVP)

- [ ] Choose Monad network (testnet when available — verify official RPC docs)
- [ ] Define minimal `SignalAnchor` contract:
  - `function anchor(bytes32 hash, string agentVersion, uint64 timestampMs)`
  - `function getAnchor(bytes32 hash) view returns (...)`
- [ ] Add deploy script (Foundry/Hardhat) — **no secrets in repo**
- [ ] Wire optional `MONAD_RPC_URL` + `ANCHOR_PRIVATE_KEY` via env (never commit)
- [ ] UI: show `anchored: false` until a real tx exists
- [ ] Integration test against Monad testnet only

---

## Environment variables (future)

| Variable | Purpose |
|----------|---------|
| `MONAD_RPC_URL` | RPC endpoint (from official Monad docs) |
| `ANCHOR_CONTRACT` | Deployed anchor contract address |
| `ANCHOR_PRIVATE_KEY` | Signer for anchor txs — **local/dev only** |

---

## Honesty policy

Until checklist items are complete and verified on a public testnet:

- README and UI must **not** claim Monad deployment
- Provenance remains **local SHA-256** only
- No fake transaction hashes or explorer links

---

## References

- [Monad documentation](https://docs.monad.xyz/) — verify current deploy guides before implementation
- Project architecture: [../ARCHITECTURE.md](../ARCHITECTURE.md)
