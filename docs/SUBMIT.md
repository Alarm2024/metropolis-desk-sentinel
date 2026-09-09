# Metropolis Submission Profile — Morning Light Desk Sentinel

✝️🧿🪬

3️⃣🧿5️⃣

**Track:** Trust / Identity & AI Infrastructure  
**Hackathon:** [Metropolis Monad](https://metropolis.monad.xyz)  
**Builder:** Wyndham Heaven / elghaly (solo)  
**Submit target:** October 13, 2026  
**Repo:** https://github.com/Alarm2024/metropolis-desk-sentinel

---

## Problem: soft-lie agents

Trading desks and judges see AI assistants that *sound* confident. They emit directional calls on thin evidence, hide uncertainty behind polished prose, and leave no audit trail when they are wrong. That is a **trust failure** — not a model failure.

---

## Solution: SAFE HOLD + provenance + hash-chained decision log

**Morning Light Desk Sentinel** is Trust / Identity infrastructure for desk agents. The product is **refusal**, not prediction:

| Layer | What it does |
|-------|----------------|
| **SAFE HOLD honesty** | When execution quality is thin, edge is weak, or score sits in a neutral band, the agent emits `HOLD` with explicit `refusal_code` and `refusal_reason` — never fake CLEAR |
| **Provenance hash** | SHA-256 over metrics, signal, `trust_posture`, `reason_codes`, and refusal fields — anyone can replay and verify |
| **Hash-chained decision log** | Append-only JSONL; each entry links to the prior `entry_hash`; tamper detection via `verify_log_integrity()` |
| **Agent identity (local, ERC-8004-inspired)** | Every card carries `agent_version`, `schema_version`, and `trust_posture` — ready for future on-chain attestation |

No live feeds. No wallet keys. No Jito. No mainnet claims in this MVP.

---

## Demo steps (judges)

### One-shot CLI (deterministic)

```bash
git clone https://github.com/Alarm2024/metropolis-desk-sentinel.git
cd metropolis-desk-sentinel
chmod +x scripts/demo.sh
./scripts/demo.sh
```

Fixed seed `metropolis-demo-2026` → identical card and `provenance_hash` every run. Exit code 0 on success.

### Interactive UI

```bash
chmod +x run.sh
./run.sh
```

Open **http://127.0.0.1:8080**

1. Enter seed `metropolis-judge-001` (or leave default)
2. Click **Evaluate mock desk** — or pick a **judge scenario** fixture
3. Confirm SAFE HOLD refusals show `refusal_code`, live provenance verify, and decision log tail

### Golden scenarios (all refusal paths covered)

```bash
python3 cli.py --scenario hold_thin_liquidity   # EXEC_QUALITY refusal
python3 cli.py --scenario hold_neutral_edge     # NO_EDGE refusal
python3 cli.py --scenario hold_neutral_band     # NEUTRAL_BAND refusal
python3 cli.py --scenario clear_bullish         # CLEAR only when trust bounds pass
python3 cli.py --scenario short_bearish         # SHORT with good execution quality
```

### Tests

```bash
python3 -m pip install -r requirements.txt
python3 -m pytest tests/ -v
```

22+ tests: golden fixtures, 100-seed sweep (never fake CLEAR on thin books), hash-chain tamper detection, provenance verification.

---

## Code link

**Repository:** https://github.com/Alarm2024/metropolis-desk-sentinel

Key paths:

| Path | Purpose |
|------|---------|
| `agent/schema.py` | Typed `SignalCardSchema` v2.0 + trust invariants |
| `agent/desk_agent.py` | Rule-based evaluator — SAFE HOLD is the product |
| `agent/provenance.py` | Hash compute + verify |
| `agent/decision_log.py` | Hash-chained append-only audit log |
| `scripts/demo.sh` | One-shot deterministic judge demo |
| `docs/MONAD_DEPLOY.md` | Future Monad hash-anchor checklist (stub) |
| `contracts/` | `SignalAnchor` interface stub for future on-chain anchoring |

---

## What we claim vs. what we do not

**Claim:** auditable local agent with verifiable identity fields, honest refusals, reproducible provenance, tamper-evident log.

**Do not claim:** live trading, mainnet/testnet deployment, LLM inference, or on-chain anchors in this repo (future work documented in `docs/MONAD_DEPLOY.md`).

---

## Submit

**Target date:** October 13, 2026  
**Track:** Trust / Identity & AI Infrastructure — Metropolis Monad Hackathon
