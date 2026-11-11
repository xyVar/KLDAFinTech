# Roadmap detail — company-capital lens

> DRAFT, 2026-11-11. One of three independent designs behind `docs/ROADMAP.md`. Numbers marked 'proposed' need owner confirmation. Legal/regulatory/tax items are questions, not facts.

## S0

Make the repo and the PC safe to hold company records. Exposed credentials are rotated, the API is local-only, only the owner can merge to master, a backup restores from outside the C: drive, and the docs state honestly what the compliance tables can and cannot prove.

**Entry criteria**
- Today is 2026-11-11. Checked-out branch lane-a/safety-gate (265ebad) is the newest. master (a61dc17) has CLAUDE.md but not docs/PROTOCOL.md, docs/RUNBOOK.md or KLDA-HFT/config/validated_patterns.json (git ls-tree master), although docs/RUNBOOK.md:64 says they are on master.
- paper_mode is true (KLDA-HFT/config/trading_config.json:3) and validated_patterns.json has validated = {} (line 14), so no live order is possible.
- The Postgres superuser password is written in 72 tracked files (git grep, vcpkg excluded) and entered git history in commit 648e74c (2026-01-16). origin is https://github.com/xyVar/KLDAFinTech and its visibility is unknown to me.

**Work**
- 1. Rotate first, on the PC, before editing any file: new password for the Postgres role postgres, new random JWT_SECRET (64+ chars), new password for user Klda. Treat the old DB password and the default JWT secret 'dev-secret-change-in-prod' (trading_api.py:43) as public forever. Paste no secret into chat, PRs or evidence files.
- 2. One credential file: KLDA-HFT/.env (untracked) plus KLDA-HFT/.env.example (tracked, placeholders). Replace the inline DB_CONFIG dicts in trading-engine/*.py, python-bridge/*.py, database/backup_db.py:27-28, mcp_server.py:25-31 and api/trading_api.py:52-56 with one shared loader that exits if a variable is missing and forces host 127.0.0.1 (CLAUDE.md rule; trading_api.py:52 defaults to 'localhost').
- 3. Split DB roles (names only in the repo, no passwords): klda_writer (bridge: INSERT ticks/current), klda_engine (signals, paper_*), klda_api (SELECT broadly, INSERT-only on audit_log, INSERT on investor_ledger and nav_history), klda_ro (research and MCP, SELECT only). postgres is used only for DDL and backups. GRANTs replace the commented RULEs at create_compliance_tables.sql:44-45.
- 4. Lock the network surface: trading_api.py exits at start if JWT_SECRET is unset or default (line 43); app.run host 127.0.0.1 instead of 0.0.0.0 (line 1174); CORS limited to http://127.0.0.1:5002 and http://localhost:5002 (line 49); start_all.bat:39 opens http://127.0.0.1:5002/ instead of the .html file path; start_all.bat:40 runs http.server 8082 with --bind 127.0.0.1 and serves a folder that does not contain cpp-backend/config.json (it holds the DB password); no raw str(e) returned to the client (trading_api.py:237-238 and the other handlers).
- 5. Make the audit log usable: stop writing a row for every authenticated GET poll (trading_api.py:178-180). Keep logins, failed logins, 401s (currently unlogged, lines 155-163), denials, every write and every export. Failed audit writes must go to a file instead of pass (lines 142-143). Cut over-long usernames before insert (audit_log.username is VARCHAR(50), create_compliance_tables.sql:27).
- 6. mcp_server.py run_query (around line 411) only checks that the text starts with SELECT or WITH and connects as postgres, so a stacked statement would pass. Connect as klda_ro with a read-only session.
- 7. .gitignore: add .env, .env.*, backups/, *.csv.gz, records/ (the nightly archives backups/ticks/ticks_YYYY-MM-DD.csv.gz are not ignored today; only *.dump and backup_*.sql are). git rm --cached the files in strategy/ that hold broker account data: 'Trade report-52028179 2025-12-26 11-50.pdf', '... 11-51.pdf', ReportTester-62101051.xlsx and the Office lock file ~$ReportTester-62101051.xlsx. Move them to C:\Users\PC\KLDA-records\ outside the repo. Do not rewrite history as a substitute for rotation.
- 8. Repo authority: confirm the GitHub repo is private; protect master (pull request required, no force-push, no deletion, owner is the only merger); merge lane-a/safety-gate into master by PR so the gate and the doctrine are on master; add .github/pull_request_template.md and .github/CODEOWNERS.
- 9. Add docs/CAPITAL_RECORDS.md: one table per record (audit_log, investor_ledger, nav_history, compliance_report, account_snapshots, paper_positions) with columns proves / does not prove / missing. Relabel 'SEC/FCA-grade' (create_compliance_tables.sql:3) and 'Compliance-Grade Platform ... audited for regulatory review' (api/trading_terminal.html:257) as 'internal audit trail'.
- 10. Access hygiene: on the PC confirm that create_compliance_tables.sql was run and that user Klda (admin) exists (no seed script in the repo; the only recipe is a comment at create_compliance_tables.sql:86-98 that creates 'admin'). Add scripts/create_admin.py (password via getpass) and a password-change endpoint plus admin reset (PUT /api/users/<id> only changes role and is_active, trading_api.py:334-341; create_user accepts any password, line 298). Require 12+ characters. List all users in the access register.
- 11. Backup honesty: BACKUP_DIR is on C: next to the database (backup_db.py:24). Copy the newest base_*.dump and a tick archive to a device that is not the PC, restore the base dump into a spare database, and compare row counts of users, audit_log, investor_ledger, nav_history.
- 12. Add docs/HANDOFF.md (append-only session log) and docs/DECISIONS.md (dated decisions with owner and superseded-by). Fix the stale lines listed under context_updates.

**Risks**
- Rotation breaks up to 72 scripts at once. Do it with the paper chain stopped and run a one-line connect test per component. Restart the bridge last so the watchdog does not loop.
- The old password stays in history and in any clone or fork. Rotation is the control, not deletion.
- Branch protection may not exist on the owner's GitHub plan. Fallback: the rule is by convention and a weekly check of git log master is recorded in HANDOFF.md.
- Restricting CORS and binding to 127.0.0.1 breaks the file:// launch route and any LAN viewing. That is intended.

**Exit gates**

| Metric | Threshold | Evidence artifact |
|---|---|---|
| Tracked files containing the OLD DB password (git grep count on the checked-out branch, vcpkg excluded) | 0 (today 72) | `docs/evidence/S0-secret-scan.md` |
| Old DB password and old JWT secret still accepted | No: psql with the old password fails authentication; a token signed with the old secret returns 401; each role connects only via 127.0.0.1 | `docs/evidence/S0-rotation.md` |
| trading_api.py listen address and start behaviour | netstat shows 127.0.0.1:5002 only (not 0.0.0.0); the server exits when JWT_SECRET is missing or default; port 8082 bound to 127.0.0.1 | `docs/evidence/S0-api-lockdown.md` |
| audit_log rows written in one hour with the terminal open and no user action | 100 or fewer (the code logs every authenticated poll today, trading_api.py:178-180) | `docs/evidence/S0-audit-volume.md` |
| Restore rehearsal: tables users, audit_log, investor_ledger, nav_history with equal row counts in source and restored copy; copy held off the PC's C: drive | 4 of 4 equal and 1 off-PC copy | `docs/evidence/S0-restore-rehearsal.md` |
| master protection and content | PR required, force-push blocked, owner sole merger; docs/PROTOCOL.md, docs/RUNBOOK.md and config/validated_patterns.json present on master | `docs/evidence/S0-github-settings.md` |
| Users in the users table not on the access register | 0; Klda confirmed as admin; every user has role and last_login recorded | `docs/evidence/S0-access-register.md` |

**Protocol — Rotate-Then-Remove**
- Rotate on the PC first. The old value is public forever because it is in history since 648e74c.
- Evidence files name the credentials rotated and the test result. They never contain a value.
- Afterwards, git grep for the old value returns 0 hits on the working tree. History is rewritten only if the owner decides.
- Each component has its own DB role. postgres is for DDL and backups only.
- If any secret is ever pasted into chat, a PR or a file, rotate it again the same day.

**Protocol — Honest Audit Label**
- Docs and UI call audit_log, investor_ledger and nav_history an internal record until a lawyer or accountant says otherwise.
- Every capital claim in a doc names the table and what it cannot prove (docs/CAPITAL_RECORDS.md).
- The audit log records auth events, denials, writes and exports. Read polls are not logged.

**Repo changes**
- `.gitignore` — Add .env, .env.*, backups/, *.csv.gz, records/. Keep *.txt and *.log ignored, and write evidence as .md or .json.
- `KLDA-HFT/.env.example` — New. Variable names with placeholders: DB_HOST=127.0.0.1, DB_USER per role, JWT_SECRET, optional SMTP settings (hourly_health_check.py:29-31 holds placeholder mail settings today).
- `KLDA-HFT/common/db_config.py` — New shared loader used by every script that now has an inline DB_CONFIG. Exits with a clear message if a variable is missing.
- `KLDA-HFT/database/roles.sql` — New. CREATE ROLE and GRANT statements for klda_writer, klda_engine, klda_api, klda_ro. No passwords. audit_log, investor_ledger and nav_history have no UPDATE or DELETE grant for klda_api.
- `KLDA-HFT/api/trading_api.py` — Refuse default JWT_SECRET (line 43); bind 127.0.0.1 (line 1174); restrict CORS (line 49); log 401s and write failures; stop logging GET polls; hide DB errors from clients; add POST /api/me/password and admin reset with 12-character minimum.
- `KLDA-HFT/mcp_server.py` — run_query connects as klda_ro with a read-only transaction; remove the superuser password literal (lines 25-31).
- `KLDA-HFT/scripts/create_admin.py` — New. Creates or resets an admin with getpass, writes a USER_CREATE audit row.
- `KLDA-HFT/start_all.bat` — Line 39 opens http://127.0.0.1:5002/; line 40 adds --bind 127.0.0.1 and serves a folder without config.json.
- `KLDA-HFT/database/create_compliance_tables.sql` — Relabel the header (line 3); replace the commented RULEs with a pointer to roles.sql; the comment recipe at lines 86-98 must not show a password.
- `KLDA-HFT/api/trading_terminal.html` — Line 257: replace 'Compliance-Grade Platform ... regulatory review' with 'Internal audit trail'.
- `strategy/` — git rm --cached the broker trade-report PDFs, ReportTester-62101051.xlsx and the ~$ lock file. Keep the .md strategy notes.
- `docs/CAPITAL_RECORDS.md` — New. Proves / does not prove / missing table for each record, plus the three-layer Capital Truth Ladder.
- `docs/HANDOFF.md` — New. Append-only session log (format under the Merge Authority protocol).
- `docs/DECISIONS.md` — New. The 5 locked decisions copied from docs/PROTOCOL.md:120-126 with a date column and a superseded-by column; later decisions are appended.
- `docs/evidence/` — New folder with the seven S0 evidence files.
- `.github/pull_request_template.md and .github/CODEOWNERS` — New. Checklist: no secrets, evidence path, paper_mode unchanged unless an S6 PR. Owner's GitHub login as owner of KLDA-HFT/config/, KLDA-HFT/trading-engine/ and docs/PROTOCOL.md.

**Context updates**
- `CLAUDE.md` — Add a 'Secrets and access' section: .env only, never print it, DB host 127.0.0.1, per-component DB roles, API is loopback-only, evidence lives in docs/evidence/. Add first-read order: docs/PROTOCOL.md, docs/CAPITAL_RECORDS.md, docs/RUNBOOK.md. Fix stale lines: SYSTEM_ARCHITECTURE.md, WHAT_WE_ARE_BUILDING.md and archive/ do not exist in the repo; test_mt5_connection.py is in KLDA-HFT/python-bridge/; compile_renaissance.bat is not in the repo.
- `docs/PROTOCOL.md` — Replace the stale top risk at line 56 ('months of engine code UNCOMMITTED', committed 2026-07-03) with the current risks: credentials in git history, no account-identity check, compliance records typed by hand. Fix 'Last updated'. Add a pointer to docs/DECISIONS.md.
- `docs/RUNBOOK.md` — Line 54 'Nothing trades automatically' must say the paper chain (signal_generator, order_router, reconciler) is started by start_all.bat:33-35 and writes paper rows only. Add section 'Rotate credentials' and a one-page 'Stop everything' card. Replace the stage list at lines 69-76 with S0 to S7. Line 76 'earliest late Sep 2026' is past; remove the date.

## S1

The first pattern's pass becomes a reproducible, hash-checked record that can later authorise capital. It is no longer a number in a JSON comment.

**Entry criteria**
- All S0 exit gates met.
- The gate constants are unchanged: 100 occurrences, 51% win rate, p below 0.05 (trading-engine/config_loader.py:26-28) and net_pnl_pct above 0 (config_loader.py:84).
- validated_patterns.json is still empty. The only recorded near-miss is SpotCrude: 58.4%, 243 trades, p=0.005, net -0.30%, PF 0.70 (trading_config.json:30), which is not in the PROTOCOL research ledger.

**Work**
- 1. Write one evidence file per candidate: docs/evidence/S1-<SYMBOL>-<PATTERN>.md from a template. Fields: script path and commit hash, data range, data source, n, win rate, p-value, net P&L after costs, exit geometry (tp_pct/sl_pct), number of variants tried in the same family, sha256 of trading_config.json.
- 2. Add evidence_sha256 and family_size to each validated_patterns.json entry. is_validated() (config_loader.py:65-92) refuses an entry whose evidence file is missing or whose hash differs.
- 3. Add the 2026-07-17 SpotCrude result to the PROTOCOL research ledger with its evidence path, and add data range, script, commit and evidence path columns to the ledger table.
- 4. A validated_patterns.json change goes in only by PR that quotes the evidence path. The owner merges it.
- 5. Resolve in PROTOCOL one definition of 'validated': CLAUDE.md:13 omits the net-positive condition that config_loader.py:84 enforces.

**Risks**
- The p-value is read on the same data the thresholds were tuned on. Recording family_size makes this visible but does not correct it. The correction method belongs to the research roadmap.
- If the evidence file is edited later, the hash check blocks live orders. This is intended friction.

**Exit gates**

| Metric | Threshold | Evidence artifact |
|---|---|---|
| Required fields present in the candidate's evidence file | 9 of 9 | `docs/evidence/S1-<SYMBOL>-<PATTERN>.md` |
| is_validated(symbol, pattern) result on the PC with the hash check enabled | (True, 'validated'); and False after one byte of the evidence file is changed | `docs/evidence/S1-gate-run.md` |
| Entry stats against the locked gate: occurrences, win_rate, p_value, net_pnl_pct | occurrences 100 or more, win_rate 0.51 or more, p_value below 0.05, net_pnl_pct above 0 | `KLDA-HFT/config/validated_patterns.json` |
| Research-ledger rows dated after 2026-07-17 that lack a data range, commit or evidence path | 0 | `docs/PROTOCOL.md` |

**Protocol — Evidence-Or-Nothing**
- No validated_patterns.json entry without an evidence file in the same PR.
- The evidence file reproduces from the recorded script and commit. A second run gives the same n, win rate and p.
- The number of variants tried is recorded so a reviewer can judge the p-value.
- Only the owner merges the PR that adds an entry.

**Repo changes**
- `docs/evidence/_TEMPLATE_gate.md` — New template with the nine required fields.
- `KLDA-HFT/config/validated_patterns.json` — Extend the _example (lines 3-13) with evidence_sha256 and family_size. Keep validated empty until a pattern passes.
- `KLDA-HFT/trading-engine/config_loader.py` — is_validated() also checks that the evidence file exists and its sha256 matches.
- `docs/PROTOCOL.md` — Research ledger: add columns data range, script, commit, evidence path; add the 2026-07-17 SpotCrude row.

**Context updates**
- `docs/PROTOCOL.md` — State the single definition of 'validated' (the four conditions in config_loader.py) and the Evidence-Or-Nothing rule.
- `CLAUDE.md` — Replace the sentence at line 13 about validation with a pointer to PROTOCOL's definition, and say that a pattern counts as validated only through an evidence file plus a validated_patterns.json entry.

## S2

Paper results become a clean, attributable track record: every decision names the account, code version and config version, and paper numbers are fenced off from capital records. The broker questionnaire goes out now because the answer lead time is unknown.

**Entry criteria**
- S1 gate met: at least one entry in validated_patterns.json with evidence.
- The paper chain is running (start_all.bat:33-35: signal_generator, order_router, reconciler).
- Known defect to respect: paper pnl_eur is pnl_points * lots * 1000 'approximate for CFDs' (broker_adapter_mt5.py:198), so it is not money. mark_signal drops its notes argument (order_router.py:58-63), so REJECT reasons are not stored.

**Work**
- 1. Add an append-only decision_log table: id, ts, signal_id, symbol, event (FIRED, REJECTED, FILLED, FAILED, CLOSED_SL, CLOSED_TP, CLOSED_EOD, KILL), reason, account_login, code_commit, config_sha256, paper. order_router.mark_signal and reconciler write to it.
- 2. code_commit comes from git on the PC. A dirty tree is recorded as 'DIRTY' and rows with DIRTY are excluded from the forward-test statistics.
- 3. Write database/seal_records.py, run after the 02:30 backup: row counts, max ids and sha256 of a canonical dump of audit_log, investor_ledger, nav_history, signals, decision_log, paper_positions, paper_orders into a small JSON. Copy the seal to a second place off the PC (email to self or cloud drive).
- 4. Add monitoring/track_record.py: reads paper_positions and decision_log and writes docs/evidence/S2-track-record.md with n, win rate, results in points (not EUR), per symbol. A second run must give the same hash.
- 5. Create docs/BROKER_ONBOARDING.md from the BROKER questions under verify_externally. Send them to Pepperstone support in writing and log the date and each answer. Start the accountant and lawyer questions in parallel.
- 6. Fence paper from capital: no paper figure goes into investor_ledger or nav_history. Make the PROTOCOL statement explicit and add a column comment on paper_positions.pnl_eur.

**Risks**
- Paper P&L is approximate (broker_adapter_mt5.py:198). Anyone comparing it to account money will be misled.
- Another signal writer (the Docker C++ live_tracker) may be inserting rows. Check signals GROUP BY pattern_name before trusting the window.
- Seals prove consistency from the day they start. They cannot prove earlier rows were honest.

**Exit gates**

| Metric | Threshold | Evidence artifact |
|---|---|---|
| paper_positions, paper_orders and signals rows created after the migration with NULL account_login, code_commit or config_sha256 | 0 | `docs/evidence/S2-provenance-check.md` |
| Trading days in the forward-test window that have a seal file in two places | 100 percent of trading days | `docs/evidence/S2-seal-coverage.md` |
| Paper positions in the window whose signal pattern_name differs from the validated pattern (for example rows from the C++ live_tracker or a hand-inserted test signal) | 0 | `docs/evidence/S2-track-record.md` |
| Track-record export run twice on the same data | identical sha256 | `docs/evidence/S2-track-record.md` |
| investor_ledger and nav_history rows created during the S2 window | 0 | `docs/evidence/S2-provenance-check.md` |
| Broker questionnaire sent in writing | 1 of 1, with date and recipient logged | `docs/BROKER_ONBOARDING.md` |

**Protocol — Provenance Stamp**
- Every decision row names account_login, code_commit and config_sha256.
- A row from a dirty tree is stamped DIRTY and never counts toward a gate.
- Test signals use pattern_name 'MANUAL_TEST' and are excluded by query. order_router takes any PENDING row, so an untagged test signal looks like a real trade.
- Only one process may write signals for the validated pattern. The C++ live_tracker also inserts PENDING BUY rows (main_live.cpp), so each row's source must be distinguishable.

**Protocol — Fence Paper From Capital**
- Paper figures are in points. No paper figure is written to investor_ledger or nav_history.
- Reports say 'paper' in the title and filename.
- The drill rows for ledger and NAV go only to a restored copy, never to production.

**Repo changes**
- `KLDA-HFT/database/migrations/001_decision_log.sql` — New decision_log table (append-only; klda_engine has INSERT and SELECT only).
- `KLDA-HFT/trading-engine/order_router.py` — mark_signal (lines 58-63) writes status and reason to decision_log; stamp provenance on FILLED.
- `KLDA-HFT/trading-engine/reconciler.py` — Write CLOSED_SL, CLOSED_TP, CLOSED_EOD events to decision_log.
- `KLDA-HFT/database/seal_records.py` — New daily seal job, scheduled after the 02:30 backup in Task Scheduler.
- `KLDA-HFT/monitoring/track_record.py` — New reproducible forward-test export.
- `docs/BROKER_ONBOARDING.md` — New. Question list, date sent, answer log, who answered. Contains no KYC documents or personal data.

**Context updates**
- `docs/PROTOCOL.md` — Add a research-ledger row for the forward-test start: date, commit, config hash, symbols. State that paper results are points-based and not capital.
- `docs/RUNBOOK.md` — Daily check (section 1) adds: today's seal exists in both places; decision_log has rows for today.
- `CLAUDE.md` — Describe decision_log and the daily seal in the data-pipeline diagram.

## S3

Real MT5 order flow on the demo account (about 25k) with account identity enforced in code, every fill recorded in the database, and the broker's own deal history reconciling to the database.

**Entry criteria**
- S2 gates met.
- A demo account exists with its login, server, leverage, currency and starting balance written down. Today no 25k demo is recorded anywhere; docs/DEMO_ACCOUNT.md describes EA-era account 62101051 with leverage, currency and balance 'To be verified'.
- Decision 4 wording is settled (it says 'on the VPS' at PROTOCOL.md:125; the project constraint is local-only). See questions_for_owner.

**Work**
- 1. Create KLDA-HFT/config/accounts.json (tracked, no passwords): login, server, kind (DEMO, LIVE_PERSONAL, LIVE_COMPANY), currency, leverage, allowed_stages, allocated_capital, status. Add the demo; add the personal account 52028179 with allowed_stages empty.
- 2. Account Identity Gate in code: broker_adapter_mt5 (live branch, lines 141-167), limits_enforcer, kill_switch, reconciler and klda_engine compare mt5.account_info().login with accounts.json for the current stage and refuse on mismatch, writing a decision_log row. Today mt5.initialize() takes no arguments and no code compares the login.
- 3. Record every live fill: the live branch returns only a dict (broker_adapter_mt5.py:168-169 and the failure branch) and writes no database row. Add an executions table: signal_id, ticket, symbol, side, lots, signal price, fill price, slippage_points, retcode, sl, tp, broker time, account_login. The MT5 order comment is already KLDA_SIG_<signal_id> (line 163), so deal history joins to signals.
- 4. Add monitoring/reconcile_broker.py: pull MT5 deal history for the window and match to executions by comment and ticket. Report unmatched in both directions.
- 5. Add a feed_sessions table written by the bridge at connect (mt5_tick_capture_ALL_TICKS.py logs Account and Server at connect): started_at, login, server, bridge commit. Every tick time range maps to an account.
- 6. Run the terminal on a read-only (investor) login for the bridge and paper chain, and the trading login only inside deliberate test windows. First confirm with the broker that a read-only password exists.
- 7. Drills on demo: wrong-account drill, kill-switch drill with open positions (kill_switch.py closes every MT5 position, with no filter on magic 234000), end-of-day flat check.
- 8. Live end-of-day close: reconciler only manages paper positions and warns that live positions are not closed (reconciler.py main). Implement and test a live equivalent on demo before S4.

**Risks**
- Demo spreads, fills and slippage may be more favourable than live (docs/DEMO_ACCOUNT.md safety notes), so S3 slippage is a floor, not a forecast.
- kill_switch.py closes every MT5 position (no magic filter). Safe only on a dedicated account.
- The live branch calls mt5.shutdown() after each order (broker_adapter_mt5.py:165); the same process pattern may also affect the reconciler's price reads. Test on demo.

**Exit gates**

| Metric | Threshold | Evidence artifact |
|---|---|---|
| Demo deals in the window with no matching executions row, plus executions rows with no MT5 deal | 0 and 0 | `docs/evidence/S3-deal-reconciliation.md` |
| Wrong-account drill: terminal logged into an account not allowed by accounts.json, router started | 100 percent refused, 0 orders sent, refusal row in decision_log (1 of 1 drill) | `docs/evidence/S3-identity-drill.md` |
| Kill-switch drill on demo with open positions: time from command to all MT5 positions flat, then next signal result | 60 seconds or less (proposed); next signal REJECTED with KILL_SWITCH_ACTIVE | `docs/evidence/S3-kill-drill.md` |
| Demo positions still open after close_all_at (23:45 broker time) over the window | 0 over at least 10 trading days | `docs/evidence/S3-eod-flat.md` |
| Demo fills recorded with slippage and rejection rate reported against the backtest cost assumptions | 100 or more fills (mirrors the occurrence floor); report written | `docs/evidence/S3-execution-quality.md` |
| Broker questionnaire items with no written answer | 0, or each explicitly deferred with reason | `docs/BROKER_ONBOARDING.md` |

**Protocol — Account Identity Gate (stage rules)**
- Only logins listed in config/accounts.json with the current stage in allowed_stages may receive an order.
- A mismatch refuses the order, writes decision_log and exits non-zero. It never falls back to the next account.
- The terminal uses a read-only login except during a recorded test window.
- Any change to accounts.json goes by PR.

**Protocol — Daily Broker Reconciliation**
- After the 23:45 broker-time close, reconcile_broker.py compares the MT5 deal list with executions.
- Any unmatched deal is an incident. It gets a file in docs/incidents/ before the next trading day.
- Broker time is derived with config_loader.broker_now(), never the PC clock.

**Repo changes**
- `KLDA-HFT/config/accounts.json` — New. Registered accounts, no secrets.
- `KLDA-HFT/trading-engine/broker_adapter_mt5.py` — Identity check before mt5.order_send; write executions row on success and failure; pass the pattern into is_validated (line 144 calls it with the symbol only).
- `KLDA-HFT/trading-engine/limits_enforcer.py` — Identity check in _mt5_init; read limits from config instead of constants (lines 27-33).
- `KLDA-HFT/database/migrations/002_executions_feed_sessions.sql` — New executions and feed_sessions tables.
- `KLDA-HFT/monitoring/reconcile_broker.py` — New. Deal-history to executions reconciliation.
- `KLDA-HFT/python-bridge/mt5_tick_capture_ALL_TICKS.py` — Insert a feed_sessions row on connect (keep the reconnect loop, time_msc dedup and rotating log intact).
- `KLDA-HFT/trading-engine/reconciler.py` — Live end-of-day close path for MT5 positions with the system's magic number.

**Context updates**
- `CLAUDE.md` — Add: config/accounts.json lists the only MT5 logins the code may use; real orders are refused otherwise. Record the demo account number, server and leverage there. Update the live-account line once the broker confirms the 10017 status.
- `docs/PROTOCOL.md` — Resolve the contradiction between line 49 (live account trade-disabled) and line 75 ('block appears lifted'); record the broker's written answer and date.
- `docs/RUNBOOK.md` — Add the demo-window procedure: who logs in, with which password type, how to log out afterwards, and where drill evidence goes.

## S4

A signed assurance packet covering strategy evidence, software controls, capital controls and drills. It has two keys (owner plus an independent reviewer) and must exist before any real capital.

**Entry criteria**
- S0 to S3 gates met; no open high-severity finding in the findings list.
- docs/RISK_POLICY.md does not yet exist.

**Work**
- 1. Write docs/RISK_POLICY.md with numbers: allocated capital for the first live tier, the funding-source cap, per-trade risk (1 percent, locked Decision 3), daily-loss halt as a percent of allocated capital (limits_enforcer.py:27 uses MAX_DAILY_LOSS_EUR = 10.0), drawdown halt, who may lift a halt, no top-up after a loss in the same month.
- 2. Move those numbers into trading_config.json under a risk key and make limits_enforcer read them. Add an automatic drawdown halt that calls the kill switch. Nothing calls kill_switch.py automatically today; it is run by hand.
- 3. Assemble docs/assurance/S4-<date>/: INDEX.md, findings.md, drills.md, plus the S0 to S3 evidence. Code review covers order_router, broker_adapter_mt5, limits_enforcer, kill_switch, config_loader, reconciler, trading_api auth and the compliance endpoints. Review by an independent person plus a tool review of the PR diff.
- 4. Six drills with evidence: D1 wrong account; D2 credential leak (rotate DB password and JWT secret following RUNBOOK); D3 owner away (no acknowledgement for 72 hours blocks new entries); D4 restore from the off-PC copy to a spare database; D5 kill switch; D6 reboot (RUNBOOK section 0 brings the stack back).
- 5. Capital dry run on the restored copy: enter a test SUBSCRIPTION, compute NAV, export the report, and tie out to a mock statement. Drill rows never go to production because investor_ledger and nav_history are permanent.
- 6. Complete the export: GET /api/compliance_report (trading_api.py:541-600) returns trades, audit_log and nav_history only. Add investor_ledger, decision_log, executions, signals and paper_positions, and write a sha256 of the export.
- 7. Decide MFA for admin (TOTP) or record the owner's written acceptance of the risk in DECISIONS.md. Password change and reset must already work (S0).

**Risks**
- A reviewer who is not a programmer can check evidence and drills but not code. Decide who covers the code reading.
- Automatic drawdown halt fires kill_switch.py, which closes every MT5 position. Wrong on any shared account (see S5 separation).
- Drills on a restored copy do not prove production permissions. Run one read-only permission check on production roles as well.

**Exit gates**

| Metric | Threshold | Evidence artifact |
|---|---|---|
| Drills D1 to D6 passed with evidence | 6 of 6 | `docs/assurance/S4-<date>/drills.md` |
| Open high-severity findings | 0 | `docs/assurance/S4-<date>/findings.md` |
| docs/RISK_POLICY.md numeric fields enforced by code (read from config, not constants) | 6 of 6 | `docs/RISK_POLICY.md` |
| Signatures on the packet PR: owner and independent reviewer | 2 of 2, both committed through the PR | `docs/assurance/S4-<date>/INDEX.md` |
| Tables included in /api/compliance_report | investor_ledger, decision_log, executions all present (3 of 3 added); export sha256 recorded | `docs/assurance/S4-<date>/compliance-export.json` |
| Capital dry run on restored copy: difference between computed NAV and mock-statement figure | 0.00 | `docs/assurance/S4-<date>/capital-dry-run.md` |

**Protocol — Two-Key Release**
- Key 1 is the owner. Key 2 is a named person who did not write the change under review.
- The reviewer reads the diff of the gate files, not a summary. Their findings go into findings.md with severity.
- A signature is a commit by that person to the packet PR. A chat message does not count.
- The signed packet's commit hash is the only commit allowed to go live. Any later change to trading-engine/ or config/ voids it.

**Protocol — Drill On The Copy**
- Ledger and NAV drills run only on a restored copy.
- Each drill file records date, who ran it, steps, expected result, actual result.
- A failed drill is fixed and rerun. The failure stays in the file.

**Repo changes**
- `docs/RISK_POLICY.md` — New one-page policy with the numbers above.
- `KLDA-HFT/config/trading_config.json` — Add a risk block (allocated capital, daily-loss percent, drawdown percent, owner-ack hours). Keep paper_mode true.
- `KLDA-HFT/trading-engine/limits_enforcer.py` — Read limits from config; add OWNER_ACK check via the system_flags table (kill_switch.py already uses it); add automatic drawdown halt.
- `KLDA-HFT/api/trading_api.py` — Extend compliance_report; add TOTP for admin if chosen.
- `docs/assurance/S4-<date>/` — New packet folder: INDEX.md, findings.md, drills.md, compliance-export.json, capital-dry-run.md.

**Context updates**
- `docs/PROTOCOL.md` — Add an 'Assurance' section defining the packet and the Two-Key Release rule as a locked decision (owner approves the wording).
- `docs/RUNBOOK.md` — Add a drills section with the exact commands for D1 to D6 so a non-programmer can rerun them every quarter.
- `CLAUDE.md` — Point to docs/RISK_POLICY.md and say the S4 packet commit is the only releasable commit.

## S5

KLDA Technologies' identity, broker account and capital become real and separate from personal funds. Capital under management is a stated number backed by bank and broker documents, reconciled monthly.

**Entry criteria**
- S4 packet signed.
- The owner has recorded in DECISIONS.md whether the company account holds only the company's own money or any third-party money.
- Lawyer, accountant and broker answers to the S5 items in verify_externally are in hand or consciously deferred with a date.

**Work**
- 1. Application: send the BROKER questions, keep the sent and received messages, log each answer in docs/BROKER_ONBOARDING.md. Store KYC documents, statements and bank details only under C:\Users\PC\KLDA-records\ (outside the repo); the repo gets a hash list.
- 2. Separate money: a company bank account used for funding this trading account (accountant to confirm treatment). The personal account 52028179 is never used by the system after this point (accounts.json allowed_stages empty). No personal positions on the company account.
- 3. Register the company account in accounts.json as LIVE_COMPANY with status PENDING. It becomes ACTIVE only after the first broker statement reconciles. Log in read-only first.
- 4. Pricing equivalence: for at least 10 trading days compare the company account's median spread per symbol with the spreads in the data behind the S1 evidence. Spread-drag was the central research finding (PROTOCOL.md:67), so a different account type can invalidate the pass.
- 5. Capital records: allocated_capital in accounts.json is the stated number. Every transfer is a SUBSCRIPTION or REDEMPTION row in investor_ledger with reference_doc naming the bank or broker reference. Entry goes through scripts/record_capital.py (shows a preview, needs typing YES, refuses an empty reference_doc) because the terminal has no form for ledger or NAV.
- 6. broker_equity_eod table filled each day by a read-only job from mt5.account_info(): date, login, server, currency, balance, equity, plus the typed month-end statement figure, its file name and sha256, difference and who reconciled.
- 7. scripts/compute_nav.py writes nav_history from broker_equity_eod and ledger flows. Month end: owner reviews, sets locked = true. Fix POST /api/nav: reject writes to a locked day, return 409 instead of a raw DB error on a duplicate nav_date (UNIQUE, create_compliance_tables.sql:72), keep corrections as a new version row; validate ledger signs (trading_api.py:455 checks only the type).
- 8. Monthly capital statement docs/capital/YYYY-MM.md (totals and hashes, no personal data). Owner signs; a second person with role risk_manager (can read ledger and NAV) countersigns outside the system.
- 9. Sizing base: apply Decision 3 (1 percent per trade) to allocated_capital, not to live equity, once the owner confirms (see questions).

**Risks**
- The company account may have different pricing from the account behind the research data (the live account 52028179 is retail with leverage 1:30 per CLAUDE.md:77). That is the main way a passed gate stops being true.
- The ledger schema uses words like investor, shares and fees (create_compliance_tables.sql:49-83). If the company holds only its own money, the labels may misrepresent it. Lawyer and accountant decide before the first row.
- One admin can enter and approve the same ledger row (approved_by is the entering admin, trading_api.py:470). Four-eyes exists only through the countersign step.

**Exit gates**

| Metric | Threshold | Evidence artifact |
|---|---|---|
| Startup assertion with the company login | passes for LIVE_COMPANY; refuses the personal login (2 of 2) | `docs/evidence/S5-identity-check.md` |
| Cash movements on the first broker statement without a ledger row, and ledger rows without a statement line | 0 and 0 | `docs/capital/<YYYY-MM>.md` |
| Month-end reconciliation: broker statement closing balance versus ledger flows plus realised result from executions | absolute difference 0.5 percent of allocated capital or less (proposed default; owner confirms in DECISIONS.md) | `docs/capital/<YYYY-MM>.md` |
| Funding trace: SUBSCRIPTION rows whose reference_doc traces to a transfer from the company bank account (accountant-confirmed); transfers from personal accounts into the trading account | 100 percent traced; 0 personal transfers | `docs/evidence/S5-funding-trace.md` |
| Median spread on the company account divided by the spread assumed in the S1 evidence, per validated symbol | 1.10 or less (proposed); otherwise the S1 gate is rerun on the new spreads | `docs/evidence/S5-pricing-equivalence.md` |
| BROKER_ONBOARDING questions without a written answer; verify_externally items open without a dated decision | 0 and 0 | `docs/DECISIONS.md` |
| nav_history coverage since first funding; closed months locked | 100 percent of trading days present; all closed months locked = true | `docs/capital/<YYYY-MM>.md` |
| Admin controls: password-change endpoint working and TOTP (or recorded acceptance) | both done | `docs/evidence/S5-access-register.md` |

**Protocol — Capital Movement Rule**
- Money moves only company bank account to broker and back. No personal account on either side.
- Every movement has a ledger row whose reference_doc names the bank or broker reference.
- Top-ups and withdrawals happen on a calendar date after month-end lock. Never right after a loss day, never to get back to a number (PROTOCOL.md:19-20 recovery-trading discipline).
- Corrections are new ADJUSTMENT rows. Rows are never edited or deleted.

**Protocol — Monthly Close**
- Day 1 to 3: download the broker statement; record its sha256 and figure in broker_equity_eod.
- Run compute_nav.py, then reconcile. Difference above tolerance blocks scale-up until explained in writing.
- Owner signs docs/capital/YYYY-MM.md; countersigner signs outside the system; set locked = true.
- Run seal_records.py and confirm the seal is in both places.

**Repo changes**
- `KLDA-HFT/config/accounts.json` — Add the company account (LIVE_COMPANY, PENDING) and allocated_capital with an as-of date. No bank details.
- `KLDA-HFT/database/migrations/003_broker_equity_eod.sql` — New broker_equity_eod table; nav_history version column and uniqueness on (nav_date, version).
- `KLDA-HFT/monitoring/equity_snapshot.py` — New read-only daily snapshot job using mt5.account_info().
- `KLDA-HFT/scripts/record_capital.py` — New guided entry for ledger and NAV through the API.
- `KLDA-HFT/scripts/compute_nav.py` — New. NAV from broker_equity_eod and ledger flows.
- `KLDA-HFT/api/trading_api.py` — POST /api/nav: reject locked day, 409 on duplicate, audit row with body; POST /api/investor_ledger: validate sign by entry_type (line 455), require reference_doc for SUBSCRIPTION and REDEMPTION.
- `docs/capital/` — New folder for monthly statements.
- `docs/DECISIONS.md` — Add capital structure, tolerance, MFA choice, sizing base, and each external answer with its date.

**Context updates**
- `CLAUDE.md` — New 'Capital records' section: never type a ledger or NAV figure from memory; paper numbers are not money; use record_capital.py; terminal has no ledger form; account numbers may be in accounts.json, but statements, KYC and bank details never go in the repo.
- `docs/RUNBOOK.md` — Add 'Monthly close' with exact commands and the countersign step; add 'What to do if the broker statement and NAV disagree'.
- `docs/PROTOCOL.md` — Record the company account (login only), its stage status and the date capital was first stated.

## S6

A small real allocation runs on the company account and scales on conformance and clean books, never on profit or loss. A hard cap on capital at work can change only through a ledger-backed PR.

**Entry criteria**
- S5 gates met; S4 packet commit is the commit running on the PC (recorded by the health report).
- Live end-of-day close and live fill recording are tested on demo (S3).
- Owner has named a delegate and the owner-ack heartbeat is working.

**Work**
- 1. Ramp ladder in RISK_POLICY.md. Proposed tiers: 10, 25, 50, 100 percent of the target allocation, each at least 20 trading days. The owner sets the real numbers.
- 2. Day-1 flip: set paper_mode false by PR with both keys. validated_patterns.json entry present. Switch the terminal from read-only to the trading login only now, and log it in HANDOFF.md.
- 3. Daily: health report, seal, equity snapshot, broker reconciliation. Weekly: automated conformance file comparing live slippage, hit rate and cost per trade with the S3 and backtest numbers.
- 4. Auto-halt: drawdown halt fires the kill switch; missing owner acknowledgement blocks new entries.
- 5. Incident file docs/incidents/YYYY-MM-DD-<title>.md for every unmatched deal, halt, rejection storm or reconciliation breach: what happened, money impact, fix, test of the fix.
- 6. Withdrawals only at month-end after lock, as ledger rows (see Capital Movement Rule).
- 7. Every tier change is a PR changing allocated_capital in accounts.json, backed by a signed capital statement.

**Risks**
- The statistical wall (about 20k trades to detect a 1 percent edge, PROTOCOL.md:79) means live results cannot prove the edge in a tier. Gates therefore test conformance, not profit.
- If the owner is away, 72 hours of blocked entries may skip valid trading days. That is the chosen cost.
- The broker can change terms or close the account (BROKER questions cover this); the plan has a single custodian until S7.

**Exit gates**

| Metric | Threshold | Evidence artifact |
|---|---|---|
| Month-end reconciliation difference for every month in the tier | within tolerance in 100 percent of months | `docs/capital/<YYYY-MM>.md` |
| Live orders sent without both SL and TP | 0 | `docs/evidence/S6-tier-<n>.md` |
| Positions open after close_all_at (23:45 broker time) | 0 across the tier window | `docs/evidence/S6-tier-<n>.md` |
| Live orders on a login not in accounts.json or a symbol outside validated_patterns.json | 0 | `docs/evidence/S6-tier-<n>.md` |
| Live median slippage and rejection rate versus the S3 envelope | within the S3 recorded range (S3-execution-quality.md) | `docs/evidence/S6-tier-<n>.md` |
| Drawdown halts that fired the kill switch automatically, each with an incident file | 100 percent of halts | `docs/incidents/` |
| Trading days between any halt and the next scale-up | 10 or more (proposed) | `docs/RISK_POLICY.md` |
| Closed months with locked NAV and a signed capital statement | 100 percent | `docs/capital/<YYYY-MM>.md` |

**Protocol — Scale On Conformance**
- A tier increase needs a clean reconciliation, zero policy breaches, and live costs within the S3 envelope for the whole tier window.
- Profit alone never triggers a scale-up. A loss alone never triggers a scale-down; the halts do.
- allocated_capital changes only by PR plus a ledger row.
- After any halt, wait the cool-off before the next tier.

**Protocol — Owner-Away Live Rule**
- Without an acknowledgement for 72 hours (proposed), new entries are blocked via system_flags OWNER_ACK.
- The delegate can run the health report and the stop-everything card. The delegate cannot change config, accounts.json or credentials.
- No flip to paper_mode false is allowed while the owner is unreachable for more than 24 hours.

**Repo changes**
- `docs/RISK_POLICY.md` — Add the ramp ladder, cool-off, delegate powers.
- `KLDA-HFT/config/trading_config.json` — paper_mode false by PR on day 1 only. Add the risk.owner_ack_hours value.
- `KLDA-HFT/monitoring/hourly_health_check.py` — Add git HEAD and dirty flag, paper_mode, execution_path, login in use and last owner acknowledgement to --report.
- `KLDA-HFT/monitoring/conformance_report.py` — New weekly live-versus-S3-versus-backtest comparison written to docs/evidence/S6-tier-<n>.md.
- `docs/incidents/` — New folder for incident files.

**Context updates**
- `docs/RUNBOOK.md` — Split section 0 and section 5 into 'paper absence' and 'live absence'. Add the 'Stop everything' card: what the delegate does, in order, with exact commands. Replace the line 'Nothing trades automatically' with the live-mode statement.
- `docs/PROTOCOL.md` — Add the ramp ledger: date, tier, allocated capital, evidence path, who signed.
- `CLAUDE.md` — State the live-mode gates in the hard-won constraints list: accounts.json, validated allowlist, intraday close, owner acknowledgement, kill switch caveat.

## S7

The capital operation survives people and machine changes: a second operator, per-agent allocations that add up to the cap, a tamper-evident audit trail held off the PC, an external review of the books and a cross-check against an independent data source.

**Entry criteria**
- S6 has run at least one full tier cleanly.
- More than one agent or market is being proposed (PROTOCOL.md:110-115 agent-per-market design).

**Work**
- 1. allocations table: agent (symbol and pattern), allocated capital, effective date, set by PR. Demotion sets it to 0 with no grandfathering (PROTOCOL.md:115). Sum of allocations must not exceed allocated_capital.
- 2. Second operator: a named person completes the owner-away drill (stop, check, restart, reconcile) without help. Recorded in HANDOFF.md.
- 3. Tamper evidence: chain each day's seal to the previous seal's hash and keep the chain off the PC. Run a yearly restore drill from the off-PC copy only.
- 4. Independent price check from the data roadmap: exceptions (bucket in one source only, or difference above a threshold) are appended to the seal and to compliance_report. Days with an unresolved exception are flagged and not used in performance claims.
- 5. Yearly external review of the books by an accountant; findings tracked in docs/assurance/.
- 6. Credential rotation every 12 months (proposed) using the S0 procedure; rotation date recorded.
- 7. If a second account, custodian or capital source is added, repeat the S5 onboarding questions and keep a separate ledger per source.

**Risks**
- More agents raise the chance that one agent's signal source (for example the Docker C++ writer) bypasses the allocation ceiling. Every signal writer needs pattern_name and provenance first.
- A second operator is a second set of credentials. Give the minimum role (viewer or risk_manager).

**Exit gates**

| Metric | Threshold | Evidence artifact |
|---|---|---|
| Days where the sum of agent allocations exceeds allocated_capital | 0 over 90 days | `docs/evidence/S7-allocations.md` |
| Second-operator drill completed unaided | 1 of 1 | `docs/assurance/S7-second-operator.md` |
| Trading days in the last 12 months with a chained seal in a second location | 100 percent; one successful restore from the off-PC copy per year | `docs/evidence/S7-seal-chain.md` |
| Unresolved price-mismatch exceptions older than 5 trading days | 0 | `docs/evidence/S7-price-exceptions.md` |
| External review findings open past their due date | 0 | `docs/assurance/S7-external-review.md` |
| Age of the last credential rotation | 365 days or less | `docs/evidence/S7-rotation.md` |

**Protocol — Allocation Ceiling**
- Agent allocations are rows in allocations, changed by PR.
- A check at day end fails loudly if the sum exceeds allocated_capital.
- An agent that stops clearing the gate gets allocation 0 the same day.

**Repo changes**
- `KLDA-HFT/database/migrations/004_allocations.sql` — New allocations table and day-end check.
- `KLDA-HFT/database/seal_records.py` — Add prev_seal_hash to each seal file.
- `docs/assurance/` — Add S7 second-operator and external-review files.

**Context updates**
- `docs/PROTOCOL.md` — Add the allocation table and rules to the agent-per-market section; record the second operator and the review cycle.
- `docs/RUNBOOK.md` — Second operator's version of the daily check and the stop-everything card; yearly calendar: rotation, restore drill, external review.

## Cross-cutting protocols

**Capital Truth Ladder** — investor_ledger and nav_history are typed numbers (trading_api.py:446-481 and 511-538). Nothing ties them to the broker. account_snapshots is written only by klda_engine.py, which the paper chain never runs. Today they prove who typed what and when, not that the money exists.
- Three layers, never mixed. L1 = external documents (bank and broker statements, file hash recorded). L2 = a daily read-only MT5 account_info row in broker_equity_eod. L3 = the declared record (investor_ledger, nav_history).
- L3 rows reference an L1 document in reference_doc. A SUBSCRIPTION or REDEMPTION with an empty reference_doc is rejected.
- NAV is computed by script from L2 and ledger flows. A hand-typed NAV needs a written reason.
- Corrections are new ADJUSTMENT rows or a new NAV version. Rows are never edited or deleted.
- Month-end difference between L1 and L3 above the tolerance (proposed 0.5 percent of allocated capital) blocks scale-up until explained in writing.
- Paper numbers (paper_positions.pnl_eur) never enter L3.

**No Secret In Git** — The Postgres superuser password is in 72 tracked files since commit 648e74c, origin is on GitHub, .gitignore has no .env entry, and several scripts share the one password.
- Secrets live in KLDA-HFT/.env (untracked) and the owner's password manager. .env.example holds placeholders.
- Before every merge, git grep for the current and old secret values returns 0 hits (values are not written in the PR).
- Statements, KYC documents, bank details and tick archives never enter the repo. Account login numbers may appear in config/accounts.json.
- One DB role per component; the superuser role is for DDL and backups only.
- Any exposure means rotation the same day, recorded by name in docs/evidence/.

**Account Identity Gate** — mt5.initialize() takes no login, so the terminal's current login decides which account receives orders. The live account number exists only in prose (CLAUDE.md:77, PROTOCOL.md:49, RUNBOOK.md:54).
- config/accounts.json is the only list of logins the code may use, with kind and allowed_stages.
- Every order path checks mt5.account_info().login against it and refuses on mismatch; nothing falls back to another account.
- Until S6 the terminal runs on a read-only or demo login.
- The personal account is never used by the system once the company account exists.
- The company account holds only system positions, because kill_switch.py closes every MT5 position.

**Merge Authority and Handoff** — master lacks the doctrine and the safety gate while docs claim otherwise; the cloud session cannot see the PC (PROTOCOL.md:29-31); docs/PROTOCOL.md carried a stale top risk for four months.
- Only the owner merges to master. AI sessions open pull requests and never merge, force-push or delete branches.
- One canonical branch for the trading system (master after S0). Research or lane branches merge by PR or are archived.
- Each session ends with an entry in docs/HANDOFF.md: date, cloud or local, branch and commit, what changed, uncommitted work (must be none), PC facts verified (with how), open questions.
- The cloud session tags anything it cannot see (users table, .env, Task Scheduler, row counts) as UNVERIFIED. The local session replaces the tag with the observed fact.
- The PC's running commit and dirty flag appear in the health report. Uncommitted trading code is an incident.
- Locked decisions change only by an owner-approved entry in docs/DECISIONS.md with date and superseded-by.

**Seal, Retain, Never Delete** — audit_log protection is commented out (create_compliance_tables.sql:44-45), the API connects as postgres, and backups sit on the same C: drive as the database (backup_db.py:24).
- Daily seal (counts, max ids, sha256) for audit_log, investor_ledger, nav_history, signals, decision_log, paper tables and executions, kept in two places, one off the PC.
- No DELETE or UPDATE grants on audit_log, investor_ledger, nav_history, decision_log for application roles.
- Never delete ledger, NAV, audit, decision, statement or KYC records. Retention periods are filled in by the accountant and lawyer in docs/CAPITAL_RECORDS.md; the default is keep everything.
- Restore is rehearsed every quarter on a spare database and the result is filed.
- Truncate or drop scripts (database/truncate_ticks.py, database/fix_ticks.py) are moved out of the daily path or require a typed confirmation.

**Owner-Away Continuity** — RUNBOOK section 0 covers Postgres autostart, MT5, bridge and watchdog only. The API and the paper chain are not in the logon tasks, and section 5 says nothing needs approval, which stops being true when real capital is at work.
- The stop-everything card is one page: what to close, in what order, which password type, whom to call. A person who cannot code can follow it.
- A sealed copy of the recovery credentials is held by a person named in DECISIONS.md. The location is not written in the repo.
- From S6, no acknowledgement for the configured hours blocks new entries (system_flags OWNER_ACK).
- The delegate has the viewer or risk_manager role and cannot change config, accounts.json or credentials.
- Every live order carries SL and TP, positions are flat by 23:45 broker time, so the maximum unattended exposure is bounded by the 3-position limit.

## Anti-patterns
- Typing a ledger or NAV figure from memory. There is no check against the broker today; the first wrong number becomes the official one.
- Feeding paper_positions.pnl_eur into NAV or any capital statement. The value is pnl_points * lots * 1000 (broker_adapter_mt5.py:198) in a column named EUR on a USD ledger.
- Calling the audit trail regulator-grade, SEC/FCA-grade or 'for regulatory review' (create_compliance_tables.sql:3, trading_terminal.html:257). The tables can be edited by the superuser the API uses.
- Rewriting git history instead of rotating the password. Clones, forks and caches keep the old value.
- Mixing personal and company money: funding the company account from a personal account, or leaving a personal position on the company account.
- Topping up the account after a loss or sizing from current equity after a good run. PROTOCOL.md:19-20 forbids P&L-driven sizing.
- Flipping paper_mode in trading_config.json on the PC without a PR, a signature and a HANDOFF entry.
- The cloud session stating PC facts it cannot see (Klda exists, JWT_SECRET is set, Task Scheduler jobs exist, row counts).
- Running ledger or NAV rehearsals on the production database. The rows are permanent.
- Using the MCP run_query tool as if it were read-only while it connects as postgres with a prefix check.
- Committing the nightly tick archives or any statement file to the repo. .gitignore does not exclude *.csv.gz today.
- Using taskkill /F /IM python.exe in any rotation or stop procedure (CLAUDE.md constraint; it kills the watchdog and MCP servers).

## Questions for the owner
- Decision 4 (PROTOCOL.md:125) says the 25k demo runs 'on the VPS first'. Your constraint is local-only. May I record 'on the owner's PC, no VPS' in DECISIONS.md? If yes, the PC is a single point of failure and the continuity plan relies on the owner-ack halt and the stop-everything card. If you want a VPS later, say at which stage.
- Decision 3 says 1 percent per trade, fixed fractional, P&L-independent. 1 percent of what base: live account equity (moves with P&L) or the allocated_capital number, which changes only through a ledger event? I recommend allocated_capital. Today the code sends a fixed 0.01 lot (limits_enforcer.py get_lot_size) and CLAUDE.md:87 says Kelly 25 percent capped at 2 to 3 percent. Confirm that PROTOCOL wins over CLAUDE.md.
- Will the KLDA company account hold only money from KLDA Technologies or its owner, or could it ever hold money from anyone else? The ledger columns (investor_name, shares_delta, mgmt_fee, perf_fee) assume outside investors. The answer decides which external questions apply and whether those words stay.
- What is the maximum total amount you accept losing, in currency, and which funds does it come from (declared risk capital)? PROTOCOL.md:18 says you are recovering a lost sum. Do you accept the rule 'no top-up within the same month as a loss'?
- Who is Key 2 (independent reviewer) and who is the delegate? Names or roles only. Can one person be both?
- Is github.com/xyVar/KLDAFinTech private? Who are the identities xyVar, Kosta Papa and xhoi-23 that appear as commit authors, and who has write access today?
- Do you want master fast-forwarded to lane-a/safety-gate now (by PR) and made owner-only to merge? What is your GitHub login for CODEOWNERS?
- On the PC: does .env set JWT_SECRET? Does user Klda (admin) exist, and how was it created? Was create_compliance_tables.sql run? I cannot see any of this from the repo.
- Admin MFA before S5: require TOTP, or accept loopback-only binding plus the Windows login as the control (to be written down in DECISIONS.md)?
- Do you accept a rule that blocks new entries when nobody acknowledges the system for 72 hours once real capital is at work? Which number of hours?
- The strategy/ folder tracks broker trade reports for account 52028179 and old EA files. May they be removed from tracking and kept outside the repo?
- Should CLAUDE.md:13 and config_loader.py:84 agree that 'validated' includes net P&L above zero? By CLAUDE.md's wording SpotCrude (58.4 percent, p=0.005, net -0.30 percent) would count as validated.

## Verify externally (broker / lawyer / accountant)
- BROKER: Does the broker open trading accounts for a limited company? Which entity of the broker group would hold the account, and which client-money arrangements apply to it?
- BROKER: Which documents are required for a company (constitution, registry extract, directors, beneficial owners, authorised signatories, proof of address, source of funds and wealth, tax residency)? Accepted format, maximum age, certified copies?
- BROKER: Can the owner be the authorised trader, can a second person be appointed, and what is the process if the owner becomes unable to act (successor, estate, account freeze)?
- BROKER: Does MT5 on this broker offer a read-only (investor) password for the corporate account, and can trading rights be restricted by login or IP?
- BROKER: Is automated trading through the MT5 Python API permitted on the corporate account? Are there order-rate limits, hedging or scalping rules, or a requirement or ban on a VPS?
- BROKER: Which account types are available, and which has the same spreads, commissions, leverage, contract sizes and symbol names (SpotCrude, GER40, NAS100, NatGas, stock CFDs) as the data behind our research? Are leverage limits different for company accounts?
- BROKER: Which funding methods are accepted for a corporate account? Must funds come from a bank account in the company's name? Are third-party payments refused? Base currency options, deposit and withdrawal fees, minimum deposit, inactivity fees.
- BROKER: What statements and exports exist (format, frequency, time zone, how long they stay online)? Can the broker issue a balance confirmation on request? Is there a deal-history export or API?
- BROKER: Can a demo account (about 25k) be linked to the corporate application, on the same server and price model? How long does a demo account live before expiry?
- BROKER: Why is live account 52028179 trade-disabled (retcode 10017), is that block still in place (PROTOCOL.md:49 and :75 disagree), and can it be lifted? What are the margin close-out and stop-out levels and negative-balance rules (we use a 200 percent margin floor in limits_enforcer.py)?
- BROKER: Do the market-data terms allow storing the tick feed in our own database and using it for the company's research and trading? Can separate accounts or sub-accounts be opened per strategy or per capital source?
- LAWYER: If KLDA Technologies trades only its own money, what authorisations or registrations does it need, in which jurisdiction? What changes if any third-party money is accepted? Is a mandate or management agreement needed?
- LAWYER: Do the words investor, fund, NAV, shares, management fee and performance fee in the schema and UI imply a regulated activity or create obligations? Should the labels change until the structure is decided?
- LAWYER: Minimum retention periods for trading records, ledgers, audit logs, statements and KYC documents. Data-protection duties for investor_email and KYC data. Is an internal audit trail of this kind acceptable evidence for regulators, auditors or tax authorities?
- LAWYER: Who can sign for the company, what are the directors' duties for this activity, and is insurance needed?
- ACCOUNTANT: How should owner-to-company transfers be classified (equity contribution or loan), and how should trading results, fees, financing charges and currency differences be booked? Should the ledger be separate from the company books?
- ACCOUNTANT: Which format do you want for the trade ledger and monthly statement (fields in /api/compliance_report)? Do broker statements suffice as source documents? Fiscal year-end versus the NAV date? Base currency of the books versus the USD columns (amount_usd).
- ACCOUNTANT: Tax treatment of CFD gains and losses for the company, any withholding, and what the broker issues at year end.
- ACCOUNTANT: Do you accept a countersigned monthly capital statement (docs/capital/YYYY-MM.md) as a control, or do you require something else?
- GITHUB: Do branch protection (PR required, no force-push, no deletion) and secret scanning with push protection work on a private repo under the owner's plan? Is storing company records and account numbers in a private GitHub repo acceptable under the broker's terms and data-protection duties?
