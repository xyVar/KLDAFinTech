# KLDA-HFT RELIABILITY SYSTEM

## Overview

This document explains the complete reliability system for solid, uninterrupted tick data ingestion.

---

## Architecture Components

### 1. Database Schema (3-Table Design)

```
CURRENT TABLE (Entry Point)
├─ 17 rows (one per symbol)
├─ Latest tick only
├─ Updated in real-time by Flask API
└─ Purpose: Fast access to current prices

HISTORY TABLES (Permanent Storage)
├─ 17 tables (one per symbol: tsla_history, vix_history, etc.)
├─ ALL ticks stored forever (TimescaleDB hypertables)
├─ Columns: time, bid, ask, spread, volume
└─ Purpose: Complete tick-by-tick history

BARS TABLES (Pre-computed OHLCV)
├─ 17 tables (one per symbol: tsla_bars, vix_bars, etc.)
├─ Pre-aggregated: M1, M5, M15, M30, H1, H4, D1, W1, MN
├─ Columns: time, timeframe, open, high, low, close, volume, spread
└─ Purpose: Fast chart rendering (continuous aggregates)
```

---

## Reliability Features

### ✅ What's Implemented

1. **Flask API Health Check**
   - Endpoint: `GET /health`
   - Returns: Database connection status
   - Monitored by: Dashboard, C++ backend

2. **Buffer System**
   - 14-tick buffer in Flask API
   - Prevents data loss during brief DB outages
   - Automatic flush every 2 seconds

3. **Error Tracking**
   - Flask `/stats` endpoint shows errors
   - Zero data loss so far (105,375 ticks processed)

4. **TimescaleDB Hypertables**
   - Automatic time-based partitioning (chunks)
   - Efficient inserts and queries
   - Compression ready (currently disabled)

### ❌ What Needs Implementation

1. **Windows Service (Flask API)**
2. **Auto-Reconnect (MT5 Bridge)**
3. **Email Monitoring (Hourly Checks)**
4. **Retry Logic (Failed Inserts)**
5. **Compression (Storage Optimization)**

---

## Implementation Plan

### Component 1: Flask as Windows Service

**File:** `flask_service.py` (NSSM wrapper)

**Steps:**
1. Install NSSM (Non-Sucking Service Manager)
2. Create service definition
3. Configure auto-restart on failure
4. Set dependencies (PostgreSQL must start first)

**Command:**
```cmd
nssm install KLDA-HFT-FlaskAPI "C:\Python313\python.exe" "C:\Users\PC\Desktop\KLDAFinTech\KLDA-HFT\api\tick_receiver.py"
nssm set KLDA-HFT-FlaskAPI AppDirectory "C:\Users\PC\Desktop\KLDAFinTech\KLDA-HFT\api"
nssm set KLDA-HFT-FlaskAPI DisplayName "KLDA-HFT Flask API"
nssm set KLDA-HFT-FlaskAPI Description "Real-time tick data receiver from MT5"
nssm set KLDA-HFT-FlaskAPI Start SERVICE_AUTO_START
nssm set KLDA-HFT-FlaskAPI AppStdout "C:\Users\PC\Desktop\KLDAFinTech\KLDA-HFT\logs\flask_service.log"
nssm set KLDA-HFT-FlaskAPI AppStderr "C:\Users\PC\Desktop\KLDAFinTech\KLDA-HFT\logs\flask_service_error.log"
nssm start KLDA-HFT-FlaskAPI
```

---

### Component 2: Auto-Reconnect MT5 Bridge

**Enhancement to:** `mt5_tick_capture_ALL_TICKS.py`

**Features:**
- Detect MT5 disconnection every 60 seconds
- Automatic reconnection with exponential backoff
- Signal capture stop via signal file: `STOP_CAPTURE.signal`

**Code Additions:**
```python
# Check connection health every minute
if iteration % 600 == 0:  # Every 60 seconds (600 * 100ms)
    if not mt5.terminal_info().connected:
        print("[WARNING] MT5 disconnected! Attempting reconnect...")
        mt5.shutdown()
        time.sleep(5)
        if not mt5.initialize():
            print("[ERROR] Reconnect failed! Retrying in 30s...")
            time.sleep(30)
            continue
        print("[OK] MT5 reconnected successfully!")

# Check for stop signal
if os.path.exists("STOP_CAPTURE.signal"):
    print("[SIGNAL] Stop signal detected. Shutting down gracefully...")
    break
```

---

### Component 3: Hourly Email Monitoring

**File:** `hourly_monitor.py`

**Features:**
- Runs every hour via Task Scheduler
- Checks tick ingestion rate
- Verifies database health
- Sends email if issues detected

**Email Triggers:**
- No new ticks in last hour
- Database connection failed
- Flask API not responding
- Disk space < 10% free

**Email Content:**
```
Subject: [KLDA-HFT] Hourly Health Check - {STATUS}

Database: KLDA-HFT_Database
Timestamp: 2026-01-21 14:00:00

TICK INGESTION (Last Hour):
- TSLA: 1,234 ticks ✅
- VIX: 2,456 ticks ✅
- NAS100: 3,678 ticks ✅
- Total: 45,123 ticks ✅

SYSTEM STATUS:
- Flask API: RUNNING ✅
- MT5 Bridge: RUNNING ✅
- PostgreSQL: RUNNING ✅
- Disk Space: 45% free ✅

ALERTS:
None - All systems operational!
```

---

### Component 4: Retry Logic (Database Inserts)

**Enhancement to:** `tick_receiver.py` (Flask API)

**Features:**
- Retry failed inserts up to 3 times
- Exponential backoff (1s, 2s, 4s)
- Persist failed ticks to disk if all retries fail
- Replay failed ticks when DB recovers

**Code Pattern:**
```python
def insert_with_retry(cursor, query, params, max_retries=3):
    for attempt in range(max_retries):
        try:
            cursor.execute(query, params)
            return True
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # 1s, 2s, 4s
                print(f"[RETRY] DB insert failed (attempt {attempt+1}/{max_retries}). Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                # Final attempt failed - persist to disk
                with open('failed_ticks.log', 'a') as f:
                    f.write(json.dumps({
                        'timestamp': datetime.now().isoformat(),
                        'query': query,
                        'params': params
                    }) + '\n')
                print(f"[ERROR] DB insert failed after {max_retries} attempts. Logged to failed_ticks.log")
                return False
```

---

### Component 5: TimescaleDB Compression

**SQL Script:** `enable_compression.sql`

**Benefits:**
- 10x storage reduction
- Faster queries (compressed chunks)
- Automatic compression of old data

**Commands:**
```sql
-- Enable compression on all history tables
ALTER TABLE tsla_history SET (
    timescaledb.compress,
    timescaledb.compress_orderby = 'time DESC',
    timescaledb.compress_segmentby = ''
);

-- Add compression policy (compress data older than 7 days)
SELECT add_compression_policy('tsla_history', INTERVAL '7 days');

-- Repeat for all 17 history tables...
```

---

## Deployment Steps

### Phase 1: Immediate (Today)
```bash
# 1. Enable compression
cd C:\Users\PC\Desktop\KLDAFinTech\KLDA-HFT\database
psql -U postgres -d KLDA-HFT_Database -f enable_compression.sql

# 2. Create continuous aggregates
psql -U postgres -d KLDA-HFT_Database -f create_continuous_aggregates.sql

# 3. Create positions table
psql -U postgres -d KLDA-HFT_Database -f create_positions_table.sql
```

### Phase 2: This Week
```bash
# 1. Install NSSM
winget install nssm

# 2. Create Flask service
nssm install KLDA-HFT-FlaskAPI ...

# 3. Set up Task Scheduler for hourly monitor
schtasks /create /tn "KLDA-HFT-Monitor" /tr "python hourly_monitor.py" /sc hourly
```

### Phase 3: Testing
```bash
# 1. Test auto-reconnect
# - Close MT5 terminal
# - Watch tick_capture.log for reconnection

# 2. Test service restart
net stop KLDA-HFT-FlaskAPI
net start KLDA-HFT-FlaskAPI

# 3. Test email alerts
python hourly_monitor.py --test
```

---

## Monitoring Dashboard

### Real-Time Metrics
- **Tick ingestion rate**: `/stats` endpoint
- **Database size**: `SELECT pg_database_size('KLDA-HFT_Database');`
- **Oldest uncompressed data**: Query hypertable chunks
- **Failed ticks**: `tail -f failed_ticks.log`

### Health Check URLs
- Flask API: `http://localhost:5000/health`
- Database: `psql -U postgres -c "\l"`
- C++ Backend: `docker ps | grep klda-hft`

---

## Troubleshooting Guide

### Issue: "No new ticks in last hour"
**Diagnosis:**
1. Check MT5 terminal is running
2. Check `mt5_tick_capture_ALL_TICKS.py` process is alive
3. Check Flask API `/health` endpoint

**Fix:**
```bash
# Restart tick capture
cd C:\Users\PC\Desktop\KLDAFinTech\KLDA-HFT\python-bridge
python mt5_tick_capture_ALL_TICKS.py
```

### Issue: "Database connection failed"
**Diagnosis:**
1. Check PostgreSQL service is running
2. Check disk space (needs > 1GB free)
3. Check max_connections in postgresql.conf

**Fix:**
```bash
# Restart PostgreSQL
net stop postgresql-x64-16
net start postgresql-x64-16
```

### Issue: "Flask API not responding"
**Diagnosis:**
1. Check port 5000 is not in use: `netstat -ano | findstr :5000`
2. Check Flask service status
3. Check error logs

**Fix:**
```bash
# Restart Flask service
net stop KLDA-HFT-FlaskAPI
net start KLDA-HFT-FlaskAPI
```

---

## Performance Tuning

### PostgreSQL Configuration
**File:** `C:\Program Files\PostgreSQL\16\data\postgresql.conf`

```ini
# Memory settings
shared_buffers = 2GB                    # 25% of RAM
effective_cache_size = 6GB              # 75% of RAM
maintenance_work_mem = 512MB

# Write performance
wal_buffers = 16MB
checkpoint_completion_target = 0.9
max_wal_size = 4GB

# Connection pooling
max_connections = 100
```

### TimescaleDB Tuning
```sql
-- Increase chunk interval for high-frequency data
SELECT set_chunk_time_interval('tsla_history', INTERVAL '1 day');

-- Enable parallel query execution
SET max_parallel_workers_per_gather = 4;
```

---

**System Status:** OPERATIONAL (with recommended improvements)
**Next Review:** Weekly or after major changes
