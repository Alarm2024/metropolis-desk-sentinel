# Monad Deploy Notes (Stub)

Morning Light Desk Sentinel — **planning document only**

> **Important:** This MVP has **not** been deployed to Monad mainnet or testnet. Nothing in this repo claims live on-chain status. These notes describe a future integration path for the Metropolis submission.

---

## Goal

Anchor each card's `provenanceHash` on Monad so third parties can verify off-chain JSON against an on-chain record.

---

## Prerequisites (when ready)

- [ ] Monad wallet with testnet MON (from official faucet — verify current URL in Monad docs)
- [ ] RPC endpoint (testnet) stored in environment variable, e.g. `MONAD_RPC_URL`
- [ ] Deployer private key in `MONAD_DEPLOYER_KEY` — **never commit**

---

## Proposed flow (not implemented)

1. Agent generates card → `data/last-card.json`
2. Extract `provenanceHash` from card
3. Call anchor contract or simple `emit Anchor(bytes32 hash, uint256 timestamp)` 
4. Store tx hash in card metadata or separate index

---

## Stub contract sketch (Solidity — reference only)

```solidity
// SPDX-License-Identifier: MIT
// NOT DEPLOYED — illustrative only
pragma solidity ^0.8.20;

contract DeskSentinelAnchor {
    event CardAnchored(bytes32 indexed provenanceHash, uint256 timestamp);

    function anchor(bytes32 provenanceHash) external {
        emit CardAnchored(provenanceHash, block.timestamp);
    }
}
```

---

## Environment variables (future)

| Variable | Description |
|----------|-------------|
| `MONAD_RPC_URL` | JSON-RPC endpoint |
| `MONAD_DEPLOYER_KEY` | Signing key (local/env only) |
| `MONAD_ANCHOR_CONTRACT` | Deployed anchor address |

---

## Verification (future)

1. Fetch card JSON from status API
2. Recompute SHA-256 over canonical body
3. Query chain for `CardAnchored` event matching hash
4. Compare timestamps

---

## Status

| Item | State |
|------|-------|
| Local agent + status page | **Done (MVP)** |
| Provenance hash in cards | **Done (MVP)** |
| Monad testnet deploy | **Not started** |
| Monad mainnet deploy | **Not planned for MVP** |

---

## References

- [Monad developer documentation](https://docs.monad.xyz/) — verify latest network names and faucet links before deploying
- Metropolis hackathon submission: **October 13, 2026**

---

*This stub will be updated when testnet deployment begins. Until then, treat all chain references as design notes only.*
