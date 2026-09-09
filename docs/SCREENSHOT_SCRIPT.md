# Demo GIF / Screenshot Script

✝️🧿🪬 · 3️⃣🧿5️⃣

Shot list for a **60–90 second** judge demo (screen recording or animated GIF).  
Record at **1280×720** or **1920×1080**, browser zoom **100%**, dark room optional (UI is light-themed).

**Before recording:**

```bash
git clone https://github.com/Alarm2024/metropolis-desk-sentinel.git
cd metropolis-desk-sentinel
chmod +x run.sh && ./run.sh
```

Open **http://127.0.0.1:8080** in Chrome or Firefox.

---

## Shot list

| Time | Frame / action | Caption (optional overlay) |
|------|----------------|----------------------------|
| 0:00 | Full page — header “Morning Light Desk Sentinel”, trust banner | *Trust / Identity for desk agents* |
| 0:05 | Slow scroll: Run evaluation panel + empty state | *The product is refusal, not prediction* |
| 0:10 | Click **`hold thin liquidity`** under Judge scenarios | *Thin book → agent refuses* |
| 0:15 | Hold on signal card: HOLD badge, REFUSAL, ⛔ SAFE HOLD | |
| 0:20 | Zoom/crop **Why we refused** — `EXEC_QUALITY` + reason text | *Explicit refusal_code — no soft lie* |
| 0:25 | Pan to **Verified: valid ✓** and **Provenance hash** | *SHA-256 anyone can replay* |
| 0:30 | Scroll to **Decision log** — entry with hash prefix, pill **chain ok** | *Hash-chained audit trail* |
| 0:35 | Click **`clear bullish`** | *Acts only when trust bounds pass* |
| 0:40 | Show CLEAR + DIRECTIONAL, refusal panel gone | |
| 0:45 | Type `metropolis-judge-001` in Demo seed | |
| 0:50 | Click **Evaluate mock desk** twice — hash unchanged | *Deterministic — same seed, same hash* |
| 0:55 | (Optional) Second terminal: `curl -s localhost:8080/api/health \| jq` | *Public health — local-mock, no secrets* |
| 1:00 | End card: repo URL on screen or pasted in editor | *github.com/Alarm2024/metropolis-desk-sentinel* |

**Total:** ~60 s tight · ~90 s with CLI curl beat.

---

## CLI-only GIF (15 s, no browser)

For README or portal thumbnail when UI is not needed:

```bash
./scripts/demo.sh
```

Capture terminal output showing:

```
signal=HOLD  trust_posture=REFUSAL  refusal_code=EXEC_QUALITY
provenance_hash=629c809f...
provenance_valid=True
=== demo OK (exit 0) ===
```

Run twice in the same recording to show identical hash.

---

## Static screenshots (portal / README)

If you prefer PNGs over GIF:

| File suggestion | Content |
|-----------------|---------|
| `docs/assets/01-refusal-hold.png` | `hold thin liquidity` — HOLD + EXEC_QUALITY panel |
| `docs/assets/02-clear-directional.png` | `clear bullish` — CLEAR + DIRECTIONAL |
| `docs/assets/03-decision-log.png` | Decision log with **chain ok** pill |
| `docs/assets/04-cli-demo.png` | Terminal output of `./scripts/demo.sh` |

*(Assets are optional — commit PNGs only if you generate them; this script is the source of truth.)*

---

## Recording tools

| OS | Suggestion |
|----|------------|
| macOS | QuickTime → File → New Screen Recording; or `Cmd+Shift+5` |
| Linux | `peek` (GIF), `wf-recorder`, or OBS |
| Windows | Xbox Game Bar (`Win+G`) or OBS |

Export GIF ≤ **5 MB** for GitHub README; MP4 ≤ **2 min** for Metropolis portal demo link.

---

## Voice-over script (optional, ~45 s)

> Morning Light Desk Sentinel is Trust infrastructure for trading desks.  
> When execution quality is thin, the agent emits SAFE HOLD — never a fake CLEAR.  
> Here’s thin liquidity: HOLD, refusal code EXEC_QUALITY, provenance verified live.  
> When trust bounds pass, we get CLEAR — directional, no refusal fields.  
> Same seed, same hash — reproducible audit.  
> Hash-chained decision log, chain OK. Local mock only — no wallet, no live trading.

---

## Do not show in demo

- Wallet connect, private keys, or mainnet/testnet claims
- Fake transaction hashes or explorer links
- Live market feeds or order execution

See [SUBMIT.md](./SUBMIT.md) for portal copy and [DEMO.md](./DEMO.md) for step-by-step judge clicks.
