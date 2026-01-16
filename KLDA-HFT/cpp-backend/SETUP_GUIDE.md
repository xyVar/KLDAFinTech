# C++ Backend Setup Guide

**Current Status:** Development environment partially set up
- ✅ Visual Studio 2022 installed
- ✅ vcpkg cloned and bootstrapped
- ✅ CMake 4.2.1 installed
- ✅ Project directory structure created
- ✅ config.json created
- ✅ Data model headers created (Tick, Bar, Asset)
- ⚠️ vcpkg having toolchain issues (detecting VS 2019 instead of VS 2022)

---

## Current Issue

vcpkg is detecting Visual Studio 2019 Build Tools instead of VS 2022, causing build failures.

**Detected compiler:**
```
C:/Program Files (x86)/Microsoft Visual Studio/2019/BuildTools/VC/Tools/MSVC/14.29.30133/bin/Hostx64/x64/cl.exe
```

**Should be:**
```
C:/Program Files/Microsoft Visual Studio/2022/.../VC/Tools/MSVC/.../bin/Hostx64/x64/cl.exe
```

---

## Recommended Next Steps

### Option 1: Fix vcpkg Toolchain (Recommended)

1. **Uninstall VS 2019 Build Tools** (if not needed):
   ```powershell
   # Open "Apps & Features" in Windows Settings
   # Search for "Visual Studio Build Tools 2019"
   # Uninstall
   ```

2. **Or configure vcpkg to use VS 2022**:
   Create file `C:\Users\PC\Desktop\KLDAFinTech\vcpkg\triplets\x64-windows-vs2022.cmake`:
   ```cmake
   set(VCPKG_TARGET_ARCHITECTURE x64)
   set(VCPKG_CRT_LINKAGE dynamic)
   set(VCPKG_LIBRARY_LINKAGE dynamic)
   set(VCPKG_PLATFORM_TOOLSET v143)  # VS 2022 toolset
   ```

   Then install with:
   ```bash
   cd C:\Users\PC\Desktop\KLDAFinTech\vcpkg
   ./vcpkg install libpqxx:x64-windows-vs2022
   ./vcpkg install nlohmann-json:x64-windows-vs2022
   ./vcpkg install spdlog:x64-windows-vs2022
   ```

### Option 2: Manual Library Installation (Simpler)

Download header-only libraries manually:

1. **nlohmann/json** (JSON parser):
   ```powershell
   # Download single-header file
   curl -o include/nlohmann/json.hpp https://github.com/nlohmann/json/releases/download/v3.11.3/json.hpp
   ```

2. **Crow** (HTTP server):
   ```powershell
   # Clone repository
   cd include
   git clone https://github.com/CrowCpp/Crow.git
   # Copy include/crow_all.h to your project
   ```

3. **libpq** (PostgreSQL C library - simpler than libpqxx):
   - Download from: https://www.postgresql.org/download/windows/
   - Or use existing PostgreSQL 16 installation:
     ```
     C:\Program Files\PostgreSQL\16\include\libpq-fe.h
     C:\Program Files\PostgreSQL\16\lib\libpq.lib
     ```

### Option 3: Start with Minimal Setup (What We'll Do Now)

Create a minimal C++ project that:
1. Reads config.json (manual parsing for now)
2. Prints database connection info
3. Compiles successfully with VS 2022

Then add libraries incrementally once toolchain is fixed.

---

## Current Project Structure

```
cpp-backend/
├── src/
│   ├── models/
│   │   ├── tick.h ✅         (Tick data structure)
│   │   ├── bar.h ✅          (Bar data structure)
│   │   └── asset.h ✅        (Asset structure)
│   ├── database/
│   ├── analysis/
│   ├── api/
│   └── utils/
├── include/                  (External headers - empty)
├── logs/                     (Runtime logs)
├── config.json ✅            (Configuration)
├── SETUP_GUIDE.md ✅         (This file)
└── README.md                 (Project overview)
```

---

## Next Session Tasks

1. **Fix vcpkg toolchain** (Option 1 or 2 above)
2. **Install required libraries:**
   - libpq or libpqxx (PostgreSQL)
   - nlohmann-json (JSON)
   - Crow (HTTP server)
   - spdlog (Logging)
3. **Create CMakeLists.txt**
4. **Create main.cpp** (entry point)
5. **Test compilation**
6. **Implement database connection layer**

---

## Manual Workaround (If Urgent)

If you need to proceed immediately without vcpkg:

1. **Use existing PostgreSQL installation** for libpq
2. **Download header-only libraries** (json, crow)
3. **Create simple CMakeLists.txt**:

```cmake
cmake_minimum_required(VERSION 3.15)
project(klda-hft-engine)

set(CMAKE_CXX_STANDARD 17)

# PostgreSQL (from existing installation)
include_directories("C:/Program Files/PostgreSQL/16/include")
link_directories("C:/Program Files/PostgreSQL/16/lib")

# nlohmann-json (header-only)
include_directories(include/nlohmann)

# Source files
add_executable(klda-hft-engine
    src/main.cpp
)

# Link PostgreSQL
target_link_libraries(klda-hft-engine PRIVATE libpq)
```

4. **Compile manually**:
```powershell
# Open "Developer Command Prompt for VS 2022"
cd C:\Users\PC\Desktop\KLDAFinTech\KLDA-HFT\cpp-backend
mkdir build
cd build
cmake ..
cmake --build . --config Release
```

---

## Files Created So Far

### config.json
- Database connection settings
- API server configuration
- Analysis parameters
- Asset list (17 assets)
- Logging configuration

### src/models/tick.h
- Tick data structure
- MT5 flag constants
- Helper methods (is_quote, is_trade, is_buy_trade, is_sell_trade)
- Spread calculation

### src/models/bar.h
- Bar data structure (OHLCV)
- Timeframe support (M1, M5, H1, D1, etc.)
- Helper methods (body, range, is_bullish, is_bearish, wicks)

### src/models/asset.h
- Asset structure
- Symbol mapping (database ↔ MT5)
- Asset type enum (STOCK, INDEX, COMMODITY)
- Latest tick storage

---

## Database Connection Strategy

Once libraries are installed, we'll use **libpq** (C library) instead of libpqxx:

```cpp
#include <libpq-fe.h>

// Connect
PGconn *conn = PQconnectdb(
    "host=localhost port=5432 "
    "dbname=KLDA-HFT_Database "
    "user=postgres "
    "password=MyKldaTechnologies2025!"
);

// Check connection
if (PQstatus(conn) != CONNECTION_OK) {
    fprintf(stderr, "Connection failed: %s", PQerrorMessage(conn));
    PQfinish(conn);
    return 1;
}

// Query
PGresult *res = PQexec(conn, "SELECT * FROM current");
if (PQresultStatus(res) != PGRES_TUPLES_OK) {
    fprintf(stderr, "Query failed: %s", PQerrorMessage(conn));
    PQclear(res);
    PQfinish(conn);
    return 1;
}

// Process results
int rows = PQntuples(res);
for (int i = 0; i < rows; i++) {
    char *symbol = PQgetvalue(res, i, 1);  // Column 1 = symbol
    // ...
}

// Cleanup
PQclear(res);
PQfinish(conn);
```

This is simpler than libpqxx and doesn't have complex dependencies.

---

## Summary

**What we have:**
- ✅ VS 2022, vcpkg, CMake installed
- ✅ Project structure created
- ✅ Configuration file ready
- ✅ Data models defined

**What we need:**
- ⚠️ Fix vcpkg toolchain issue
- ⚠️ Install C++ libraries
- ⚠️ Create build system (CMakeLists.txt)
- ⚠️ Create main.cpp and test compilation

**Recommended path forward:**
1. Fix vcpkg to use VS 2022 (see Option 1 above)
2. Install libraries via vcpkg
3. Create CMakeLists.txt
4. Implement database connection layer
5. Build and test

---

Last Updated: 2026-01-13
