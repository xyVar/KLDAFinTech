# KLDA-HFT Project Structure

**Database:** PostgreSQL 16 + TimescaleDB 2.24.0
**Environment:** Windows 11, Python 3.13, C++ 17

---

## Directory Organization

```
KLDA-HFT/
│
├── api/                           [Flask API Server]
│   ├── tick_receiver.py          → Receives ticks from Python bridge
│   │                              → Writes to PostgreSQL database
│   │                              → Exposes HTTP endpoints
│   └── README.md                 → API documentation
│
├── python-bridge/                [MT5 ↔ API Bridge]
│   ├── mt5_tick_capture.py       → Main: Connects to MT5, captures ticks
│   ├── test_mt5_connection.py    → Test MT5 connection
│   ├── debug_mt5_tick.py         → Debug MT5 tick structure
│   ├── fix_mt5_config.py         → Fix MT5 WebRequest config
│   ├── fix_mt5_webrequest.bat    → Windows batch for config fix
│   └── README.md                 → Bridge documentation
│
├── database/                     [Database Setup & Management]
│   ├── setup_database.py         → Initial database creation
│   ├── create_bar_tables.py      → Create BAR tables
│   ├── import_historical_bars.py → Import historical CSV data
│   ├── add_order_flow_columns.py → Add buy/sell volume columns
│   ├── verify_full_database.py   → Complete DB verification
│   ├── verify_tables.py          → Table structure check
│   ├── check_all_data.py         → Data coverage check
│   ├── schema.sql                → Full database schema
│   ├── create_schema.sql         → Table creation SQL
│   ├── add_volume_column.sql     → Add volume columns
│   ├── tracking_queries.sql      → Example queries
│   └── README.md                 → Database documentation
│
├── cpp-backend/                  [C++ Analysis Engine - FUTURE]
│   ├── src/
│   │   ├── main.cpp              → Entry point
│   │   ├── database/             → PostgreSQL connection layer
│   │   ├── models/               → Data structures (Tick, Bar, Asset)
│   │   ├── analysis/             → Analysis algorithms
│   │   ├── api/                  → REST API server
│   │   └── utils/                → Config, logging
│   ├── include/                  → External headers
│   ├── config.json               → Configuration file
│   ├── CMakeLists.txt            → Build configuration
│   └── README.md                 → C++ backend documentation
│
├── scripts/                      [Utility & Testing Scripts]
│   ├── check_current_table.py    → Check CURRENT table
│   ├── check_database_ticks.py   → Verify tick data
│   ├── test_manual_tick.py       → Send test tick to API
│   └── README.md                 → Scripts documentation
│
├── docs/                         [Documentation]
│   ├── DATABASE_SCHEMA.md        → Complete database schema
│   ├── CPP_BACKEND_CONFIG.md     → C++ backend setup guide
│   ├── TICK_DATA_EXPLAINED.md    → MT5 tick flags reference
│   ├── BROKER_CONNECTION_SETUP.md → MT5 connection setup
│   └── PROJECT_STRUCTURE.md      → This file
│
├── config/                       [Configuration Files]
│   └── (future config files)
│
├── frontend/                     [Web Dashboard - FUTURE]
│   └── (future frontend code)
│
└── logs/                         [Log Files]
    └── (runtime logs)
```

---

## Data Flow Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                  MT5 Terminal (Broker Server)                │
│              17 assets × live tick stream                    │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         │ MetaTrader5 Python API
                         │ Polls every 1 second
                         ↓
┌──────────────────────────────────────────────────────────────┐
│           PYTHON BRIDGE (python-bridge/)                     │
│  File: mt5_tick_capture.py                                   │
│  - Connects to MT5 terminal                                  │
│  - Captures tick data (bid, ask, volume, flags)              │
│  - Formats timestamps (microseconds)                         │
│  - Sends batch HTTP POST                                     │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         │ HTTP POST /tick/batch
                         │ JSON: {ticks: [...]}
                         ↓
┌──────────────────────────────────────────────────────────────┐
│                   API SERVER (api/)                          │
│  File: tick_receiver.py                                      │
│  - Flask HTTP server (port 5000)                             │
│  - Receives tick batches                                     │
│  - Maps MT5 symbols → Database symbols                       │
│  - Separates buy/sell volume by flags                        │
│  - Buffers ticks (max 100 or 1 second)                       │
│                                                              │
│  Endpoints:                                                  │
│  - POST /tick         (single tick)                          │
│  - POST /tick/batch   (batch ticks)                          │
│  - GET  /stats        (API statistics)                       │
│  - GET  /health       (health check)                         │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         │ psycopg2 (PostgreSQL driver)
                         │ SQL: UPDATE current + INSERT history
                         ↓
┌──────────────────────────────────────────────────────────────┐
│              POSTGRESQL DATABASE (database/)                 │
│  Database: KLDA-HFT_Database                                 │
│  Engine: PostgreSQL 16 + TimescaleDB 2.24.0                  │
│                                                              │
│  Tables (35 total):                                          │
│  - current (1 table, 17 rows)                                │
│    → Latest tick per asset (UPDATES)                         │
│                                                              │
│  - *_history (17 tables)                                     │
│    → Append-only tick archives (INSERTS)                     │
│    → TimescaleDB hypertables                                 │
│                                                              │
│  - *_bars (17 tables)                                        │
│    → Historical OHLCV data (16+ years)                       │
│    → Static, for backtesting                                 │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         │ libpqxx (C++ client) [FUTURE]
                         │ Read-only queries
                         ↓
┌──────────────────────────────────────────────────────────────┐
│             C++ BACKEND ENGINE (cpp-backend/)                │
│  [FUTURE - Not yet built]                                    │
│  - Reads CURRENT/HISTORY/BARS tables                         │
│  - Performs pattern analysis                                 │
│  - Generates trading signals                                 │
│  - Exposes REST API (port 8080)                              │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         │ HTTP REST API
                         │ JSON responses
                         ↓
┌──────────────────────────────────────────────────────────────┐
│               FRONTEND DASHBOARD (frontend/)                 │
│  [FUTURE - Not yet built]                                    │
│  - React/Vue web application                                 │
│  - User authentication                                       │
│  - Live data visualization                                   │
│  - Trading signals display                                   │
│  - Control panel                                             │
└──────────────────────────────────────────────────────────────┘
```

---

## Component Roles

### 1. Python Bridge (python-bridge/)
**Status:** ✅ RUNNING (Tasks: b796f34, bd8a243)
**Role:** "Electricity Provider" - Data capture only
**Function:**
- Connects to MT5 terminal via MetaTrader5 Python library
- Polls broker server every 1 second
- Captures 17 assets simultaneously
- Sends ticks to API via HTTP POST
- **NO analysis, NO storage** - just data movement

**Key File:** `mt5_tick_capture.py`

---

### 2. API Server (api/)
**Status:** ✅ RUNNING (Task: bd8a243)
**Role:** Data receiver and database writer
**Function:**
- Receives ticks from Python bridge (HTTP POST)
- Validates and maps symbols
- Separates buy/sell volume based on MT5 flags
- Writes to PostgreSQL:
  - UPDATE `current` table (latest tick per asset)
  - INSERT into `*_history` tables (append-only archive)
- Exposes HTTP endpoints for monitoring

**Key File:** `tick_receiver.py`
**Port:** 5000

**Important:** API has TWO connections:
1. **INPUT:** Python bridge → API (HTTP POST, receives broker data)
2. **OUTPUT:** API → PostgreSQL (SQL INSERT/UPDATE, stores data)

---

### 3. Database (database/)
**Status:** ✅ OPERATIONAL
**Role:** Central data storage
**Function:**
- Stores all tick data (live and historical)
- Three table types:
  1. `current` - Live snapshot (17 rows, updated continuously)
  2. `*_history` - Tick archives (append-only, growing)
  3. `*_bars` - Historical bars (170,544 bars, static)
- TimescaleDB hypertables for efficient time-series queries
- PostgreSQL on port 5432

**Database:** `KLDA-HFT_Database`
**Tables:** 35 total (1 + 17 + 17)
**Size:** 642 MB

---

### 4. C++ Backend (cpp-backend/)
**Status:** 📋 PLANNED (not built yet)
**Role:** Analysis engine and API server
**Function:**
- **Read-only** database access (no writes)
- Performs analysis:
  - Order flow imbalance
  - Spread analysis
  - Quote-to-trade ratio
  - Pattern detection
  - Signal generation
- Exposes REST API for frontend
- User authentication (JWT)
- Backtesting engine

**Port:** 8080 (planned)

---

### 5. Frontend Dashboard (frontend/)
**Status:** 📋 PLANNED (not built yet)
**Role:** User interface
**Function:**
- Web-based dashboard
- Connects to C++ backend REST API
- Displays:
  - Live tick data
  - Trading signals
  - Analysis results
  - Historical charts
- User authentication
- Control panel for C++ engine

---

### 6. Scripts (scripts/)
**Status:** ✅ AVAILABLE
**Role:** Testing and verification utilities
**Files:**
- `check_current_table.py` - Verify CURRENT table updates
- `check_database_ticks.py` - Verify tick data in HISTORY tables
- `test_manual_tick.py` - Send test tick to API

---

### 7. Docs (docs/)
**Status:** ✅ COMPLETE
**Role:** Technical documentation
**Files:**
- `DATABASE_SCHEMA.md` - Complete database schema
- `CPP_BACKEND_CONFIG.md` - C++ backend setup guide
- `TICK_DATA_EXPLAINED.md` - MT5 tick flags explained
- `BROKER_CONNECTION_SETUP.md` - MT5 connection guide

---

## Current System Status

### Running Components:
1. ✅ PostgreSQL Database (port 5432)
2. ✅ Python Bridge (task b796f34) - Capturing ticks
3. ✅ API Server (task bd8a243) - Receiving and storing ticks

### Data Flow:
```
MT5 Broker → Python Bridge → API Server → PostgreSQL
            (every 1 sec)   (HTTP POST)   (SQL INSERT/UPDATE)
```

### Statistics (as of 2026-01-13 17:54):
- Ticks captured: 14,715
- Ticks per asset: ~466
- Database size: 642 MB
- Historical bars: 170,544 (16+ years)

---

## Next Steps

1. ✅ **Database infrastructure** - COMPLETE
2. ✅ **Python bridge** - RUNNING
3. ✅ **API server** - RUNNING
4. ✅ **Documentation** - COMPLETE
5. 📋 **C++ backend** - TODO
6. 📋 **Frontend dashboard** - TODO

---

## How Components Communicate

### Current (Live System):
```
MT5 Terminal
    ↓ (MetaTrader5 Python API)
Python Bridge (mt5_tick_capture.py)
    ↓ (HTTP POST: http://localhost:5000/tick/batch)
API Server (tick_receiver.py)
    ↓ (PostgreSQL: psycopg2)
Database (KLDA-HFT_Database)
```

### Future (Complete System):
```
MT5 Terminal
    ↓
Python Bridge
    ↓ (HTTP)
API Server
    ↓ (SQL)
Database
    ↑ (SQL READ-ONLY)
C++ Backend
    ↓ (HTTP REST API)
Frontend Dashboard
```

---

## Configuration Files

### Python Bridge:
- Connection: Direct to MT5 terminal (no config needed)
- API target: `http://localhost:5000`

### API Server:
- Port: 5000
- Database: `localhost:5432/KLDA-HFT_Database`
- Credentials: In `tick_receiver.py` (line 17-23)

### Database:
- Host: localhost
- Port: 5432
- Database: KLDA-HFT_Database
- User: postgres
- Password: MyKldaTechnologies2025!

### C++ Backend (future):
- Configuration: `cpp-backend/config.json`
- Database: Read-only connection
- API port: 8080

---

## Important Notes

1. **Python bridge** runs independently - never stops unless you kill it
2. **API server** runs independently - receives from bridge, writes to DB
3. **Database** stores everything - never deletes old ticks
4. **C++ backend** will be separate - reads DB, does analysis, exposes API
5. **Frontend** will be separate - connects to C++ API, displays data

**Separation of Concerns:**
- Python bridge: Data capture ONLY
- API server: Data storage ONLY
- C++ backend: Analysis ONLY (future)
- Frontend: Display ONLY (future)

---

**Last Updated:** 2026-01-13
**Version:** 1.0
