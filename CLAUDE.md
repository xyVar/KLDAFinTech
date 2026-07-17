# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

Renaissance/Medallion-inspired tick-data trading system: capture every tick from MetaTrader 5 (Pepperstone), store in PostgreSQL + TimescaleDB, detect 5 statistical patterns (target 51%+ win rate), generate intraday signals, execute via MT5. All active work lives in `KLDA-HFT/`. Everything else that looks like a trading project (`archive/`, the root `README.md` describing manual Martingale/TSMC strategies) is **archived history — do not reintroduce it or take it as current**.

`SYSTEM_ARCHITECTURE.md` and `WHAT_WE_ARE_BUILDING.md` describe the vision; parts are aspirational (React frontend not built, MQL5 tick-capture EA superseded by the Python bridge). `KLDA-HFT/README.md` and `KLDA-HFT/MANAGE_MT5_BRIDGE.md` are stale — they describe the old Flask tick-receiver pipeline and advise `taskkill /F /IM python.exe`, both contradicted by the constraints below.

The 5 patterns: Mean Reversion, Gap Fill, Pairs Divergence, Event Drift, Momentum Exhaustion. A pattern only counts as validated at ≥100 occurrences, ≥51% win rate, p < 0.05.

## Live Data Pipeline (what actually runs)

```
MT5 terminal (Pepperstone, dynamic Market Watch symbol set)
  → KLDA-HFT/python-bridge/mt5_tick_capture_ALL_TICKS.py
      writes DIRECTLY to Postgres via psycopg2 (no Flask receiver —
      api/tick_receiver.py is legacy)
  → TimescaleDB "KLDA-HFT_Database"
      current            ← latest snapshot, one row per symbol
      ticks              ← universal append-only hypertable (~357M rows)
      cagg_bars_m5       ← continuous aggregate used by signal generator
      signals / trades / positions / audit tables
      *_history          ← legacy per-symbol tick tables (pre-universal schema)
  → trading-engine/signal_generator.py   (5 metrics → PENDING rows in signals)
  → trading-engine/klda_engine.py        (executes signals via MT5, monitors positions)
  → api/trading_api.py                   (Flask, port 5002, JWT/RBAC, audit log)
  → cpp-backend (Docker)                 (reads `current` 1x/sec → live_ticks.json → HTML dashboards)
```

The symbol universe is **dynamic** — the bridge captures whatever is visible in MT5 Market Watch, no hardcoded list. Check with `SELECT symbol FROM current`.

## Commands

There is no test suite, linter, or CI. Python scripts run on system Python (needs `MetaTrader5`, `psycopg2-binary`, `Flask`, `PyJWT`, `bcrypt`, `python-dotenv`). MT5 terminal must be running and logged in for anything touching `mt5.*`.

```bash
# Start/stop the whole stack (Postgres, bridge, C++ engine, API, engine, terminal)
KLDA-HFT/start_all.bat
KLDA-HFT/stop_all.bat        # WARNING: kills ALL python.exe on the machine

# Run components individually (each from its own directory)
python KLDA-HFT/python-bridge/mt5_tick_capture_ALL_TICKS.py   # tick capture
python KLDA-HFT/python-bridge/watchdog.py                     # restarts bridge on stall (surgical, WMI-matched)
python KLDA-HFT/trading-engine/signal_generator.py
python KLDA-HFT/trading-engine/klda_engine.py
python KLDA-HFT/api/trading_api.py                            # port 5002

# Health / debugging
python test_mt5_connection.py                                 # MT5 connectivity
tail KLDA-HFT/python-bridge/bridge.log                        # is the feed alive?
QUICK_CHECK_PRICES.bat                                        # latest DB prices
python KLDA-HFT/monitoring/hourly_health_check.py

# C++ backend (Docker; outputs live_ticks.json for the HTML dashboards)
cd KLDA-HFT/cpp-backend && docker-compose up                  # container: klda-hft-cpp-backend
KLDA-HFT/cpp-backend/start_web_server.bat                     # dashboards at localhost:8082

# MQL5 EA compile (Renaissance 5-metric EA, lives in the MT5 terminal tree)
compile_renaissance.bat

# Nightly DB backup (idempotent, safe to run manually)
python KLDA-HFT/database/backup_db.py
```

## Hard-Won Constraints (violating these has broken the system before)

- **DB host must be `127.0.0.1`, not `localhost`** — `::1` can be claimed by a WSL postgres relay with different credentials. DB credentials live in `.env` and inline `DB_CONFIG` dicts in the scripts.
- **Broker server time is UTC+3.** All tick timestamps are broker time. Never judge feed freshness with `NOW() - last_updated`; check that `MAX(last_updated)` in `current` is *advancing* between polls (this is what watchdog.py does).
- **Never `taskkill /F /IM python.exe`** in monitoring/automation code — it kills MCP servers, running backtests, and the watchdog itself. watchdog.py matches the bridge's command line via WMI; keep it that way.
- **Don't strip the bridge's resilience features** (rotating file log, reconnect loop, `time_msc` dedup, 10s lookback). They exist because the feed silently died without them.
- **`ticks.spread` is stored in points, not dollars.** `database/backtest_5metric.py` has a known bug treating it as dollars (tx_cost ~$18/trade swallows all gross gain) — fix units before trusting any backtest numbers.
- **Don't run two backtests in parallel** — the machine OOMs.
- **The live Pepperstone account (52028179) is trade-disabled at the broker** — `order_send` returns retcode 10017. Read-only API and `order_calc_*` work. The `.env` broker section is stale (old demo account, wrong leverage — real leverage is 1:30).
- **Intraday only** — positions close before rollover to avoid swap costs; no overnight holds.
- **Never search or glob into `vcpkg/`** — it's a vendored C++ dependency tree (hundreds of files of lz4/nlohmann-json noise). Scope searches to `KLDA-HFT/`.

## Component Notes

- **cpp-backend** — C++17, CMake (`find_package(PostgreSQL)`, nlohmann/json vendored in `include/`). Built and run via Docker (Ubuntu 22.04); connects to Windows Postgres through `host.docker.internal`. Two executables: `klda-hft-engine` (main.cpp) and `live_tracker` (main_live.cpp). REST API mapped to host port 8081 (8080 is taken by another service).
- **trading-engine** — `klda_engine.py` runs 3 threads: signal executor (picks up PENDING signals), position monitor, account snapshot every 5s. Magic number 234000. `signal_generator.py` supports `PAPER_MODE`. Config via env vars with hardcoded fallbacks.
- **database/** — grab-bag of schema files and one-off scripts. `create_schema.sql` is the legacy per-symbol layout; `restructure_universal.sql` and `schema.sql` reflect the universal `ticks` layout. Nightly backup strategy: small base dump excluding ticks data + append-only per-day `ticks_YYYY-MM-DD.csv.gz` archives in `backups/`.
- **Position sizing** — Kelly Criterion at 25% fraction, capped ~2-3% risk per trade, max 20% total exposure.
- Trading hours: Monday 03:00 – Friday 23:55 broker time (~24/5).
