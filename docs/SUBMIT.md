# Metropolis Submission Profile — Morning Light Desk Sentinel

✝️🧿🪬

3️⃣🧿5️⃣

**Track:** Trust / Identity & AI Infrastructure  
**Hackathon:** [Metropolis Monad](https://metropolis.monad.xyz) · submit at [hackathon.monad.xyz](https://hackathon.monad.xyz)  
**Builder:** Wyndham Heaven / elghaly (solo)  
**Deadline:** Wed 14 Oct 2026, 03:59 UTC  
**Repo:** https://github.com/Alarm2024/metropolis-desk-sentinel

---

## Portal copy-paste (hackathon.monad.xyz)

Use these values in the Metropolis project profile. Portal display name may show as **Skyline** or **Morning Light Desk Sentinel** — both refer to this repo.

| Portal field | Copy |
|--------------|------|
| **Project name** | Morning Light Desk Sentinel |
| **Track** | Trust / Identity & AI Infrastructure |
| **One-liner** | Desk agents that refuse soft lies — SAFE HOLD with a provenance hash, a hash-chained decision log, and card hashes recorded on Monad Testnet. |
| **Description** | Trading desks need AI that refuses to fake conviction. Morning Light Desk Sentinel emits HOLD with explicit `refusal_code` when execution quality is thin or edge is weak, ships a SHA-256 provenance hash that reproduces exactly on replay, and appends every evaluation to a hash-chained decision log that flags edits to a logged entry (not a deleted tail or a full rewrite — see README). ERC-8004-inspired agent fields (`agent_version`, `schema_version`, `trust_posture`). Rule-based, deterministic, local mock — no wallet keys in the agent, no order execution. A small `SentinelLog` contract on Monad Testnet (chainId 10143) records each card's `provenance_hash` with its SAFE HOLD verdict and reason, and a read-only page lists them. Contract address: **PENDING deploy**. |
| **Problem** | AI desk assistants sound confident but emit directional calls on thin evidence with nothing to check afterward when wrong — a trust failure, not a model failure. |
| **Solution** | SAFE HOLD honesty + provenance hash + hash-chained decision log + typed signal card schema with machine-readable refusal codes. |
| **Demo link** | Read-only page: https://alarm2024.github.io/metropolis-desk-sentinel/ (**PENDING**: after the deploy and Pages are on). Run locally: `./run.sh` → http://127.0.0.1:8080 — see [DEMO.md](./DEMO.md). CLI: `./scripts/demo.sh` (15 s, deterministic). |
| **Code link** | https://github.com/Alarm2024/metropolis-desk-sentinel |
| **Public health check** | `GET /api/health` — see [API.md](./API.md). Example: `curl -s http://127.0.0.1:8080/api/health` |
| **On Monad** | `SentinelLog` on Monad Testnet (chainId 10143) at **PENDING** · explorer: `https://testnet.monadscan.com/address/<address>` · source: `contracts/SentinelLog.sol` · deploy steps: [MONAD_DEPLOY.md](./MONAD_DEPLOY.md) |
| **Built during Metropolis** | Yes — Trust / Identity MVP (Sep 2026 build window) |

**Demo video / GIF:** Follow [SCREENSHOT_SCRIPT.md](./SCREENSHOT_SCRIPT.md) (60–90 s shot list). Upload MP4 to portal or embed in project profile per Metropolis rules.

---

## Problem: soft-lie agents

Trading desks and judges see AI assistants that *sound* confident. They emit directional calls on thin evidence, hide uncertainty behind polished prose, and leave nothing to check afterward when they are wrong. That is a **trust failure** — not a model failure.

---

## Solution: SAFE HOLD + provenance + hash-chained decision log

**Morning Light Desk Sentinel** is Trust / Identity infrastructure for desk agents. The product is **refusal**, not prediction:

| Layer | What it does |
|-------|----------------|
| **SAFE HOLD honesty** | When execution quality is thin, edge is weak, or score sits in a neutral band, the agent emits `HOLD` with explicit `refusal_code` and `refusal_reason` — never fake CLEAR |
| **Provenance hash** | SHA-256 over metrics, signal, `trust_posture`, `reason_codes`, `refusal_code`, `refusal_reason`, `summary`, `reasons`, and `confidence` — reproduces exactly on replay; confirms those fields weren't edited after hashing (not who produced the card, and not that the signal is correct for the metrics) |
| **Hash-chained decision log** | Append-only JSONL; each entry links to the prior `entry_hash`; `verify_log_integrity()` flags an edited entry (a deleted tail or a full rewrite with recomputed hashes is not detected) |
| **Agent identity (local, ERC-8004-inspired)** | Every card carries `agent_version`, `schema_version`, and `trust_posture` — ready for future on-chain attestation |

No real-time market feeds. No wallet keys in the agent. No Jito. No mainnet. The only chain use is a testnet log of card hashes (below).

---

## Demo steps (judges)

**Full click path:** [DEMO.md](./DEMO.md)  
**Recording script:** [SCREENSHOT_SCRIPT.md](./SCREENSHOT_SCRIPT.md)

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

1. Click **`hold thin liquidity`** under Judge scenarios — HOLD + `EXEC_QUALITY`
2. Click **`clear bullish`** — CLEAR + DIRECTIONAL (refusal panel hidden)
3. Enter seed `metropolis-judge-001` → **Evaluate mock desk** twice — same hash
4. Confirm Decision log pill shows **chain ok**

### Health endpoint (public, no secrets)

```bash
curl -s http://127.0.0.1:8080/api/health | python3 -m json.tool
```

Returns `status`, `mode: local-mock`, `agent_version`, `schema_version`. Full reference: [API.md](./API.md).

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

82 tests: golden fixtures, 100-seed sweep (never fake CLEAR on thin books), hash-chain edit detection, provenance hash checks, API health.

---

## Code link

**Repository:** https://github.com/Alarm2024/metropolis-desk-sentinel

Key paths:

| Path | Purpose |
|------|---------|
| `agent/schema.py` | Typed `SignalCardSchema` v2.0 + trust invariants |
| `agent/desk_agent.py` | Rule-based evaluator — SAFE HOLD is the product |
| `agent/provenance.py` | Hash compute + verify |
| `agent/decision_log.py` | Hash-chained append-only decision log |
| `scripts/demo.sh` | One-shot deterministic judge demo |
| `docs/DEMO.md` | Exact judge clicks (UI + CLI) |
| `docs/SCREENSHOT_SCRIPT.md` | GIF/video shot list for portal demo |
| `docs/API.md` | `/api/health` and full HTTP reference |
| `docs/MONAD_DEPLOY.md` | Copy-paste runbook: throwaway key, faucet, deploy to Monad Testnet, record cards, Pages |
| `contracts/SentinelLog.sol` | The Monad Testnet log of card hashes + SAFE HOLD verdicts (Foundry tests in `test/`) |
| `contracts/ISignalAnchor.sol` | Interface only, for later anchoring work (not deployed) |
| `docs/index.html` | Read-only page that lists recorded cards over the public RPC (no wallet) |

---

## What we claim vs. what we do not

**Claim:** local agent with honest refusals, a reproducible provenance hash, an edit-evident decision log (confirms hashed fields weren't changed after the fact — it does not catch a deleted tail or a full rewrite, and doesn't prove who produced a card; see README), a public `/api/health` health check, and (once deployed) card hashes with SAFE HOLD verdicts recorded on Monad Testnet by one recorder address.

**Do not claim:** order execution, mainnet, LLM inference, that a recorded verdict was right, or the fuller `SignalAnchor` / ERC-8004 identity work (not built; see `docs/MONAD_DEPLOY.md`). Until `deployments/monad-testnet.json` has an address, do not claim the testnet deployment either.

---

## Submit

**Deadline:** Wed 14 Oct 2026, 03:59 UTC  
**Track:** Trust / Identity & AI Infrastructure — Metropolis Monad Hackathon  
**Portal:** [hackathon.monad.xyz](https://hackathon.monad.xyz)
