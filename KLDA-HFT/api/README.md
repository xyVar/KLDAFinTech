# API Server - Tick Receiver & Database Writer

**Role:** Receives tick data from Python bridge and writes to PostgreSQL
**Status:** ✅ RUNNING (Task ID: bd8a243)
**Port:** 5000

---

## Purpose

This Flask API server acts as the middleman between the Python bridge (data capture) and the PostgreSQL database (data storage). It receives tick batches via HTTP POST, validates them, and writes to the database.

---

## File

**`tick_receiver.py`** - Main API server
- Flask HTTP server
- Receives POST requests from Python bridge
- Maps MT5 symbols → Database symbols
- Separates buy/sell volume based on MT5 flags
- Buffers ticks (max 100 or 1 second flush)
- Writes to PostgreSQL:
  - UPDATE `current` table
  - INSERT into `*_history` tables

---

## Architecture

```
┌────────────────────────────────────────────────────────┐
│            Python Bridge (HTTP Client)                 │
│  Sends: POST /tick/batch                               │
│  JSON: {ticks: [{symbol, bid, ask, ...}]}             │
└──────────────────────┬─────────────────────────────────┘
                       │
                       │ HTTP POST
                       ↓
┌────────────────────────────────────────────────────────┐
│              API SERVER (tick_receiver.py)             │
│  Port: 5000                                            │
│                                                        │
│  ┌──────────────────────────────────────────────┐     │
│  │ 1. Receive HTTP POST                         │     │
│  │    - Validate JSON structure                 │     │
│  │    - Check required fields                   │     │
│  └──────────────────────────────────────────────┘     │
│                       ↓                                │
│  ┌──────────────────────────────────────────────┐     │
│  │ 2. Symbol Mapping                            │     │
│  │    - MT5: 'TSLA.US' → DB: 'TSLA'           │     │
│  │    - MT5: 'NATGAS' → DB: 'NatGas'          │     │
│  └──────────────────────────────────────────────┘     │
│                       ↓                                │
│  ┌──────────────────────────────────────────────┐     │
│  │ 3. Flag Interpretation & Volume Separation   │     │
│  │    - flags & 8: Trade tick                   │     │
│  │    - flags & 32: BUY → buy_volume           │     │
│  │    - flags & 64: SELL → sell_volume         │     │
│  │    - else: Quote tick → both volumes = 0     │     │
│  └──────────────────────────────────────────────┘     │
│                       ↓                                │
│  ┌──────────────────────────────────────────────┐     │
│  │ 4. Buffer Management                         │     │
│  │    - Add to tick_buffer[]                    │     │
│  │    - If buffer full (100) → flush           │     │
│  │    - Background thread: flush every 1 sec    │     │
│  └──────────────────────────────────────────────┘     │
│                       ↓                                │
│  ┌──────────────────────────────────────────────┐     │
│  │ 5. Database Write                            │     │
│  │    - UPDATE current SET ... WHERE symbol     │     │
│  │    - INSERT INTO tsla_history (...)          │     │
│  │    - Batch insert (execute_batch)            │     │
│  └──────────────────────────────────────────────┘     │
│                                                        │
└──────────────────────┬─────────────────────────────────┘
                       │
                       │ psycopg2 (PostgreSQL driver)
                       ↓
┌────────────────────────────────────────────────────────┐
│            PostgreSQL Database                         │
│  - CURRENT table (17 rows, UPDATED)                   │
│  - HISTORY tables (17 tables, INSERTS)                │
└────────────────────────────────────────────────────────┘
```

---

## Endpoints

### POST /tick
**Description:** Receive single tick
**Request:**
```json
{
  "symbol": "TSLA.US",
  "bid": 448.67,
  "ask": 449.00,
  "spread": 33.0,
  "volume": 0,
  "flags": 6,
  "timestamp": "2026-01-13 17:54:43.205123"
}
```
**Response:**
```json
{
  "status": "success"
}
```

### POST /tick/batch
**Description:** Receive batch of ticks (MAIN ENDPOINT)
**Request:**
```json
{
  "ticks": [
    {
      "symbol": "TSLA.US",
      "bid": 448.67,
      "ask": 449.00,
      "spread": 33.0,
      "volume": 0,
      "flags": 6,
      "timestamp": "2026-01-13 17:54:43.205123"
    },
    {
      "symbol": "NVDA.US",
      "bid": 184.43,
      "ask": 184.46,
      "spread": 3.0,
      "volume": 0,
      "flags": 6,
      "timestamp": "2026-01-13 17:54:43.556000"
    }
  ]
}
```
**Response:**
```json
{
  "status": "success",
  "received": 2
}
```

### GET /stats
**Description:** Get API statistics
**Response:**
```json
{
  "ticks_received": 14715,
  "ticks_processed": 14715,
  "buffer_size": 0,
  "errors": 0,
  "last_flush": "2026-01-13T17:54:39.424515"
}
```

### GET /health
**Description:** Health check (database connectivity)
**Response:**
```json
{
  "status": "healthy",
  "database": "connected"
}
```

---

## Configuration

### Database Connection
```python
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'KLDA-HFT_Database',
    'user': 'postgres',
    'password': 'MyKldaTechnologies2025!'
}
```

### Symbol Mapping (MT5 → Database)
```python
SYMBOL_MAP = {
    'TSLA.US': 'TSLA',
    'NVDA.US': 'NVDA',
    'AAPL.US': 'AAPL',
    'MSFT.US': 'MSFT',
    'ORCL.US': 'ORCL',
    'PLTR.US': 'PLTR',
    'AMD.US': 'AMD',
    'AVGO.US': 'AVGO',
    'META.US': 'META',
    'AMZN.US': 'AMZN',
    'CSCO.US': 'CSCO',
    'GOOG.US': 'GOOG',
    'INTC.US': 'INTC',
    'VIX': 'VIX',
    'NAS100': 'NAS100',
    'NATGAS': 'NatGas',       # Special: Maps to 'NatGas'
    'CRUDEOIL': 'SpotCrude'   # Special: Maps to 'SpotCrude'
}
```

### Buffer Settings
```python
MAX_BUFFER_SIZE = 100    # Flush when buffer reaches 100 ticks
FLUSH_INTERVAL = 1.0     # Flush every 1 second (background thread)
```

---

## Flag Interpretation Logic

### Volume Separation Algorithm
```python
flags = tick.get('flags', 0)

if flags & 8:  # This is a TRADE tick (LAST flag set)
    buy_vol = tick['volume'] if (flags & 32) else 0   # BUY flag
    sell_vol = tick['volume'] if (flags & 64) else 0  # SELL flag
else:  # This is a QUOTE tick (bid/ask update only)
    buy_vol = 0
    sell_vol = 0
```

### Examples
| flags | flags & 8 | flags & 32 | flags & 64 | Type | buy_volume | sell_volume |
|-------|-----------|------------|------------|------|------------|-------------|
| 6     | 0 (False) | -          | -          | QUOTE| 0          | 0           |
| 40    | 8 (True)  | 32 (True)  | 0 (False)  | BUY  | volume     | 0           |
| 72    | 8 (True)  | 0 (False)  | 64 (True)  | SELL | 0          | volume      |

---

## Database Operations

### UPDATE: CURRENT table
**Purpose:** Keep latest tick for each asset (live snapshot)
**SQL:**
```sql
UPDATE current
SET bid = %s,
    ask = %s,
    spread = %s,
    volume = %s,
    buy_volume = %s,
    sell_volume = %s,
    flags = %s,
    last_updated = %s
WHERE symbol = %s;
```
**Frequency:** Every tick (overwrites previous value)

### INSERT: HISTORY tables
**Purpose:** Archive every tick forever (time-series)
**SQL:**
```sql
INSERT INTO tsla_history (time, bid, ask, spread, volume, buy_volume, sell_volume, flags)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (time) DO NOTHING;
```
**Frequency:** Every tick (append-only, no updates)
**Optimization:** Batch insert with `execute_batch()` for performance

---

## Running the Server

### Start Server
```bash
cd KLDA-HFT/api
python tick_receiver.py
```

**Output:**
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
```

### Check if Running
```bash
curl http://localhost:5000/health
```

**Response:**
```json
{
  "status": "healthy",
  "database": "connected"
}
```

### Check Statistics
```bash
curl http://localhost:5000/stats
```

---

## Performance

### Current Statistics (2026-01-13 17:54)
- Ticks received: 14,715
- Ticks processed: 14,715
- Errors: 0
- Buffer size: 0 (flushed)
- Throughput: ~98 ticks/minute

### Expected at Market Open
- Ticks per second: ~1,700 (17 assets × 100 ticks/sec)
- Database writes: ~1,700 INSERTs/sec + 17 UPDATEs/sec
- Batch insert optimization: Groups ticks by symbol

### Buffer Strategy
- **Small batches (< 100 ticks):** Flushed every 1 second
- **Large batches (≥ 100 ticks):** Flushed immediately
- Prevents memory buildup during high-volume periods

---

## Error Handling

### Database Connection Lost
**Behavior:**
- Error logged: `[ERROR] Database flush failed: <reason>`
- Tick buffer NOT cleared (retries on next flush)
- Stats counter incremented: `errors++`

**Recovery:**
- Automatic retry on next flush (1 second later)
- No data loss

### Invalid Symbol
**Behavior:**
- HTTP 400 response: `{"status": "error", "message": "Unknown symbol: <symbol>"}`
- Tick rejected
- Stats counter incremented: `errors++`

**Solution:**
- Check `SYMBOL_MAP` in code
- Verify MT5 symbol name matches

### Missing Fields
**Behavior:**
- HTTP 400 response: `{"status": "error", "message": "Missing required fields"}`
- Tick rejected

**Required Fields:**
- symbol, bid, ask, spread, volume, flags, timestamp

---

## Monitoring

### Real-time Flush Logs
```
[FLUSH] Processed 17 ticks | Total: 14715
[FLUSH] Processed 17 ticks | Total: 14732
[FLUSH] Processed 17 ticks | Total: 14749
```

### Statistics Dashboard
```bash
watch -n 5 curl -s http://localhost:5000/stats | jq
```

---

## Security Considerations

1. **No Authentication:** Currently open (localhost only)
2. **SQL Injection Protection:** Using parameterized queries (`%s`)
3. **Database Credentials:** Hardcoded (should be in config file)
4. **CORS:** Not enabled (not needed for localhost)

---

## Important Notes

1. **This API does NOT perform analysis** - only stores data
2. **Two connections:**
   - INPUT: Receives from Python bridge (HTTP)
   - OUTPUT: Writes to PostgreSQL (SQL)
3. **Stateless:** No session management, no caching
4. **Thread-safe:** Background flusher uses `buffer_lock`
5. **Idempotent:** `ON CONFLICT DO NOTHING` prevents duplicate inserts

---

## Requirements

### Python Libraries
```bash
pip install flask
pip install psycopg2
```

### PostgreSQL
- Must be running on localhost:5432
- Database `KLDA-HFT_Database` must exist
- User `postgres` must have INSERT/UPDATE permissions

---

**Last Updated:** 2026-01-13
