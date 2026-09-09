# Morning Light Desk Sentinel

✝️🧿🪬

3️⃣🧿5️⃣

**Track:** Trust / Identity & AI Infrastructure — [Metropolis Monad Hackathon](https://metropolis.monad.xyz)  
**Builder:** Wyndham Heaven / elghaly solo  
**Submit target:** ~October 13, 2026  
**Repo:** [Alarm2024/metropolis-desk-sentinel](https://github.com/Alarm2024/metropolis-desk-sentinel)

A local desk sentinel that reads **mock** metrics and emits short, auditable **CLEAR / SHORT / HOLD** JSON cards. When conditions are ambiguous or execution quality is poor, the agent applies **SAFE HOLD honesty** — it holds, logs an explicit **refusal code**, and never fakes conviction.

---

## Why honesty beats fake confidence (Trust / AI pitch)

Many trading assistants optimize for *sounding* confident. Morning Light Desk Sentinel optimizes for **trust**:

| Fake-confidence pattern | This agent |
|-------------------------|------------|
| Always emits BUY/SELL | Emits HOLD when edge or execution quality is insufficient |
| Hides uncertainty | Surfaces `safe_hold`, `refusal_code`, and `refusal_reason` |
| Black-box decisions | Append-only decision log + SHA-256 provenance hash |
| Unversioned outputs | Card `schema_version` for audit trail upgrades |

The goal is **identity-grade auditability**: anyone can replay inputs, verify the hash, and inspect why the agent refused to act.

---

## Quick start

```bash
git clone https://github.com/Alarm2024/metropolis-desk-sentinel.git
cd metropolis-desk-sentinel
chmod +x run.sh
./run.sh
```

Open **http://127.0.0.1:8080** — enter an optional **demo seed** for repeatable hashes, then click **Run desk evaluation**.

### CLI (JSON only)

```bash
python3 -m pip install -r requirements.txt
python3 cli.py --seed demo-001
```

### Tests

```bash
python3 -m pytest tests/ -v
```

---

## What this project claims

- Local mock desk metrics (deterministic with seed)
- Rule-based CLEAR / SHORT / HOLD with explicit SAFE HOLD refusals
- Append-only JSONL decision log (`data/decision_log.jsonl`)
- Card schema v1.1 with provenance hashing
- Optional keyless read-only public summary (`PUBLIC_METRICS=1`)

## What this project does NOT claim

- Live market data, mainnet, or testnet trading
- Wallet keys, Jito, MEV, or order execution
- LLM inference (deterministic rules only — auditable by design)
- On-chain deployment (future stub in `docs/MONAD_DEPLOY.md`)

---

## API

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/health` | Liveness + mode flags |
| `GET` | `/api/metrics?seed=` | Mock metrics snapshot (optional seed) |
| `POST` | `/api/evaluate` | Run agent → signal card JSON. Body: `{"seed": "demo-001"}` |
| `GET` | `/api/last` | Last card from this server process |
| `GET` | `/api/decisions?limit=` | Recent entries from append-only decision log |
| `GET` | `/api/public/summary` | Read-only aggregates (**only when `PUBLIC_METRICS=1`**) |
| `GET` | `/` | Status UI |

### Deterministic demos

```bash
curl -X POST http://127.0.0.1:8080/api/evaluate \
  -H 'Content-Type: application/json' \
  -d '{"seed":"hackathon-demo"}'
```

Same seed → same metrics → same provenance hash.

### Optional public metrics (off by default)

```bash
PUBLIC_METRICS=1 ./run.sh
curl http://127.0.0.1:8080/api/public/summary
```

Returns aggregate signal counts and SAFE HOLD rates — no secrets, no live trading claims.

---

## Signals & refusals

| Signal | Meaning |
|--------|---------|
| `CLEAR` | Bullish desk bias within trust bounds |
| `SHORT` | Bearish desk bias within trust bounds |
| `HOLD` | No actionable edge — often with `safe_hold: true` |

When `safe_hold` is true, the card includes:

| `refusal_code` | When |
|----------------|------|
| `EXEC_QUALITY` | Liquidity/spread below trust threshold |
| `NO_EDGE` | Composite score too weak |
| `NEUTRAL_BAND` | Score inside neutral band — no fake conviction |

---

## Provenance & audit trail

Each card includes:

- **`schema_version`** — card format version (currently `1.1`)
- **`provenance_hash`** — SHA-256 over schema version, metrics, signal, `safe_hold`, and `refusal_code`
- **Decision log** — every evaluation appended to `data/decision_log.jsonl`

Example card:

```json
{
  "signal": "HOLD",
  "summary": "Hold — conditions ambiguous or untrusted for directional action",
  "safe_hold": true,
  "refusal_code": "EXEC_QUALITY",
  "refusal_reason": "Refused directional action: execution quality below trust threshold",
  "confidence": 0.312,
  "reasons": ["Thin liquidity — execution risk elevated", "SAFE HOLD: insufficient execution quality"],
  "schema_version": "1.1",
  "agent_version": "0.2.0-trust",
  "provenance_hash": "a1b2c3..."
}
```

---

## Scenario tests

Golden fixtures in `tests/fixtures/` prove behavior across five market scenarios:

| Fixture | Expected |
|---------|----------|
| `clear_bullish` | CLEAR, no refusal |
| `short_bearish` | SHORT, no refusal |
| `hold_thin_liquidity` | HOLD + EXEC_QUALITY |
| `hold_neutral_edge` | HOLD + NO_EDGE |
| `hold_neutral_band` | HOLD + NEUTRAL_BAND |

Run: `python3 -m pytest tests/test_scenarios.py -v`

---

## Project layout

```
agent/              Desk agent, mock metrics, decision log, fixtures loader
server/             FastAPI app
ui/                 Status page (SAFE HOLD badge, provenance, demo seed)
tests/fixtures/     Scenario fixtures + golden expectations
cli.py              One-shot JSON evaluator
docs/               Monad deploy stub
data/               Append-only decision log (gitignored)
```

See [ARCHITECTURE.md](./ARCHITECTURE.md) for design detail.

---

## License

MIT — hackathon scaffold.
