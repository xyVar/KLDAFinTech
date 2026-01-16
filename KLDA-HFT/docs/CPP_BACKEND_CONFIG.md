# C++ Backend Configuration & Setup

**Project:** KLDA-HFT C++ Analysis Engine
**Purpose:** Read database, perform pattern analysis, expose REST API
**Role:** Read-only database access, computation engine, API server

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│                    PostgreSQL Database                       │
│  Host: localhost:5432                                        │
│  Database: KLDA-HFT_Database                                 │
│  Tables: CURRENT (17 rows) + HISTORY + BARS                 │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         │ libpqxx (C++ PostgreSQL client)
                         │ Connection: Read-only queries
                         ↓
┌──────────────────────────────────────────────────────────────┐
│              C++ BACKEND ENGINE (klda-hft-engine)            │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 1. DATABASE LAYER (database.cpp)                     │   │
│  │    - Connection pooling (libpqxx)                    │   │
│  │    - Query executor                                  │   │
│  │    - Data structures (Tick, Bar, Asset)             │   │
│  └──────────────────────────────────────────────────────┘   │
│                         │                                    │
│                         ↓                                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 2. ANALYSIS ENGINE (analysis.cpp)                    │   │
│  │    - Order flow imbalance                            │   │
│  │    - Spread analysis                                 │   │
│  │    - Quote-to-trade ratio                            │   │
│  │    - Pattern detection algorithms                    │   │
│  │    - Signal generation                               │   │
│  └──────────────────────────────────────────────────────┘   │
│                         │                                    │
│                         ↓                                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 3. REST API SERVER (api_server.cpp)                  │   │
│  │    - HTTP server (Crow framework)                    │   │
│  │    - JSON responses                                  │   │
│  │    - Authentication (JWT)                            │   │
│  │    - Endpoints:                                      │   │
│  │      GET  /api/current         (live data)          │   │
│  │      GET  /api/history/:symbol (tick history)       │   │
│  │      GET  /api/analysis/:symbol (run analysis)      │   │
│  │      GET  /api/signals         (trading signals)    │   │
│  │      POST /api/backtest        (run backtest)       │   │
│  └──────────────────────────────────────────────────────┘   │
│                         │                                    │
│                         ↓                                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 4. CONFIGURATION (config.json)                       │   │
│  │    - Database connection settings                    │   │
│  │    - API server settings                             │   │
│  │    - Analysis parameters                             │   │
│  │    - User credentials                                │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         │ HTTP REST API (port 8080)
                         │ JSON responses
                         ↓
┌──────────────────────────────────────────────────────────────┐
│                  FRONTEND DASHBOARD                          │
│  - React/Vue web app                                         │
│  - Connects to C++ backend via HTTP                          │
│  - Displays live data, signals, analysis                     │
│  - User authentication                                       │
└──────────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
KLDA-HFT/
│
├── cpp-backend/                    (C++ backend source code)
│   ├── src/
│   │   ├── main.cpp               (Entry point)
│   │   ├── database/
│   │   │   ├── connection.cpp     (PostgreSQL connection)
│   │   │   ├── connection.h
│   │   │   ├── queries.cpp        (SQL query functions)
│   │   │   └── queries.h
│   │   ├── models/
│   │   │   ├── tick.h             (Tick data structure)
│   │   │   ├── bar.h              (Bar data structure)
│   │   │   └── asset.h            (Asset metadata)
│   │   ├── analysis/
│   │   │   ├── order_flow.cpp     (Order flow analysis)
│   │   │   ├── order_flow.h
│   │   │   ├── spread.cpp         (Spread analysis)
│   │   │   ├── spread.h
│   │   │   └── signals.cpp        (Signal generation)
│   │   ├── api/
│   │   │   ├── server.cpp         (HTTP server)
│   │   │   ├── server.h
│   │   │   ├── routes.cpp         (API endpoints)
│   │   │   └── auth.cpp           (Authentication)
│   │   └── utils/
│   │       ├── config.cpp         (Configuration loader)
│   │       ├── config.h
│   │       ├── logger.cpp         (Logging utility)
│   │       └── logger.h
│   ├── include/                   (External headers)
│   ├── config.json                (Configuration file)
│   ├── CMakeLists.txt             (Build configuration)
│   └── README.md
│
├── api/                           (Python bridge - already exists)
│   └── tick_receiver.py
│
├── database/                      (Database setup scripts)
│   └── ...
│
└── frontend/                      (Frontend dashboard - future)
    └── ...
```

---

## Configuration File (config.json)

```json
{
  "database": {
    "host": "localhost",
    "port": 5432,
    "name": "KLDA-HFT_Database",
    "user": "postgres",
    "password": "MyKldaTechnologies2025!",
    "connection_pool_size": 10,
    "connection_timeout": 30
  },

  "api_server": {
    "host": "0.0.0.0",
    "port": 8080,
    "threads": 4,
    "enable_cors": true,
    "jwt_secret": "your-secret-key-here-change-this"
  },

  "analysis": {
    "order_flow_window": 300,
    "spread_window": 3600,
    "quote_trade_window": 900,
    "signal_threshold": 0.65
  },

  "assets": [
    "TSLA", "NVDA", "AAPL", "MSFT", "ORCL",
    "PLTR", "AMD", "AVGO", "META", "AMZN",
    "CSCO", "GOOG", "INTC", "VIX", "NAS100",
    "NATGAS", "SPOTCRUDE"
  ],

  "users": [
    {
      "username": "admin",
      "password_hash": "$2b$12$...",
      "role": "manager",
      "permissions": ["read", "write", "admin"]
    }
  ],

  "logging": {
    "level": "info",
    "file": "logs/klda-hft-engine.log",
    "max_size_mb": 100,
    "rotate": true
  }
}
```

---

## Required C++ Libraries

### 1. libpqxx (PostgreSQL C++ Client)
**Purpose:** Connect to PostgreSQL database and execute queries

**Installation (Windows):**
```bash
# Using vcpkg (recommended)
vcpkg install libpqxx:x64-windows

# Or download from: https://github.com/jtv/libpqxx
```

**Usage:**
```cpp
#include <pqxx/pqxx>

pqxx::connection conn(
    "host=localhost port=5432 "
    "dbname=KLDA-HFT_Database "
    "user=postgres "
    "password=MyKldaTechnologies2025!"
);

pqxx::work txn(conn);
pqxx::result res = txn.exec("SELECT * FROM current;");
txn.commit();
```

### 2. Crow (C++ HTTP Server Framework)
**Purpose:** Expose REST API endpoints

**Installation:**
```bash
# Header-only library
git clone https://github.com/CrowCpp/Crow.git
# Copy include/crow_all.h to your project
```

**Usage:**
```cpp
#include "crow_all.h"

crow::SimpleApp app;

CROW_ROUTE(app, "/api/current")
([]() {
    return crow::response(200, "{\"status\":\"ok\"}");
});

app.port(8080).multithreaded().run();
```

### 3. nlohmann/json (JSON Parser)
**Purpose:** Parse config.json and create JSON responses

**Installation:**
```bash
# Header-only library
vcpkg install nlohmann-json:x64-windows
```

**Usage:**
```cpp
#include <nlohmann/json.hpp>

nlohmann::json j = nlohmann::json::parse(file_content);
std::string db_host = j["database"]["host"];
```

### 4. spdlog (Fast Logging)
**Purpose:** Logging system

**Installation:**
```bash
vcpkg install spdlog:x64-windows
```

**Usage:**
```cpp
#include <spdlog/spdlog.h>

spdlog::info("Server started on port 8080");
spdlog::error("Database connection failed");
```

### 5. jwt-cpp (JWT Authentication)
**Purpose:** User authentication with JWT tokens

**Installation:**
```bash
vcpkg install jwt-cpp:x64-windows
```

**Usage:**
```cpp
#include <jwt-cpp/jwt.h>

auto token = jwt::create()
    .set_issuer("klda-hft")
    .set_subject("admin")
    .set_expires_at(std::chrono::system_clock::now() + std::chrono::hours{24})
    .sign(jwt::algorithm::hs256{"secret"});
```

---

## Data Structures

### Tick Structure
```cpp
// models/tick.h
#pragma once
#include <string>
#include <chrono>

struct Tick {
    std::chrono::system_clock::time_point time;
    std::string symbol;
    double bid;
    double ask;
    double spread;
    int64_t volume;
    int64_t buy_volume;
    int64_t sell_volume;
    int flags;

    // Helper methods
    bool is_quote() const { return (flags & 8) == 0; }
    bool is_trade() const { return (flags & 8) != 0; }
    bool is_buy_trade() const { return (flags & 32) != 0; }
    bool is_sell_trade() const { return (flags & 64) != 0; }
};
```

### Bar Structure
```cpp
// models/bar.h
#pragma once
#include <string>
#include <chrono>

struct Bar {
    std::chrono::system_clock::time_point time;
    std::string symbol;
    std::string timeframe;  // "M1", "M5", "H1", "D1", etc.
    double open;
    double high;
    double low;
    double close;
    int64_t volume;
    int spread;
};
```

### Asset Structure
```cpp
// models/asset.h
#pragma once
#include <string>

struct Asset {
    int symbol_id;
    std::string symbol;       // "TSLA"
    std::string mt5_symbol;   // "TSLA.US"
    Tick latest_tick;
};
```

---

## Database Connection Layer

### connection.h
```cpp
#pragma once
#include <pqxx/pqxx>
#include <memory>
#include <string>

class DatabaseConnection {
public:
    DatabaseConnection(const std::string& connection_string);
    ~DatabaseConnection();

    // Connection management
    bool connect();
    void disconnect();
    bool is_connected() const;

    // Query execution
    pqxx::result execute_query(const std::string& query);

    // Connection pool
    static std::shared_ptr<DatabaseConnection> get_instance();

private:
    std::string connection_string_;
    std::unique_ptr<pqxx::connection> conn_;
    bool connected_;
};
```

### queries.h
```cpp
#pragma once
#include <vector>
#include <string>
#include "models/tick.h"
#include "models/bar.h"
#include "models/asset.h"

class DatabaseQueries {
public:
    explicit DatabaseQueries(std::shared_ptr<DatabaseConnection> db);

    // CURRENT table queries
    std::vector<Asset> get_all_current_ticks();
    Tick get_latest_tick(const std::string& symbol);

    // HISTORY table queries
    std::vector<Tick> get_recent_ticks(const std::string& symbol, int seconds);
    std::vector<Tick> get_ticks_range(
        const std::string& symbol,
        const std::chrono::system_clock::time_point& start,
        const std::chrono::system_clock::time_point& end
    );

    // BARS table queries
    std::vector<Bar> get_historical_bars(
        const std::string& symbol,
        const std::string& timeframe,
        const std::chrono::system_clock::time_point& start
    );

private:
    std::shared_ptr<DatabaseConnection> db_;
};
```

---

## Analysis Engine

### order_flow.h
```cpp
#pragma once
#include <string>
#include <vector>
#include "models/tick.h"

struct OrderFlowAnalysis {
    int64_t buy_volume;
    int64_t sell_volume;
    int64_t flow_imbalance;      // buy_volume - sell_volume
    int buy_trades_count;
    int sell_trades_count;
    double imbalance_ratio;      // flow_imbalance / total_volume
};

class OrderFlowAnalyzer {
public:
    OrderFlowAnalysis analyze(const std::vector<Tick>& ticks);

    // Analyze order flow for a symbol over last N seconds
    OrderFlowAnalysis analyze_symbol(
        const std::string& symbol,
        int window_seconds
    );
};
```

### spread.h
```cpp
#pragma once
#include <string>
#include <vector>
#include "models/tick.h"

struct SpreadAnalysis {
    double avg_spread;
    double min_spread;
    double max_spread;
    double spread_volatility;  // Standard deviation
    int quote_count;
};

class SpreadAnalyzer {
public:
    SpreadAnalysis analyze(const std::vector<Tick>& ticks);

    // Analyze spread for a symbol over last N seconds
    SpreadAnalysis analyze_symbol(
        const std::string& symbol,
        int window_seconds
    );
};
```

### signals.h
```cpp
#pragma once
#include <string>
#include <vector>
#include "order_flow.h"
#include "spread.h"

enum class SignalType {
    BUY,
    SELL,
    NEUTRAL
};

struct TradingSignal {
    std::string symbol;
    SignalType signal;
    double confidence;  // 0.0 to 1.0
    std::string reason;
    std::chrono::system_clock::time_point timestamp;
};

class SignalGenerator {
public:
    TradingSignal generate_signal(
        const std::string& symbol,
        const OrderFlowAnalysis& order_flow,
        const SpreadAnalysis& spread
    );

    std::vector<TradingSignal> generate_all_signals();
};
```

---

## REST API Endpoints

### GET /api/current
**Description:** Get latest tick for all assets
**Response:**
```json
{
  "status": "success",
  "data": [
    {
      "symbol": "TSLA",
      "bid": 448.67,
      "ask": 449.00,
      "spread": 33.0,
      "volume": 0,
      "buy_volume": 0,
      "sell_volume": 0,
      "flags": 6,
      "last_updated": "2026-01-13T17:54:43.205000+01:00"
    },
    ...
  ]
}
```

### GET /api/current/:symbol
**Description:** Get latest tick for specific symbol
**Example:** `/api/current/TSLA`
**Response:**
```json
{
  "status": "success",
  "data": {
    "symbol": "TSLA",
    "bid": 448.67,
    "ask": 449.00,
    "spread": 33.0,
    "volume": 0,
    "last_updated": "2026-01-13T17:54:43.205000+01:00"
  }
}
```

### GET /api/history/:symbol
**Description:** Get tick history for symbol
**Query Parameters:**
- `seconds` - Time window (default: 300)
**Example:** `/api/history/TSLA?seconds=600`
**Response:**
```json
{
  "status": "success",
  "symbol": "TSLA",
  "window_seconds": 600,
  "tick_count": 1250,
  "data": [
    {
      "time": "2026-01-13T17:54:43.205000+01:00",
      "bid": 448.67,
      "ask": 449.00,
      "spread": 33.0,
      "volume": 0,
      "flags": 6
    },
    ...
  ]
}
```

### GET /api/analysis/:symbol
**Description:** Run analysis on symbol
**Query Parameters:**
- `window` - Time window in seconds (default: 300)
**Example:** `/api/analysis/TSLA?window=600`
**Response:**
```json
{
  "status": "success",
  "symbol": "TSLA",
  "window_seconds": 600,
  "analysis": {
    "order_flow": {
      "buy_volume": 125000,
      "sell_volume": 98000,
      "flow_imbalance": 27000,
      "buy_trades": 45,
      "sell_trades": 38,
      "imbalance_ratio": 0.121
    },
    "spread": {
      "avg_spread": 28.5,
      "min_spread": 20.0,
      "max_spread": 45.0,
      "spread_volatility": 5.2,
      "quote_count": 1205
    },
    "signal": {
      "type": "BUY",
      "confidence": 0.72,
      "reason": "Strong buy imbalance (27K) with low spread volatility"
    }
  }
}
```

### GET /api/signals
**Description:** Get trading signals for all assets
**Response:**
```json
{
  "status": "success",
  "signals": [
    {
      "symbol": "TSLA",
      "signal": "BUY",
      "confidence": 0.72,
      "reason": "Strong buy imbalance",
      "timestamp": "2026-01-13T17:55:00.000000+01:00"
    },
    {
      "symbol": "NVDA",
      "signal": "NEUTRAL",
      "confidence": 0.45,
      "reason": "Balanced flow",
      "timestamp": "2026-01-13T17:55:00.000000+01:00"
    },
    ...
  ]
}
```

### POST /api/backtest
**Description:** Run backtest on historical data
**Request Body:**
```json
{
  "symbol": "TSLA",
  "start_date": "2020-01-01",
  "end_date": "2024-12-31",
  "timeframe": "D1",
  "strategy": "order_flow_imbalance",
  "parameters": {
    "threshold": 0.65,
    "window": 300
  }
}
```
**Response:**
```json
{
  "status": "success",
  "backtest_results": {
    "total_trades": 1250,
    "winning_trades": 675,
    "losing_trades": 575,
    "win_rate": 0.54,
    "profit": 125000.50,
    "max_drawdown": -15000.25
  }
}
```

### POST /api/auth/login
**Description:** User authentication
**Request Body:**
```json
{
  "username": "admin",
  "password": "your-password"
}
```
**Response:**
```json
{
  "status": "success",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 86400,
  "user": {
    "username": "admin",
    "role": "manager"
  }
}
```

---

## Build Configuration (CMakeLists.txt)

```cmake
cmake_minimum_required(VERSION 3.15)
project(klda-hft-engine VERSION 1.0)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find packages
find_package(libpqxx CONFIG REQUIRED)
find_package(nlohmann_json CONFIG REQUIRED)
find_package(spdlog CONFIG REQUIRED)

# Source files
set(SOURCES
    src/main.cpp
    src/database/connection.cpp
    src/database/queries.cpp
    src/analysis/order_flow.cpp
    src/analysis/spread.cpp
    src/analysis/signals.cpp
    src/api/server.cpp
    src/api/routes.cpp
    src/api/auth.cpp
    src/utils/config.cpp
    src/utils/logger.cpp
)

# Include directories
include_directories(src)
include_directories(include)

# Executable
add_executable(klda-hft-engine ${SOURCES})

# Link libraries
target_link_libraries(klda-hft-engine PRIVATE
    libpqxx::pqxx
    nlohmann_json::nlohmann_json
    spdlog::spdlog
)

# Windows-specific
if(WIN32)
    target_link_libraries(klda-hft-engine PRIVATE ws2_32)
endif()
```

---

## Development Environment Setup

### 1. Install Visual Studio 2022
- Download from: https://visualstudio.microsoft.com/
- Select "Desktop development with C++"

### 2. Install vcpkg (Package Manager)
```powershell
# Clone vcpkg
git clone https://github.com/Microsoft/vcpkg.git
cd vcpkg

# Bootstrap
.\bootstrap-vcpkg.bat

# Integrate with Visual Studio
.\vcpkg integrate install
```

### 3. Install Required Libraries
```powershell
# Install all dependencies
.\vcpkg install libpqxx:x64-windows
.\vcpkg install nlohmann-json:x64-windows
.\vcpkg install spdlog:x64-windows
.\vcpkg install jwt-cpp:x64-windows
```

### 4. Build the Project
```powershell
cd KLDA-HFT/cpp-backend
mkdir build
cd build

# Configure with CMake
cmake .. -DCMAKE_TOOLCHAIN_FILE=C:/path/to/vcpkg/scripts/buildsystems/vcpkg.cmake

# Build
cmake --build . --config Release
```

### 5. Run the Engine
```powershell
.\Release\klda-hft-engine.exe
```

---

## Configuration on First Run

1. **Edit config.json:**
   - Set database credentials
   - Set API server port
   - Set JWT secret key
   - Configure analysis parameters

2. **Generate Admin Password Hash:**
```cpp
#include <bcrypt/BCrypt.hpp>
std::string hash = BCrypt::generateHash("your-password", 12);
// Put hash in config.json users section
```

3. **Start the Engine:**
```bash
./klda-hft-engine
```

4. **Test API:**
```bash
curl http://localhost:8080/api/health
curl http://localhost:8080/api/current
```

---

## Security Considerations

1. **Database Access:** Read-only user credentials (recommended)
2. **API Authentication:** JWT tokens with 24-hour expiration
3. **HTTPS:** Use reverse proxy (nginx) for production
4. **Password Storage:** Bcrypt hashing with salt rounds = 12
5. **Configuration:** Keep config.json out of version control

---

## Monitoring & Logging

**Log Levels:**
- DEBUG: Detailed execution flow
- INFO: General operations (API requests, queries)
- WARN: Non-critical issues (slow queries)
- ERROR: Critical failures (DB connection lost)

**Log File Location:** `logs/klda-hft-engine.log`

**Metrics to Track:**
- Database query latency
- API response times
- Analysis computation time
- Memory usage
- Active connections

---

## Next Steps

1. Create project directory structure
2. Install development tools (VS2022 + vcpkg)
3. Install required libraries
4. Implement database connection layer
5. Implement basic API server
6. Test database connectivity
7. Implement analysis algorithms
8. Build frontend dashboard

---

**End of C++ Backend Configuration Document**
