# Hackathon verdicts (Oct 2026)

**Builder:** Wyndham Heaven / elghaly  
**Decided:** 2026-10-12 (within 45-minute review window)

| Event | Verdict | Reason | Source |
|-------|---------|--------|--------|
| Metropolis (Monad) | **GO** | Testnet deploy is done (no card/KYC); faucet + public RPC work; remaining work is demo video + portal submit (~≤6 h). | [Metropolis schedule](https://www.monad.xyz/metropolis) · [Submission cutoff (11:59 PM ET → 03:59 UTC / 06:59 Cairo)](https://hackathon.monad.xyz) |
| Serverpod / BuilderBase | **SKIP** | No `elghaly` entry repo yet; BuilderBase submit + Serverpod Cloud credits need owner Luma registration and email invite; minimal full-stack entry cannot start by PR until the repo exists. | [BuilderBase event (deadline `2026-10-14T21:59:00Z` = 00:59 Cairo Oct 15)](https://builderbase.com/event/build-something-real-the-serverpod-hackathon) · [Luma overview](https://luma.com/builde-mked) |

---

## Metropolis — GO detail

### Deadline (confirmed)

- Official build window ends **13 Oct** on [monad.xyz/metropolis](https://www.monad.xyz/metropolis).
- Portal submissions close **13 Oct 11:59 PM ET** (= **14 Oct 03:59 UTC** = **14 Oct 06:59 Africa/Cairo**). Aim ready by **14 Oct 03:00 Cairo** (2 h buffer before Cairo display time).

### GO gates (all pass)

| Gate | Status | Evidence |
|------|--------|----------|
| (a) Testnet-only deploy, fresh key via env, no card/KYC | Pass | [MONAD_DEPLOY.md](./MONAD_DEPLOY.md) — `MONAD_TESTNET_KEY`, chainId 10143 only |
| (b) Faucet works | Pass | https://faucet.monad.xyz (HTTP reachable; fund throwaway address before redeploy) |
| (c) Fits in 6 hours | Pass | Contract deployed + 2 cards recorded; Pages demo live; pytest 82/82 |

### Links (submission pack)

| Item | URL |
|------|-----|
| Code | https://github.com/Alarm2024/metropolis-desk-sentinel |
| Read-only Monad demo | https://alarm2024.github.io/metropolis-desk-sentinel/ |
| Explorer | https://testnet.monadscan.com/address/0xc8f9Fd87AAd99FCd19d223fA08B0959bD031Ca3d |
| Portal copy + paste fields | [SUBMIT.md](./SUBMIT.md) |
| Video shot list | [SCREENSHOT_SCRIPT.md](./SCREENSHOT_SCRIPT.md) |

### Owner actions before cutoff

1. Record **60–90 s** demo MP4 per [SCREENSHOT_SCRIPT.md](./SCREENSHOT_SCRIPT.md) (include GitHub Pages + Monadscan beats).
2. Paste [SUBMIT.md](./SUBMIT.md) portal table into [hackathon.monad.xyz](https://hackathon.monad.xyz).
3. Upload demo video to the portal profile.
4. Optional redeploy only with a **new throwaway** key — never commit or paste the key.

---

## Serverpod / BuilderBase — SKIP detail

See [hackathons/SERVERPOD_BUILDERBASE_SKIP.md](./hackathons/SERVERPOD_BUILDERBASE_SKIP.md).

**If revisiting:** owner creates `elghaly-dev/<name>` (README + MIT), registers on [Luma](https://luma.com/builde-mked), claims credits on BuilderBase, then open a PR for a minimal Serverpod backend + one working flow before **14 Oct 21:59 UTC** (00:59 Cairo **15 Oct**).
