# Deploy SentinelLog to Monad Testnet — copy-paste runbook

✝️🧿🪬

3️⃣🧿5️⃣

**Status:** not deployed yet. The address is PENDING until `deployments/monad-testnet.json` has one.
**Who runs this:** the maintainer, once, on a computer with a terminal. Judges don't need it.
**Time:** about 15 minutes. **Cost:** nothing; testnet MON is free and has no value.

Rules for this whole page:
- Use a **brand-new throwaway key** made in step 4. Never a wallet that holds anything of value.
- The key goes into **one environment variable**, `MONAD_TESTNET_KEY`, typed into a hidden prompt. It is never a command-line argument, never in a file, never committed, never pasted into a chat.
- Monad **Testnet** only (chainId **10143**). The scripts refuse any other chain.

---

## 1. Install Foundry (skip if `forge --version` already works)

```bash
curl -L https://foundry.paradigm.xyz | bash
# open a new terminal, then:
foundryup
forge --version && cast --version
```

## 2. Get the code

```bash
git clone https://github.com/Alarm2024/metropolis-desk-sentinel.git
cd metropolis-desk-sentinel
git fetch origin pull/11/head:pr-11 && git checkout pr-11   # PR #11; use main once it is merged
git submodule update --init                 # lib/forge-std
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt   # record_card.sh runs the local agent
forge test                                  # the contract tests; all must pass
```

## 3. Check the network

```bash
cast chain-id --rpc-url https://testnet-rpc.monad.xyz
```

It must print `10143`. If it fails or prints another number, take the RPC URL from Monad's testnet page (https://docs.monad.xyz/developer-essentials/testnets) and use it for the rest of this page:

```bash
export RPC_URL='<the testnet RPC URL from Monad docs>'
cast chain-id --rpc-url "$RPC_URL"           # must print 10143
```

## 4. Make a throwaway key

```bash
cast wallet new
```

It prints an **Address** (`0x` + 40 characters) and a **Private key** (`0x` + 64 characters).
- Write the **address** down; it is public and safe to share.
- Leave the **private key** on screen only until step 6. Do not save it in a file, a note or a message.

## 5. Fund the address with testnet MON

1. Open https://faucet.monad.xyz and paste the **address** from step 4.
2. Wait for the faucet, then check:

```bash
cast balance <ADDRESS> --ether --rpc-url "${RPC_URL:-https://testnet-rpc.monad.xyz}"
```

It must print more than `0`.

## 6. Deploy

```bash
read -rsp 'Testnet key: ' MONAD_TESTNET_KEY && export MONAD_TESTNET_KEY
# paste the private key from step 4 and press Enter (nothing is shown)
clear                                        # wipe the key from the screen
./scripts/deploy_testnet.sh
```

What you should see:
- `SentinelLog: 0x…` — the contract address;
- `recorder: 0x…` — the address from step 4 (only it can record);
- `Wrote deployments/monad-testnet.json and docs/deployments/monad-testnet.json`.

The script refuses if the RPC is not chainId 10143, and the Solidity script checks the chain again before it broadcasts.

## 7. Record two real cards

```bash
./scripts/record_card.sh hold_thin_liquidity
./scripts/record_card.sh hold_neutral_band
```

Each runs the local agent, takes the card's `provenance_hash`, and records it with its SAFE HOLD verdict and reason. `record_card.sh` also honours `RPC_URL`.

## 8. Forget the key

```bash
unset MONAD_TESTNET_KEY
```

The key was typed into a hidden prompt, not a command, so it is not in your shell history.

## 9. Check what changed, then commit

```bash
git status --short
```

Only these two files may appear:

```
 M deployments/monad-testnet.json
 M docs/deployments/monad-testnet.json
```

`broadcast/`, `cache/`, `out/` and `.env` are in `.gitignore`. Safety check; it must print nothing, because a 64-character hex string could be a private key:

```bash
git diff | grep -E '0x[0-9a-fA-F]{64}'
```

Then:

```bash
git add deployments/monad-testnet.json docs/deployments/monad-testnet.json
git commit -m "SentinelLog on Monad Testnet"
git push
```

## 10. Check it on an explorer

```
https://testnet.monadscan.com/address/<CONTRACT ADDRESS>
```

You should see the contract creation and two `record` transactions. Monad's docs list Monadscan, MonadVision (testnet.monadvision.com) and Socialscan (monad-testnet.socialscan.io) as testnet explorers.

## 11. Turn on the page (GitHub Pages)

1. GitHub → the repository → **Settings → Pages → Build and deployment → Source: GitHub Actions**.
2. Once PR #11 is merged to `main`, the **Pages (demo page)** workflow publishes `docs/` to https://alarm2024.github.io/metropolis-desk-sentinel/.
3. Open it: it reads the address from `docs/deployments/monad-testnet.json` and lists the recorded cards (hash, verdict, reason, block time in UTC) over the public RPC. No wallet needed.

## 12. Send the contract address to Claude

Only the **contract address** (it is public). Claude then fills it into the README table and `docs/SUBMIT.md` and removes "PENDING".

---

## If something goes wrong

| Message | Meaning | Fix |
|---|---|---|
| `refusing: the RPC answered chainId …` | The RPC is not Monad Testnet | Step 3: set `RPC_URL` from Monad's docs |
| `Deploy: Monad Testnet (chainId 10143) only` | The same, caught inside the Solidity script | Same |
| `insufficient funds` | The address has no testnet MON | Step 5 again |
| `set MONAD_TESTNET_KEY …` | The variable is empty in this terminal | Step 6 again, in the same terminal |
| `Foundry is not installed` | `forge` is not on PATH | Step 1, then open a new terminal |
| `NotRecorder(0x…)` (revert) | Recording with a different key than the deployer's | Use the key from step 4 |

---

## Later (not built): anchoring and agent identity

The local cards already carry ERC-8004-inspired fields: `agent_version`, `schema_version`, `trust_posture`, `refusal_code`, and a SHA-256 `provenance_hash`. `SentinelLog` records that hash with a verdict. Two things are not built and are not claimed:
- the fuller `SignalAnchor` design in `contracts/ISignalAnchor.sol` (an interface only);
- binding `agent_version` to an on-chain agent registry (ERC-8004 Identity) once one exists on Monad.

A recorded entry shows that the recorder address published this card hash at this block time. It does not show that the verdict was right, and it does not prove who built the card off-chain.

References: [Monad testnets](https://docs.monad.xyz/developer-essentials/testnets) · [EIP-8004](https://eips.ethereum.org/EIPS/eip-8004) · [ARCHITECTURE.md](../ARCHITECTURE.md) · [SUBMIT.md](./SUBMIT.md)
