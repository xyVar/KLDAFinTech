# C++ Backend Engine - Analysis & API Server

**Role:** Analysis engine, signal generation, REST API server
**Status:** 📋 PLANNED (not built yet)
**Port:** 8080 (when built)

---

## Purpose

This component will:
1. **Read database** (CURRENT, HISTORY, BARS tables) - Read-only
2. **Perform analysis:**
   - Order flow imbalance
   - Spread analysis
   - Quote-to-trade ratio
   - Pattern detection
   - Signal generation
3. **Expose REST API** for frontend dashboard
4. **User authentication** (JWT tokens)
5. **Backtesting engine** on historical data

---

## Architecture (Planned)

```
PostgreSQL Database
    ↓ (libpqxx - READ ONLY)
┌────────────────────────────────────────┐
│      C++ Backend Engine                │
│                                        │
│  Database Layer → Analysis Engine →   │
│  Signal Generator → API Server         │
└────────────────────────────────────────┘
    ↓ (HTTP REST API on port 8080)
Frontend Dashboard
```

---

## Planned Directory Structure

```
cpp-backend/
├── src/
│   ├── main.cpp              (Entry point)
│   ├── database/
│   │   ├── connection.cpp    (PostgreSQL connection pool)
│   │   ├── connection.h
│   │   ├── queries.cpp       (SQL query functions)
│   │   └── queries.h
│   ├── models/
│   │   ├── tick.h            (Tick data structure)
│   │   ├── bar.h             (Bar data structure)
│   │   └── asset.h           (Asset metadata)
│   ├── analysis/
│   │   ├── order_flow.cpp    (Order flow imbalance)
│   │   ├── order_flow.h
│   │   ├── spread.cpp        (Spread analysis)
│   │   ├── spread.h
│   │   └── signals.cpp       (Signal generation)
│   ├── api/
│   │   ├── server.cpp        (HTTP server - Crow framework)
│   │   ├── server.h
│   │   ├── routes.cpp        (API endpoints)
│   │   └── auth.cpp          (JWT authentication)
│   └── utils/
│       ├── config.cpp        (Config loader)
│       ├── config.h
│       ├── logger.cpp        (Logging - spdlog)
│       └── logger.h
├── include/                  (External headers)
├── config.json               (Configuration)
├── CMakeLists.txt            (Build configuration)
└── README.md                 (This file)
```

---

## Required Libraries

### 1. libpqxx (PostgreSQL C++ client)
```bash
vcpkg install libpqxx:x64-windows
```

### 2. Crow (HTTP server framework)
```bash
# Header-only library
git clone https://github.com/CrowCpp/Crow.git
```

### 3. nlohmann/json (JSON parser)
```bash
vcpkg install nlohmann-json:x64-windows
```

### 4. spdlog (Logging)
```bash
vcpkg install spdlog:x64-windows
```

### 5. jwt-cpp (JWT authentication)
```bash
vcpkg install jwt-cpp:x64-windows
```

---

## Planned API Endpoints

### GET /api/current
Get latest tick for all assets

### GET /api/current/:symbol
Get latest tick for specific symbol

### GET /api/history/:symbol?seconds=300
Get tick history for symbol

### GET /api/analysis/:symbol?window=600
Run analysis on symbol:
- Order flow imbalance
- Spread analysis
- Trading signal

### GET /api/signals
Get trading signals for all assets

### POST /api/backtest
Run backtest on historical data

### POST /api/auth/login
User authentication (JWT)

---

## Configuration (config.json)

```json
{
  "database": {
    "host": "localhost",
    "port": 5432,
    "name": "KLDA-HFT_Database",
    "user": "postgres",
    "password": "MyKldaTechnologies2025!",
    "connection_pool_size": 10
  },
  "api_server": {
    "host": "0.0.0.0",
    "port": 8080,
    "threads": 4,
    "enable_cors": true
  },
  "analysis": {
    "order_flow_window": 300,
    "spread_window": 3600,
    "signal_threshold": 0.65
  }
}
```

---

## Build Process (When Implemented)

### 1. Install Visual Studio 2022
Download from: https://visualstudio.microsoft.com/

### 2. Install vcpkg
```powershell
git clone https://github.com/Microsoft/vcpkg.git
cd vcpkg
.\bootstrap-vcpkg.bat
.\vcpkg integrate install
```

### 3. Install Dependencies
```powershell
.\vcpkg install libpqxx:x64-windows
.\vcpkg install nlohmann-json:x64-windows
.\vcpkg install spdlog:x64-windows
.\vcpkg install jwt-cpp:x64-windows
```

### 4. Build
```powershell
cd KLDA-HFT/cpp-backend
mkdir build
cd build
cmake .. -DCMAKE_TOOLCHAIN_FILE=C:/path/to/vcpkg/scripts/buildsystems/vcpkg.cmake
cmake --build . --config Release
```

### 5. Run
```powershell
.\Release\klda-hft-engine.exe
```

---

## Documentation

See: `docs/CPP_BACKEND_CONFIG.md` for complete setup guide

---

## Status

**Current:** Not built yet
**Next Steps:**
1. Set up development environment
2. Install required libraries
3. Implement database connection layer
4. Implement analysis algorithms
5. Build REST API server
6. Test with frontend

---

**Last Updated:** 2026-01-13
