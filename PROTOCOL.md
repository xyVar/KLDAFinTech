# PROTOCOL — Canonical Project Memory

> This file is the persistent memory of the project's goal and decisions.
> Sessions forget everything else. If it is not written here (or in code), it does not survive.

**Last updated:** 2026-07-02

---

## GOAL — the Medallion doctrine

Build a **fully systematic, agent-per-market trading system** in the spirit of Renaissance
Technologies' Medallion fund: models architected by the human, triggers pulled only by the
machine, zero emotional pollution in execution. Aim is **positive expectancy over many
trades**, never certainty on any single one.

### Context (read this every session)
- The user is recovering a previously lost sum deposited with the broker (Pepperstone).
- **Recovery-trading discipline is mandatory:** position size is driven by the *rules*, never
  by account P&L. The system sizes identically in drawdown and in profit.
- "Medallion" in this project ALWAYS means the Renaissance fund model — systematic,
  emotionless, signal-driven. (Not the data-lakehouse term.)

---

## THE REAL SYSTEM — KLDA-HFT (discovered 2026-07-02)

The production system is **KLDA-HFT** on the user's local Windows machine
(`C:\Users\PC\Desktop\KLDAFinTech\KLDA-HFT`), driven by a **separate local Claude Code
session** that has hands on that machine. THIS sandbox cannot reach it.

**Division of labor between sessions:**
- **Local KLDA-HFT session** = the hands: touches MT5, Postgres, runs backtests/sweeps.
- **This session (repo)** = doctrine + protocol memory: architecture decisions, agent
  specification, honest record of findings.

### KLDA-HFT pipeline (as verified by the local session)
```
MT5 (Pepperstone) → Python bridge (mt5_tick_capture_ALL_TICKS.py, self-healing)
   → TimescaleDB/Postgres (ticks: ~357M rows total; SpotCrude ~14.5M; ~25 symbols)
   → C++ backend (main_live.cpp) + React frontend
trading-engine/ : signal generator, order router, KILL SWITCH, limits enforcer,
                  reconciler, MT5 broker adapter, watchdog, APIs
database/backtest_5metric.py : research harness (spread-unit cost bug FIXED —
                  real cost ≈ $0.03/trade round-trip, not $18)
```

### Known state / risks (2026-07-02)
- **Pepperstone Live 52028179 is trade-disabled at broker (retcode 10017)** — read-only.
  Execution testing must run on DEMO (user rule: demo ~25k first, always).
- Tick capture has GAPS — only ~14 distinct trading days between Mar 9–Apr 30, 2026;
  bridge historically dies silently. Feed was dead ~2 months; being restored.
- Postgres was down; local session restarted it via `pg_ctl` under user account —
  **will NOT survive a reboot** until the Windows service is fixed from an elevated prompt.
- Two Postgres instances observed (source of auth confusion); IPv4 path works.
- **Months of trading-engine code are UNCOMMITTED** on the local machine. Highest
  operational risk in the project. Commit it.

---

## RESEARCH LEDGER — honest record of tested signals

| Date | Signal | Test | Result | Verdict |
|------|--------|------|--------|---------|
| 2026-07-02 | 5-metric mean-reversion entry, SpotCrude | TP0.5%/SL1.0% (asymmetric) | 52.2% win | **Artifact** — asymmetric barriers make coin-flips look like edge |
| 2026-07-02 | same, symmetric 0.5%/0.5% barriers | 26 trades, one afternoon | 34.6% win (p≈0.08) | Too small; hints signal may be **inverted** |
| 2026-07-02 | same — FULL SWEEP, 6 symbols, both directions, symmetric barriers, real spread at entry | 16,478 resolved trades | LONG 40.0% (z=−18.0), SHORT 39.9% (z=−18.4) — both directions lose identically | **Structural, not signal:** spread-drag. Median barrier 0.014% of price; spread eats ~10pts of win rate each side |

### Structural doctrine established 2026-07-02 (from the sweep)
1. **Tick horizon is BANNED** on retail CFD costs — spread-dominated, unwinnable for any
   signal. (Renaissance plays tick-scale on institutional costs; we cannot.)
2. **Spread-floor rule:** any tradable pattern must have a profit target that is a large
   multiple of the spread (minute-scale and up). Cost model must use real spread at entry.
3. **"Inverted signal" hypothesis is dead** — both directions losing equally proves the
   loss is cost-drag, not mispolarity. Do not resurrect the fade.
4. **Sample-size wall:** detecting a ~1% edge needs ~20,000 trades; we had 869 at the
   workable scale. Bottleneck = days of continuous feed, not code. Feed uptime is the
   research program.
5. **Next hypotheses (being built by local session):** conditional edges — time-of-day ×
   regime (trend/range) × cross-asset confirmation, swept across all 25 symbols. The naive
   "price stretched → trade" versions are dead by measurement; 4 of 5 planned patterns
   remain unbuilt/untested.

**Reading key for the sweep (decision gate):**
- Win rate **> 50% with decent z-score** on hundreds of trades → real edge → promote toward demo.
- Win rate **≈ 50%** → entry rule has no predictive power → rework threshold/regime filter.
- Win rate **persistently ≪ 50%** (e.g. ~35%) across symbols → signal is *inverted* →
  test the faded (opposite) entry as its own hypothesis; it must then clear the same gate.

Doctrine note: most signals SHOULD die here. Renaissance rejected the overwhelming majority
of hypotheses; the machine rejecting them (not a hopeful human keeping them) IS the edge.

---

## AGENT-PER-MARKET ARCHITECTURE (target design)

- **One agent per symbol** = one signal-model instance with its OWN fitted parameters
  (crude's thresholds ≠ gold's ≠ NAS100's — microstructure differs).
- **One shared risk spine** — kill switch, limits enforcer, reconciler (already built in
  trading-engine/). Agents PROPOSE; only the risk layer touches the account.
- **Promotion pipeline per agent:** backtest gate → demo (25k) → live allocation.
  Agents that stop clearing the gate are demoted automatically. No grandfathering.
- Risk: **1% per trade**, fixed fractional, P&L-independent (locked decision).

## DECISIONS (locked)

| # | Decision | Choice |
|---|----------|--------|
| 1 | Universe | Everything, ranked — the data/score decides, no hand-picked basket |
| 2 | Path | Validate edge first — no real money on unproven signals |
| 3 | Risk | 1% per trade, fixed fractional, hard-coded |
| 4 | Deployment | Demo account (~25k) on the VPS first; live only after demo proves out |
| 5 | Doctrine | Medallion model: human architects, machine executes; no manual triggers |

---

## LEGACY / PARKED
- `TRADING_STRATEGY_SPEC.md` — early VIX-checkpoint intraday idea (3am/6am/10am +1/+2/+3%).
  Parked, not blessed; needs intraday VIX data to validate. May return as one agent's signal.
- `edge_validation.py` — daily cross-sectional ranking harness for the old Polygon daily DB.
  Superseded by KLDA-HFT's tick-level harness, kept as reference.
- KLDAFinTech (this repo): Polygon→Postgres daily-data platform + Flask/Express API.
  Research-era infrastructure; the live system is KLDA-HFT.
