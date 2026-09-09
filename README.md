# Morning Light Desk Sentinel

✝️🧿🪬

3️⃣🧿5️⃣

**Track:** Trust / Identity & AI Infrastructure — [Metropolis Monad Hackathon](https://metropolis.monad.xyz)  
**Builder:** Wyndham Heaven / elghaly solo  
**Submit target:** ~October 13, 2026  
**Agent version:** `1.0.0-metropolis` · **Card schema:** `2.0`

---

## The pitch: desks need agents that refuse soft lies

Trading desks drown in AI assistants that *sound* confident. They emit BUY/SELL on thin evidence, hide uncertainty behind polished prose, and leave no audit trail when they are wrong.

**Morning Light Desk Sentinel** inverts that. The product is not prediction — it is **refusal**:

- When execution quality is thin → **SAFE HOLD** with `EXEC_QUALITY`
- When edge is too weak → **SAFE HOLD** with `NO_EDGE`
- When score sits in the neutral band → **SAFE HOLD** with `NEUTRAL_BAND` — never fake CLEAR

Every refusal ships with crisp human reasons, machine-readable `reason_codes`, a typed card schema, and a **SHA-256 provenance hash** anyone can replay and verify. Evaluations append to a **hash-chained decision log** — tamper-evident, no secrets, no wallet keys, no live trading.

This is Trust / Identity infrastructure: an agent with a verifiable identity (`agent_version`), a versioned output contract (`schema_version`), and an honest posture field (`trust_posture: REFUSAL | DIRECTIONAL`).

---

## Quick start

```bash
git clone https://github.com/Alarm2024/metropolis-desk-sentinel.git
cd metropolis-desk-sentinel
chmod +x run.sh
./run.sh
```

Open **http://127.0.0.1:8080**

1. Enter a demo seed (e.g. `metropolis-judge-001`) for repeatable hashes
2. Click **Evaluate mock desk** — or pick a **judge scenario** fixture
3. Watch SAFE HOLD refusals surface with provenance verification live in the UI

### One-shot demo (judges)

```bash
chmod +x scripts/demo.sh
./scripts/demo.sh
```

Fixed seed `metropolis-demo-2026` → identical card and `provenance_hash` every run. Exit 0 on success.

**Exact judge clicks:** [docs/DEMO.md](./docs/DEMO.md) · **Demo GIF script:** [docs/SCREENSHOT_SCRIPT.md](./docs/SCREENSHOT_SCRIPT.md)

### CLI

```bash
python3 -m pip install -r requirements.txt
python3 cli.py --seed metropolis-judge-001 --verify
python3 cli.py --scenario hold_thin_liquidity
```

### Tests (airtight)

```bash
python3 -m pytest tests/ -v
```

61 tests including golden fixtures, 100-seed sweep (never fake CLEAR), hash-chain tamper detection, provenance verification, and API health.

---

## What we claim

| Capability | Detail |
|------------|--------|
| SAFE HOLD honesty | Every HOLD is `trust_posture=REFUSAL` with explicit `refusal_code` + `refusal_reason` |
| Typed card schema | Pydantic-validated `SignalCardSchema` v2.0 — invariants enforced at emission |
| Provenance | SHA-256 over metrics, signal, trust_posture, reason_codes, refusal_code |
| Decision log | Append-only JSONL, hash-chained entries, provenance gate on append |
| Deterministic demos | Same seed → identical metrics, card, and hash |
| Judge scenarios | Five golden fixtures covering CLEAR, SHORT, and all refusal paths |

## What we do NOT claim

- Live market data, mainnet, testnet, or order execution
- Wallet keys, Jito, MEV, or broker connectivity
- LLM inference (rule-based only — auditable by design)
- On-chain deployment in this repo (future stub: `docs/MONAD_DEPLOY.md`)

---

## API

Interactive docs: **http://127.0.0.1:8080/docs** · Full reference: [docs/API.md](./docs/API.md)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/health` | Public liveness — `status`, `mode: local-mock`, agent + schema version (no secrets) |
| `GET` | `/api/schema` | JSON Schema + trust invariants for judges |
| `POST` | `/api/evaluate` | Evaluate mock desk. Body: `{"seed":"..."}` |
| `GET` | `/api/scenarios` | List named judge fixtures |
| `POST` | `/api/scenarios/{name}/evaluate` | Run fixture (deterministic) |
| `GET` | `/api/decisions` | Hash-chained log + integrity status |
| `POST` | `/api/verify` | Verify provenance_hash for a card JSON |
| `GET` | `/api/public/summary` | Read-only aggregates (`PUBLIC_METRICS=1` only) |

### Health check (public, no auth)

```bash
curl -s http://127.0.0.1:8080/api/health | jq
```

### Deterministic demo

```bash
curl -s -X POST http://127.0.0.1:8080/api/evaluate \
  -H 'Content-Type: application/json' \
  -d '{"seed":"metropolis-judge-001"}' | jq '.provenance_hash, .refusal_code, .trust_posture'
```

Run twice — hash is identical.

---

## Signal card (schema 2.0)

```json
{
  "signal": "HOLD",
  "summary": "Hold — conditions untrusted for directional action",
  "safe_hold": true,
  "trust_posture": "REFUSAL",
  "refusal_code": "EXEC_QUALITY",
  "refusal_reason": "Refused directional action: execution quality below trust threshold",
  "confidence": 0.312,
  "reasons": ["Thin liquidity — execution risk elevated", "SAFE HOLD: insufficient execution quality"],
  "reason_codes": ["THIN_LIQUIDITY", "REFUSAL_EXEC_QUALITY"],
  "schema_version": "2.0",
  "agent_version": "1.0.0-metropolis",
  "provenance_hash": "a1b2c3..."
}
```

Directional cards (`CLEAR` / `SHORT`) omit refusal fields and set `trust_posture: DIRECTIONAL`.

---

## Golden scenarios

| Fixture | Expected | Why judges care |
|---------|----------|-----------------|
| `clear_bullish` | CLEAR | Acts only when trust bounds pass |
| `short_bearish` | SHORT | Bearish with good execution quality |
| `hold_thin_liquidity` | HOLD + EXEC_QUALITY | Strong flow still refused on thin book |
| `hold_neutral_edge` | HOLD + NO_EDGE | No fake conviction on weak edge |
| `hold_neutral_band` | HOLD + NEUTRAL_BAND | Neutral band → honest hold |

---

## Project layout

```
agent/
  schema.py         Typed Pydantic card schema + trust invariants
  desk_agent.py     Rule-based evaluator — SAFE HOLD is the product
  provenance.py     Hash compute + verify
  decision_log.py   Hash-chained append-only audit log
  metrics.py        Deterministic mock metrics
server/app.py       FastAPI + OpenAPI docs
ui/                 Judge demo UI (branding, scenarios, log, verify)
scripts/demo.sh     One-shot deterministic judge demo (fixed seed)
tests/fixtures/     Golden scenarios + expected outputs
contracts/          SignalAnchor interface stub (future Monad anchor)
docs/
  SUBMIT.md         Metropolis portal copy-paste + submission profile
  DEMO.md           Exact judge clicks (UI + CLI)
  SCREENSHOT_SCRIPT.md  GIF/video shot list for portal demo
  API.md            /api/health and HTTP reference
  MONAD_DEPLOY.md   ERC-8004-inspired identity map + Monad checklist
```

See [ARCHITECTURE.md](./ARCHITECTURE.md) for design detail and [docs/SUBMIT.md](./docs/SUBMIT.md) for the public hackathon write-up.

---

## License

MIT
