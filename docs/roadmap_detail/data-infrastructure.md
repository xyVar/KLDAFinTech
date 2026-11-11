# Roadmap detail — data-infrastructure lens

> DRAFT, 2026-11-11. One of three independent designs behind `docs/ROADMAP.md`. Numbers marked 'proposed' need owner confirmation. Legal/regulatory/tax items are questions, not facts.

## S0

A cornerstone you can prove: gaps catalogued, a gap ledger and per-day certification running, one restore rehearsed from an off-machine copy, reboot and failure drills passed, alerts that reach your phone from outside the PC, nothing listening beyond 127.0.0.1. Carries most of this lens's work.

**Entry criteria**
- Stack runs via KLDA-HFT/start_all.bat on lane-a/safety-gate (265ebad or later), paper_mode true (KLDA-HFT/config/trading_config.json:3).
- LOCAL session has Postgres + MT5 access; owner is available for hardware/Windows/account steps (tagged OWNER).
- Owner answered questions 1, 3, 4, 6 before Waves B and C.

**Work**
- WAVE A (days 1-3: measure, contain, see). A1 [LOCAL] Measure first, change nothing, save to docs/evidence/s0/baseline.md: describe table ticks (any unique index?), timescaledb_information.jobs (look for policy_retention: database/schema.sql:43 defines a 1-year retention that would silently delete ticks; data starts Mar 2026), timescaledb_information.continuous_aggregates (materialized_only is not set in repo SQL), SELECT count(*) FROM current (docs say 26, 64, 66), SHOW timezone, Windows tzutil /g, hypertable_detailed_size('ticks'), free GB on C:, backups folder size, tail of backup.log, SHOW listen_addresses.
- A2 [OWNER] Set service postgresql-x64-16 to Automatic (RUNBOOK.md:14-17; PROTOCOL.md:73 still lists it open). Confirm with sc qc postgresql-x64-16.
- A3 [LOCAL] LOCKDOWN protocol (below): bind every listener to 127.0.0.1; add .env, backups/, *.csv.gz to .gitignore (backup dir sits inside the repo folder, backup_db.py:24, and only *.dump/*.log/*.txt are ignored today).
- A4 [LOCAL] Alert v0: new monitoring/alert.py (SMTP + outbound heartbeat ping, secrets from .env) and monitoring/feed_monitor.py run every minute by Task Scheduler. Plain mode of hourly_health_check.py is dead (queries dropped {symbol}_history tables, lines 87-101; email fields are placeholders, lines 26-32); only --report works.
- A5 [LOCAL] Fix watchdog.py blind spots: a DB error (hw None) is counted as a feed stall and kills the bridge (line 143); add an hourly OK line (RUNBOOK.md:36 expects healthy lines the watchdog never writes); suppress weekend restart loop using the session profile from C1.
- WAVE B (weeks 1-2: recoverability). B1 [LOCAL] Harden backup_db.py: sha256 manifest per file, verify yesterday's files, raise P1 on any failure (today only backup.log, line 51-54), replace SELECT DISTINCT time::date (line 67, a cast on the partition column; check its runtime in backup.log), write row count per archived day, re-export a day as .v2 if its count later changes (line 71-72 never re-exports).
- B2 [OWNER+LOCAL] Off-machine copy per RECOVERABLE protocol: second medium plus one copy outside the building, encrypted, key kept off-PC and off-repo.
- B3 [LOCAL] RESTORE-REHEARSAL protocol; write RUNBOOK section 7 (restore steps with timescaledb_pre_restore/post_restore, tick COPY-back, cagg refresh). Today the only restore instruction in the repo is the docstring at backup_db.py:10.
- B4 [LOCAL] Disk runway: measure GB/day for 14 days; compare with schema.sql:45 (~200GB/year claim) vs backup_db.py:5 (~20GB free on C:). KEEP_BASE_DUMPS=7 (line 25) x ~1,046MB (PROTOCOL.md:72) is ~7GB of that. Set tiered retention (2 dumps on C:, rest on second medium); never auto-prune tick archives.
- B5 [OWNER] Power and OS: UPS present? BIOS restore-on-AC-loss, sleep Never (RUNBOOK.md:25), Windows Update active hours or restart pause, laptop lid action, decide auto-logon (MT5 is a GUI app; Task Scheduler 'whether logged on or not' cannot start it).
- B6 [LOCAL] Boot choreography: scripts/boot_stack.ps1 waits on conditions, not the fixed timeouts in start_all.bat: Postgres accepting connections -> MT5 running and connected -> watchdog (it adopts or starts the bridge, watchdog.py:119-124) -> API -> paper chain. scripts/install_tasks.ps1 registers all tasks (backup 02:30, feed_monitor, boot, restart-on-failure for watchdog) so the setup lives in the repo, not in one person's Task Scheduler.
- WAVE C (weeks 2-4: truth). C1 [LOCAL] TIMEBASE proof (below). Also build the empirical session profile: per symbol, weekday and hour, share of last 4 weeks with ticks; this defines 'expected active' without relying on unverified MT5 session APIs.
- C2 [LOCAL] GAP-CENSUS over 2026-03-09 to today: classify every symbol-day CLEAN / GAPPED / NO_DATA; confirm or correct the '~14 distinct trading days Mar 9-Apr 30' claim (PROTOCOL.md:51).
- C3 [LOCAL] Bridge hardening, additive only (CLAUDE.md forbids stripping the rotating log, reconnect loop, time_msc dedup, 10s lookback): (a) advance last_msc only after commit (set at line 120, commit at 184); (b) spool a failed batch to a local file and replay (lines 190-192 lose it); (c) WARN when Market Watch symbols return zero ticks for N seconds in expected-active time (lines 112-113 are silent); (d) after C1, on start/reconnect seed from DB MAX(time) and catch up with copy_ticks_range into the gap (lines 62-66 skip everything missed); (e) write a feed_heartbeat row per minute with the account/server it captures from.
- C4 [LOCAL] SCHEMA-AND-ROLES protocol: baseline migration from the live DB, migrate.py, roles, legacy DDL moved to database/legacy/, typed-confirmation guards on truncate_ticks.py and fix_ticks.py (both wipe all of ticks, no prompt).
- C5 [LOCAL] Centralise credentials in common/db.py, then rotate the DB password in one weekend-window cutover (77 files in this clone contain the literal), set JWT_SECRET in .env and make the API exit if it is the default (trading_api.py:43).
- C6 [LOCAL] monitoring/daily_certify.py v0: per symbol-day coverage, longest gap, spread=0 share, crossed quotes (ask<bid), non-positive prices, 1-tick jumps; daily symbol_specs_history snapshot (point, digits, contract size) because ticks.spread is stored in points (bridge lines 122-130) and a point change silently rescales history; universe diff vs yesterday. Writes data_day_status, symbol_events.
- C7 [LOCAL] Reconciliation R1 (completeness, same broker, different path): nightly compare the broker's own M1 bars for the previous day (mt5.copy_rates_range, already used in database/backfill_all_history.py) with minutes present in cagg_bars_m1; write recon_results. This detects pipeline loss, the actual failure mode so far.
- C8 [LOCAL+OWNER] FAILURE-DRILL protocol, then start the 14-day clock (only after C3 and C6 are live). Maintenance window for all data-path edits: Fri 23:55 to Mon 03:00 broker time (CLAUDE.md trading hours).
- C9 [CLOUD] Docs: fix RUNBOOK.md:37 (backups are in the repo-root backups folder per backup_db.py:24, not KLDA-HFT/backups), add alert-to-action table, create docs/evidence/README.md.

**Risks**
- Edits to the bridge during market hours create new gaps; do them only in the window and keep all resilience features.
- A unique index or new column on a 357M-row compressed hypertable may be refused or lock; rehearse on the restore copy and fall back to sidecar tables.
- Retiring Postgres network access breaks the C++ Docker path (host.docker.internal); decision in question 6.
- Password rotation across 77 files breaks anything missed; centralise first, rotate once, grep after.
- Restore rehearsal needs free space that C: may not have; use the external drive.
- Auto-logon trades physical security for unattended recovery; owner decision.

**Exit gates**

| Metric | Threshold | Evidence artifact |
|---|---|---|
| Feed coverage: share of expected-active symbol-minutes with >=1 tick, 14 consecutive days | >=99.0% for each of the 4 symbols signal_generator scans (signal_generator.py:46-53) and >=95% of other symbols; 0 whole-feed gaps >10 min in market hours without a feed_gaps row stating cause and resolution | `docs/evidence/s0/coverage_14d.md (export of feed_gaps + data_day_status)` |
| Gap census completeness | 100% of symbol-days from 2026-03-09 classified; PROTOCOL.md:51 claim confirmed or corrected | `docs/evidence/s0/gap_census.md` |
| Timebase proof: stored ticks.time minus true UTC | offset is a constant multiple of 30 min within +-5s on >=5 samples across >=3 days and 2 sessions; written as decision D6 in docs/PROTOCOL.md | `docs/evidence/s0/timebase_proof.md` |
| Restore rehearsal from the OFF-MACHINE copy into a scratch database | base dump + >=10 random tick-day archives restored; per-day row count equals archive line count for 100% of sampled days; cagg_bars_m5 refresh completes; health --report runs against it; elapsed time recorded as RTO | `docs/evidence/s0/restore_rehearsal.md` |
| Off-machine copy freshness and integrity | newest base dump and newest tick archive exist on a second medium and one off-site; age <=36h; sha256 manifest verifies 100% | `docs/evidence/s0/offsite_manifest.md` |
| Failure-drill matrix (reboot, kill MT5, kill bridge, kill watchdog, stop Postgres service, unplug network 5 min) | 6/6 recover with no typing; feed advancing <=10 min after power-on; phone alert <=5 min after each fault; dead-man's-switch alert <=20 min after heartbeat stops | `docs/evidence/s0/drill_matrix.md` |
| Network exposure | 0 listening sockets on 0.0.0.0 or [::] for ports 5000,5001,5002,8081,8082 (and 5432 per question 6); probe from a second LAN device refused for each; no inbound allow rule for them | `docs/evidence/s0/exposure_scan.md` |
| Secrets hygiene | old DB password string count in working tree = 0; API refuses default JWT_SECRET; .env, backups/, *.csv.gz ignored; no password literal in any new file | `docs/evidence/s0/secrets_scan.md and .gitignore` |
| Disk runway = free GB / measured GB-per-day (14-day average) | >=90 days, or offload plan executed; free space >10% (existing threshold, hourly_health_check.py:409) | `docs/evidence/s0/disk_runway.md` |

**Protocol — TIMEBASE-PROOF**
- Bridge stores datetime.fromtimestamp(tick time) in PC local zone (mt5_tick_capture_ALL_TICKS.py:126) into a TIMESTAMPTZ column, so the meaning depends on PC zone and DST; treat it as unproven until measured.
- Each minute feed_monitor writes newest ticks.time, PC UTC now, MT5 tick epoch and tz settings into feed_heartbeat.
- Compare with config_loader.broker_utc_offset_hours(); hourly_health_check.py --report already prints this mismatch check (lines 280-289).
- Run across a quiet weekend restart and at least one US or EU DST change window, or document that it is still unobserved.
- Result becomes D6 plus a data_epochs row (effective_from, meaning, conversion). History is not rewritten without owner approval.

**Protocol — GAP-CENSUS**
- Read-only first: per symbol-day tick count, first/last tick, longest inter-tick gap.
- Compare each day against the broker's M1 bars via copy_rates_range; record how far back the server still serves history.
- Every GAPPED or NO_DATA day gets cause (bridge dead, Postgres down, market closed, MT5 logged out, unknown) or 'unknown'.
- Backfill only inside recorded gaps, only if timebase is proven, recomputing spread from bid/ask and point (backfill_all_history.py:156 writes 0.0).
- Backfilled days are status BACKFILLED, excluded from cost-sensitive research until reviewed.

**Protocol — RESTORE-REHEARSAL**
- Restore into a scratch database on a different folder or drive, never over production; confirm free space first (C: had ~20GB free per backup_db.py:5, a full rehearsal may need the external drive).
- Check whether pg_dump --exclude-table-data=ticks (line 48) really excluded hypertable chunk rows: compare dump size to hypertable_size('ticks').
- Restore base dump, then COPY back >=10 random tick-days, then refresh caggs; compare per-day counts to manifest.
- Run one schema migration on the scratch copy before it ever touches production.
- Time every step; write RTO and RPO into RUNBOOK section 7.

**Protocol — FAILURE-DRILL**
- Run in the weekend window; announce start and end in the evidence file.
- One fault at a time, from the matrix; record time of fault, time alert reached phone, time feed advanced again.
- Include: does killing terminal64.exe get MT5 back by itself, or only on next logon? (unknown from the repo)
- A drill that needs typing is a fail; fix the boot chain, not the checklist.
- Repeat the full matrix after any change to start_all.bat, watchdog.py or the scheduled tasks.

**Protocol — LOCKDOWN**
- Edit host to 127.0.0.1: api/trading_api.py:1174, tick_api.py:183, positions_api.py:152, tick_receiver.py:800; python -m http.server 8082 --bind 127.0.0.1 (start_all.bat:40, cpp-backend/start_web_server.bat); docker publish 127.0.0.1:8081:8081 (docker-compose.yml).
- Restrict CORS in trading_api.py:49 to http://127.0.0.1:5002 and http://localhost:5002; open the terminal at http://127.0.0.1:5002/ not file:// (start_all.bat:39).
- Answer any Windows firewall 'allow access' prompt with Cancel; list inbound rules and delete or scope any for the KLDA ports (cpp-backend/DOCKER_INVESTIGATION.md:437 recommends an unscoped inbound 5432 allow rule).
- Verify with netstat -ano (look for 127.0.0.1: versus 0.0.0.0: or [::]:) and a phone on the same Wi-Fi opening http://PC-IP:5002/ and :8082/config.json; both must fail.
- Check the router for port-forwards or UPnP mappings (owner).

**Repo changes**
- `KLDA-HFT/monitoring/feed_monitor.py (new) and monitoring/alert.py (new)` — Per-minute heartbeat, advancing-high-water test, per-symbol silence vs session profile, DB/disk/MT5/process checks, writes feed_heartbeat and feed_gaps, sets system_flags FEED_UNHEALTHY, sends alerts and the outbound dead-man ping.
- `KLDA-HFT/monitoring/daily_certify.py (new)` — Nightly DQ checks, data_day_status, symbol_specs_history, symbol_events, universe diff, R1 reconciliation into recon_results.
- `KLDA-HFT/python-bridge/mt5_tick_capture_ALL_TICKS.py` — Additive: commit-then-advance last_msc, spool/replay, zero-tick warning, DB-based catch-up on restart, heartbeat row.
- `KLDA-HFT/python-bridge/watchdog.py` — DB error is not a stall; hourly OK line; weekend suppression from the session profile; Task Scheduler restart-on-failure.
- `KLDA-HFT/database/backup_db.py` — Manifest, verification, failure alert, versioned day archives, cheaper day listing, off-machine sync hook.
- `KLDA-HFT/database/migrations/ (new), database/migrate.py (new), database/restore_test.py (new), database/legacy/ (new)` — Baseline from live DB, forward-only migrations creating schema_migrations, feed_heartbeat, feed_gaps, data_day_status, symbol_specs_history, symbol_events, recon_results, data_epochs; legacy DDL and destructive scripts moved with DO-NOT-RUN headers.
- `KLDA-HFT/scripts/boot_stack.ps1, install_tasks.ps1 (new); start_all.bat; stop_all.bat` — Condition-based boot chain and scheduled tasks in the repo; bind flags; stop_all docker stop via same wsl path as start (start_all.bat:25 vs stop_all.bat:21).
- `.gitignore, KLDA-HFT/common/db.py (new), .env.example (new)` — Ignore .env, backups/, *.csv.gz; one credential loader; template without secrets.
- `docs/evidence/ (new, with README.md)` — Versioned, secret-free evidence per stage. Use .md/.json/.csv only: .gitignore ignores *.txt and *.log, so health_*.txt and daily_*_SpotCrude.txt reports are never versioned.

**Context updates**
- `CLAUDE.md` — Add 'Data-path rules': ticks is append-only; never run truncate_ticks.py/fix_ticks.py/restructure_universal.sql/schema.sql; the proven meaning of ticks.time (D6); maintenance window; evidence goes in docs/evidence as .md; how to run feed_monitor and the restore test.
- `docs/PROTOCOL.md` — Add decisions D6 timebase, D7 local-only binding, D8 only CLEAN days feed research; update the Known state lines 51-54 with census result and autostart status; add a DATA LEDGER (clean days per symbol, last restore rehearsal, last drill).
- `docs/RUNBOOK.md` — Rewrite section 0 as the boot chain, section 1 as 'read the daily digest', add alert-to-action table, section 7 Restore, section 8 Maintenance window; fix backup path (line 37) and watchdog log expectation (line 36).

## S1

Research can only consume certified data, every result is reproducible from a manifest, and time-of-day research stands on a proven clock.

**Entry criteria**
- S0 gates for coverage, gap census, timebase, restore rehearsal all met.
- daily_certify has produced data_day_status for the whole history.

**Work**
- Add database/research_data.py: load_ticks(symbol, from, to) refuses days not CLEAN and writes a dataset manifest. database/backtest_5metric.py currently loads every tick for one symbol with no date filter or quality filter (lines 49-55) and hard-codes SYMBOL, POINT_SIZE and host 'localhost' (lines 13, 20, 41).
- Segment series at gaps and session breaks: no rolling window (MA50, 100, 200) and no TP/SL barrier may span a gap longer than a set threshold.
- Time-of-day features computed from UTC in the instrument session zone, never from stored wall clock; GER40 and US instruments shift relative to broker time when US and EU DST dates differ (verify on measured tick activity).
- Discontinuity scan for the 4 scanned symbols: overnight jump vs typical range, roll candidates into symbol_events with disposition EXCLUDE / SPLIT / OK.
- Determinism: rerun each candidate backtest on the restored scratch DB and compare trade-list hash.
- Clean-day accrual forecast: required days D = ceil(20,000 trades / observed trades per clean symbol-day) from PROTOCOL.md:89; publish weekly.
- Run R1 reconciliation nightly and review breaches weekly; keep running one backtest at a time (CLAUDE.md OOM rule).

**Risks**
- Few CLEAN days after filtering may push the 20k-trade wall out by months; the forecast makes that visible early.
- Timebase finding may force re-labelling of older data; handled by data_epochs, not rewrite.
- Gap segmentation changes past backtest numbers; re-run before trusting old verdicts.

**Exit gates**

| Metric | Threshold | Evidence artifact |
|---|---|---|
| Clean symbol-days in the dataset manifest of each candidate | >= D (computed as above and written in the manifest) | `docs/evidence/s1/<candidate>/dataset_manifest.json` |
| Research runs on non-CLEAN days | 0 (loader-enforced; run log shows rejected days) | `docs/evidence/s1/<candidate>/run_log.md` |
| Reproducibility: trade-list sha256 on production vs restored copy | identical, 2 of 2 reruns | `docs/evidence/s1/<candidate>/repro.md` |
| Spread=0 tick share on each tested day | <= 3x the symbol's S0 median share; no BACKFILLED day in a cost-sensitive test | `docs/evidence/s1/<candidate>/cost_integrity.md` |
| Discontinuity dispositions | 100% of flagged days dispositioned in symbol_events | `docs/evidence/s1/<candidate>/discontinuities.md` |

**Protocol — MANIFEST-OR-IT-DIDNT-HAPPEN**
- Every ledger row in PROTOCOL.md (lines 63-67) cites a manifest path, code commit and schema version.
- The manifest lists symbols, date range, CLEAN/excluded day counts, per-day row counts and a checksum.
- validated_patterns.json 'evidence' field must point to the manifest.
- Changing a threshold on the same data after seeing results creates a new manifest id, never an overwrite.

**Repo changes**
- `KLDA-HFT/database/research_data.py (new)` — Certified-day loader plus manifest writer.
- `KLDA-HFT/database/backtest_5metric.py` — Use the loader, read point size from symbol_specs_history, host 127.0.0.1 via common/db.py, gap-segmented windows.
- `docs/evidence/s1/ (new)` — Manifests, repro and discontinuity notes.

**Context updates**
- `docs/PROTOCOL.md` — Ledger row template: date, hypothesis, manifest path, commit, n, result, verdict; add the 2026-07-17 SpotCrude result now only in trading_config.json:30.
- `CLAUDE.md` — State that research must go through research_data.py and one backtest at a time.

## S2

The paper forward-test is run on a feed the engine itself refuses to trust when unhealthy, and the paper record is sealed so it cannot be quietly rewritten.

**Entry criteria**
- S1 exit gates met for the pattern entering paper test.
- feed_monitor writes FEED_UNHEALTHY reliably (S0 drills passed).

**Work**
- Feed-health gate: limits_enforcer.allow_trade gains a feed check that FAILS CLOSED for new entries when the flag is set, the flag table is unreadable, or the monitor heartbeat is older than 3 min. Contrast is_kill_switch_active, which fails open on any error (limits_enforcer.py:154-167). Exits and reconciler are never blocked.
- signal_generator.calculate_metrics (lines 82-103) has no freshness check (grep finds none in the engine); add tick-age (broker-time aware) and last-bar-age checks.
- broker_adapter_mt5.send_order falls back to the last current.ask when MT5 gives no tick (lines 97-108); refuse that fallback when the feed is unhealthy and store price_source and tick_age_s on paper_orders via migration.
- Paper-vs-ticks replay: nightly, for each paper entry, reconstruct the fill from ticks at signal time and compare with the recorded fill.
- Seal the record: nightly export of signals, paper_positions, paper_orders to docs/evidence/s2/ledger/YYYY-MM-DD.csv with a chained sha256 in seal.csv; commit and push (off-machine, timestamped by git history). signal_generator daily reports are .txt (line 327) and git-ignored, and the already-ran check relies on a local file (line 391).
- Keep R1 running; add weekly drift report on spread distribution per symbol.

**Risks**
- False positives at session edges miss entries; accept, log, tune from the session profile.
- Seal files in git expose strategy details if the repo is ever shared; keep secret-free and confirm repo visibility.
- Paper P&L formula is approximate (pnl_points*lots*1000, broker_adapter_mt5.py ~line 196); sealing preserves it, does not fix it.

**Exit gates**

| Metric | Threshold | Evidence artifact |
|---|---|---|
| Paper entries taken while FEED_UNHEALTHY or monitor silent | 0; blocked attempts logged as blocked_by_feed | `docs/evidence/s2/gate_log.md` |
| Tick age at entry (broker-time aware) | p99 <=5s, max <=30s over the whole test | `docs/evidence/s2/tick_age.md` |
| Paper fill vs replayed tick fill | |difference| <= 1 median spread for >=99% of entries | `docs/evidence/s2/replay_check.md` |
| Feed coverage during the test window (>=20 trading days) | >=99.0% on traded symbols, 0 unexplained gaps >10 min | `docs/evidence/s2/coverage.md` |
| Sealed record continuity | one seal row per trading day, chain verifies end to end, pushed to remote within 24h | `docs/evidence/s2/seal.csv` |

**Protocol — FAIL-CLOSED-ENTRIES**
- No data health signal means no new entry.
- Gate reason is stored with the blocked signal (mark_signal ignores its notes argument today).
- Gate thresholds live in config/trading_config.json, not in code.
- Any gate change restarts the evidence window.

**Repo changes**
- `KLDA-HFT/trading-engine/limits_enforcer.py, signal_generator.py, broker_adapter_mt5.py, order_router.py` — Feed gate, freshness checks, price_source/tick_age columns, store block reason.
- `KLDA-HFT/monitoring/seal_day.py (new)` — Nightly export plus hash chain.
- `KLDA-HFT/config/trading_config.json` — Add feed_gate block (max tick age, max bar age, heartbeat timeout).

**Context updates**
- `docs/RUNBOOK.md` — What 'blocked_by_feed' means and the first three things to check.
- `docs/PROTOCOL.md` — Decision D9: engine fails closed on data health.

## S3

Broker truth reconciles with our database: every demo order, fill, position and balance is matched to MT5 records, and the demo/live feed difference is measured.

**Entry criteria**
- S2 gates met.
- Demo account identity recorded (login, server, base currency, leverage); none is recorded in the repo for the ~25k stage.

**Work**
- Migration adding account_id and mode (PAPER/DEMO/LIVE) to signals, paper_*, trades, account_snapshots so modes never mix.
- Nightly broker_deals import from MT5 history (history_deals_get) and reconcile to our orders by ticket; positions_get vs DB positions.
- Account snapshot writer for the order_router path (account_snapshots is written only by klda_engine.py today).
- Slippage measured against OUR tick stream at order time, which needs the S0 timebase.
- Record which account/server the bridge captures from (logged at bridge line 76); if execution account differs from capture account, measure demo-vs-capture mid difference over 10 days.
- Boot lock: after any restart, entries stay disabled until positions_get equals DB positions (RECONCILED flag).

**Risks**
- Demo and live quotes may differ, weakening paper-to-demo comparison.
- MT5 history depth limits late reconciliation; import nightly.

**Exit gates**

| Metric | Threshold | Evidence artifact |
|---|---|---|
| Demo orders matched to a broker deal ticket | 100% | `docs/evidence/s3/deal_match.md` |
| Unexplained position or balance differences broker vs DB | 0 over 20 trading days | `docs/evidence/s3/recon_daily.md` |
| Slippage and demo-vs-capture quote difference | distribution published; median |mid difference| <= 1 median spread, or divergence explained | `docs/evidence/s3/slippage_feed_diff.md` |
| Post-reboot reconciliation | entries stay locked until RECONCILED; tested once with open demo position | `docs/evidence/s3/reboot_with_position.md` |

**Protocol — BROKER-IS-TRUTH-FOR-MONEY**
- Positions, fills and balances come from MT5; ticks come from our DB; the two are reconciled daily.
- Any mismatch is P1 and blocks entries.
- Every money row carries account_id and mode.

**Repo changes**
- `KLDA-HFT/database/migrations/ (add)` — account_id/mode columns, broker_deals table, reconciliation view.
- `KLDA-HFT/monitoring/broker_recon.py (new)` — Deals and positions import plus daily diff.

**Context updates**
- `docs/PROTOCOL.md` — Record demo account identity and capture account; fix RUNBOOK.md:75 vs docs/DEMO_ACCOUNT.md:20 (4+ weeks vs 2 weeks).
- `docs/RUNBOOK.md` — RECONCILED lock and how to clear it.

## S4

A data-side assurance pack that an outsider could audit: disaster recovery proven from the off-machine copy, first independent price check, lineage replay, least-privilege roles and exposure evidence.

**Entry criteria**
- S3 gates met.
- No open P1 alert for 30 days.

**Work**
- DR drill: restore from the off-machine copy onto a different folder/drive, run health --report and a backtest, compare hashes.
- Reconciliation R2 first pass: independent price source on the 2+ symbols the validated pattern trades, 4 weeks (tier chosen in question 9). Compare per 5-min bucket close and tick-count ratio.
- Lineage replay: for 3 random trades, rebuild signal inputs from restored archives and match pattern_data.
- Roles live: bridge uses klda_writer, engine and API klda_app, dashboards and MCP klda_ro; verify truncate as app role fails.
- Re-run exposure scan and secrets scan; confirm repo visibility and history exposure of the old password.
- Evidence index docs/evidence/INDEX.md covering S0-S3.

**Risks**
- Symbol naming and contract-roll differences make cross-source comparison noisy; start with 2 liquid symbols.
- Vendor/second-broker licence terms (verify_externally).

**Exit gates**

| Metric | Threshold | Evidence artifact |
|---|---|---|
| DR drill age and result | <=30 days old, counts and hashes match, RTO within RUNBOOK target | `docs/evidence/s4/dr_drill.md` |
| R2 coverage and divergence on traded symbols | bucket coverage >=99.0%; divergence beyond max(3x median spread, calibrated bps) in <=0.5% of buckets; each breach explained | `docs/evidence/s4/recon_r2.md` |
| Lineage replay | 3/3 reproduce recorded inputs within 0.01% relative | `docs/evidence/s4/lineage.md` |
| Least privilege | app role cannot TRUNCATE/DROP ticks; writer role cannot read users | `docs/evidence/s4/roles_test.md` |
| Exposure and secrets re-scan | same as S0 gates, repeated | `docs/evidence/s4/exposure_secrets.md` |

**Protocol — INDEPENDENCE-TIERS**
- R1 pipeline-independent: same broker, different path (broker M1 history).
- R2 broker-independent: another broker or vendor price.
- A source counts as independent only if its failure causes differ from the primary.
- Breaches are investigated before any allocation decision.

**Repo changes**
- `KLDA-HFT/database/migrations/ (add)` — ticks_ref hypertable (time, symbol, source, bid, ask) isolated from ticks so nothing existing reads it.
- `KLDA-HFT/monitoring/recon_r2.py (new)` — Ingest second source and compare.
- `docs/evidence/INDEX.md (new)` — Index of all gates and artifacts.

**Context updates**
- `docs/PROTOCOL.md` — Second source choice, symbol mapping table location, calibrated thresholds.
- `CLAUDE.md` — Roles and which script uses which credential.

## S5

Company-grade records: tamper-evident audit data, short recovery point for state tables, evidence register with hashes, and monthly reconciliation to broker statements.

**Entry criteria**
- S4 gates met.
- Account opened; identity and base currency written down (not in the repo today).

**Work**
- Enable audit_log immutability: the RULEs are commented out (create_compliance_tables.sql near line 44) and the API connects as postgres; use a role without UPDATE/DELETE on audit_log.
- Hourly dump of state tables (signals, paper_*, trades, audit_log, investor_ledger, nav_history, users, account_snapshots, broker_deals) to the off-machine target: RPO <=1h for state, 24h for ticks.
- evidence_files table: sha256, kind, period for broker statements, agreements and monthly reports kept outside git; register at ingest.
- Monthly statement reconciliation: DB-derived balance vs broker statement.
- Account identity monitor: alert if mt5.account_info login/server differs from expected record.
- Audit-volume control: trading_terminal.html polls every 0.3s and 1s (lines 1399-1400) and each request writes an audit row (trading_api.py:177-181); decide what is logged before the table drowns real events.

**Risks**
- Local-only storage of investor data has data-protection implications (verify_externally).
- Hourly sync to a disconnected drive is impossible; use a networked or cloud target for state tables only.

**Exit gates**

| Metric | Threshold | Evidence artifact |
|---|---|---|
| audit_log tamper test as application role | UPDATE and DELETE rejected | `docs/evidence/s5/audit_immutability.md` |
| State-table restore to T-1h in rehearsal | succeeds; row counts match | `docs/evidence/s5/rpo_test.md` |
| Monthly broker-statement reconciliation | |DB balance - statement balance| <= 0.01 account currency, 2 consecutive months | `docs/evidence/s5/statement_recon.md` |
| Evidence register coverage | 100% of statements and agreements registered with sha256 | `docs/evidence/s5/evidence_register.md` |

**Protocol — RECORDS-NEVER-AUTO-DELETE**
- No retention policy deletes company records; deletion is a manual, logged, owner-approved action after external advice on retention periods.
- Backups of records are encrypted; keys not in repo.
- Monthly: verify one random record restores from off-site.

**Repo changes**
- `KLDA-HFT/database/migrations/ (add)` — evidence_files, roles and grants, audit_log rules.
- `KLDA-HFT/monitoring/state_backup.py (new)` — Hourly state dump plus sync.

**Context updates**
- `docs/RUNBOOK.md` — Monthly close checklist: statement ingest, reconcile, seal, off-site verify.
- `docs/PROTOCOL.md` — Record RPO/RTO and retention rules once advisers confirm.

## S6

Operational resilience under real capital: every allocation increase is gated on a data-health certificate, and a PC outage has a rehearsed human fallback.

**Entry criteria**
- S5 gates met.
- Written PC-dead procedure exists.

**Work**
- Ramp certificate before each increase: last 20 trading days data-health summary from feed_gaps, recon_results, alert log.
- PC-dead procedure: how to close positions from the broker mobile app, whom to call, what the reconciler cannot do (it manages only PAPER positions, reconciler.py:159-161; live positions rely on broker-side SL/TP).
- UPS runtime test and unplanned-power test with open position; verify RECONCILED lock.
- Weekly data-health review; monthly alert test; quarterly DR drill.

**Risks**
- Phone fallback depends on broker app access; test it.
- Paper-mode flag is the only guard until S6; changing it follows engine/governance lenses.

**Exit gates**

| Metric | Threshold | Evidence artifact |
|---|---|---|
| Data-health certificate per ramp step | coverage >=99.0%, 0 unreconciled positions, 0 P1 unacknowledged >15 min, DR drill <=30 days, UPS test <=90 days | `docs/evidence/s6/ramp_log.md` |
| Power-loss test with open position | orderly recovery; RECONCILED before entries; no unprotected position | `docs/evidence/s6/power_loss_test.md` |

**Protocol — NO-CERTIFICATE-NO-INCREASE**
- Allocation changes are a ramp_log row with the certificate attached.
- A failed certificate blocks the increase, not trading at the current size.
- Any P1 data incident resets the 20-day window.

**Repo changes**
- `docs/evidence/s6/ramp_log.md (new)` — Certificates.
- `KLDA-HFT/monitoring/ramp_certificate.py (new)` — Generates the certificate from tables.

**Context updates**
- `docs/RUNBOOK.md` — PC-dead procedure and contacts.

## S7

Independence at scale: broker-independent price checks on all traded symbols, a second capture path, cold-storage tiering and capacity headroom.

**Entry criteria**
- S6 running stably for >=60 days.

**Work**
- R2 on every traded symbol, automated alerts on divergence.
- Second capture path (second PC or second terminal) writing to ticks_ref; failover drill.
- Cold tier: move old tick archives to external/NAS; optional columnar export for research speed.
- Capacity test at 2x symbols.
- Universe governance: new Market Watch symbol requires a spec snapshot and warm-up days before it can trade.

**Risks**
- Second machine means second place secrets must be protected.
- Vendor cost and licence.

**Exit gates**

| Metric | Threshold | Evidence artifact |
|---|---|---|
| R2 coverage and divergence over 60 days | coverage >=99.5%; breaches <=0.1% of buckets, each explained | `docs/evidence/s7/recon_r2_60d.md` |
| Failover drill | capture resumes <=15 min after primary loss; gap recorded and backfilled | `docs/evidence/s7/failover.md` |
| Capacity at 2x symbol count | p95 insert latency <1s, signal cycle unaffected | `docs/evidence/s7/capacity.md` |

**Protocol — UNIVERSE-CHANGE**
- Universe diff alert on any add or drop.
- New symbol: spec snapshot, 20 clean days, then eligible.
- Dropped symbol: stays in history; marked in symbol_events.

**Repo changes**
- `KLDA-HFT/monitoring/ (extend)` — Automated R2 and failover checks.

**Context updates**
- `docs/PROTOCOL.md` — Independence tiers achieved and dates.

## Cross-cutting protocols

**FEED-TRUTH** — Feed died silently ~2 months (PROTOCOL.md:51-52); sample-size wall makes every lost day costly (PROTOCOL.md:89-91). ticks has no unique index (restructure_universal.sql), so ON CONFLICT DO NOTHING in the bridge (line 162) never fires and only the in-memory last_msc prevents duplicates.
- Raw ticks are append-only: no UPDATE/DELETE/TRUNCATE outside a numbered, rehearsed migration; quality flags live in sidecar tables.
- Every expected-active minute is covered or has a feed_gaps row with cause and resolution; unexplained = P1.
- Each completed day per symbol has data_day_status (CLEAN/GAPPED/BACKFILLED/SUSPECT/NO_DATA) by 06:00 next day; research and evidence use CLEAN only.
- Backfill only into recorded gaps, recompute spread in points, log the batch, mark the day BACKFILLED.
- Freshness = advancing high-water mark or tick time vs broker_now(); never NOW() - last_updated (still in QUICK_CHECK_PRICES.bat:10, trading_api.py, main_live.cpp:376).
- Completeness is cross-checked nightly against the broker's own bars; price correctness against an independent source from S4.

**TIMEBASE** — Stored time = PC-zone rendering of the MT5 epoch (bridge line 126) into TIMESTAMPTZ; time-of-day research (PROTOCOL.md:92-94) is only valid on an exact clock, and DST in PC, US and EU zones change on different dates.
- One documented meaning of ticks.time and current.last_updated, proven by measurement (D6).
- New tables store true UTC timestamptz; broker time derived through config_loader.broker_now / to_broker_time.
- Time-of-day features computed from UTC in the instrument session zone.
- Any change in how time is written needs a data_epochs row, a PROTOCOL decision, and a weekend-window restart.
- feed_heartbeat records newest-tick-minus-UTC every minute; alert when it moves >=1h from the proven offset.
- PC clock sync status is checked and reported daily.

**RECOVERABLE** — backup_db.py:10 holds the only restore instruction in the repo; backups share C: with the database (line 24); base-dump behaviour on the hypertable is unverified.
- 3 copies, 2 media, 1 off-site; at least one copy disconnected from the PC.
- sha256 manifest for every backup file, verified daily; a failed or missing backup is P1.
- Restore rehearsal quarterly and after any backup-script change; RTO/RPO written in RUNBOOK.
- Day archives are versioned, never overwritten.
- Nothing is deleted locally until the same file is verified on the second medium; tick archives are never auto-pruned.
- Encryption keys stored outside the repo and outside the PC.

**BOOT-AND-WATCH** — Pipeline dies silently on reboot (RUNBOOK.md:12); start_all.bat uses fixed timeouts, does not launch MT5, and nothing supervises watchdog.py (line 56).
- Power-on to feed-advancing needs no human step, proven by drill.
- Every long-running process restarts itself and writes a heartbeat; silence is an alert.
- One alert path lives outside the PC (dead-man's switch), because a dead PC cannot report itself.
- Each alert text names the RUNBOOK section to read; P1 reaches the phone in <=5 min; monthly test alert.
- Data-path edits and restarts only in the window Fri 23:55 to Mon 03:00 broker time, except incident response.
- After any unplanned reboot the first check is feed advancing.

**LOCAL-ONLY** — trading_api.py:1174, tick_api.py:183, positions_api.py:152 and tick_receiver.py:800 bind 0.0.0.0; http.server 8082 and docker 8081 listen on all interfaces and serve config.json with the DB password.
- Every listener binds 127.0.0.1 explicitly.
- No inbound firewall allow rule for KLDA ports; firewall prompts get Cancel.
- Exposure is verified by command plus a second-device probe after every change to start scripts and quarterly.
- Secrets only in .env or Windows Credential Manager; one loader; no password literal in committed files.
- Remote access only via a private VPN or none; no router port-forward or UPnP.
- Outbound-only traffic is allowed: broker link, alerts, backups, time sync.

**SCHEMA-AND-ROLES** — Several overlapping DDL files (restructure_universal.sql drops tables; schema.sql adds a 1-year ticks retention; create_schema.sql legacy); signals DDL in the repo does not match the columns the code uses.
- The live DB is the truth: migrations/0001_baseline.sql is a schema-only dump; all later changes are numbered forward-only migrations rehearsed on the restore copy.
- Legacy DDL and destructive scripts move to database/legacy/ with DO-NOT-RUN headers and typed confirmation.
- Roles: klda_writer (bridge), klda_app (engine, API), klda_ro (dashboards, MCP, research); postgres only for migrate, backup, restore.
- From S3 every row about intent or money carries account_id and mode.
- No automatic data-deleting policy without a PROTOCOL decision.
- Every migration records who, when, checksum in schema_migrations.

## Anti-patterns
- Do not judge freshness with NOW() - last_updated (QUICK_CHECK_PRICES.bat:10, trading_api.py, main_live.cpp:376); use the advancing high-water mark.
- Do not repair or delete raw ticks in place; flag in sidecar tables.
- Do not run backfill_all_history.py over ranges the bridge already captured: no unique key, duplicates double SUM(volume) in cagg_bars_*; its spread is 0.0 (line 156).
- Do not treat 'a backup file exists' as 'backups work'; only a rehearsed restore counts.
- Do not rely on in-PC alerts alone; a dead PC sends nothing.
- Do not click Allow on a Windows firewall prompt for python or postgres, and do not add an inbound 5432 rule 'temporarily'.
- Do not run restructure_universal.sql, schema.sql, create_schema.sql, truncate_ticks.py, fix_ticks.py on the live DB.
- Do not let the engine fail open on data health; is_kill_switch_active (fails open) is the pattern to avoid.
- Do not edit bridge, watchdog or schema during market hours Mon 03:00 to Fri 23:55 broker time.
- Do not use taskkill /F /IM python.exe in any script (CLAUDE.md); match by command line.
- Do not tune thresholds or compute rolling windows across gaps or on non-CLEAN days.
- Do not commit evidence as .txt or .log: .gitignore ignores both.
- Do not put the DB password, JWT secret, or backup keys in new files; rotate the old password rather than hoping the repo is private.

## Questions for the owner
- Locked decision D4 (PROTOCOL.md:125) says the demo account runs 'on the VPS first'. You want local-only. Should D4 be amended to 'on this PC (optionally a second local machine)', or is an outbound-only VPS allowed? I assumed local-only and changed nothing.
- Locked decision D1 says universe = everything, ranked. The bridge captures whatever is in Market Watch, read once at start (mt5_tick_capture_ALL_TICKS.py:213). I kept it dynamic and added universe-change alerts instead of pinning a list. Agree?
- Alerts: may the PC send outbound email (Gmail app password in .env) and a data-free outbound ping to an external heartbeat service so you are alerted if the whole PC dies? Which phone and email?
- Off-machine backups: which medium (rotating external drive, second PC at another location, encrypted cloud)? Are you comfortable storing encrypted tick archives off-site (see broker terms in verify list)?
- Is github.com/xyVar/KLDAFinTech private? The DB password is in 77 files in this clone and in git history; rotation is needed either way. History rewrite only if it was ever public or shared.
- Retire the C++ Docker live_tracker? It is a second PENDING-signal writer (main_live.cpp:261) and the only reason Postgres must accept Docker connections (DOCKER_INVESTIGATION.md:437). If retired, Postgres can be loopback-only.
- Remote access: RUNBOOK.md section 1 mentions checking the PC via phone or RDP. Local-only means no inbound remote access. Accept alerts-only plus physical checks, or allow a private VPN?
- Hardware: UPS? Laptop or desktop? Is the Desktop folder (backup dir is under it) synced by a cloud client? Current free space on C:? Budget for an external drive? Is Windows auto-logon acceptable?
- Second data source tier at S4 and S7: (a) same-broker second capture path (free, detects pipeline loss), (b) another broker's demo MT5 on this PC (free, independent quotes), (c) paid vendor for the traded symbols. Which, and what budget?
- Should the engine refuse NEW paper entries whenever the feed monitor reports unhealthy or goes silent, even at the cost of missed entries?
- If measurement shows ticks.time is 'broker wall clock labelled as UTC' or PC-zone dependent, do you accept documenting it as an epoch with conversion rules rather than rewriting ~357M rows?
- Keep raw ticks forever on external storage (my assumption, since feed days are the bottleneck), or drop after N months?

## Verify externally (broker / lawyer / accountant)
- Broker (Pepperstone): how far back the server still serves tick history per symbol (backfill feasibility); written terms for storing, archiving and copying market data off-machine; published roll and rollover schedule and price-adjustment rules for SpotCrude, NatGas, NAS100, GER40; notice process for symbol spec changes (digits, point, contract size); server-time convention (NY-close, UTC+2/+3) in writing; whether demo-server quotes equal live-server quotes; trading hours and holiday calendar; how long a demo account stays available.
- Lawyer or accountant (not asserted here): record-keeping periods and formats for company trading records, ledger, NAV and audit trail; whether a PC-local database with off-site copies satisfies them; data-protection duties for investor names and emails held in investor_ledger and in backups; whether hash-chained exports and git push timestamps have any evidentiary value; who may access company records.
- Data vendor or second broker (if chosen): licence to store and reconcile their data, symbol mapping, timestamp convention, outage terms.
- PC state I could not read from this sandbox: contents of .env (JWT_SECRET, DB_HOST); Postgres listen_addresses and pg_hba.conf; Windows firewall inbound rules for 5432, 5002, 5001, 5000, 8081, 8082; router port-forwards or UPnP; Task Scheduler entries 'KLDA-HFT DB Backup' and 'KLDA-DailySpotCrude' and their last results; postgresql-x64-16 start type; whether timescaledb jobs include a retention policy; whether ticks has any unique index; materialized_only on cagg_bars_m5; PC and Postgres time zones; free disk; whether killing terminal64.exe restarts MT5 or the bridge recovers it; behaviour of mt5.initialize when the terminal is closed.
- TimescaleDB version constraints to check against installed docs: unique indexes and added columns on a compressed hypertable; how pg_dump --exclude-table-data treats hypertable chunk tables; restore procedure order.
- Commands in this plan (netstat, tzutil, sc qc, w32tm, scheduled-task settings) were not run here; the local session should run them and record output in docs/evidence.
