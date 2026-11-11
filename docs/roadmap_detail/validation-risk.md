# Roadmap detail — validation-risk lens

> DRAFT, 2026-11-11. One of three independent designs behind `docs/ROADMAP.md`. Numbers marked 'proposed' need owner confirmation. Legal/regulatory/tax items are questions, not facts.

## S0

Make the measuring instruments trustworthy BEFORE anything is measured: one written definition of 'validated', no evidence contamination (second signal writer, broken paper exits, fake-EUR P&L), pinned meaning of tick timestamps, evidence files that git will actually keep, and an inventory of the barriers that keep real money out. No strategy claims are made in S0.

**Entry criteria**
- Branch lane-a/safety-gate is the one deployed branch (verified: master lacks docs/PROTOCOL.md, docs/RUNBOOK.md and config/validated_patterns.json; it only has config/trading_config.json).
- config/trading_config.json:3 paper_mode=true and config/validated_patterns.json:14 'validated': {} (no real-money path open).
- The owner agrees evidence windows are declared in advance (a start date written in docs/PROTOCOL.md).

**Work**
- Write ONE gate definition in docs/PROTOCOL.md. CLAUDE.md:13 says >=100 / >=51% / p<0.05; trading-engine/config_loader.py:26-28,81-84 also requires net_pnl_pct>0. The code version is the floor; S1 additions sit on top.
- Switch off the second signal writer during evidence windows: Docker container klda-hft-cpp-backend (start_all.bat:25) inserts PENDING BUY rows with no pattern_name (cpp-backend/src/main_live.cpp:261,326) and order_router.py:47-55 consumes ANY PENDING row; in paper mode there is no pattern filter (order_router.py:80).
- Fix harness defects that falsify paper results, then prove the fix: broker_adapter_mt5.py:83 calls mt5.shutdown() inside close_paper_position, so the reconciler process likely loses MT5 and reconciler.py:67-69 silently skips every later SL/TP check (code reading, not run); reconciler.py:76,80 format pnl with '+' and raise on a failed close; no signal expiry; stale current.ask used as the fill when MT5 is down (broker_adapter_mt5.py:97-108); mark_signal drops its notes argument (order_router.py:58-63) so reject reasons are not stored.
- Retire pnl_eur as evidence: broker_adapter_mt5.py:198 is pnl_points*lots*1000, with no contract size or currency. Evidence uses (exit_price-entry_price)/entry_price in bps from the stored paper_positions columns.
- Pin what ticks.time means with a 20-tick spot test against MT5 and write the rule in docs/RUNBOOK.md. Day-blocks, clean-day counts and the 'broker day' all depend on it (limits_enforcer.py:57 and reconciler.py:119 still use the PC's date.today(), against CLAUDE.md).
- Build the clean-day ledger: per symbol and broker day, tick count, first/last tick, max gap. Proposed clean day: no gap over 300 s inside the symbol's active hours and tick count at least 50% of that symbol's median day. PROTOCOL.md:51 admits only ~14 distinct trading days between Mar 9 and Apr 30.
- Make evidence keepable: .gitignore:11-12 ignore *.log and *.txt, so signal_generator.py:327 daily_*.txt reports and health_*.txt never reach git. Write evidence as .json/.csv/.md under KLDA-HFT/reports/{research,paper,audits,demo}/.
- Create a read-only Postgres role for research and backtests (truncate_ticks.py:13 runs TRUNCATE ticks and fix_ticks.py:22 drops all chunks, both with the shared superuser).
- Write the real-money barrier inventory in docs/RUNBOOK.md: (1) paper_mode, (2) empty allowlist, (3) the broker trade-block on 52028179 (PROTOCOL.md:49 says disabled, :75 says 'appears lifted': unresolved), (4) MT5 Algo Trading switch OFF whenever the terminal is on a non-demo account (verify its effect on demo first). Rule: at least two barriers verified by a test, not by reading.

**Risks**
- start_all.bat:25 restarts the C++ container with 'docker start', so contamination can return silently; the router pattern filter is the backstop.
- Fixing the reconciler changes behaviour mid-stream, so all earlier paper rows are void for evidence (hence evidence_start).
- If ticks.time turns out to be shifted by hours, every earlier day-block statistic must be recomputed.
- Some of these defects are read from code, not observed; the harness acceptance test may show they are smaller or larger than described.

**Exit gates**

| Metric | Threshold | Evidence artifact |
|---|---|---|
| Consecutive SL/TP closes made by ONE reconciler process with no restart and no skipped check | >= 3 | `KLDA-HFT/reports/audits/harness_acceptance_<date>.md` |
| Signals consumed by order_router in the last 7 days whose pattern_name is NULL or not MEAN_REVERSION | 0 | `KLDA-HFT/reports/audits/harness_acceptance_<date>.md` |
| Tick-time spot test: |ticks.time - MT5 tick time under the documented rule| | 0 s on 20 of 20 sampled ticks | `KLDA-HFT/reports/audits/time_semantics_<date>.md` |
| Clean-day ledger coverage for the 4 symbols in signal_generator.SYMBOLS | 100% of captured broker days listed, per symbol | `KLDA-HFT/reports/research/data_days.csv` |
| Evidence files ignored by git (git check-ignore on sample .json, .csv, .md under reports/) | no match | `KLDA-HFT/reports/audits/harness_acceptance_<date>.md` |
| Differences between the gate numbers in CLAUDE.md, docs/PROTOCOL.md and config_loader.py | 0 | `docs/PROTOCOL.md section GATE` |
| Research role attempts INSERT/TRUNCATE on ticks | permission denied | `KLDA-HFT/reports/audits/harness_acceptance_<date>.md` |
| Real-money barriers shown in force by test | >= 2 | `docs/RUNBOOK.md section BARRIERS (dated)` |

**Protocol — Evidence hygiene**
- Evidence is script output plus a git commit, never a chat statement.
- Every evidence file records data window, row counts per symbol-day, config_hash, git commit and script path.
- pnl_eur is never quoted; results are bps of price.
- Contamination sources (C++ signal writer, MANUAL_TEST rows) are off or excluded and listed.
- Evidence is written as .json, .csv or .md only.
- Rows from before the declared evidence_start date never count.

**Protocol — Barrier inventory**
- Real-money barriers are written down with the test that proves each one.
- At least two stay in force at all times.
- Before removing a barrier, its replacement must be tested.
- A barrier that exists only in a config file counts as one barrier, not two.

**Repo changes**
- `KLDA-HFT/trading-engine/broker_adapter_mt5.py` — Stop shutting MT5 down inside _get_current_price (:83) or let callers re-initialize; refuse fills whose price source is older than 5 s and record fill_age_s; keep pnl_points but stop labelling pnl_eur as money.
- `KLDA-HFT/trading-engine/reconciler.py` — Re-initialize MT5 every cycle; guard the '+' formatting at :76,:80 against failed closes; use broker date instead of date.today() at :119.
- `KLDA-HFT/trading-engine/order_router.py` — Consume only PENDING rows whose pattern_name is in the registered set; mark rows older than 60 s EXPIRED; store the reject reason (mark_signal ignores notes at :58-63).
- `KLDA-HFT/database/migrations/001_validation_columns.sql` — New. ALTER ... ADD COLUMN IF NOT EXISTS: signals.config_hash, signals.reason; paper_positions.config_hash, signal_price, fill_age_s. CREATE TABLE data_day_quality. Check against the live DB first: the live signals DDL is not in the repo.
- `KLDA-HFT/database/build_data_days.py` — New. Builds the clean-day ledger from ticks using the read-only role.
- `.gitignore` — Add explicit negations for KLDA-HFT/reports/research|paper|audits|demo/ so evidence is never silently ignored.
- `KLDA-HFT/tests/test_risk_spine.py` — New. First tests in the repo (CLAUDE.md says there is no suite): kill flag blocks, gate refuses unlisted symbol, position and lot limits.

**Context updates**
- `CLAUDE.md` — Correct the stale 'backtest_5metric.py spread-as-dollars bug' line: the code converts points at backtest_5metric.py:85-86 and charges no double spread (:112-115), and PROTOCOL.md:44 says FIXED. Point to KLDA-HFT/reports/{research,paper,audits}/ for evidence and say .txt is gitignored.
- `docs/PROTOCOL.md` — Add section GATE (single definition). Add the 2026-07-17 SpotCrude row to the ledger: 58.4% on 243 trades is below the 66.7% break-even of 0.5/1.0, and p=0.005 is against a 50% null. Mark the :56 'UNCOMMITTED' risk resolved (commit 1b295d0, :70). Record evidence_start.
- `docs/RUNBOOK.md` — Fix :64 (these docs live on lane-a/safety-gate, not master). Add BARRIERS and 'evidence windows: stop the cpp-backend container' sections.

## S1

A candidate (pattern x symbol x parameters x exit geometry) earns a PASS from a script on registered, multiplicity-corrected, out-of-sample, cost-stressed, placebo-beaten, rule-parity-checked evidence. FAIL and INCONCLUSIVE are first-class outcomes; most candidates should die (PROTOCOL.md:103).

**Entry criteria**
- All S0 exit gates met.
- The candidate is registered as a row in KLDA-HFT/research/hypothesis_log.csv in a git commit made BEFORE the run.
- data_days.csv shows the clean-day count per candidate symbol, and the lock-box window is written in the registration.

**Work**
- Backfill hypothesis_log.csv with everything already run; all of it counts toward the family size m: the 2026-07-02 asymmetric and symmetric SpotCrude tests, the 6-symbol x 2-direction sweep (16,478 trades), the 1-minute z-score sweep (869 trades), the 2026-07-17 SpotCrude run, backtest_exit_geometry.py (4 geometries x 2 stop variants = 8 looks), optimize_spotcrude.py grids (4+3+4 window values at :36,:58,:82), and the 12 symbols screened on this signal (4 kept, 8 removed: signal_generator.py:46-53).
- Make the backtest the live rule. They differ today: backtest_5metric.py:69,93-98 uses 50/100/200 TICK windows, 'regime != BEARISH' and no cost condition; signal_generator.py:109-146,170 uses 50/100 M5-BAR windows from cagg_bars_m5, regime in regime_allow, a tx-cost condition and a Kelly boolean. One shared rule module, imported by both.
- Model system latency in the backtest: enter at the first tick >= signal time + 15 s (signal loop 10 s, signal_generator.py:59; router poll 5 s, order_router.py:36); exit SL/TP at the first tick >= crossing time + 30 s at that tick's bid (reconciler poll 30 s, reconciler.py:30; exit at the current tick, broker_adapter_mt5.py:192), not at the exact level (backtest_5metric.py:144,161). Apply trading_config.json:11-14 (no entries from 23:30, close all at 23:45 broker time).
- Split by clean broker days: design window, 1-day embargo, validation window, lock-box. For SpotCrude every day up to 2026-07-17 is burned by sweeps (trading_config.json:30); the lock-box is data captured after that date, if data_days.csv shows it clean.
- Test statistic: net bps per trade after spread (ask in, bid out), aggregated by broker day, 90% CI by day-block bootstrap (>=5,000 resamples). Holm-adjust p across every row of the family. Benjamini-Hochberg q=0.10 may only shortlist candidates for the lock-box.
- Placebo: >=1,000 random-entry runs on the same days, matched on time-of-day and trade count, with identical exit, latency and cost. The candidate must sit above the 95th percentile.
- Cost stress at 1.5x and 2.0x spread and +0.5x spread adverse slippage per side. Spread-floor check: median TP distance >= 10x median round-trip spread (k=10 proposed; PROTOCOL.md:84 says only 'large multiple'). Commission stays 0 only if verified for the account type (verify_externally).
- validate_candidate.py writes the evidence JSON and exits 0/1/2 for PASS/FAIL/INCONCLUSIVE. On PASS a human adds a 'candidates' entry (stage PAPER) to validated_patterns.json. The live-only 'validated' block stays empty.
- Report the sample size needed for 80% power at the observed effect, n = ((z_a+z_b)*s/e)^2. If the feed cannot deliver that in 90 trading days the verdict is INCONCLUSIVE. Derived reference: 51% vs 50% win rate needs ~15,400 trades, 55% ~615, 60% ~152 (one-sided alpha 0.05, power 0.8); this matches PROTOCOL.md:89 (~20k trades).
- Log every FAIL in the ledger with the same fields as a PASS.

**Risks**
- Most likely outcome is FAIL or INCONCLUSIVE for every candidate (PROTOCOL.md:89; ~14 clean days in Mar-Apr). Do not lower thresholds; extend feed uptime or move to a longer horizon.
- Ticks after 2026-07-17 may be gappy (PC reboots, a 15-day absence), so the lock-box may be too small.
- The exit-geometry sweep results were never stored, so those 8 looks can only be counted, not audited.
- Parity may show the live rule fires rarely or never: cagg_bars_m5 materializes up to 5 min behind (create_continuous_aggregates_universal.sql:116-119); whether real-time aggregation is on is not in the repo (unverified).
- Reading both p-values correctly may show the SpotCrude entry has no edge at all; that is a valid result.

**Exit gates**

| Metric | Threshold | Evidence artifact |
|---|---|---|
| Registration precedes run | 100% of rows used by the candidate have a git commit earlier than the evidence file | `KLDA-HFT/research/hypothesis_log.csv + git log` |
| Pooled out-of-sample trades (validation + lock-box) | >= 100 trades AND >= 30 clean broker days | `KLDA-HFT/reports/research/<pattern>_<symbol>_<date>.json` |
| Mean net bps per trade, lower 90% day-block bootstrap bound (spread inside prices, latency modelled) | > 0 | `KLDA-HFT/reports/research/<pattern>_<symbol>_<date>.json` |
| Holm-adjusted p across the family (m printed with it) | < 0.05 | `KLDA-HFT/reports/research/<pattern>_<symbol>_<date>.json` |
| Lock-box: run exactly once; net bps and win rate vs the placebo or geometry null | net bps > 0 and win rate >= null | `hypothesis_log.csv column lockbox_run_date + the evidence JSON` |
| Placebo percentile of the candidate's mean net bps | >= 95 | `KLDA-HFT/reports/research/<pattern>_<symbol>_<date>.json` |
| Net bps at 2.0x spread | > 0 | `KLDA-HFT/reports/research/<pattern>_<symbol>_<date>.json` |
| Spread-floor ratio (median TP distance / median round-trip spread) | >= 10 (proposed k) | `KLDA-HFT/reports/research/<pattern>_<symbol>_<date>.json` |
| Rule parity on 10 sampled clean days: signals from live code vs backtest code | >= 95% matched within +/-1 M5 bar in both directions; trade count within +/-10% | `KLDA-HFT/reports/research/parity_<id>_<date>.json` |
| Existing floors still true (config_loader.py:26-28,81-84) | >=100 trades, win rate >=0.51, p<0.05, net_pnl_pct>0 | `candidates entry in KLDA-HFT/config/validated_patterns.json` |

**Protocol — Pre-registration and lock-box**
- No run without a committed row in hypothesis_log.csv: symbols, every parameter value, exit geometry, windows, statistic, null, alpha.
- Rows are append-only. Failed and abandoned runs stay in the log and in m.
- Lock-box days are excluded from every design query (scripts take --max-date). The lock-box is run once per candidate.
- A burned lock-box cannot judge a re-parameterised version of the same pattern; wait for fresh data.
- Anything not in the registration is exploratory and cannot enter candidates or validated.

**Protocol — Honest test**
- Null = random-entry placebo with identical exit, latency and cost. The geometry null SL/(TP+SL) is allowed only for pure TP/SL with no time stop. Never 50% unless TP equals SL.
- Never derive the null from the sample's own average win and loss (backtest_exit_geometry.py:156 does; that restates 'net>0' and is not an edge test).
- Win rate is descriptive. The gate is net bps with a CI.
- Trades overlap and cluster: resample by broker day, never by trade.
- Print m, raw p and Holm p together. Derived references: Bonferroni threshold 0.0019 for m=26 and 0.00038 for m=130; uncorrected chance of at least one false pass at 0.05 is about 74% for m=26.
- INCONCLUSIVE never promotes.

**Protocol — Rule parity and cost realism**
- One rule module; signal_generator.py and the backtest import it.
- Backtest latency equals system latency (15 s in, 30 s out) until measured values replace it in a new registration.
- The parity run is inside the gate script, not a manual step.
- A condition that cannot fail (kelly_ok is constant true under default config, signal_generator.py:139-146, so confidence is always 100) is reported 'inactive' and not counted.
- Per-symbol contract facts come from MT5 symbol_info into a table, not from constants (backtest_5metric.py:20 hard-codes SpotCrude's point size).

**Repo changes**
- `KLDA-HFT/research/hypothesis_log.csv` — New, append-only. Columns: id, date, author, pattern, symbols, parameter values, exit geometry, windows, statistic, null, alpha, commit_at_registration, lockbox_run_date, result_path, verdict.
- `KLDA-HFT/research/strategy_rule.py` — New. Single mean-reversion rule; signal_generator.calculate_metrics (:74-171) and the validator import it.
- `KLDA-HFT/research/validate_candidate.py` — New. Walk-forward, lock-box, Holm, day-block bootstrap, placebo, cost stress, parity. Writes the evidence JSON and exit code 0/1/2.
- `KLDA-HFT/database/backtest_5metric.py` — Mark as legacy in its header; stop quoting its p-value as the gate.
- `KLDA-HFT/config/validated_patterns.json` — Add a 'candidates' block (stage, hypothesis_id, evidence path, evidence sha256, config_hash). 'validated' stays live-only and empty.
- `KLDA-HFT/trading-engine/config_loader.py` — is_validated (:65-89) also requires the evidence file to exist and match its sha256 and 'expires' not to be past. Add is_cleared(symbol, pattern, mode).
- `KLDA-HFT/database/migrations/002_symbol_specs.sql` — New table symbol_specs (point, contract size, currency, volume min/step) filled from MT5 symbol_info.

**Context updates**
- `CLAUDE.md` — Add: before proposing a signal read research/hypothesis_log.csv; a result without a registered row is exploratory. Replace the 'validated' definition with a pointer to PROTOCOL.md GATE.
- `docs/PROTOCOL.md` — Ledger columns: id, date, signal, data window, script@commit, n, win rate, mean net bps, CI, m, p_raw, p_holm, verdict, evidence path. Add the backfilled rows.
- `docs/RUNBOOK.md` — How to read a verdict: PASS (log it; the owner takes no action), FAIL (logged; nothing to do), INCONCLUSIVE (wait for data; do not edit thresholds).

## S2

The frozen candidate runs on paper. 'Matches the backtest' becomes numeric: mechanics, rule parity, costs, statistics, and a risk-spine dry run. Paper can prove the machinery works and add genuine out-of-sample days. At N around 100 it cannot prove an edge on its own, so the mechanical checks carry most of the weight.

**Entry criteria**
- S1 PASS evidence JSON, and a 'candidates' entry (stage PAPER) in validated_patterns.json.
- git tag freeze-<pattern>-<symbol>-<date>; signal_generator, order_router and reconciler all log the same config_hash and git hash at startup.
- Contamination off (S0 gates) and harness acceptance green within the last 7 days.
- SPRT boundaries, minimum counts and exclusion rules written into the registration before the first paper trade.

**Work**
- The clock starts only when the three processes print identical config_hash. Any edit to thresholds, symbols, exits or rule code restarts the clock and needs a new registration.
- Daily paper_report.py writes .csv/.md: n trades; entry delay (signals.time to paper_positions.opened_at); entry slippage vs signals.price in bps and in spreads; exit timeliness vs the first crossing tick in the ticks table; net bps from stored entry/exit prices; cost per trade vs the backtest model; win rate; excluded trades with reason.
- Nightly parity_replay.py re-runs the shared rule over that day's ticks and diffs the result against the signals table (matched / missing / extra).
- Sequential decision (SPRT) on daily net bps: H0 mu=0, H1 mu=lower-90% bound of the S1 OOS result, alpha 0.05, beta 0.20, sigma from the lock-box. Accept boundary ln(16)=+2.77, stop boundary ln(0.2/0.95)=-1.56 (derived). Printed daily as CONTINUE / ACCEPT / STOP.
- Dry-run the S3 loss ladder on paper P&L in R units (R = stop distance): log 'would have halted' events; run the synthetic day in tests/test_risk_spine.py (3 stop-outs triggers the halt).
- Build research/mc_drawdown.py: bootstrap-resample the validated trade sequence to get the max-drawdown distribution for 50, 100 and 200 trades. WATCH/SUSPEND thresholds and the tier risk ceiling come from it, not from guesses.
- Pooled OOS: lock-box plus paper days through the same validate_candidate.py statistic.
- Log every day excluded by the clean-day rule; excluded days do not count toward the 30.

**Risks**
- Trade rate may make 100 trades take much longer than 30 days; the gate stays 'later of the two'. Do not shorten it.
- The 30 s reconciler poll can make exit slippage exceed the model. If exit timeliness fails, fix the harness, not the threshold.
- SPRT assumes roughly Gaussian daily returns; news days have fat tails, so the CI and the best-day concentration check are the backstop.
- Paper days must never be used for tuning, or they stop being out-of-sample.

**Exit gates**

| Metric | Threshold | Evidence artifact |
|---|---|---|
| Sample: clean trading days AND closed trades per symbol-pattern | >= 30 days AND >= 100 trades (the later of the two) | `KLDA-HFT/reports/paper/paper_report_<date>.csv` |
| Rule parity: share of live signals matched by shared-rule replay (and the reverse), per audited day | >= 95% on every audited day | `KLDA-HFT/reports/paper/parity_<date>.json` |
| Entry delay signals.time to opened_at | median <= 10 s, p95 <= 30 s | `KLDA-HFT/reports/paper/paper_report_<date>.csv` |
| Entry slippage |fill - signals.price| | <= 1 median spread on >= 95% of fills | `KLDA-HFT/reports/paper/paper_report_<date>.csv` |
| Exit timeliness: SL/TP closes within 60 s of the first crossing tick; missed exits; positions open past close_all_at + 5 min | >= 95% within 60 s; 0 missed; 0 past cutoff | `KLDA-HFT/reports/audits/harness_acceptance_<date>.md (weekly)` |
| Realized cost per trade (entry ask minus exit bid) vs backtest model on the same trades | within +/-20% | `KLDA-HFT/reports/paper/paper_report_<date>.csv` |
| SPRT decision AND pooled OOS lower-90% mean net bps | ACCEPT and > 0 | `KLDA-HFT/reports/paper/sprt_<date>.json` |
| Forward trades/day vs replay trades/day | between 0.5x and 2x | `KLDA-HFT/reports/paper/paper_report_<date>.csv` |
| Share of total net bps from the best single day | <= 30% (proposed) | `KLDA-HFT/reports/paper/paper_report_<date>.csv` |
| Signals consumed with unregistered pattern_name; risk-spine dry-run | 0 consumed; all tests pass | `KLDA-HFT/reports/audits/harness_acceptance_<date>.md + tests/test_risk_spine.py output` |

**Protocol — Frozen forward test**
- Freeze = git tag plus config_hash stored on every signal and paper_positions row. Rows with another hash are excluded.
- No edits to thresholds, symbols, exits or the C++ writer during the clock. Any edit restarts it under a new registration.
- Paper results are quoted in bps of price. pnl_eur is never quoted.
- No manual signals. MANUAL_TEST rows are excluded and listed.
- Interim judgement only through the SPRT; no ad-hoc 'looks good'.
- STOP retires this parameter set; it can return only as a new registration.

**Protocol — Weekly harness audit**
- Query positions whose bid/ask crossed sl/tp (from ticks) but closed late or not at all.
- Query OPEN positions older than the broker day.
- Query signals stuck in EXECUTING over 10 min (order_router.py:107 sets it, and has_pending_signal at signal_generator.py:174-179 counts it, so a stuck row silences that symbol): mark FAILED and log.
- Check that all three engine processes were alive every hour.
- Any failure voids the days since the last green audit for evidence.

**Repo changes**
- `KLDA-HFT/monitoring/paper_report.py` — New. Daily .csv/.md report with the metrics above, bps units, exclusions listed.
- `KLDA-HFT/research/parity_replay.py` — New. Nightly replay of the shared rule over the day's ticks; diff vs signals.
- `KLDA-HFT/research/sprt.py` — New. Sequential test with boundaries read from the registration.
- `KLDA-HFT/research/mc_drawdown.py` — New. Bootstrap max-drawdown distribution by trade count.
- `KLDA-HFT/trading-engine/build_info.py` — New. Prints and returns git short hash plus config_hash (sha256 of canonical trading_config.json + validated_patterns.json); imported at startup by signal_generator, order_router and reconciler.
- `KLDA-HFT/trading-engine/signal_generator.py` — Write config_hash on each signal; do not write a new signal while a paper position is open for the symbol (today it writes one every ~10 s that the router REJECTs as already_in).
- `KLDA-HFT/reports/paper/` — New folder for daily outputs.

**Context updates**
- `docs/PROTOCOL.md` — Add 'Paper forward-test': the five numeric checks, SPRT constants, freeze tag, evidence_start.
- `docs/RUNBOOK.md` — Daily owner check = read reports/paper/paper_report_<date>.md and note three lines: parity %, harness audit green/red, SPRT decision. On red: stop the router; do not edit config.
- `CLAUDE.md` — Warn: paper pnl_eur is not money; evidence is in bps.

## S3

Real MT5 order_send on a DEMO account (~25k) through the unchanged risk spine and the real sizing code. It measures what paper cannot: slippage, rejections, latency, broker-side stops, DB-vs-broker position agreement. Demo proves plumbing and an optimistic cost bound, not real-money fills (docs/DEMO_ACCOUNT.md:88-90). Needs an owner decision (question 2).

**Entry criteria**
- All S2 exit gates met.
- Demo account recorded in config/accounts.json: login, server, trade_mode DEMO, currency, leverage, hedging or netting. docs/DEMO_ACCOUNT.md:32-34 still says 'To be verified' and no ~25k account number is recorded anywhere.
- execution_mode (paper|demo|live) and the per-order identity guard implemented and reviewed.
- Live-path gaps closed: EOD close of MT5 positions (reconciler.py:159-161 does not do it), fill recording, kill-switch fixes, real loss ladder.
- Owner has answered questions 1-3.

**Work**
- Identity guard before EVERY order: mt5.account_info().login equals accounts.json and trade_mode equals DEMO (hourly_health_check.py:277 already reads trade_mode); otherwise refuse and log P1. Today mt5.initialize() takes no login (broker_adapter_mt5.py:149), so paper_mode=false would trade whatever account the terminal holds.
- executions table: signal_id, requested and fill price/time, retcode, order and position ticket, deviation, latency ms, spread at send, tick age. broker_adapter_mt5.py:170-172 returns the fill only as a dict.
- Sizing: risk = tier ceiling x equity / stop distance, using symbol_info and mt5.order_calc_profit; refuse, never round up, when the minimum lot already exceeds the ceiling. This replaces the fixed 0.01 lot (limits_enforcer.py:196-201).
- Reconciler manages MT5 positions: close at close_all_at, filter by magic 234000, heartbeat rows. guardian flattens and halts if the reconciler or router heartbeat is older than 120 s while positions are open.
- Implement the loss-limit ladder (cross-cutting protocol) from MT5 equity on the broker day. Replace limits_enforcer.py:27 (EUR 10), :66-68 (allows when no snapshot exists), :166-167 (kill flag fails open), :180 (paper skips the check). All fail CLOSED.
- Kill switch: filter by magic (kill_switch.py:63 closes every MT5 position), also close paper rows, make signal_generator read the flag, and let guardian call it on L4/L5.
- Drills on demo: kill switch with an open position; halt by lowering the daily limit; DB down during an open position; terminal logged into a wrong account.
- Weekly demo_report: slippage, rejects and latency vs the paper baseline for the same signals.

**Risks**
- First-ever execution of broker_adapter_mt5.py:142-176; IOC filling may be rejected on some symbols, so expect retcode rejections that are not strategy failures.
- Demo account type (hedging, DEMO_ACCOUNT.md:6) may differ from the company account (netting vs hedging unverified).
- A PC reboot with an open demo position leaves only broker-side SL/TP; record it as a defect, not as a pass.
- Demo expiry and balance-reset rules are unknown (verify with the broker).

**Exit gates**

| Metric | Threshold | Evidence artifact |
|---|---|---|
| Duration and sample (stricter of RUNBOOK.md:75 '4+ weeks' and DEMO_ACCOUNT.md:20 '2 weeks') | >= 20 trading days AND >= 60 executed trades | `KLDA-HFT/reports/demo/demo_report_<date>.md` |
| Non-DONE order results, excluding deliberate risk-gate rejects | <= 2% of attempts; every one with its retcode | `executions table export KLDA-HFT/reports/demo/executions_<date>.csv` |
| Entry slippage in median spreads | median <= 1.0, p95 <= 3.0, and demo median <= paper median + 0.5 | `KLDA-HFT/reports/demo/demo_report_<date>.md` |
| Signal-to-fill latency; order_send call time | p95 <= 20 s; p95 <= 2 s | `KLDA-HFT/reports/demo/demo_report_<date>.md` |
| DB open positions vs MT5 positions_get (magic 234000), checked every 60 s | 0 mismatches over 120 s; 0 orphans; 0 positions past close_all_at + 5 min | `KLDA-HFT/reports/audits/reconcile_<date>.csv` |
| Realized risk at stop / equity at entry | never above the ceiling; within 0.1 pp of it on >= 95% of trades | `KLDA-HFT/reports/demo/demo_report_<date>.md` |
| Identity guard: orders accepted with the terminal on a non-registered account | 0 of >= 10 attempts | `docs/incidents/drill_identity_<date>.md` |
| Kill-switch drill: time until positions_get is empty | <= 60 s on 2 passes | `docs/incidents/drill_kill_<date>.md` |
| Halt drill (limit lowered to trip on demo) | new entries blocked within one cycle; book flat | `docs/incidents/drill_halt_<date>.md` |
| Paper net bps minus demo net bps on the same rule | <= 1 median spread | `KLDA-HFT/reports/demo/demo_report_<date>.md` |
| Pooled evidence (lock-box + paper + demo) lower-90% net bps | > 0 | `KLDA-HFT/reports/demo/pooled_<date>.json` |

**Protocol — Demo execution rules**
- execution_mode 'demo' can only address an account whose trade_mode is DEMO and whose login equals accounts.json.
- paper_mode stays true in the real-money sense: no code path reaches a REAL account.
- Every order carries broker-side SL and TP in the request (broker_adapter_mt5.py:159-160); an order without them is refused.
- Every sent order is written to executions before the router marks the signal FILLED.
- Sizing never rounds up past the ceiling.
- A 'candidates' entry at stage DEMO is required; the empty 'validated' block stays empty.

**Repo changes**
- `KLDA-HFT/config/trading_config.json` — Add execution_mode: paper|demo|live. paper_mode keeps meaning 'no real-money orders'.
- `KLDA-HFT/config/accounts.json` — New. Registry: login, server, trade_mode, currency, leverage, account type, status. Single source of truth for account facts.
- `KLDA-HFT/config/risk_limits.json` — New. Ladder values in R, tier ceilings, correlation groups. Replaces constants at limits_enforcer.py:27-33.
- `KLDA-HFT/trading-engine/broker_adapter_mt5.py` — Identity guard before order_send; executions insert; keep the MT5 session alive; demo branch separate from live.
- `KLDA-HFT/trading-engine/limits_enforcer.py` — Sizing from equity and stop distance; fail-closed checks; broker-day boundaries via config_loader.broker_now; read risk_limits.json.
- `KLDA-HFT/trading-engine/reconciler.py` — Close MT5 positions at close_all_at (magic filter); write heartbeats.
- `KLDA-HFT/trading-engine/kill_switch.py` — Magic filter at :63; close paper rows; fail-closed flag read; callable from guardian.
- `KLDA-HFT/trading-engine/guardian.py` — New. Per-strategy state machine, heartbeat watcher, ladder enforcement; writes strategy_status.
- `KLDA-HFT/database/migrations/003_executions_heartbeats.sql` — New tables executions, heartbeats, strategy_status.
- `KLDA-HFT/monitoring/demo_report.py` — New. Weekly demo report.

**Context updates**
- `CLAUDE.md` — Replace 'Keep paper_mode: true until an entry there is earned' with the three execution modes and the accounts.json identity rule. Add 'demo fills are optimistic'.
- `docs/PROTOCOL.md` — Amend decision #4 (VPS to local PC) only if the owner agrees. Add the demo stage and its gates.
- `docs/RUNBOOK.md` — Exact commands: python kill_switch.py --reason "<text>" and --clear; the drill procedure; what each router and reconciler log line means.

## S4

Independent re-derivation and failure testing before any real capital: a second party (fresh AI session and/or a human) reproduces every number from raw evidence, and each way the system could lose money unnoticed has a control with a test that can fail.

**Entry criteria**
- All S3 exit gates met; 0 open P1/P2 defects.
- Evidence pack folder docs/assurance/<date>/ created with the registration row, git tag, data manifest and scripts.
- Reviewer named (question 7).

**Work**
- Clean-room replication: the reviewer receives only the hypothesis row, git tag, data snapshot manifest and scripts, reruns validate_candidate.py, paper_report.py and demo_report.py, and compares with the originals.
- Restore drill: restore the latest base dump plus tick-day archives (database/backup_db.py; its docstring line 10 is the only restore instruction, per the data-layer reader) into a scratch database and rerun the gate for one symbol.
- Failure-mode matrix on demo, expected vs observed per row: PC reboot with an open position; MT5 disconnect; Postgres down at entry and at exit; bridge stall with an open position; wrong account login; config edited while processes run (hash mismatch alarm); stale or duplicate signal; reconciler dead at EOD; router dead.
- Timezone fallback check: config_loader.py:97-104 falls back to utc_offset_hours 3 (trading_config.json:8) when tzdata is missing, which is wrong in northern winter and shifts the 23:30/23:45 cutoffs by an hour. Compare broker_now() with the MT5 clock.
- Exposure test from a second LAN device: trading_api.py:1174 and tick_api.py:183 bind 0.0.0.0 and start_all.bat:40 serves cpp-backend over http.server; ports 5001, 5002, 8081, 8082 must refuse.
- Pre-mortem: ten ways to lose money, each mapped to a control and a test.
- Owner signs the risk statement (risk capital, ladder values, tier table) and the assurance checklist.

**Risks**
- Independence is weak with one owner and AI sessions; use a different session and, if possible, a human reviewer.
- Time pressure (RUNBOOK.md:76 'earliest late Sep 2026' has already passed) is the main pressure to skip gates.
- Replication tolerance may fail because of nondeterminism or late-backfilled ticks; record per-day row counts at run time.

**Exit gates**

| Metric | Threshold | Evidence artifact |
|---|---|---|
| Replication match: n_trades, win rate, mean net bps, verdict | n exact; win rate within 1.0 pp; mean net bps within 0.5 bps or 5%; same verdict | `docs/assurance/<date>/replication.json` |
| Failure-mode matrix rows with expected == observed | 100% | `docs/assurance/<date>/failure_matrix.md` |
| Restore drill reproduces the gate numbers | n_trades identical; mean net bps within 0.1 | `docs/assurance/<date>/restore_drill.md` |
| Kill and halt drills on demo, two passes at least 7 days apart | 2 of 2 | `docs/incidents/drill_*.md` |
| Open P1/P2 defects | 0 | `docs/assurance/<date>/defects.md` |
| Ports reachable from another LAN device | 0 | `docs/assurance/<date>/exposure_test.md` |
| Unexplained kill or halt events in the last 10 trading days of demo | 0 | `KLDA-HFT/reports/demo/demo_report_<date>.md` |
| Signed checklist carrying config_hash and git tag assured-<date> | present | `docs/assurance/ASSURANCE_<date>.md` |

**Protocol — Assurance review**
- The reviewer did not write the code under review and was not in the conversation that produced it.
- Re-derive from the raw snapshot and scripts, not from the author's reports.
- Any mismatch beyond tolerance is a FAIL, not something to explain away.
- Every control claimed in a doc needs a test that can fail.
- Findings are logged with severity; P1 and P2 block.
- The review is tied to a git tag; a later C2 or C3 change voids it for the changed component.

**Repo changes**
- `docs/assurance/` — New. One folder per review plus ASSURANCE_<date>.md checklist.
- `KLDA-HFT/database/restore_drill.md` — New. Tested step list: create DB, timescaledb_pre_restore, pg_restore base dump, COPY tick-day files, refresh continuous aggregates, run gate.
- `KLDA-HFT/tests/failure_modes.md` — New. Matrix with commands, expected outcome and last result for each row.
- `KLDA-HFT/trading-engine/config_loader.py` — Startup warning when the tzdata fallback is used.

**Context updates**
- `CLAUDE.md` — Rule: live orders only from a tag named assured-*; any later C2/C3 change voids it for that component.
- `docs/PROTOCOL.md` — Add the assurance section and the signed ledger entry.
- `docs/RUNBOOK.md` — Add the tested restore procedure and the exposure-test command.

## S5

The first real-money account is the company's, and the system proves it is trading THAT account: identity registry, per-order guard, capital records that reconcile to broker statements, and risk limits expressed against recorded equity. Legal, regulatory and tax questions are in verify_externally and are not asserted here.

**Entry criteria**
- All S4 exit gates met; assurance tag exists.
- Owner has opened the account with the broker (external step). Its facts are in accounts.json with status PENDING and trading not permitted (allowlist empty, Algo Trading OFF).
- Owner has stated risk_capital_usd, the maximum total loss they will accept.

**Work**
- accounts.json: add the company account (login, server, entity name as on broker documents, base currency, leverage, trade_mode REAL, status). PENDING to READY is a C3 change. Register 52028179 as 'never trade'.
- Guard test: run the system with the terminal on other accounts (demo, 52028179) and confirm every order is refused.
- Daily reconcile_account.py: MT5 balance and equity vs (investor_ledger SUBSCRIPTION minus REDEMPTION plus cumulative realized P&L from executions) and vs nav_history.total_aum.
- Record capital: investor_ledger row via POST /api/investor_ledger (trading_api.py:446; the terminal has no form for it), reference_doc = broker deposit confirmation, with a hash of that document in notes.
- risk_limits.json in R units plus the absolute risk_capital_usd; a minimum-lot feasibility table: symbols whose minimum-lot risk exceeds the tier ceiling at the stated equity are blocked by a test.
- Five trading-day dry run attached to the company account with trading disabled: guard and reconcile only.
- Define how monthly broker-statement deals are tied out to the executions table.
- Label every performance figure by source: backtest, paper, demo, live. Sources are never merged in one number.

**Risks**
- Funding itself is a risk: a funded account with trading enabled before the system is ready. Keep the allowlist empty and Algo Trading OFF until S6.
- Company-account type (netting vs hedging) may differ from the demo.
- Entity and broker-document names may differ; the guard compares login, not names.
- Legal status of the account and of any outside capital is unresolved here; see verify_externally.

**Exit gates**

| Metric | Threshold | Evidence artifact |
|---|---|---|
| Orders accepted with the terminal logged into a non-registered account | 0 of >= 10 attempts | `docs/incidents/guard_test_<date>.md` |
| Consecutive trading days with reconcile_account.py green during the dry run | >= 5 | `KLDA-HFT/reports/reconciliation/<date>.csv` |
| Recorded capital (ledger) vs broker balance at funding | difference <= 0.1% or 1 currency unit | `KLDA-HFT/reports/reconciliation/funding_<date>.md` |
| Minimum-lot feasibility table covers every allowed symbol | 100%; infeasible symbols blocked by test | `KLDA-HFT/config/risk_limits.json + tests/test_risk_spine.py output` |
| Owner-signed risk_capital_usd and ladder values with config_hash | present | `docs/CHANGELOG_LIVE.md` |
| Orders sent to the company account before accounts.json status READY | 0 | `executions table export` |

**Protocol — Account identity and capital reconciliation**
- Identity is checked at startup and before every order; a mismatch raises P1 and sets the kill flag.
- Reconciliation tolerance is 0.1% or 1 currency unit; one breach is P2, two consecutive days halt new entries.
- Every capital movement has a ledger row with a reference document before tier size can change.
- Limits scale automatically with recorded equity; manual override only through C3.
- No trading on a day when reconcile_account.py has not run.
- Any position with magic other than 234000 on the company account is P1 until explained (PROTOCOL.md:74 records earlier phone trades).

**Repo changes**
- `KLDA-HFT/config/accounts.json` — Add company account and the never-trade entry for 52028179.
- `KLDA-HFT/monitoring/reconcile_account.py` — New. Daily MT5 vs ledger vs nav_history reconciliation, writes the .csv; heartbeat.
- `KLDA-HFT/config/risk_limits.json` — Add risk_capital_usd, tier table, feasibility table.
- `KLDA-HFT/api/trading_api.py` — Extend GET /api/compliance_report (:541-600; per the api reader it omits investor_ledger) with investor_ledger, signals, executions and strategy_status.
- `docs/CHANGELOG_LIVE.md` — New. Every C3 change: what, why, evidence, old and new values, config_hash old and new, approver.

**Context updates**
- `CLAUDE.md` — Replace stale account statements (.env broker section is stale; 52028179 trade-disabled) with a pointer to config/accounts.json as the only source of account facts.
- `docs/PROTOCOL.md` — Resolve the :49 vs :75 contradiction about 52028179; add an Account registry section.
- `docs/RUNBOOK.md` — Funding checklist, daily reconcile routine, curl recipe for ledger entries.

## S6

Real orders from the company account at the smallest feasible size, scaled only on evidence, scaled down automatically, with a hard total-loss budget and a dead-man's switch.

**Entry criteria**
- S4 assurance tag and S5 exit gates met.
- A 'validated' entry added by a C3 change: stats from the gate JSON, evidence path with sha256, 'expires' date, stage LIVE_RAMP.
- Start day chosen with the owner present; kill drill passed in the last 7 days; reconcile green.

**Work**
- Tier T1: 0.10% risk per trade, 1 symbol, 1 open position, at least 20 trading days AND at least 40 live trades.
- T2: 0.25%, up to 2 positions, at least 20 more days and cumulative at least 100 trades.
- T3: 0.50%, up to 3 positions, at least 30 more days and cumulative at least 200 trades.
- T4: 1.00% (the ceiling in locked decision #3), up to 3 positions. Each tier risk must also satisfy the Monte-Carlo rule: the 95th-percentile 200-trade max drawdown (research/mc_drawdown.py) is at most 50% of the L4 cap.
- Advance only when all hold: median live entry slippage (in spreads) <= 1.5x demo; live SPRT is not STOP; zero P1/P2 in the tier; tier max drawdown <= MC 75th percentile; reconcile green every day; monthly broker tie-out clean.
- Automatic scale-down: WATCH holds the tier; SUSPEND sends that strategy back to S2 paper; L3 drops one tier; L4, L5 or any P1 flattens, halts and resumes only at T1 after a C3 restart.
- Dead-man's switch: owner runs monitoring/ack.py daily. Two missed trading days stop new entries; five flatten and halt.
- Tier changes only at the start of a broker week, book flat, through C3.
- Correlation groups defined before go-live in risk_limits.json (a-priori: NAS100/GER40; SpotCrude/NatGas): at most 1 open position per group.
- Weekly review file reports/live/week_<yyyy-ww>.md auto-generated; owner adds three lines.

**Risks**
- First real-money week carries the largest model risk (fills, rejects). Start where a total loss is trivial.
- Recovery-trading urge after a loss (PROTOCOL.md:19-20). The C3 cool-off and no-loosening-while-underwater rules are the control.
- With small trade counts, tier gates mostly test mechanics, not edge; accept slow scaling.
- Minimum lot may exceed the tier risk on a small account, so the system may place no trades at all.

**Exit gates**

| Metric | Threshold | Evidence artifact |
|---|---|---|
| Tier completion: days and trades per tier met before each advance | T1 >=20 d/40 tr; T2 +20 d/100 cum; T3 +30 d/200 cum | `KLDA-HFT/reports/live/tier_log.md` |
| Median live entry slippage in spreads vs demo at each advance | <= 1.5x | `KLDA-HFT/reports/live/week_<yyyy-ww>.md` |
| Monthly broker-statement deals matched to executions rows (both directions) | 100% | `KLDA-HFT/reports/reconciliation/tieout_<yyyy-mm>.csv` |
| Live SPRT state (H1 = validated expectancy) | not STOP at every advance | `KLDA-HFT/reports/live/sprt_<date>.json` |
| P1/P2 incidents inside the tier | 0 to advance; closing one resets that tier's clock | `docs/incidents/` |
| Tier max drawdown vs MC 75th percentile for the same trade count | <= | `KLDA-HFT/reports/live/week_<yyyy-ww>.md` |
| Cumulative live loss as a share of risk_capital_usd at each advance | < 50% | `KLDA-HFT/reports/live/tier_log.md` |

**Protocol — Ramp ladder and scale-down**
- Tiers move one step at a time, never skip.
- No tier change in the same week as a WATCH, SUSPEND or L2+ event.
- Minimum-lot rule: if the minimum lot's risk exceeds the tier ceiling, no trade is placed. Never round up.
- Scale-down is automatic; scale-up needs C3.
- Live results are compared with the validated expectancy and with demo, each labelled by source.
- After any L4/L5 or P1, restart at T1.

**Protocol — Dead-man's switch**
- monitoring/ack.py writes a dated acknowledgement; guardian reads it.
- Two missed trading days: no new entries.
- Five missed trading days: flatten and halt.
- The acknowledgement requires reading the weekly review's red/green lines.
- RUNBOOK §0 (15-day absence) is superseded: live tiers do not run unattended.

**Repo changes**
- `KLDA-HFT/config/ramp.json` — New. Tier table and current tier state; changed only through C3.
- `KLDA-HFT/trading-engine/guardian.py` — Extend: tier enforcement, automatic scale-down, ack check, correlation-group cap.
- `KLDA-HFT/monitoring/ack.py` — New. Daily acknowledgement.
- `KLDA-HFT/monitoring/live_report.py` — New. Weekly review generator.
- `KLDA-HFT/config/validated_patterns.json` — First 'validated' entry with stage, expires, evidence sha256.

**Context updates**
- `docs/RUNBOOK.md` — Ramp table; the daily owner routine; what to do on each automatic halt; replace §0 absence plan for live tiers.
- `docs/PROTOCOL.md` — Add a live ledger with source labels; record each tier decision with its evidence path.
- `CLAUDE.md` — Live orders only through config/ramp.json and the assured tag; never edit these files by hand.

## S7

More agents and markets without inflating false positives; edges that survive a second independent price source and periodic re-validation; independence of builder and approver.

**Entry criteria**
- T4 reached and no unresolved P1/P2 for 60 trading days (or an explicit owner decision).
- hypothesis_log.csv complete for all prior work.

**Work**
- Family accounting across all agents: cumulative m per data window and online alpha spending, alpha_i = 0.05*(6/pi^2)/i^2 (sums to at most 0.05, derived); each new window gets a fresh lock-box.
- New patterns (Gap Fill, Pairs Divergence, Event Drift, Momentum Exhaustion: CLAUDE.md:13; only MEAN_REVERSION exists in code) each run S1 to S6; none inherits another's validation (PROTOCOL.md:115 'no grandfathering').
- Second-source test: the edge must survive on a second independent price source: net bps within 1 median spread of source A and still > 0; 5-minute bar-close agreement report.
- Automatic re-validation monthly on the trailing window; validated entries carry 'expires' (default 90 days, proposed); is_validated refuses expired ones; guardian demotes to PAPER.
- Aggregate the loss ladder across agents; position-count caps and correlation groups scale with the number of agents.
- Builder is never the approver on C3; reviewer rotation; quarterly assurance re-run, kill drill and restore drill.

**Risks**
- A second source with different symbol names or timestamp convention can create false disagreement; map symbols and times first.
- Expiry and demotion could silently stop all trading; the owner must see the state every day.
- Alpha spending makes late candidates nearly impossible to promote; that is intended, but it will feel like the system is stuck.

**Exit gates**

| Metric | Threshold | Evidence artifact |
|---|---|---|
| Validated entries unexpired with last re-validation PASS | 100% | `KLDA-HFT/reports/research/revalidation_<date>.json` |
| Second-source agreement: |net bps A - net bps B|, and B's sign | <= 1 median spread and B > 0 | `KLDA-HFT/reports/research/second_source_<id>_<date>.json` |
| Family ledger: cumulative m and alpha spent per window published; promotions used adjusted alpha | 100% of promotions | `KLDA-HFT/research/hypothesis_log.csv` |
| Automatic demotion drill with simulated decay | entry demoted within one guardian cycle; orders refused | `docs/incidents/drill_demotion_<date>.md` |
| Quarterly assurance, kill and restore drills | on schedule and passing | `docs/assurance/` |
| C3 changes where approver differs from author | 100% | `docs/CHANGELOG_LIVE.md` |

**Protocol — Family-wise accounting and re-validation**
- Every look is a row in hypothesis_log.csv; m only grows within a data window.
- Promotions use the alpha for their position in the sequence.
- Entries expire; expiry is checked in code, not by memory.
- A second source must agree before an agent goes beyond T2.
- A decayed edge is demoted automatically; re-entry is a new registration.
- No agent shares another agent's validation.

**Repo changes**
- `KLDA-HFT/research/revalidate.py` — New. Monthly re-run of validate_candidate.py on the trailing window; updates expires.
- `KLDA-HFT/research/second_source_check.py` — New. Compares bar closes and edge on source B.
- `KLDA-HFT/trading-engine/guardian.py` — Expiry demotion and aggregate ladder.
- `KLDA-HFT/database/migrations/004_ticks_source.sql` — New table ticks_ref with a source column. Do not add a source column to ticks (the C++ code and cagg_bars_m5 read ticks directly).

**Context updates**
- `docs/PROTOCOL.md` — Add family ledger rules, expiry rule, second-source rule.
- `docs/RUNBOOK.md` — Quarterly drill calendar and the monthly re-validation routine.
- `CLAUDE.md` — Add the guardian states and where strategy_status is read.

## Cross-cutting protocols

**Loss-limit ladder and automatic demotion** — Today no loss limit actually works in any mode: the daily-loss check is skipped in paper (limits_enforcer.py:180), allows trading when no snapshot exists (:66-68), is hard-coded at EUR 10 (:27), and the kill flag fails open (:166-167). Nothing demotes a strategy. Values are proposals for the owner to confirm. R = risk per trade in the current tier, so limits scale with size.
- L1 per trade: risk at the stop <= tier ceiling x recorded equity (never above 1%, decision #3). Minimum lot above the ceiling means no trade.
- L2 day: loss >= 3R (realized plus floating, broker day) means no new entries and flat book until the next broker day.
- L3 week: loss >= 6R means all strategies SUSPENDED until a written review.
- L4 drawdown from the equity high-water mark >= min(10R, 8% of equity) means kill_switch (flatten plus flag), a P1 incident, and restart only via C3 at T1.
- L5 risk budget: cumulative loss since go-live >= 50% of risk_capital_usd halts and triggers review; 100% stops permanently.
- Strategy states ACTIVE, WATCH, SUSPENDED, KILLED. WATCH: last 30 trades mean net bps < 0, or running drawdown above the MC 75th percentile. SUSPENDED: SPRT STOP, or drawdown above the MC 95th percentile, or median slippage > 2x demo for 20 trades. KILLED: two SUSPENDs in 60 trading days or a failed re-validation.
- Reinstatement from SUSPENDED is via S2 paper (>= 20 clean days plus a fresh SPRT), never directly to live.
- Fail CLOSED: any unreadable flag, limit, equity or clock stops new entries. MC calibration matters: at a 40% win rate a 10-loss streak occurs in 500 trades about 71% of the time (simulated), so a fixed 10% kill threshold at 1% risk would fire on ordinary variance.

**Change control** — The config is edited by hand, cached at import (config_loader.py:30-44), consumed by three separate processes, and decides whether real orders are possible. A non-programmer owner under recovery-trading pressure (PROTOCOL.md:19-20) is the highest-risk editor.
- C0 docs and read-only observability: free.
- C1 risk-tightening (lower limits or size, remove a symbol, add an alarm): any time, logged in docs/CHANGELOG_LIVE.md.
- C2 strategy change (thresholds, symbols, exits, rule code): new registration, the candidate returns to S1 or S2 and its live entry is demoted.
- C3 risk-loosening or capability-adding (execution_mode, allowlist add, limits up, tier up, accounts.json status, kill --clear): needs the gate JSON or incident closure as evidence, a CHANGELOG_LIVE.md entry (what, why, evidence, old and new values, old and new config_hash), approver different from author when a second person exists, otherwise a 24 h cool-off between commit and activation.
- C3 is applied only with a flat book and outside the entry window, then ALL three engine processes are restarted and their startup lines must show the new config_hash.
- No C3 while any strategy is WATCH or SUSPENDED, within 5 trading days of an L2+ event, or with an open P1/P2.
- One deploy branch; deploy only from a git tag; the PC prints the tag at startup.

**Incident response** — The owner is not a programmer and may be absent (RUNBOOK §0, 15 days), so the default must be flat, and what happened must be reconstructable.
- P1 (money at risk now or a control bypassed: unexpected order or foreign-magic position, account mismatch, L4/L5, kill fired, feed stale > 5 min with open positions, DB vs MT5 position mismatch > 120 s): run python kill_switch.py --reason "<text>" first, diagnose second; confirm positions_get is empty and paper OPEN rows are closed. Flatten within 5 minutes of detection.
- P2 (control degraded: a process dead, heartbeat gap, reconcile breach, DB write failures): triage within 1 trading day; two consecutive reconcile breaches halt entries.
- Within 24 h write docs/incidents/YYYY-MM-DD-<slug>.md: timeline (broker time), detection, positions and P&L affected, root cause, corrective action, test or alarm added, config_hash.
- Preserve evidence: copy the process logs and export signals, executions and paper_positions for the window; record sha256 in the incident file.
- No restart and no kill_switch.py --clear until root cause and corrective action are written (C3).
- Every P1/P2 produces at least one new test or alarm. Run a kill-switch and halt fire drill on demo monthly. kill_switch.py is an emergency tool, not a routine one (it closes every MT5 position, kill_switch.py:63).

**Provenance and recovery-trading discipline** — A number no one can reproduce is not evidence, and the owner's own history shows manual trades after losses (PROTOCOL.md:74-75). Rules decide sizing and promotion, not account P&L.
- config_hash is stored on every signal, paper_position and execution; evidence JSON carries commit, tag, script, data window, per-day row counts and the sha256 of the tick-day archives used.
- A result that cannot be re-created from its provenance is void.
- Position size comes from the tier table only; no manual order path exists on the system's account (decision #5).
- After a loss, limits may only tighten (C1) for 5 trading days.
- Never describe backtest, paper or demo results as live performance in any record; label the source.

## Anti-patterns
- Judging an asymmetric-geometry strategy by win rate. SpotCrude's 58.4% (trading_config.json:30) is BELOW the 66.7% break-even of TP 0.5%/SL 1.0%, and its p=0.005 is against a 50% null.
- Tuning on the data that judges the result: backtest_5metric.py:23 'OPTIMIZED FOR SPOTCRUDE'; optimize_spotcrude.py window grids (:36,:58,:82); exit-geometry sweep on the same history.
- Keeping winners and forgetting losers: signal_generator.py:46-53 labels 4 symbols 'Backtest-confirmed' though only SpotCrude was backtested, and 8 removed symbols appear in no ledger.
- Deriving the null from the sample's own average win and loss (backtest_exit_geometry.py:156): it restates 'net>0' and is not an edge test.
- Lowering a threshold, or calling INCONCLUSIVE 'basically a pass', to get a stage over with.
- Typing statistics into validated_patterns.json by hand instead of letting validate_candidate.py write them.
- Quoting paper pnl_eur as money (broker_adapter_mt5.py:198: pnl_points*lots*1000, no contract size or currency).
- Treating overlapping or clustered trades as independent samples.
- Reading backtest_5metric.py returns as 1%-risk results: line 121 sizes 1% of capital as notional, about 0.01% risk at a 1% stop (derived).
- Testing the gate by flipping paper_mode to false: mt5.initialize() has no login (broker_adapter_mt5.py:149), so orders go to whichever account the terminal holds.
- Editing config while processes run: config is cached per process (config_loader.py:30-44), so the three processes can disagree.
- Treating demo fills as proof of live fills (docs/DEMO_ACCOUNT.md:88-90).
- Letting a drawdown change limits or sizing, or placing manual trades beside the system.
- Safety checks that fail open (limits_enforcer.py:66-68,166-167).
- Peeking at the lock-box or reusing a burned one for a re-parameterised version.
- Using kill_switch.py as a routine tool, or running it with positions of other origin open (it closes every MT5 position, kill_switch.py:63).

## Questions for the owner
- Decision #4 says 'demo ~25k on the VPS'. The stack is local-only. May S3 run on the PC and the VPS wording be dropped? Which exact demo account is the ~25k one? None is recorded; docs/DEMO_ACCOUNT.md:3 lists 62101051 with balance and leverage 'To be verified'.
- paper_mode=false today means real order_send to whichever account the MT5 terminal is logged into. S3 needs real orders on a demo account. May we add a third setting, execution_mode (paper|demo|live), plus a per-order account-identity check, so paper_mode stays true (meaning no real-money orders) until S6?
- Decision #3 '1% per trade': does it mean 1% of equity lost if the stop is hit? backtest_5metric.py:121 sizes 1% of capital as notional, so its return and drawdown numbers are about 100x smaller than a 1%-risk system's. May the ramp tiers be 0.10 / 0.25 / 0.50 / 1.00% with 1% as the ceiling (the locked text says 'hard-coded')?
- Gate: keep the locked floor (>=100 trades, >=51% win rate, p<0.05, net>0) and add S1 requirements on top (explicit null, Holm-adjusted p, lock-box, placebo, cost stress, rule parity)? This makes passing harder, and every candidate may end FAIL or INCONCLUSIVE for months. Do you accept that?
- Decision #1 'everything, ranked': may the correction cover the full ~26-symbol universe and ranked winners be reported only after the lock-box, or should the family be restricted in advance to the current 4 symbols (which were themselves chosen after looking at data)?
- Loss ladder (proposed): day 3R, week 6R, drawdown min(10R, 8%). What total loss (risk_capital_usd) are you prepared to lose in the whole project? RUNBOOK.md:54 says the live account has about $7 equity.
- Who is the second reviewer for S4 and C3 changes? If nobody, do you accept a fresh AI-session replication plus a 24 h cool-off as the substitute?
- May ticks captured after 2026-07-17 (the last recorded SpotCrude sweep) be reserved as the SpotCrude lock-box, never queried while designing, if data_days.csv shows them clean?
- Stage timing: RUNBOOK.md:75 says demo 4+ weeks, DEMO_ACCOUNT.md:20 says 2 weeks, RUNBOOK.md:76 'earliest late Sep 2026' has passed. Use gate-based stages with minimum days (S2 30 clean days, S3 20 trading days) instead of dates?
- Account 52028179: PROTOCOL.md:49 says trade-disabled, :75 says 'appears lifted'. Should it be registered as 'never trade' once the company account exists?
- Daily acknowledgement (dead-man's switch) for live tiers: acceptable, given RUNBOOK §0 plans 15-day unattended absences?

## Verify externally (broker / lawyer / accountant)
- Broker (Pepperstone): does demo reproduce live execution for the traded instruments (spreads, slippage, requotes, stop levels, filling modes, hedging vs netting)? Demo expiry and balance-reset rules?
- Broker: commission, swap and financing schedule per instrument for the account type to be used; is commission really 0 (backtest_5metric.py:21 assumes 'built into spread')? Does the company account type permit API/Algo trading, and which leverage and margin close-out level apply?
- Broker: contract size, tick value, quote currency, minimum lot and lot step for NatGas, SpotCrude, NAS100 and GER40; the broker server-time convention per product; trading-hours and maintenance windows.
- Broker: is the trade block on live account 52028179 lifted or not (PROTOCOL.md:49 vs :75)? What does the MT5 Algo Trading switch return to an API order when OFF?
- Broker: corporate account-opening requirements, which documents they need, and whether the account's client classification changes leverage or protections.
- Lawyer: whether running an automated strategy on the company's own capital, or accepting outside capital (investor_ledger SUBSCRIPTION rows), triggers any authorisation or registration obligation in the owner's jurisdiction.
- Lawyer: what may be said publicly about backtest, paper, demo or live performance, and any mandate or management agreement required between KLDA Technologies and a capital provider.
- Lawyer: data-protection obligations for investor records held in the database; broker market-data licence terms for internal research use.
- Accountant: tax treatment of CFD gains and losses in the entity; how to record realized vs unrealized P&L, fees and NAV; year-end valuation; record-retention periods.
- Accountant: is an internal NAV plus broker statements an acceptable record, or is an audited statement or an administrator needed?
