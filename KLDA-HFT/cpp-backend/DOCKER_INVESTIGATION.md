# Docker Investigation & Architecture Plan

**Date:** 2026-01-13
**Purpose:** Investigate Docker setup and plan C++ backend container architecture

---

## Current Docker Environment

### Docker Installation ✅
```
Docker version: 29.0.1
Context: desktop-linux
Status: RUNNING
```

### Existing Containers (5 running)

| Container | Image | Ports | Status |
|-----------|-------|-------|--------|
| rateradar-api | rateradarcom-backend-api | 8000:8000 | Up 3 weeks |
| rateradar-frontend | rateradarcom-frontend | 3000:3000 | Up 3 weeks |
| rateradar-websocket | rateradarcom-websocket-server | **8080:8080** | Up 3 weeks |
| rateradar-postgres | timescale/timescaledb:latest-pg15 | 5432:5432 | Up 3 weeks |
| rateradar-redis | redis:7-alpine | 6379:6379 | Up 3 weeks |

### Networks
- `rateradarcom_rateradar-network` (bridge)
- `bridge` (default)
- `host`
- `none`

---

## ⚠️ PORT CONFLICTS DISCOVERED

### Port 5432 (PostgreSQL)
**Issue:** TWO PostgreSQL services listening on port 5432:
1. **Docker PostgreSQL** (rateradar-postgres container)
2. **Windows PostgreSQL 16** (native installation)

**Question:** Which one has KLDA-HFT_Database?
- Docker PostgreSQL: Need to check
- Windows PostgreSQL: Need to verify

### Port 8080 (REST API)
**Issue:** Already used by `rateradar-websocket` container

**Solution:** Change KLDA-HFT C++ backend to different port (e.g., **8081**)

---

## Proposed Architecture

### Option 1: Connect to Windows PostgreSQL (Recommended)

```
┌─────────────────────────────────────────────────────────┐
│                    Windows Host                         │
│                                                         │
│  ┌──────────────────────┐   ┌─────────────────────┐   │
│  │ PostgreSQL 16        │   │ Python Bridge       │   │
│  │ (Native Windows)     │   │ (mt5_tick_capture)  │   │
│  │ Port: 5432          │◄──│                     │   │
│  │ DB: KLDA-HFT_Database│   └─────────────────────┘   │
│  └──────────┬───────────┘                             │
│             │ host.docker.internal                     │
│             │ (Docker → Windows bridge)                │
│  ┌──────────▼───────────┐                             │
│  │ Docker Container     │                             │
│  │                      │                             │
│  │  klda-hft-cpp-backend│                             │
│  │  - Ubuntu 22.04      │                             │
│  │  - g++ compiler      │                             │
│  │  - libpq             │                             │
│  │  - Port: 8081:8081   │                             │
│  └──────────────────────┘                             │
└─────────────────────────────────────────────────────────┘
```

**Connection String in Container:**
```
host=host.docker.internal
port=5432
dbname=KLDA-HFT_Database
user=postgres
password=MyKldaTechnologies2025!
```

**Advantages:**
- Uses existing PostgreSQL with all data
- Python bridge and API already connected
- No data migration needed

**Disadvantages:**
- Requires Windows firewall to allow container access
- Slightly more complex network setup

---

### Option 2: Connect to Docker PostgreSQL

```
┌─────────────────────────────────────────────────────────┐
│                Docker Network: bridge                   │
│                                                         │
│  ┌──────────────────────┐   ┌─────────────────────┐   │
│  │ rateradar-postgres   │   │ klda-hft-cpp-backend│   │
│  │ TimescaleDB          │   │ Ubuntu 22.04        │   │
│  │ Port: 5432          │◄──┤ Port: 8081          │   │
│  │                      │   │                     │   │
│  └──────────────────────┘   └─────────────────────┘   │
│             ▲                                           │
│             │ (need to migrate data)                    │
│  ┌──────────┴───────────┐                             │
│  │ Windows Host         │                             │
│  │ Python Bridge        │                             │
│  │ API Server           │                             │
│  └──────────────────────┘                             │
└─────────────────────────────────────────────────────────┘
```

**Connection String:**
```
host=rateradar-postgres
port=5432
dbname=KLDA-HFT_Database
user=postgres
password=<need_password>
```

**Advantages:**
- All database containers in same Docker network
- Simpler networking (no host.docker.internal)

**Disadvantages:**
- Need to CREATE KLDA-HFT_Database in Docker PostgreSQL
- Need to migrate/reimport all data (170,544 bars + live ticks)
- Need to reconfigure Python bridge and API server

---

## Investigation Tasks

### 1. Determine Database Location ✓ (Partially)

**Finding:**
- Port 5432 has TWO listeners (Docker + Windows)
- Need to verify which one has KLDA-HFT_Database

**Action:** Run query on both:
```bash
# Windows PostgreSQL
"C:\Program Files\PostgreSQL\16\bin\psql.exe" -h localhost -U postgres -c "\l" | grep KLDA

# Docker PostgreSQL
docker exec rateradar-postgres psql -U postgres -c "\l" | grep KLDA
```

### 2. Check Python Bridge & API Server Connection

**Current Status:** Both running (tasks b796f34, bd8a243)

**Question:** Which PostgreSQL are they connected to?

**Check:** Look at API server logs or config:
```bash
# API server config (tick_receiver.py line 17-23)
DB_CONFIG = {
    'host': 'localhost',  # ← This is Windows PostgreSQL
    'port': 5432,
    'database': 'KLDA-HFT_Database',
    'user': 'postgres',
    'password': 'MyKldaTechnologies2025!'
}
```

**Answer:** They connect to **Windows PostgreSQL** (localhost = Windows host, not Docker)

### 3. Resolve Port Conflicts

**Port 8080:** Already used by rateradar-websocket

**Solution:** Change C++ backend to port 8081

**Update docker-compose.yml:**
```yaml
services:
  cpp-backend:
    ports:
      - "8081:8081"  # Changed from 8080
```

---

## Recommended Architecture (FINAL)

### Architecture Diagram

```
┌───────────────────────────────────────────────────────────────┐
│                      WINDOWS HOST                             │
│                                                               │
│  ┌────────────────┐   ┌────────────────┐   ┌──────────────┐ │
│  │ MT5 Terminal   │   │ PostgreSQL 16  │   │ Python Bridge│ │
│  │ (Broker)       │──►│ Native Windows │◄──│ Task b796f34 │ │
│  └────────────────┘   │ Port: 5432    │   └──────────────┘ │
│                       │ KLDA-HFT_DB    │                     │
│  ┌────────────────┐   │ 35 tables      │                     │
│  │ API Server     │──►│ 170,544 bars   │                     │
│  │ Task bd8a243   │   └────────┬───────┘                     │
│  │ Port: 5000     │            │                             │
│  └────────────────┘            │                             │
│                                │ host.docker.internal        │
│  ┌─────────────────────────────▼────────────────────────┐   │
│  │         DOCKER CONTAINER                              │   │
│  │  ┌──────────────────────────────────────────────┐    │   │
│  │  │  klda-hft-cpp-backend                        │    │   │
│  │  │  - Ubuntu 22.04                              │    │   │
│  │  │  - g++ 11.4.0                                │    │   │
│  │  │  - libpq-dev (PostgreSQL C library)          │    │   │
│  │  │  - nlohmann-json (JSON parser)               │    │   │
│  │  │                                               │    │   │
│  │  │  Functions:                                   │    │   │
│  │  │  1. Read CURRENT table (live ticks)          │    │   │
│  │  │  2. Read HISTORY tables (tick archives)      │    │   │
│  │  │  3. Read BARS tables (historical data)       │    │   │
│  │  │  4. Perform analysis (order flow, spread)    │    │   │
│  │  │  5. Generate trading signals                 │    │   │
│  │  │  6. Expose REST API (port 8081)              │    │   │
│  │  └──────────────────────────────────────────────┘    │   │
│  │                                                       │   │
│  │  Exposed Port: 0.0.0.0:8081 → 8081                  │   │
│  └───────────────────────────────────────────────────────┘   │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **MT5 Broker** → Python Bridge (every 1 sec)
2. **Python Bridge** → API Server (HTTP POST)
3. **API Server** → Windows PostgreSQL (SQL INSERT/UPDATE)
4. **C++ Backend Container** → Windows PostgreSQL (SQL SELECT, read-only)
5. **C++ Backend** → REST API (port 8081) [FUTURE: Frontend]

---

## Docker Build Process

### What Happens When We Run `docker-compose build`:

```
1. Downloads Ubuntu 22.04 image (~70 MB)
   └─► FROM ubuntu:22.04

2. Installs build tools
   ├─► apt-get install build-essential (g++, make)
   ├─► apt-get install cmake
   ├─► apt-get install libpq-dev (PostgreSQL C library)
   └─► apt-get install postgresql-client (psql tool)

3. Copies source code into container
   ├─► COPY src/ → /app/src/
   ├─► COPY include/ → /app/include/
   ├─► COPY config.json → /app/
   └─► COPY CMakeLists.txt → /app/

4. Compiles C++ code
   ├─► cmake .. (configure build)
   └─► make (compile)
        ├─► Compiles src/main.cpp
        ├─► Compiles src/database/connection.cpp
        └─► Links with libpq
        └─► Creates executable: build/klda-hft-engine

5. Sets up runtime
   ├─► EXPOSE 8081 (REST API port)
   └─► CMD ["./build/klda-hft-engine"] (run on start)

Total build time: ~2-3 minutes (first time)
Image size: ~500 MB
```

### What Happens When We Run `docker-compose up`:

```
1. Creates container from image
   └─► klda-hft-cpp-backend

2. Configures networking
   ├─► Connects to klda-network (bridge)
   └─► Maps host.docker.internal → Windows host IP

3. Sets environment variables
   ├─► DATABASE_HOST=host.docker.internal
   ├─► DATABASE_PORT=5432
   ├─► DATABASE_NAME=KLDA-HFT_Database
   ├─► DATABASE_USER=postgres
   └─► DATABASE_PASSWORD=MyKldaTechnologies2025!

4. Runs the executable
   └─► ./build/klda-hft-engine
        ├─► Reads config.json
        ├─► Connects to PostgreSQL (Windows host)
        ├─► Queries CURRENT table
        └─► Prints 17 assets with prices

5. Keeps running (ready for future REST API)
```

---

## Configuration Changes Needed

### 1. Update docker-compose.yml Port

**Change:**
```yaml
ports:
  - "8081:8081"  # Changed from 8080 (conflict with rateradar-websocket)
```

### 2. Verify Database Connection String

**In config.json:**
```json
{
  "database": {
    "host": "localhost",  ← Will be overridden by docker-compose
    "port": 5432,
    "name": "KLDA-HFT_Database",
    "user": "postgres",
    "password": "MyKldaTechnologies2025!"
  }
}
```

**Override in docker-compose.yml:**
```yaml
environment:
  - DATABASE_HOST=host.docker.internal
```

This way config.json works for both:
- Local development (host=localhost)
- Docker container (host=host.docker.internal from environment)

---

## Testing Plan

### Phase 1: Build Image
```bash
cd C:\Users\PC\Desktop\KLDAFinTech\KLDA-HFT\cpp-backend
docker-compose build
```

**Expected output:**
- Downloading Ubuntu image
- Installing packages
- Compiling C++ code
- "Successfully built klda-hft-cpp-backend"

### Phase 2: Test Database Connection
```bash
docker-compose up
```

**Expected output:**
```
======================================
KLDA-HFT C++ Backend Engine
======================================

[1] Loading configuration...
[OK] Configuration loaded

[2] Connecting to PostgreSQL...
[OK] Connected to PostgreSQL database

[3] Querying CURRENT table...
[OK] Found 17 assets

Symbol     | Bid       | Ask       | Last Updated
-------------------------------------------------------------
AAPL       | 259.94    | 260.06    | 2026-01-13 17:54:42
AMD        | 221.25    | 221.49    | 2026-01-13 17:54:43
...

======================================
[SUCCESS] Database connection test passed!
======================================
```

### Phase 3: Verify Container Status
```bash
docker ps
```

**Expected:**
```
CONTAINER ID   IMAGE                    STATUS      PORTS
<id>           klda-hft-cpp-backend     Up          0.0.0.0:8081->8081/tcp
```

---

## Next Steps After Connection Confirmed

1. **Add Analysis Algorithms**
   - Order flow imbalance calculation
   - Spread analysis
   - Pattern detection

2. **Implement REST API**
   - Crow HTTP server (C++)
   - Endpoints: /api/current, /api/analysis, /api/signals

3. **Add Logging**
   - spdlog library
   - Log to /app/logs/

4. **Frontend Integration**
   - React/Vue dashboard
   - Connect to port 8081

---

## Risks & Mitigation

### Risk 1: Docker can't reach Windows PostgreSQL
**Symptom:** Connection timeout or refused
**Cause:** Windows Firewall blocking container
**Solution:**
```powershell
# Allow PostgreSQL through firewall
New-NetFirewallRule -DisplayName "PostgreSQL Docker" -Direction Inbound -LocalPort 5432 -Protocol TCP -Action Allow
```

### Risk 2: Wrong PostgreSQL detected
**Symptom:** Database not found
**Cause:** Connecting to Docker PostgreSQL instead of Windows
**Solution:** Verify connection string uses `host.docker.internal`

### Risk 3: Port 8081 also in use
**Symptom:** Port binding error
**Cause:** Another service using 8081
**Solution:** Change to 8082 or check with `netstat -ano | findstr :8081`

---

## Summary

**Current Findings:**
- ✅ Docker installed and running (v29.0.1)
- ✅ 5 existing containers (including PostgreSQL + websocket)
- ⚠️ Port conflicts: 8080 (websocket), 5432 (dual PostgreSQL)
- ✅ Python bridge + API server connected to Windows PostgreSQL
- ✅ KLDA-HFT_Database is on Windows PostgreSQL (not Docker)

**Recommended Approach:**
1. Keep existing Windows PostgreSQL (has all data)
2. Create Docker container for C++ backend
3. Container connects to Windows PostgreSQL via host.docker.internal
4. Change API port from 8080 to 8081
5. All components connected:
   ```
   Python → API → Windows PostgreSQL ← Docker C++ Backend
   ```

**Next Action:**
1. Update docker-compose.yml (port 8081)
2. Run `docker-compose build`
3. Run `docker-compose up`
4. Verify connection to KLDA-HFT_Database

---

**Last Updated:** 2026-01-13
