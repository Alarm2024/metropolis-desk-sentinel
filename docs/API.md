# HTTP API Reference

✝️🧿🪬 · 3️⃣🧿5️⃣

**Base URL (local):** `http://127.0.0.1:8080`  
**OpenAPI:** `http://127.0.0.1:8080/docs`

No authentication. No secrets. No live trading — all evaluations use deterministic mock metrics.

---

## Health — `GET /api/health`

Public liveness probe. Safe to expose on any deployed demo instance (read-only, no keys).

### Request

```bash
curl -s http://127.0.0.1:8080/api/health
```

### Response `200 OK`

```json
{
  "status": "ok",
  "mode": "local-mock",
  "agent_version": "1.0.0-metropolis",
  "schema_version": "2.0",
  "public_metrics": false,
  "product": "SAFE HOLD honesty — agents that refuse soft lies"
}
```

| Field | Meaning |
|-------|---------|
| `status` | `"ok"` when the service is up |
| `mode` | Always `"local-mock"` in this MVP — no live feeds |
| `agent_version` | Semver pin for agent identity (ERC-8004-inspired) |
| `schema_version` | Signal card schema version (`2.0`) |
| `public_metrics` | `true` only when `PUBLIC_METRICS=1` — enables `/api/public/summary` |
| `product` | One-line product statement for monitors and judges |

### Use cases

- **Uptime monitors** — expect HTTP 200 and `"status":"ok"`
- **Judges** — confirm `"mode":"local-mock"` before trusting demo claims
- **CI smoke test** — `curl -sf localhost:8080/api/health | jq -e '.status == "ok"'`

---

## Schema — `GET /api/schema`

Returns JSON Schema for `SignalCardSchema` v2.0 plus trust invariants.

```bash
curl -s http://127.0.0.1:8080/api/schema | jq '.trust_invariants'
```

---

## Evaluate — `POST /api/evaluate`

Run the desk agent on mock metrics.

```bash
curl -s -X POST http://127.0.0.1:8080/api/evaluate \
  -H 'Content-Type: application/json' \
  -d '{"seed":"metropolis-judge-001"}' \
  | jq '{signal, trust_posture, refusal_code, provenance_hash}'
```

Same `seed` → identical response and hash.

**Refusal fields on CLEAR/SHORT:** `refusal_code` and `refusal_reason` are **omitted** (not `null`) when `trust_posture` is `DIRECTIONAL`. HOLD responses always include both fields with explicit enum codes (`EXEC_QUALITY`, `NO_EDGE`, `NEUTRAL_BAND`).

---

## Scenarios — `GET /api/scenarios` · `POST /api/scenarios/{name}/evaluate`

Named golden fixtures for judge demos.

```bash
curl -s http://127.0.0.1:8080/api/scenarios | jq '.[].name'

curl -s -X POST http://127.0.0.1:8080/api/scenarios/hold_thin_liquidity/evaluate \
  | jq '{signal, refusal_code, provenance_hash}'
```

---

## Audit — `GET /api/decisions` · `POST /api/verify`

```bash
# Hash-chained log + integrity
curl -s 'http://127.0.0.1:8080/api/decisions?limit=5' \
  | jq '{count, integrity_ok, integrity_message}'

# Verify a card's provenance_hash
curl -s -X POST http://127.0.0.1:8080/api/verify \
  -H 'Content-Type: application/json' \
  -d @card.json | jq
```

---

## Public summary — `GET /api/public/summary`

**Only when `PUBLIC_METRICS=1`.** Read-only aggregates over the decision log. Returns 404 when disabled.

---

## Environment variables

| Variable | Default | Effect |
|----------|---------|--------|
| `PUBLIC_METRICS` | off | Set `1` / `true` / `yes` to expose `/api/public/summary` |
| `DECISION_LOG_PATH` | `data/decision_log.jsonl` | Append-only audit log location |

No wallet keys. No RPC URLs in MVP.

---

See [DEMO.md](./DEMO.md) for judge click paths and [SUBMIT.md](./SUBMIT.md) for hackathon portal copy.
