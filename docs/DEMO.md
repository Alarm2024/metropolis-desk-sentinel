# Judge Demo — Exact Clicks

✝️🧿🪬 · 3️⃣🧿5️⃣

**Project:** Morning Light Desk Sentinel *(portal alias: Skyline)*  
**Track:** Trust / Identity & AI Infrastructure — Metropolis Monad  
**Time:** ~90 seconds for the full UI path · ~15 seconds for CLI

No wallet. No secrets. Dry/read-only: no order execution. Local mock only.

---

## Path A — CLI (fastest, deterministic)

Judges who only want proof of honesty + provenance:

```bash
git clone https://github.com/Alarm2024/metropolis-desk-sentinel.git
cd metropolis-desk-sentinel
chmod +x scripts/demo.sh
./scripts/demo.sh
```

**Expected output (every run, same hash):**

```
signal=HOLD  trust_posture=REFUSAL  refusal_code=EXEC_QUALITY
agent_version=1.0.0-metropolis
provenance_hash=5250739379c6334af880d7742d6541dac3712f8c86201beaa9ff29d68db15bcd
provenance_valid=True
=== demo OK (exit 0) ===
```

Exit code **0** = the provenance hash matches. Same seed → same hash.

---

## Path B — Interactive UI (recommended for judges)

### 1. Start the server

```bash
git clone https://github.com/Alarm2024/metropolis-desk-sentinel.git
cd metropolis-desk-sentinel
chmod +x run.sh
./run.sh
```

Open **http://127.0.0.1:8080**

### 2. Health check (optional, 5 s)

In a second terminal:

```bash
curl -s http://127.0.0.1:8080/api/health | python3 -m json.tool
```

Expect `"status": "ok"`, `"mode": "local-mock"`, `"schema_version": "2.0"`.

### 3. Click — refusal on thin liquidity (30 s)

| Step | Action | What you should see |
|------|--------|-------------------|
| 1 | Under **Judge scenarios**, click **`hold thin liquidity`** | Status pill shows `hold_thin_liquidity` |
| 2 | Look at the signal card | Badge **HOLD**, posture **REFUSAL**, ⛔ **SAFE HOLD** |
| 3 | Read **Why we refused** | `EXEC_QUALITY` + human reason about execution quality |
| 4 | Check **Hash matches** in metadata | `yes ✓` (hash recomputed and compared) |
| 5 | Scroll to **Decision log** | New entry `#N` · HOLD · EXEC_QUALITY · hash prefix |

**Judge takeaway:** Thin liquidity alone triggers the refusal — order flow is neutral and volume is flat, and the agent still will not fake CLEAR on a thin book.

### 4. Click — directional only when trust passes (20 s)

| Step | Action | What you should see |
|------|--------|-------------------|
| 1 | Click **`clear bullish`** | Badge **CLEAR**, posture **DIRECTIONAL** |
| 2 | Confirm refusal panel is hidden | No `refusal_code` — honest conviction only when bounds pass |
| 3 | Note **Provenance hash** changed | New hash; **Hash matches** still `yes ✓` |

### 5. Click — seed replay (20 s)

| Step | Action | What you should see |
|------|--------|-------------------|
| 1 | In **Demo seed**, type `metropolis-judge-001` | — |
| 2 | Click **Evaluate mock desk** | Card updates; status `updated` |
| 3 | Click **Evaluate mock desk** again | Identical card and **same provenance hash** |
| 4 | Check **Decision log** pill | `chain ok` — hash-chained; flags an edited entry (not a deleted tail or a full rewrite) |

### 6. OpenAPI (optional, 10 s)

Open **http://127.0.0.1:8080/docs** — interactive API explorer for `/api/evaluate`, `/api/verify`, `/api/decisions`.

---

## Path C — Golden scenarios (CLI, all refusal paths)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python3 cli.py --scenario hold_thin_liquidity   # EXEC_QUALITY
python3 cli.py --scenario hold_neutral_edge     # NO_EDGE
python3 cli.py --scenario hold_neutral_band     # NEUTRAL_BAND
python3 cli.py --scenario clear_bullish         # CLEAR when trust bounds pass
python3 cli.py --scenario short_bearish         # SHORT with good execution quality
```

Add `--verify` to any command to assert provenance on stdout.

---

## What judges should verify

| Claim | How to verify in 30 s |
|-------|----------------------|
| Agent refuses soft lies | Scenario `hold thin liquidity` → HOLD + EXEC_QUALITY |
| Provenance is replayable | Same seed twice → identical `provenance_hash` (shows hashed fields unchanged; does not prove who made the card) |
| Log flags edited entries | UI shows **chain ok** after evaluations |
| Dry/read-only, no order execution | `/api/health` → `"mode": "local-mock"` |
| Typed schema | `/api/schema` → JSON Schema + trust invariants |

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Port 8080 in use | `PORT=8081 ./run.sh` then open `http://127.0.0.1:8081` |
| Missing deps | `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt` (`./run.sh` does this for you) |
| Empty scenario buttons | Refresh page; server must be running |
| `integrity_ok: false` / 409 "decision log is malformed; append refused" after upgrading | This release changes the provenance hash formula (it now covers the card's agent_version, schema_version, top-level timestamp_ms, summary, reasons, confidence, and refusal_reason), so a `decision_log.jsonl` written by an older version fails the hash check. Move or rotate the old log (e.g. `mv data/decision_log.jsonl data/decision_log.pre-upgrade.jsonl`) before starting the new version. |

See [SCREENSHOT_SCRIPT.md](./SCREENSHOT_SCRIPT.md) for a 60–90 s screen-recording shot list.
