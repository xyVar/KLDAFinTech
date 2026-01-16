# KLDA-HFT Broker Connection Setup

## Complete Broker-to-Database Connection

This guide shows how to connect your MT5 broker to the PostgreSQL database for real-time tick capture.

---

## System Architecture

```
MT5 Broker (17 assets)
      ↓ OnTick()
[KLDA_TickCapture_EA.ex5] - Captures every tick
      ↓ HTTP POST (JSON)
[tick_receiver.py] - Python Flask API Server
      ↓ PostgreSQL Connection
Database:
  ├── CURRENT table (UPDATE 17 rows)
  └── HISTORY tables (INSERT ticks forever)
```

---

## Files Created

### 1. Python API Server
**Location:** `C:\Users\PC\Desktop\KLDAFinTech\KLDA-HFT\api\tick_receiver.py`

**Purpose:** Receives tick data via HTTP and writes to database

**Features:**
- Batch processing (100 ticks per batch)
- Background flusher (1 second interval)
- Updates CURRENT table on every tick
- Archives to HISTORY tables
- Statistics tracking

### 2. MQL5 Expert Advisor
**Location:** `C:\Users\PC\AppData\Roaming\MetaQuotes\Terminal\73B7A2420D6397DFF9014A20F1201F97\MQL5\Experts\Kosta EA\KLDA_TickCapture_EA.mq5`

**Compiled:** `KLDA_TickCapture_EA.ex5`

**Purpose:** Captures ticks from MT5 and sends to API

**Features:**
- Monitors 17 symbols simultaneously
- Batches ticks (17 per batch)
- Millisecond timestamp precision
- JSON format
- Error handling and retry

---

## Setup Instructions

### Step 1: Install Python Dependencies

```bash
cd C:\Users\PC\Desktop\KLDAFinTech\KLDA-HFT\api
pip install flask psycopg2
```

### Step 2: Start the API Server

Open Command Prompt and run:

```bash
cd C:\Users\PC\Desktop\KLDAFinTech\KLDA-HFT\api
python tick_receiver.py
```

You should see:

```
============================================================
KLDA-HFT Tick Receiver API
============================================================
Starting background flusher thread...
API Server starting on http://localhost:5000
Endpoints:
  POST /tick        - Receive single tick
  POST /tick/batch  - Receive batch of ticks
  GET  /stats       - View statistics
  GET  /health      - Health check
============================================================
 * Running on http://0.0.0.0:5000
```

**IMPORTANT:** Keep this window open! The API must run continuously.

### Step 3: Enable WebRequest in MT5

1. Open MetaTrader 5
2. Go to: **Tools → Options → Expert Advisors**
3. Enable: **"Allow WebRequest for listed URL"**
4. Add URL: `http://localhost:5000`
5. Click **OK**

### Step 4: Load the Expert Advisor

1. In MT5, press **Ctrl+N** (Navigator window)
2. Expand: **Expert Advisors → Kosta EA**
3. Find: **KLDA_TickCapture_EA**
4. Drag it onto **any chart** (symbol doesn't matter - EA monitors all 17 symbols)
5. In settings dialog:
   - API_URL: `http://localhost:5000/tick/batch`
   - BATCH_SIZE: `17`
   - ENABLE_LOGGING: `true`
6. Click **OK**

### Step 5: Verify Connection

#### Check MT5 Experts Log:

You should see:

```
========================================
KLDA-HFT Tick Capture EA Started
========================================
Monitoring 17 symbols
API: http://localhost:5000/tick/batch
Batch size: 17
IMPORTANT: Add 'http://localhost:5000' to Tools -> Options -> Expert Advisors -> Allow WebRequest
========================================
[OK] Sent 17 ticks | Total: 17
[OK] Sent 17 ticks | Total: 34
```

#### Check API Server Console:

```
[FLUSH] Processed 17 ticks | Total: 17
[FLUSH] Processed 17 ticks | Total: 34
```

#### Check Database:

Open pgAdmin4 and run:

```sql
-- Check CURRENT table (should have 17 rows updated)
SELECT symbol, bid, ask, last_updated
FROM current
ORDER BY symbol;

-- Check HISTORY tables (should have ticks accumulating)
SELECT COUNT(*) FROM tsla_history;
SELECT COUNT(*) FROM nvda_history;

-- View recent ticks
SELECT time, bid, ask, spread, volume
FROM tsla_history
ORDER BY time DESC
LIMIT 10;
```

---

## Monitoring

### View API Statistics

Open browser: http://localhost:5000/stats

Example response:

```json
{
  "ticks_received": 1700,
  "ticks_processed": 1700,
  "buffer_size": 0,
  "errors": 0,
  "last_flush": "2026-01-13T15:30:45.123456"
}
```

### View Database Statistics

```sql
-- Current table status
SELECT
    symbol,
    bid,
    ask,
    spread,
    volume,
    last_updated
FROM current
ORDER BY last_updated DESC;

-- History table sizes
SELECT
    'tsla_history' as table_name,
    COUNT(*) as tick_count,
    MIN(time) as first_tick,
    MAX(time) as last_tick
FROM tsla_history
UNION ALL
SELECT
    'nvda_history',
    COUNT(*),
    MIN(time),
    MAX(time)
FROM nvda_history;
```

---

## Troubleshooting

### Problem: EA shows "WebRequest not allowed"

**Solution:** Add `http://localhost:5000` to allowed URLs in MT5:
- Tools → Options → Expert Advisors → Allow WebRequest

### Problem: API returns 404 or connection refused

**Solution:** Make sure API server is running:

```bash
cd C:\Users\PC\Desktop\KLDAFinTech\KLDA-HFT\api
python tick_receiver.py
```

### Problem: No ticks in database

**Solution:** Check MT5 Experts log for errors. Make sure:
1. EA is attached to a chart
2. "AutoTrading" is enabled (green button in MT5)
3. Market is open (ticks only arrive during market hours)

### Problem: Database connection error

**Solution:** Verify PostgreSQL is running:

```bash
"C:\Program Files\PostgreSQL\16\bin\pg_ctl.exe" status -D "C:\Program Files\PostgreSQL\16\data"
```

If not running:

```bash
"C:\Program Files\PostgreSQL\16\bin\pg_ctl.exe" start -D "C:\Program Files\PostgreSQL\16\data"
```

---

## System Performance

### Expected Tick Rate

- **Market hours:** 100-1,000 ticks/second (17 assets × 5-60 ticks/asset/second)
- **After hours:** 1-10 ticks/second (low volume)
- **Weekend:** 0 ticks/second (markets closed)

### Database Growth

- **CURRENT table:** Always 17 rows (updated, not inserted)
- **HISTORY tables:** ~1 million ticks/day during active trading
- **Storage:** ~100 MB/day (compressed by TimescaleDB)

### Resource Usage

- **API Server:** ~50 MB RAM, <1% CPU
- **PostgreSQL:** ~200 MB RAM, 5-10% CPU
- **MT5 EA:** <1 MB RAM, <0.1% CPU

---

## Production Deployment

### Running API as Windows Service

For 24/7 operation, convert Python script to Windows service using NSSM:

```bash
# Download NSSM from https://nssm.cc/
nssm install KLDA-API "C:\Python313\python.exe" "C:\Users\PC\Desktop\KLDAFinTech\KLDA-HFT\api\tick_receiver.py"
nssm start KLDA-API
```

### Auto-start EA on MT5 Launch

1. In MT5, right-click the chart with EA
2. Template → Save Template → "KLDA_Tick_Capture"
3. File → Open Data Folder → config
4. Edit `terminal.ini`:
   ```
   [Startup]
   Template=KLDA_Tick_Capture
   ```

---

## What's Happening

When you run this system:

1. **MT5 EA captures ticks** every millisecond for 17 assets
2. **Batches 17 ticks** (one per symbol) into JSON
3. **Sends HTTP POST** to Flask API server
4. **API buffers 100 ticks** before writing to database
5. **Database UPDATE** on CURRENT table (17 rows always)
6. **Database INSERT** to HISTORY tables (append forever)

**Result:** Real-time tick stream stored with microsecond precision for pattern detection and HFT strategy execution.

---

## Next Steps

1. ✓ API Server created
2. ✓ MT5 EA created and compiled
3. ✓ Database structure ready
4. ✓ Historical bars imported (575,816 bars)
5. **NOW:** Start capturing live ticks
6. **NEXT:** Build C++ pattern detection engine
7. **NEXT:** Implement HMM regime detection
8. **NEXT:** Execute Renaissance-style HFT strategy

---

## Support

If you encounter issues:

1. Check MT5 Experts log
2. Check API server console
3. Check PostgreSQL logs: `C:\Program Files\PostgreSQL\16\data\log\`
4. Verify network: `curl http://localhost:5000/health`
