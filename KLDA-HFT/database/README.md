# KLDA-HFT DATABASE

**Renaissance Philosophy: 50.75% win rate through 300,000 trades/day**

---

## HOW PRICE DATA FLOWS THROUGH THE SYSTEM

```
MT5 TICK
   ↓
📊 TABLE: ticks (raw price changes)
   ↓ (aggregate every M1, M5, H1, D1)
📊 TABLE: bars (OHLCV candles)
   ↓ (calculate MA, RSI, ATR, HMM)
📊 TABLE: indicators (technical analysis)
   ↓ (detect patterns: mean reversion, HMM regime)
📊 TABLE: signals (buy/sell recommendations)
   ↓ (C++ backend executes trade)
📊 TABLE: trades (executed orders)
   ↓ (update position)
📊 TABLE: portfolio (real-time state)
   ↓ (calculate metrics)
📊 TABLE: performance (win rate, P&L, Sharpe)
```

---

## WHAT YOU CAN TRACK

### 1. **Track Every Price Change**
```sql
-- See last 10 ticks for TSLA
SELECT time, symbol, bid, ask, volume FROM ticks
WHERE symbol = 'TSLA.US-24' ORDER BY time DESC LIMIT 10;
```

### 2. **Track Bar Formation**
```sql
-- See today's D1 bars
SELECT * FROM bars WHERE timeframe = 'D1' AND time >= CURRENT_DATE;
```

### 3. **Track Indicators (MA, RSI, HMM)**
```sql
-- Current MA20, RSI for TSLA
SELECT b.close, i.ma20, i.rsi14, i.hmm_state FROM bars b
JOIN indicators i USING (symbol, time, timeframe)
WHERE symbol = 'TSLA.US-24' AND timeframe = 'D1' ORDER BY time DESC LIMIT 1;
```

### 4. **Track Pattern Signals**
```sql
-- All signals generated today
SELECT * FROM signals WHERE time >= CURRENT_DATE ORDER BY confidence DESC;
```

### 5. **Track Executed Trades**
```sql
-- Open positions right now
SELECT * FROM trades WHERE status = 'OPEN';
```

### 6. **Track Portfolio State**
```sql
-- Real-time portfolio
SELECT * FROM portfolio WHERE position != 0;
```

### 7. **Track Win Rate (Target: 50.75%)**
```sql
-- Today's win rate
SELECT * FROM get_win_rate(CURRENT_DATE);
```

### 8. **Track Performance**
```sql
-- Today's performance
SELECT * FROM performance WHERE period = 'DAILY' AND time >= CURRENT_DATE;
```

See `tracking_queries.sql` for 50+ more tracking queries.

---

## SETUP INSTRUCTIONS

### Step 1: Check PostgreSQL Installation

You have **PostgreSQL 16** installed at: `C:\Program Files\PostgreSQL\16\`

### Step 2: Install TimescaleDB Extension

**Option A: Windows Installer (Recommended)**
1. Download: https://docs.timescale.com/self-hosted/latest/install/installation-windows/
2. Run installer
3. Select PostgreSQL 16
4. Follow wizard

**Option B: Manual (if installer fails)**
```bash
# Will provide manual instructions if needed
```

### Step 3: Create Database

Open pgAdmin4 or command line:

```bash
# Command line method:
cd "C:\Program Files\PostgreSQL\16\bin"
psql -U postgres

# Then in psql:
CREATE DATABASE klda_hft;
\c klda_hft
CREATE EXTENSION timescaledb CASCADE;
```

### Step 4: Run Schema

```bash
# In psql:
\i 'C:/Users/PC/Desktop/KLDAFinTech/KLDA-HFT/database/schema.sql'
```

This creates:
- 7 tables (ticks, bars, indicators, signals, trades, portfolio, performance)
- Hypertables for time-series optimization
- Compression policies (save 50-90% space)
- Continuous aggregates (auto-calculate M5 bars, hourly performance)
- Helper functions (get_win_rate, get_portfolio_summary)

### Step 5: Import Historical Data

We'll create a script to import your 575,816 existing bars from CSV files:
```bash
# To be created: import_historical_data.py
```

### Step 6: Test Tracking

```bash
# In psql:
\i 'C:/Users/PC/Desktop/KLDAFinTech/KLDA-HFT/database/tracking_queries.sql'
```

---

## DATABASE TABLES OVERVIEW

| Table | Purpose | Size | Update Frequency |
|-------|---------|------|------------------|
| **ticks** | Raw tick data from MT5 | ~200GB/year | Every tick (microseconds) |
| **bars** | OHLCV candles (M1-MN) | ~18GB/year | Every bar close |
| **indicators** | MA, RSI, ATR, HMM | ~30GB/year | Every bar close |
| **signals** | Pattern detections | ~36GB/year | When pattern found |
| **trades** | Executed orders | ~55GB/year | On trade open/close |
| **portfolio** | Current positions | <1MB | Every tick |
| **performance** | Win rate, P&L, Sharpe | <1GB/year | Hourly/daily |

**Total: ~340GB/year** (with compression)

---

## TIMESCALEDB FEATURES IN USE

### 1. **Hypertables**
- Automatic time-based partitioning
- 10-100x faster than regular PostgreSQL for time-series
- All time-series tables converted to hypertables

### 2. **Compression**
- Compress data older than 7-30 days
- Saves 50-90% space
- Query speed unchanged

### 3. **Continuous Aggregates**
- Auto-calculate M5 bars from ticks
- Auto-calculate hourly performance from trades
- Materialized views that update automatically

### 4. **Retention Policies**
- Delete ticks older than 1 year (save space)
- Keep bars/trades forever (for backtesting)

---

## NEXT STEPS

1. ✅ PostgreSQL 16 installed
2. ✅ Schema file created
3. ✅ Tracking queries created
4. ⏳ Install TimescaleDB extension
5. ⏳ Create klda_hft database
6. ⏳ Run schema.sql
7. ⏳ Import 575,816 historical bars
8. ⏳ Connect C++ backend to database
9. ⏳ Start live data feed from MT5

---

## FILES IN THIS FOLDER

```
database/
├── README.md                 ← You are here
├── schema.sql                ← Create all tables
├── tracking_queries.sql      ← How to track everything
└── (coming next)
    ├── import_historical_data.py
    ├── test_connection.cpp
    └── setup.bat
```

---

## RENAISSANCE VALIDATION

Your database tracks everything needed to achieve **50.75% win rate**:

✅ **Tick data** - "Tick data collection when providers only offered open/close"
✅ **Multiple timeframes** - "Five-minute intervals for market analysis"
✅ **HMM states** - "Hidden Markov Models observe prices, infer hidden states"
✅ **Transaction costs** - "'The Devil' - difference between theory and execution"
✅ **Win rate tracking** - "50.75% win rate... you can make billions that way"
✅ **Real-time metrics** - "Optimization processes several times per hour"
✅ **Portfolio state** - "4,000 long and 4,000 short positions simultaneously"

---

## SUPPORT

- PostgreSQL docs: https://www.postgresql.org/docs/16/
- TimescaleDB docs: https://docs.timescale.com/
- pgAdmin4 docs: https://www.pgadmin.org/docs/

---

**Built with Renaissance Technologies philosophy in mind.**
