# ROADMAP — how KLDA-HFT gets from "infrastructure built" to "company trading live"

> **Status: DRAFT for owner approval (2026-11-11). Not yet part of PROTOCOL.md.**
> Built from a full read of the repo (6 readers; the API, terminal and engine maps were re-checked by skeptics) and
> three independent designs: **validation/risk**, **data/infrastructure**, **company/capital**.
> Full detail of each design: `docs/roadmap_detail/`. Every number marked *proposed* is a default for the owner to confirm.
> Nothing here asserts legal, regulatory or tax facts — those are listed as questions in section 6.

## 1. Where we are today (facts, 2026-11-11)

- **Stage: S0 (Foundation).** The software runs on paper only (`paper_mode: true`). **No pattern has passed the validation gate.**
- **Built:** MT5 tick bridge -> Postgres/TimescaleDB; watchdog; nightly backup; signal generator (1 of the 5 named patterns,
  `MEAN_REVERSION`, BUY only); order router -> paper positions; reconciler; read-only web terminal (port 5002); user/audit/ledger tables.
- **Not built:** the other 4 patterns; any SELL/exit signal; a screen for paper positions; account recording in paper mode;
  NAV computed from broker data; second data source; alerts that reach the owner.
- **The feed has failed three times in 2026** (Mar 12, Sep 9, Nov 10). Each time nothing noticed and nothing restarted it.
  Restored 2026-11-11 14:22 with the watchdog. Ticks from the outages are missing (the bridge drops ticks when the DB is down).
- **Confirmed by reading the code:** a second, uncontrolled signal writer exists (the C++ `live_tracker`, different rule, no duplicate check);
  the terminal's header shows a saved account row from **2026-03-12** with green "ENGINE/MT5" dots that only mean "API answered";
  green symbol dots mean "has a price", not "fresh"; the API listens on all interfaces; there is no change-password feature;
  the signal generator has no data-freshness check.
- **Reported by readers, not yet re-verified by me:** the backtest that "validated" SpotCrude used tick windows while the live rule uses
  5-minute bars; `renaissance_trading_engine.py` and `klda_engine.py` can send real orders without the safety gates if started by mistake;
  paper P&L is `points x lots x 1000` in a column named EUR; position sizing is described four ways and the code uses a fifth (fixed 0.01 lots).

## 2. The stages (gate-based, not date-based)

A stage ends when its **gates** are met and their **evidence files are committed** — never because a date passed.

| Stage | Goal | Headline gates (proposed) | Evidence lives in |
|---|---|---|---|
| **S0 Foundation** *(we are here)* | Make the measuring instruments trustworthy before measuring anything | Old DB password in 0 tracked files (today 72), rotated; API on 127.0.0.1 only; feed coverage >=99% for 14 straight days on the 4 signal symbols; gap census from Mar 9; clock (timebase) proven; one backup restored from an off-machine copy; reconciler makes >=3 SL/TP closes in one run; 0 signals without `pattern_name` (C++ writer retired) | `docs/evidence/s0/`, `KLDA-HFT/reports/audits/` |
| **S1 Research gate** | A pattern earns a PASS from a script on registered, corrected, out-of-sample evidence | Hypothesis registered in git *before* the run; >=100 out-of-sample trades over >=30 clean broker days; lower 90% bound of mean net bps > 0; Holm-adjusted p < 0.05; `is_validated()` re-checks the evidence file hash | `KLDA-HFT/research/hypothesis_log.csv`, `KLDA-HFT/reports/research/` |
| **S2 Paper forward-test** | The frozen pattern runs on paper and matches its backtest numerically | >=30 clean days AND >=100 trades; >=95% rule parity vs replay; median entry delay <=10 s; slippage <=1 median spread; 0 entries while the feed is unhealthy; every row stamped with account, code commit, config version | `KLDA-HFT/reports/paper/`, `docs/evidence/s2/` |
| **S3 Demo (~25k)** | Real MT5 orders on a DEMO account through the unchanged risk layer | >=20 trading days and >=60 trades; <=2% non-DONE results; demo orders 100% matched to broker deals; wrong-account drill refused; kill switch flat in <=60 s; 0 positions after 23:45 broker time | `KLDA-HFT/reports/demo/`, `docs/evidence/s3/` |
| **S4 Pre-live assurance** *(the "protocolled assurance")* | A second party re-derives every number and every failure mode has a control | Independent replication (win rate within 1 pp, same verdict); failure-mode matrix 100% as expected; restore drill reproduces the gate numbers; kill/halt drills twice, >=7 days apart; 0 open high findings; **two-key release** (owner + independent reviewer) | `docs/assurance/<date>/` |
| **S5 KLDA company account** | KLDA Technologies' identity, broker account and capital become real and separate from personal funds | Account registry (`config/accounts.json`); software refuses any non-registered login (2 of 2); funding traced to the company bank account (0 personal transfers); monthly broker-statement vs ledger difference <=0.5% of allocated capital (*proposed*); tamper-evident audit data | `docs/capital/YYYY-MM.md`, `docs/evidence/s5/` |
| **S6 Live ramp** | Smallest real allocation, scaled on conformance — never on profit or loss | Tiers T1 >=20 d/40 trades, T2 +20 d/100 cum., T3 +30 d/200 cum.; each step needs a data-health certificate; loss ladder day 3R / week 6R / drawdown min(10R, 8%) (*proposed*); dead-man's switch (daily acknowledgement) | `KLDA-HFT/reports/live/` |
| **S7 Scale and independence** | More agents/markets without inflating false positives; a second independent price source | Second source agrees within 1 median spread; family-wise error accounting for every promotion; automatic demotion drill; second-operator drill; failover capture <=15 min | `docs/evidence/s7/` |

## 3. Protocols to enable (named, short, testable)

**Cross-cutting (switched on from S0):**
- **FEED-TRUTH / FAIL-CLOSED** — no fresh prices, no signal, no entry. Freshness is judged by the advancing high-water mark, never `NOW() - last_updated` (broker time offset).
- **TIMEBASE** — what `ticks.time` means is measured and written down before any time-of-day research.
- **RECOVERABLE** — only a *rehearsed restore from an off-machine copy* counts as a backup.
- **BOOT-AND-WATCH** — the PC reboots without silently killing the pipeline; alerts reach the owner's phone from outside the PC.
- **LOCAL-ONLY** — API, Postgres and dashboards bind to loopback; no inbound remote access.
- **No Secret In Git** — rotate first, then remove; secrets live in `.env`, which is git-ignored.
- **Account Identity Gate** — `mt5.initialize()` takes no login today, so the terminal's login decides which account trades; a registry plus a per-order check removes that risk. Adds `execution_mode = paper | demo | live`.
- **Change control** — config that can enable real orders changes only through a reviewed PR; paper numbers never feed capital records.
- **Loss ladder and automatic demotion**, **Incident response** (default = flat), **Provenance** (every number reproducible from a manifest), **Capital Truth Ladder** (every ledger/NAV figure ties to a broker document), **Seal, retain, never delete** (audit trail), **Owner-away continuity**.

**Per stage:** Evidence hygiene (S0) -> Pre-registration and lock-box (S1) -> Frozen forward test (S2) -> Demo execution rules (S3) ->
Assurance review / Two-key release (S4) -> Capital movement rule and Monthly close (S5) -> Ramp ladder and dead-man's switch (S6) -> Family-wise accounting (S7).

## 4. How the repo and the context evolve

**Branches.** `master` is the one canonical line. Work happens on short-lived `lane-x/<topic>` branches and reaches `master` only by the owner's merge.
`claude/trading-strategy-indicators-B4bOp` (old Polygon/Express research) and `main` (RateRadar) stay archives and are **never merged into master**.

**New files, created stage by stage (nothing exists yet):**
`docs/DECISIONS.md` (locked decisions with dated changes) · `docs/RISK_POLICY.md` (numbers enforced by code) · `docs/evidence/s0..s7/` ·
`docs/assurance/<date>/` · `docs/capital/YYYY-MM.md` · `docs/incidents/` · `KLDA-HFT/research/hypothesis_log.csv` ·
`KLDA-HFT/reports/{audits,research,paper,demo,live,reconciliation}/` · `KLDA-HFT/config/accounts.json` and `risk_limits.json` · `KLDA-HFT/tests/` (risk-layer tests).

**Context a fresh session reads (so nothing is lost when a conversation ends):** `CLAUDE.md` (hard constraints + a one-line "current stage"),
`docs/PROTOCOL.md` (doctrine, decisions, research ledger — every tested signal gets a row), `docs/RUNBOOK.md` (owner's manual procedures),
this roadmap (stage gates). Rule: if a result is not in the ledger and an evidence file, it did not happen.

**Cloud session vs local session.** The cloud session sees only what is pushed to GitHub; only the local session can touch MT5, Postgres and the PC.
Hand-offs go through committed evidence files, never through memory.

## 5. Decisions needed from the owner (merged from the three designs)

1. **Locked decision D4** says the demo runs "on the VPS first". The stack is local-only. Amend to "on this PC"?
2. **"1% per trade"** — 1% of *what*: allocated capital (recommended, changes only through a ledger event) or live equity? Is it the loss at the stop? Today the code sends a fixed 0.01 lots (no 1%, no Kelly).
3. **The gate.** Keep the locked floor (>=100 trades, >=51%, p<0.05, net>0) and add the S1 requirements on top? Passing gets harder; most candidates may end FAIL.
4. **Universe.** Correct for the full ~26-symbol universe, or restrict the family in advance to the 4 symbols (which were themselves picked after looking at data)?
5. **Maximum total loss** you accept, in currency, and from which funds. (RUNBOOK says the live account holds about $7.)
6. **Whose money:** only KLDA Technologies' / the owner's, or could outside money ever enter? This decides which legal questions apply.
7. **Second reviewer** for S4: who? Substitute if nobody: a fresh AI-session replication plus a 24-hour cool-off.
8. **GitHub:** is `xyVar/KLDAFinTech` private? Who has write access? Branch protection and "only the owner merges to master" as a rule?
9. **Retire the C++ `live_tracker`** (a second signal writer; the dashboards it feeds are mostly stale)?
10. **Alerts and backups:** which phone/email, an external heartbeat ping, off-machine backup medium (external drive / second site / encrypted cloud), a UPS?
11. **Second data source** at S4/S7: (a) a second capture path on the same broker, (b) another broker's demo on this PC, (c) a paid vendor — which, and budget?
12. **Live account 52028179:** record it as "never trade" once the company account exists?
13. **Admin protection** before S5: TOTP, or loopback-only plus the Windows login (written into DECISIONS.md)?

## 6. Questions to put to the broker, a lawyer and an accountant (not answered here)

- **Broker:** corporate-account opening and required documents; funding rules; authorised-trader and succession rules; read-only (investor) password; whether the MT5 Python API is allowed; account type with the same spreads/symbols as the research data; statement and deal-history exports; tick-history depth and data-storage terms; why live account 52028179 is trade-disabled and whether that is lifted.
- **Lawyer:** authorisation/registration duties for trading own money vs accepting outside money; whether "investor / fund / NAV / shares / fees" in the schema imply a regulated activity; retention periods; data-protection duties for investor records; who may sign for the company.
- **Accountant:** classification of owner-to-company transfers; booking of results, fees and financing; tax treatment of CFD gains in the entity; whether internal NAV plus broker statements is enough.

## 7. First actions (S0), in order

1. Feed back and watched (done 2026-11-11; the watchdog still needs auto-start after a reboot).
2. Merge `lane-a/safety-gate` to `master` (router/reconciler fixes, broker-time rule, watchdog in `start_all.bat`) — **owner approves**.
3. Rotate the Postgres password and set a real `JWT_SECRET`; bind the API to 127.0.0.1.
4. "No fresh prices, no signal" gate; bridge buffers and retries failed writes, then backfills the gap from MT5's own tick history where available.
5. Retire the second signal writer; neutralise the legacy executors that can send real orders.
6. Honest terminal: show "as of" times; green only for fresh; a read-only account recorder; a screen for paper positions.
7. Gap census, timebase proof, restore rehearsal — each with an evidence file.
