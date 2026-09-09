# Morning Light Desk Sentinel

✝️🧿🪬

3️⃣🧿5️⃣

**Track:** Trust / Identity & AI Infrastructure  
**Builder:** Wyndham Heaven / elghaly solo  
**Repo:** [Alarm2024/metropolis-desk-sentinel](https://github.com/Alarm2024/metropolis-desk-sentinel)

A local MVP desk sentinel that reads **mock** metrics and emits short, auditable **CLEAR / SHORT / HOLD** JSON cards. When conditions are ambiguous or execution quality is poor, the agent applies **SAFE HOLD honesty** — it holds and says so explicitly instead of faking conviction.

No live feeds, no secrets, no Jito, no mainnet claims.

---

## Quick start

```bash
git clone https://github.com/Alarm2024/metropolis-desk-sentinel.git
cd metropolis-desk-sentinel
chmod +x run.sh
./run.sh
```

Open **http://127.0.0.1:8080** — click **Run desk evaluation** to generate the latest signal card and provenance hash.

### CLI (JSON only)

```bash
python3 -m pip install -r requirements.txt
python3 cli.py
```

Example output:

```json
{
  "signal": "HOLD",
  "summary": "Hold — edge too weak to act; staying honest",
  "safe_hold": true,
  "confidence": 0.412,
  "reasons": ["Order flow near neutral", "SAFE HOLD: score inside neutral band"],
  "metrics": { "...": "mock snapshot" },
  "provenance_hash": "a1b2c3...",
  "agent_version": "0.1.0-mvp",
  "timestamp_ms": 1725900000000
}
```

---

## API

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/health` | Liveness check (`local-mock` mode) |
| `GET` | `/api/metrics` | Current mock desk metrics snapshot |
| `POST` | `/api/evaluate` | Run agent → returns signal card JSON |
| `GET` | `/api/last` | Last card from this server process |
| `GET` | `/` | Status UI |

---

## Signals

| Signal | Meaning |
|--------|---------|
| `CLEAR` | Bullish desk bias within trust bounds |
| `SHORT` | Bearish desk bias within trust bounds |
| `HOLD` | No actionable edge — often with `safe_hold: true` |

**SAFE HOLD honesty:** the agent prefers HOLD when liquidity is thin, spreads are wide, volatility is elevated, or the composite score sits in a neutral band. The UI surfaces a **SAFE HOLD** badge when `safe_hold` is true.

---

## Provenance

Each card includes a **SHA-256 provenance hash** over:

- Agent version
- Full metrics snapshot
- Emitted signal
- `safe_hold` flag

This gives a reproducible audit trail for trust / identity workflows without claiming on-chain deployment in this MVP.

See [ARCHITECTURE.md](./ARCHITECTURE.md) for design detail and [docs/MONAD_DEPLOY.md](./docs/MONAD_DEPLOY.md) for future Monad deployment notes (stub only).

---

## Project layout

```
agent/          Desk agent + mock metrics
server/         FastAPI app
ui/             Status page (last card + hash)
cli.py          One-shot JSON evaluator
docs/           Monad deploy stub
```

---

## License

MIT — hackathon MVP scaffold.
