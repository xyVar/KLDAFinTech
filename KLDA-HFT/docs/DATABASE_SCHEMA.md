# KLDA-HFT Database Schema Documentation

**Database:** `KLDA-HFT_Database`
**Engine:** PostgreSQL 16 + TimescaleDB 2.24.0
**Total Tables:** 35 tables (1 CURRENT + 17 HISTORY + 17 BARS)

---

## Table Structure Overview

```
KLDA-HFT_Database
│
├── current                 (1 table)  → Live snapshot of latest tick per asset
│
├── *_history              (17 tables) → Append-only tick archives
│   ├── tsla_history
│   ├── nvda_history
│   ├── aapl_history
│   ├── msft_history
│   ├── orcl_history
│   ├── pltr_history
│   ├── amd_history
│   ├── avgo_history
│   ├── meta_history
│   ├── amzn_history
│   ├── csco_history
│   ├── goog_history
│   ├── intc_history
│   ├── vix_history
│   ├── nas100_history
│   ├── natgas_history
│   └── spotcrude_history
│
└── *_bars                 (17 tables) → Historical OHLCV data (16+ years)
    ├── tsla_bars
    ├── nvda_bars
    ├── aapl_bars
    ├── msft_bars
    ├── orcl_bars
    ├── pltr_bars
    ├── amd_bars
    ├── avgo_bars
    ├── meta_bars
    ├── amzn_bars
    ├── csco_bars
    ├── goog_bars
    ├── intc_bars
    ├── vix_bars
    ├── nas100_bars
    ├── natgas_bars
    └── spotcrude_bars
```

---

## Table 1: CURRENT (Live Data Snapshot)

**Purpose:** Stores the latest tick for each asset (17 rows total, continuously updated)

**Schema:**
```sql
CREATE TABLE current (
    symbol_id       SERIAL PRIMARY KEY,
    symbol          VARCHAR(20) NOT NULL UNIQUE,
    mt5_symbol      VARCHAR(50) NOT NULL,
    bid             DECIMAL(18,8) NOT NULL,
    ask             DECIMAL(18,8) NOT NULL,
    spread          DECIMAL(10,5) DEFAULT 0,
    last_updated    TIMESTAMPTZ(6) NOT NULL,
    volume          BIGINT DEFAULT 0,
    buy_volume      BIGINT DEFAULT 0,
    sell_volume     BIGINT DEFAULT 0,
    flags           INTEGER DEFAULT 0
);
```

**Columns:**
| Column        | Type              | Description                                    |
|---------------|-------------------|------------------------------------------------|
| symbol_id     | SERIAL            | Auto-increment primary key                     |
| symbol        | VARCHAR(20)       | Database symbol (e.g., 'TSLA', 'NVDA')        |
| mt5_symbol    | VARCHAR(50)       | MT5 broker symbol (e.g., 'TSLA.US', 'NVDA.US')|
| bid           | DECIMAL(18,8)     | Current bid price                              |
| ask           | DECIMAL(18,8)     | Current ask price                              |
| spread        | DECIMAL(10,5)     | Spread in points (ask - bid) × 10^5           |
| last_updated  | TIMESTAMPTZ(6)    | Timestamp with microsecond precision           |
| volume        | BIGINT            | Last tick volume (0 for quotes)                |
| buy_volume    | BIGINT            | Buy-side volume (only for trades)              |
| sell_volume   | BIGINT            | Sell-side volume (only for trades)             |
| flags         | INTEGER           | MT5 tick flags (see Flag Reference below)      |

**Data Behavior:**
- **17 rows total** (one per asset)
- **Updated every ~1 second** by Python bridge
- SQL operation: `UPDATE current SET ... WHERE symbol = 'TSLA'`

**Current Assets (17 total):**
```
1.  TSLA       (Tesla)
2.  NVDA       (Nvidia)
3.  AAPL       (Apple)
4.  MSFT       (Microsoft)
5.  ORCL       (Oracle)
6.  PLTR       (Palantir)
7.  AMD        (AMD)
8.  AVGO       (Broadcom)
9.  META       (Meta)
10. AMZN       (Amazon)
11. CSCO       (Cisco)
12. GOOG       (Google)
13. INTC       (Intel)
14. VIX        (Volatility Index)
15. NAS100     (NASDAQ-100)
16. NATGAS     (Natural Gas)
17. SPOTCRUDE  (Crude Oil)
```

---

## Tables 2-18: *_history (Tick Archives)

**Purpose:** Append-only storage of every tick received from broker (time-series hypertables)

**Schema Template:**
```sql
CREATE TABLE tsla_history (
    time            TIMESTAMPTZ(6) NOT NULL,
    bid             DECIMAL(18,8) NOT NULL,
    ask             DECIMAL(18,8) NOT NULL,
    spread          DECIMAL(10,5) DEFAULT 0,
    volume          BIGINT DEFAULT 0,
    buy_volume      BIGINT DEFAULT 0,
    sell_volume     BIGINT DEFAULT 0,
    flags           INTEGER DEFAULT 0,
    PRIMARY KEY (time)
);

-- Convert to TimescaleDB hypertable
SELECT create_hypertable('tsla_history', 'time');
```

**Columns:**
| Column        | Type              | Description                                    |
|---------------|-------------------|------------------------------------------------|
| time          | TIMESTAMPTZ(6)    | Tick timestamp (primary key)                   |
| bid           | DECIMAL(18,8)     | Bid price at this time                         |
| ask           | DECIMAL(18,8)     | Ask price at this time                         |
| spread        | DECIMAL(10,5)     | Spread in points                               |
| volume        | BIGINT            | Tick volume (0 for quotes, >0 for trades)      |
| buy_volume    | BIGINT            | Buy-side volume (only for BUY trades)          |
| sell_volume   | BIGINT            | Sell-side volume (only for SELL trades)        |
| flags         | INTEGER           | MT5 tick flags                                 |

**Data Behavior:**
- **Append-only** (INSERT, never UPDATE)
- SQL operation: `INSERT INTO tsla_history (...) VALUES (...) ON CONFLICT (time) DO NOTHING`
- TimescaleDB automatically partitions by time (chunks)
- Current size: ~466 ticks per asset (growing continuously)

**All History Tables:**
```
tsla_history, nvda_history, aapl_history, msft_history, orcl_history,
pltr_history, amd_history, avgo_history, meta_history, amzn_history,
csco_history, goog_history, intc_history, vix_history, nas100_history,
natgas_history, spotcrude_history
```

---

## Tables 19-35: *_bars (Historical OHLCV Data)

**Purpose:** Store historical bar data (Open, High, Low, Close, Volume) for backtesting

**Schema Template:**
```sql
CREATE TABLE tsla_bars (
    time            TIMESTAMPTZ(6) NOT NULL,
    timeframe       VARCHAR(5) NOT NULL,
    open            DECIMAL(18,8) NOT NULL,
    high            DECIMAL(18,8) NOT NULL,
    low             DECIMAL(18,8) NOT NULL,
    close           DECIMAL(18,8) NOT NULL,
    volume          BIGINT DEFAULT 0,
    spread          INTEGER DEFAULT 0,
    PRIMARY KEY (time, timeframe)
);

-- Convert to TimescaleDB hypertable
SELECT create_hypertable('tsla_bars', 'time');
```

**Columns:**
| Column        | Type              | Description                                    |
|---------------|-------------------|------------------------------------------------|
| time          | TIMESTAMPTZ(6)    | Bar opening time (part of primary key)         |
| timeframe     | VARCHAR(5)        | Timeframe (M1, M5, M15, M30, H1, H4, D1, W1, MN1) |
| open          | DECIMAL(18,8)     | Opening price                                  |
| high          | DECIMAL(18,8)     | Highest price in period                        |
| low           | DECIMAL(18,8)     | Lowest price in period                         |
| close         | DECIMAL(18,8)     | Closing price                                  |
| volume        | BIGINT            | Total volume in period                         |
| spread        | INTEGER           | Average spread in period                       |

**Timeframes Available:**
- **M1:** 1 minute
- **M5:** 5 minutes
- **M15:** 15 minutes
- **M30:** 30 minutes
- **H1:** 1 hour
- **H4:** 4 hours
- **D1:** 1 day
- **W1:** 1 week
- **MN1:** 1 month

**Data Coverage:**
| Asset | Date Range           | Years | Total Bars |
|-------|----------------------|-------|------------|
| TSLA  | 2010-06-01 to 2026   | 16    | 34,889     |
| NVDA  | 2005-01-01 to 2026   | 21    | 36,350     |
| AAPL  | 2006-07-01 to 2026   | 20    | 36,063     |
| MSFT  | 2019-08-01 to 2026   | 7     | 32,036     |
| (etc) | ...                  | ...   | ...        |
| **TOTAL** |                  |       | **170,544**|

**Data Behavior:**
- **Static data** (imported from CSV files)
- No automatic updates (historical only)
- Used for backtesting algorithms

---

## MT5 Tick Flags Reference

**Flag Values:**
```
TICK_FLAG_BID    = 2   (Bid price changed)
TICK_FLAG_ASK    = 4   (Ask price changed)
TICK_FLAG_LAST   = 8   (Last trade price)
TICK_FLAG_VOLUME = 16  (Volume available)
TICK_FLAG_BUY    = 32  (Buyer initiated trade)
TICK_FLAG_SELL   = 64  (Seller initiated trade)
```

**Common Flag Combinations:**

| Flags | Binary      | Meaning                                          | Volume | buy_volume | sell_volume |
|-------|-------------|--------------------------------------------------|--------|------------|-------------|
| 2     | 0000010     | Bid updated only                                 | 0      | 0          | 0           |
| 4     | 0000100     | Ask updated only                                 | 0      | 0          | 0           |
| **6** | **0000110** | **Bid + Ask updated (QUOTE tick)**              | **0**  | **0**      | **0**       |
| 8     | 0001000     | Trade occurred (last price)                      | >0     | 0          | 0           |
| 40    | 0101000     | BUY trade (flags 8+32)                           | >0     | >0         | 0           |
| 72    | 1001000     | SELL trade (flags 8+64)                          | >0     | 0          | >0          |
| 30    | 0011110     | All prices updated (2+4+8+16)                    | >0     | varies     | varies      |

**How Python Bridge Separates Volume:**
```python
flags = tick.get('flags', 0)

if flags & 8:  # This is a TRADE tick
    buy_vol = tick['volume'] if (flags & 32) else 0   # BUY flag
    sell_vol = tick['volume'] if (flags & 64) else 0  # SELL flag
else:  # This is a QUOTE tick (bid/ask update only)
    buy_vol = 0
    sell_vol = 0
```

---

## Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   MT5 Terminal (Broker)                     │
│                17 assets × tick stream                      │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ MetaTrader5 Python API
                         ↓
┌─────────────────────────────────────────────────────────────┐
│          Python Bridge (mt5_tick_capture.py)                │
│  - Polls MT5 every 1 second                                 │
│  - Captures tick data with microsecond timestamps           │
│  - Sends batch HTTP POST to API                             │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ HTTP POST /tick/batch
                         ↓
┌─────────────────────────────────────────────────────────────┐
│             Flask API (tick_receiver.py)                    │
│  - Receives ticks via HTTP                                  │
│  - Maps MT5 symbols → Database symbols                      │
│  - Separates buy/sell volume based on flags                 │
│  - Buffers ticks (max 100 or 1 second)                      │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ psycopg2 (PostgreSQL driver)
                         ↓
┌─────────────────────────────────────────────────────────────┐
│              PostgreSQL + TimescaleDB                       │
│                                                             │
│  UPDATE current SET ... WHERE symbol = ?                    │
│  INSERT INTO tsla_history (...) VALUES (...)                │
│                                                             │
│  35 tables total:                                           │
│  - 1 CURRENT (17 rows, updated)                            │
│  - 17 HISTORY (append-only inserts)                        │
│  - 17 BARS (static, for backtesting)                       │
└─────────────────────────────────────────────────────────────┘
                         │
                         │ libpqxx (C++ client) [FUTURE]
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                C++ Backend Engine (FUTURE)                  │
│  - Reads CURRENT for live data                             │
│  - Reads HISTORY for tick analysis                         │
│  - Reads BARS for backtesting                              │
│  - Exposes REST API for frontend                           │
└─────────────────────────────────────────────────────────────┘
```

---

## SQL Query Examples for C++ Backend

### 1. Get Latest Tick for All Assets
```sql
SELECT symbol, bid, ask, spread, volume, buy_volume, sell_volume, flags, last_updated
FROM current
ORDER BY symbol;
```

### 2. Get Recent Ticks for One Asset (Last 5 Minutes)
```sql
SELECT time, bid, ask, spread, volume, buy_volume, sell_volume, flags
FROM tsla_history
WHERE time >= NOW() - INTERVAL '5 minutes'
ORDER BY time DESC;
```

### 3. Order Flow Imbalance (Last 15 Minutes)
```sql
SELECT
    SUM(buy_volume) - SUM(sell_volume) as flow_imbalance,
    SUM(CASE WHEN flags & 32 > 0 THEN 1 ELSE 0 END) as buy_trades,
    SUM(CASE WHEN flags & 64 > 0 THEN 1 ELSE 0 END) as sell_trades,
    COUNT(*) as total_ticks
FROM tsla_history
WHERE time >= NOW() - INTERVAL '15 minutes'
  AND flags & 8 > 0;  -- Only trades, not quotes
```

### 4. Spread Analysis (Last 1 Hour)
```sql
SELECT
    AVG(spread) as avg_spread,
    MIN(spread) as min_spread,
    MAX(spread) as max_spread,
    STDDEV(spread) as spread_volatility
FROM tsla_history
WHERE time >= NOW() - INTERVAL '1 hour'
  AND flags = 6;  -- Only quote ticks
```

### 5. Quote-to-Trade Ratio
```sql
SELECT
    COUNT(CASE WHEN flags = 6 THEN 1 END) as quotes,
    COUNT(CASE WHEN flags & 8 > 0 THEN 1 END) as trades,
    COUNT(CASE WHEN flags = 6 THEN 1 END)::float /
        NULLIF(COUNT(CASE WHEN flags & 8 > 0 THEN 1 END), 0) as quote_trade_ratio
FROM tsla_history
WHERE time >= NOW() - INTERVAL '15 minutes';
```

### 6. Get Historical Bars (Backtesting)
```sql
SELECT time, timeframe, open, high, low, close, volume
FROM tsla_bars
WHERE timeframe = 'D1'
  AND time >= '2020-01-01'
ORDER BY time ASC;
```

### 7. Multi-Asset Query (Live Data)
```sql
SELECT symbol, bid, ask, spread,
       (ask - bid) as spread_dollars,
       last_updated
FROM current
WHERE symbol IN ('TSLA', 'NVDA', 'AAPL', 'MSFT')
ORDER BY last_updated DESC;
```

---

## Python Bridge Configuration

**File:** `KLDA-HFT/mt5_tick_capture.py`

**Symbol Mapping (MT5 → Database):**
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
    'NATGAS': 'NatGas',      # Note: Maps to 'NatGas'
    'CRUDEOIL': 'SpotCrude'  # Note: Maps to 'SpotCrude'
}
```

**Capture Frequency:** 1 second per batch (17 assets)

---

## Flask API Configuration

**File:** `KLDA-HFT/api/tick_receiver.py`

**Endpoints:**
- `POST /tick` - Receive single tick
- `POST /tick/batch` - Receive batch of ticks
- `GET /stats` - Get API statistics
- `GET /health` - Health check

**Buffer Settings:**
- Max buffer size: 100 ticks
- Flush interval: 1.0 second

---

## Database Connection Details

**Connection String:**
```
host: localhost
port: 5432
database: KLDA-HFT_Database
user: postgres
password: MyKldaTechnologies2025!
```

**For C++ (libpqxx):**
```cpp
pqxx::connection conn(
    "host=localhost port=5432 "
    "dbname=KLDA-HFT_Database "
    "user=postgres "
    "password=MyKldaTechnologies2025!"
);
```

---

## Database Statistics

**Current Status (as of 2026-01-13 17:54):**
- Total tables: 35
- CURRENT table: 17 rows (one per asset)
- HISTORY tables: ~466 ticks per asset (growing)
- BARS tables: 170,544 historical bars
- Database size: 642 MB
- Tick capture rate: ~17 ticks/second (17 assets × 1 batch/second)

**Expected Growth:**
- Ticks per day: ~1.5 million (17 assets × 86,400 seconds)
- Ticks per month: ~45 million
- Ticks per year: ~540 million

**TimescaleDB Optimization:**
- Auto-partitioning by time chunks
- Efficient time-based queries
- Automatic data retention policies (can be configured)

---

## Notes for C++ Backend Development

1. **Read-Only Access:** C++ backend should only READ from database
2. **Write Operations:** Only Python bridge writes to database (separation of concerns)
3. **Connection Pooling:** Use libpqxx connection pool for efficiency
4. **Query Optimization:** Always use indexes (time column) for range queries
5. **Timestamp Handling:** All timestamps are UTC with microsecond precision
6. **Flags Interpretation:** Use bitwise AND (&) to check flags (see examples above)
7. **NULL Handling:** volume, buy_volume, sell_volume default to 0 (never NULL)

---

## End of Schema Documentation

**Last Updated:** 2026-01-13
**Version:** 1.0
**Maintained By:** KLDA FinTech
