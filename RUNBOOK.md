# RUNBOOK — KLDA-HFT Manual Operations Guide

> Human-followable procedures. No code knowledge required.
> System lives on the Windows PC: `C:\Users\PC\Desktop\KLDAFinTech\KLDA-HFT`

**Last updated:** 2026-07-03

---

## 0. BEFORE LEAVING FOR 15 DAYS (do once, ~10 minutes)

The whole pipeline dies silently if the PC reboots (Windows Update!). Insurance:

1. **Fix Postgres autostart** — open PowerShell **as Administrator**, run:
   ```
   Set-Service postgresql-x64-16 -StartupType Automatic
   Start-Service postgresql-x64-16
   ```
2. **Auto-start the stack at logon** — Task Scheduler → create tasks "At log on":
   - MT5 terminal (`terminal64.exe`)
   - `python KLDA-HFT\python-bridge\mt5_tick_capture_ALL_TICKS.py`
   - `python KLDA-HFT\python-bridge\watchdog.py`
3. **Enable auto-logon after reboot** (or disable automatic Windows Update restarts:
   Settings → Windows Update → Advanced → pause updates for the absence).
4. **Leave the PC on**, sleep disabled (Power settings → Never sleep).

If step 1–3 are skipped: accept that one reboot = data collection stops until return.

---

## 1. DAILY HEALTH CHECK (2 minutes, can be done via phone/RDP)

| Check | How | Healthy looks like |
|---|---|---|
| Feed alive | RDP in → is MT5 open? bridge console scrolling? | ticks scrolling, no red errors |
| Watchdog | `KLDA-HFT\python-bridge\watchdog.log` (last lines) | recent "OK/healthy" lines, no repeated RESTART |
| Backups | `KLDA-HFT\backups\backup.log` | a run at 02:30 last night, "=== backup run" with no ERROR |
| Disk | File Explorer → C: | several GB free |

If feed is dead and watchdog didn't fix it: reboot PC (if §0 done, everything returns alone).

---

## 2. THE SYSTEM AT A GLANCE (what runs, where)

```
MT5 (Pepperstone) → python-bridge (tick capture, 26 symbols)
   → Postgres/TimescaleDB "KLDA-HFT_Database" (ticks, bars, 357M+ rows)
   → research harness (database/backtest_5metric.py + sweeps)
guarded by: watchdog.py (restarts bridge only, surgical)
protected by: nightly backup 02:30 (Task "KLDA-HFT DB Backup" → KLDA-HFT\backups\)
```

**Nothing trades automatically.** Live account 52028179 has ~$7 equity; no validated
signal exists; execution is gated behind: signal passes stats → demo 25k → then live.

---

## 3. WHERE EVERYTHING IS COMMITTED

| What | Where |
|---|---|
| Engine, watchdog, backup system, bridge, harness | github.com/xyVar/KLDAFinTech **master** |
| Doctrine, decisions, research ledger, this runbook | branch **claude/trading-strategy-indicators-B4bOp** (`PROTOCOL.md`, `RUNBOOK.md`) |
| Tick data + backups | PC only: Postgres + `KLDA-HFT\backups\` (never in git) |

---

## 4. DEV STAGES REMAINING (the road ahead)

1. **Data accumulation** ← current stage; runs unattended, needs weeks. Absence = fine.
2. **Widen harness to all 25 symbols** (code exists, ~no new code) — more trades/day.
3. **Conditional patterns** — time-of-day × regime × cross-asset; 4 of 5 patterns unbuilt.
4. **Statistical gate** — a signal must show >50% + costs with real z-score (~20k trades).
5. **Demo deployment** — 25k demo account, 1%/trade, 4+ weeks matching backtest.
6. **Live** — only after 5 passes AND account is funded/enabled. Earliest: late Sep 2026.

## 5. WHAT HAPPENS DURING A 15-DAY ABSENCE

- Machine collects ~15 days × 26 symbols of ticks → roughly doubles the usable dataset.
- Watchdog restarts the bridge on stalls; backups run nightly.
- Nothing trades. Nothing needs approval. No money is at risk.
- On return: run the conditional-split research on the enlarged dataset — that's the
  next research session's first command.

## 6. EMERGENCY CONTACTS / ACTIONS

- Feed dead + watchdog looping: reboot PC once; if still dead, it waits for return — data
  gap, not damage.
- Suspected unauthorized trading on live account: change MT5 master password + contact
  Pepperstone support. (June's MU.US trades were confirmed as the user's own phone trades.)
- Disk full: delete oldest `backups\base_*.dump` files first (keep newest 2).
