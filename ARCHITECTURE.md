# Architecture — Morning Light Desk Sentinel

Metropolis Trust / Identity & AI Infrastructure MVP

---

## Overview

Morning Light Desk Sentinel is a two-process local stack:

```
┌─────────────────┐     writes      ┌──────────────────┐
│  agent/sentinel │ ──────────────► │ data/last-card   │
│  (mock metrics) │                 │     .json        │
└─────────────────┘                 └────────┬─────────┘
                                             │ reads
                                             ▼
                                    ┌──────────────────┐
                                    │  status/server   │
                                    │  + static UI     │
                                    └──────────────────┘
                                             │
                                             ▼
                                    Browser / API client
```

The agent produces **cards** — self-describing JSON documents. The status server is read-only over generated artifacts.

---

## Card schema (v1.0.0)

| Field | Purpose |
|-------|---------|
| `cardId` | UUID — unique card instance |
| `version` | Schema version |
| `generatedAt` | ISO-8601 timestamp |
| `branding.owner` / `branding.bot` | Separate lines — never combined |
| `desk` | Mock desk metrics (symbol, position, PnL, volatility, etc.) |
| `signal.action` | One of: `SAFE HOLD`, `CLEAR`, `SHORT`, `HOLD` |
| `signal.rationale` | Human-readable reason for the action |
| `signal.confidence` | 0–1 score (rule-derived, not ML) |
| `signal.honesty` | Disclaimer, data source, limitations |
| `trust` | Identity/trust layer stub for Metropolis track |
| `provenanceHash` | SHA-256 of sorted JSON body (excluding hash field) |

### Provenance

The hash is computed over the card body **before** the hash field is appended:

```js
canonical = JSON.stringify(body, sortedKeys)
provenanceHash = sha256(canonical)
```

This enables future on-chain anchoring: publish `provenanceHash` to Monad (or another chain) and verify off-chain JSON against the anchor.

---

## Signal engine

The MVP uses **deterministic rules** over mock metrics — no ML, no external APIs.

| Condition | Signal |
|-----------|--------|
| `volatilityIndex > 75` and position ≠ flat | CLEAR |
| `pnl24hPct < -1.5` and position = long | SHORT |
| `volatilityIndex > 60` or `liquidityScore < 0.3` | SAFE HOLD |
| otherwise | HOLD |

Rules are intentionally simple and auditable. Production would swap `mockDeskMetrics()` for authenticated feed adapters while keeping the honesty envelope.

---

## Trust / Identity layer (stub)

Each card includes:

```json
"trust": {
  "identityLayer": "stub",
  "attestations": [],
  "policyVersion": "trust-v0.1",
  "metropolisTrack": "Trust / Identity & AI Infrastructure"
}
```

**Planned extensions (post-MVP):**

1. **Identity** — wallet or DID binding; optional SIWE-style proof
2. **Attestations** — signed statements from operator or third-party oracle
3. **Policy** — versioned trust policy document hashed alongside cards
4. **Chain anchor** — `provenanceHash` posted to Monad testnet (see `docs/MONAD_DEPLOY.md`)

---

## Status page

- **Stack:** Node.js `http` module, zero dependencies
- **Bind:** `0.0.0.0:$PORT` (default 3847) — Render-compatible
- **Routes:**
  - `/` — HTML status UI
  - `/api/card` — JSON card
  - `/api/health` — liveness

The UI polls `/api/card` every 15s. Branding displays owner and bot on separate lines.

---

## Security & honesty principles

1. **Mock by default** — `dataSource: "mock"` on every card
2. **Human in the loop** — `humanReviewRequired: true`
3. **No secrets in repo** — future keys via environment variables only
4. **No execution path** — agent writes JSON; no order routing
5. **No Jito / MEV** — out of scope

---

## Deployment topology (future)

```
Agent (cron / worker)  →  Object store or DB  →  Status web service
                              ↓
                     Monad testnet (hash anchor)
```

Current MVP collapses storage to a local JSON file for simplicity.

---

## Solo attribution

Wyndham Heaven / elghaly — Morning Light Desk Sentinel
