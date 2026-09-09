# Morning Light Desk Sentinel

✝️🧿🪬

3️⃣🧿5️⃣

**Metropolis Trust / Identity & AI Infrastructure MVP**

A minimal desk-sentinel stack that emits structured, honest JSON cards from mock trading metrics, surfaces them on a local status page with provenance hashing, and stubs Monad deployment for the Metropolis hackathon.

| | |
|---|---|
| **Track** | Trust / Identity & AI Infrastructure |
| **Submit target** | Metropolis — **October 13, 2026** |
| **Solo** | Wyndham Heaven / elghaly |
| **Status** | MVP — mock data, local-only |

---

## What this does

1. **Agent** (`agent/sentinel.js`) — reads simulated desk metrics, applies transparent rule-based logic, and writes a JSON **card** to `data/last-card.json`.
2. **Status page** (`status/`) — serves the last card and its **provenance hash** (SHA-256 over the canonical card body) at `http://localhost:3847`.
3. **Trust layer stub** — each card carries identity/trust metadata and an explicit **honesty block** (mock source, human review required, limitations listed).

This is a demonstration scaffold. It does **not** connect to live exchanges, execute trades, or claim mainnet deployment.

---

## Signal honesty — SAFE HOLD / CLEAR / SHORT / HOLD

The agent emits exactly one of four actions per card:

| Signal | Meaning (mock logic) |
|--------|----------------------|
| **SAFE HOLD** | Uncertain conditions — preserve capital, no new entries |
| **CLEAR** | Elevated volatility with open exposure — reduce risk |
| **SHORT** | Underwater long with negative 24h PnL — bias to de-risk |
| **HOLD** | Metrics within normal band — maintain stance |

Every card includes:

- `signal.honesty.disclaimer` — not financial advice
- `signal.honesty.dataSource: "mock"`
- `signal.honesty.humanReviewRequired: true`
- `signal.honesty.limitations[]` — explicit gaps (no ML, no chain attestation in MVP)

We do not overclaim predictive accuracy or live execution readiness.

---

## Quick start (local)

**Requirements:** Node.js 18+

```bash
# Clone
git clone https://github.com/Alarm2024/metropolis-desk-sentinel.git
cd metropolis-desk-sentinel

# Generate a card
npm run agent

# Start status page (default port 3847)
npm run status
```

Open [http://localhost:3847](http://localhost:3847) — you should see the last card, signal banner, and provenance hash.

**One-liner (agent + status):**

```bash
npm start
```

**API:**

- `GET /api/card` — full JSON card
- `GET /api/health` — health check

**Custom port:**

```bash
PORT=8080 npm run status
```

---

## Project layout

```
├── agent/sentinel.js      # Mock desk agent → JSON cards
├── data/last-card.json    # Latest card (generated)
├── status/                # Status page + HTTP server
│   ├── server.js
│   └── public/
├── docs/MONAD_DEPLOY.md   # Monad deploy notes (stub)
├── ARCHITECTURE.md        # System design
└── package.json
```

---

## Metropolis submission checklist

- [x] Trust / Identity & AI Infrastructure track alignment
- [x] Structured JSON cards with provenance hash
- [x] Honest signal labeling (SAFE HOLD / CLEAR / SHORT / HOLD)
- [x] Status page with last card + hash
- [x] Architecture documentation
- [x] Monad deploy notes stub (no fake mainnet claims)
- [ ] On-chain identity attestation (future)
- [ ] Live desk feed integration (future)
- [ ] Monad testnet anchor (future — see `docs/MONAD_DEPLOY.md`)

---

## Constraints

- **English only**
- **No secrets** — nothing in repo; use env vars for future keys
- **No Jito** — no MEV / bundle dependencies
- **No fake mainnet claims** — Monad section is explicitly a stub

---

## License

MIT — Wyndham Heaven / elghaly
