# END-TO-END TICK FLOW
## Complete Journey of One VIX Tick from Broker to Dashboard

**Date:** 2026-01-22
**System:** KLDA-HFT Real-Time Trading Infrastructure

---

## STAGE 1: TICK CAPTURE (Pepperstone Broker → Python Bridge)

**File:** `python-bridge/mt5_tick_capture_ALL_TICKS.py`

### What Happens:
```python
# Line 112: Fetch ALL ticks since last check (100ms polling)
ticks_raw = mt5.copy_ticks_range(symbol, from_time, now, mt5.COPY_TICKS_ALL)

# Example VIX tick captured:
{
    'time': 1737487712,          # Unix timestamp (broker server time)
    'time_msc': 1737487712995,   # Milliseconds
    'bid': 17.73,                # Bid price
    'ask': 17.89,                # Ask price
    'volume': 0,                 # Tick volume
    'flags': 2                   # BID tick (quote update)
}
```

### Data Transformation:
```python
# Lines 125-142: Convert to API format
{
    'symbol': 'VIX',
    'bid': 17.73,
    'ask': 17.89,
    'spread': 16.0,              # (17.89 - 17.73) / 0.01 = 16 points
    'volume': 0,
    'flags': 2,
    'timestamp': '2026-01-21 20:08:32.995000'  # Formatted timestamp
}
```

### Batching:
- Polls broker every **100ms**
- Captures **3-5 ticks per second per asset**
- Batches ticks from all 17 assets
- Sends batch every **2 seconds** via HTTP POST

---

## STAGE 2: API INGESTION (Python Bridge → Flask API)

**File:** `api/tick_receiver.py`

### HTTP Request:
```http
POST http://localhost:5000/tick/batch
Content-Type: application/json

{
    "ticks": [
        {
            "symbol": "VIX",
            "bid": 17.73,
            "ask": 17.89,
            "spread": 16.0,
            "volume": 0,
            "flags": 2,
            "timestamp": "2026-01-21 20:08:32.995000"
        },
        ... (40-60 ticks total in batch)
    ]
}
```

### API Processing:
```python
# Lines 265-285: Add ticks to buffer
tick_buffer.append({
    'symbol': 'VIX',           # Mapped from MT5 'VIX' → 'VIX'
    'bid': 17.73,
    'ask': 17.89,
    'spread': 16.0,
    'volume': 0,
    'flags': 2,
    'timestamp': datetime(2026, 1, 21, 20, 8, 32, 995000)
})

# Lines 240-241: Force flush if buffer reaches 100 ticks
if len(tick_buffer) >= MAX_BUFFER_SIZE:
    threading.Thread(target=flush_ticks_to_db).start()
```

### Buffer Flushing:
- Background thread flushes every **1 second** (line 189)
- Or immediately when buffer reaches **100 ticks**
- Average: 40-60 ticks flushed every 1-2 seconds

---

## STAGE 3: DATABASE WRITE (Flask API → PostgreSQL)

**File:** `api/tick_receiver.py` (lines 73-180)

### Database Tables Touched:

#### Table 1: CURRENT (1 row updated)
```python
# Lines 117-138: UPDATE CURRENT table
UPDATE current
SET bid = 17.73,
    ask = 17.89,
    spread = 16.0,
    volume = 0,
    buy_volume = 0,    # Calculated from flags
    sell_volume = 0,
    flags = 2,
    last_updated = '2026-01-21 20:08:32.995000'
WHERE symbol = 'VIX';
```

**Result:**
```
Table: current
Rows: 17 (one per symbol)
VIX row updated with latest price
```

#### Table 2: vix_history (1 row inserted)
```python
# Lines 145-170: INSERT INTO HISTORY table
INSERT INTO vix_history (time, bid, ask, spread, volume, buy_volume, sell_volume, flags)
VALUES ('2026-01-21 20:08:32.995000', 17.73, 17.89, 16.0, 0, 0, 0, 2)
ON CONFLICT (time) DO NOTHING;  # Prevents duplicate ticks
```

**Result:**
```
Table: vix_history
Type: TimescaleDB hypertable (time-series)
Total rows: 690,038+ ticks (all symbols combined)
New row: VIX tick at 20:08:32.995 archived forever
```

#### Table 3: vix_bars (NOT TOUCHED)
```
Status: EMPTY or STALE
Purpose: Pre-computed OHLCV candles
Problem: No automatic update mechanism!
Solution: Needs continuous aggregates (not deployed yet)
```

### Database Commit:
```python
# Line 172: Commit transaction
conn.commit()
```

**Total latency:** < 10ms (batch write)

---

## STAGE 4: C++ ANALYSIS (PostgreSQL → C++ Backend)

**File:** `cpp-backend/src/main_live.cpp`

### Database Read (every 1 second):
```cpp
// Lines 289-293: Query CURRENT table ONLY
SELECT symbol, bid, ask, spread, volume, buy_volume, sell_volume, last_updated,
       EXTRACT(EPOCH FROM (NOW() - last_updated)) AS seconds_ago
FROM current
ORDER BY symbol;
```

**Result:**
```
17 rows returned (one per symbol)
VIX row:
- symbol: VIX
- bid: 17.73
- ask: 17.89
- spread: 16.0
- last_updated: 2026-01-21 20:08:32.995
- seconds_ago: 10 (depends on when C++ reads it)
```

### Renaissance Metrics Calculation:

#### Metric 1: Mean Reversion (lines 58-94)
```cpp
// Reads from vix_history table
SELECT bid FROM vix_history ORDER BY time DESC LIMIT 50;

// Calculate MA50
double ma50 = sum_of_50_ticks / 50.0;  // = 17.5872
double current_price = (17.73 + 17.89) / 2.0;  // = 17.81
double deviation_pct = ((17.81 - 17.5872) / 17.5872) * 100.0;  // = 1.27%

// Result
{
    "value": 1.27,
    "ma50": 17.5872,
    "signal": false,   // Only true if deviation < -1%
    "status": "SELL_ZONE"  // Price > MA50
}
```

#### Metric 2: Order Flow (lines 97-135)
```cpp
// Reads from vix_history table
SELECT buy_volume, sell_volume FROM vix_history ORDER BY time DESC LIMIT 50;

// Sum volumes
long long total_buy = 0;
long long total_sell = 0;
long long net_flow = total_buy - total_sell;  // = 0 (VIX has no volume)

// Result
{
    "value": 0,
    "buy_volume": 0,
    "sell_volume": 0,
    "signal": false,  // Only true if net_flow > 2000
    "status": "NEUTRAL"
}
```

#### Metric 3: Spread Volatility (lines 138-174)
```cpp
// Reads from vix_history table
SELECT spread FROM vix_history ORDER BY time DESC LIMIT 100;

// Calculate average spread
double avg_spread = sum_of_100_spreads / 100.0;  // = 16.22
double current_spread = 16.0;
double spread_vol_pct = ((16.0 - 16.22) / 16.22) * 100.0;  // = -1.36%

// Result
{
    "value": -1.36,
    "avg_spread": 16.22,
    "signal": false,  // Only true if spread_vol_pct > 20%
    "status": "NORMAL"
}
```

#### Metric 4: HMM Regime (lines 177-226)
```cpp
// Reads from vix_history table
SELECT bid FROM vix_history ORDER BY time DESC LIMIT 200;

// Compare recent 100 vs older 100 ticks
double recent_avg = sum_of_recent_100 / 100.0;  // = 17.67
double older_avg = sum_of_older_100 / 100.0;    // = 17.53
double trend_pct = ((17.67 - 17.53) / 17.53) * 100.0;  // = 0.78%

// Determine regime
string regime = (trend_pct > 0.5) ? "BULLISH" : "NEUTRAL";  // = "BULLISH"

// Result
{
    "value": "BULLISH",
    "trend_pct": 0.78,
    "signal": true,   // BULLISH gives BUY signal
    "status": "BULLISH"
}
```

#### Metric 5: Transaction Cost (lines 229-248)
```cpp
// No database read - calculated from current tick
double spread_cost = 16.0 / 2.0;  // = 8.0 EUR
double daily_swap = 0.096;        // = 0.096 EUR
double total_cost = 8.0 + 0.096;  // = 8.096 EUR

// Result
{
    "value": 8.096,
    "spread_cost": 8.0,
    "swap_cost": 0.096,
    "signal": true,   // Cost < 10 EUR is acceptable
    "status": "ACCEPTABLE"
}
```

#### Metric 6: Kelly Position Size (lines 251-283)
```cpp
// No database read - fixed calculation
// Renaissance Medallion: 50.75% win rate, 0.75% edge
double win_rate = 0.5075;
double avg_win = 15.0;
double avg_loss = 14.25;
double kelly_fraction = (0.5075 * (15.0/14.25) - 0.4925) / (15.0/14.25);
double kelly_pct = (kelly_fraction / 2.0) * 100.0;  // Half Kelly for safety
double position_size = 1000.0 * 0.02;  // Capped at 2%

// Result
{
    "value": 19.81,     // EUR 19.81 position size
    "kelly_pct": 1.98,  // 1.98% of account
    "signal": true,     // Safe (< 2%)
    "status": "SAFE"
}
```

### Overall Signal (lines 331-339):
```cpp
// ALL 6 conditions must be TRUE for ENTER_LONG
bool all_conditions =
    mean_reversion.signal &&      // false (price > MA50)
    order_flow.signal &&          // false (no volume)
    spread_volatility.signal &&   // false (spread normal)
    hmm_regime.signal &&          // TRUE (BULLISH)
    transaction_cost.signal &&    // TRUE (cost acceptable)
    kelly_size.signal;            // TRUE (safe size)

// Result: "WAIT" (not all conditions met)
tick["renaissance"]["overall_signal"] = "WAIT";
```

---

## STAGE 5: JSON OUTPUT (C++ Backend → File System)

**File:** `cpp-backend/src/main_live.cpp` (lines 384-397)

### JSON Structure:
```cpp
// Line 395: Write to Docker volume mount
std::ofstream outfile("/app/output/live_ticks.json");
outfile << output.dump(2);  // Pretty print
```

**File Location:** `C:\Users\PC\Desktop\KLDAFinTech\KLDA-HFT\cpp-backend\live_ticks.json`

**Content:**
```json
{
  "timestamp": 1769100361,
  "update_count": 242967,
  "total_assets": 17,
  "ticks": [
    {
      "symbol": "VIX",
      "bid": 17.73,
      "ask": 17.89,
      "spread": 16.0,
      "volume": 0,
      "buy_volume": 0,
      "sell_volume": 0,
      "last_updated": "2026-01-21 20:08:32.995+01",
      "seconds_ago": 77863.425208,
      "renaissance": {
        "mean_reversion": {
          "value": 1.27,
          "ma50": 17.5872,
          "signal": false,
          "status": "SELL_ZONE"
        },
        "order_flow": {
          "value": 0,
          "buy_volume": 0,
          "sell_volume": 0,
          "signal": false,
          "status": "NEUTRAL"
        },
        "spread_volatility": {
          "value": -1.36,
          "avg_spread": 16.22,
          "signal": false,
          "status": "NORMAL"
        },
        "hmm_regime": {
          "value": "BULLISH",
          "trend_pct": 0.78,
          "signal": true,
          "status": "BULLISH"
        },
        "transaction_cost": {
          "value": 8.096,
          "spread_cost": 8.0,
          "swap_cost": 0.096,
          "signal": true,
          "status": "ACCEPTABLE"
        },
        "kelly_size": {
          "value": 19.81,
          "kelly_pct": 1.98,
          "signal": true,
          "status": "SAFE"
        },
        "overall_signal": "WAIT"
      }
    },
    ... (16 more assets)
  ]
}
```

**Update Frequency:** Every 1 second (line 405)

---

## STAGE 6: DASHBOARD DISPLAY (JSON File → Browser)

**File:** `cpp-backend/bloomberg_terminal.html`

### JavaScript Fetch (lines 408-420):
```javascript
// Line 410: Fetch JSON with cache-busting timestamp
const response = await fetch('live_ticks.json?' + Date.now());
const data = await response.json();
```

### Data Rendering (lines 364-405):
```javascript
// Line 368: Loop through all ticks
data.ticks.forEach(tick => {
    const symbol = tick.symbol;          // "VIX"
    const bid = tick.bid.toFixed(2);     // "17.73"
    const ask = tick.ask.toFixed(2);     // "17.89"
    const spread = tick.spread.toFixed(2);  // "16.00"
    const age = formatAge(tick.seconds_ago);  // "21.6h"
    const status = (tick.seconds_ago < 5) ? "LIVE" : "STALE";

    // Render table row
    tbody.innerHTML += `
        <tr class="stale">
            <td><span class="symbol-name">VIX</span></td>
            <td class="price-bid">17.73</td>
            <td class="volume-value">0</td>
            <td class="price-ask">17.89</td>
            <td class="volume-value">0</td>
            <td class="spread-value">16.00</td>
            <td class="volume-value">0</td>
            <td class="ticks-per-sec">0</td>
            <td class="timestamp">21/01/2026 20:08:32</td>
            <td>21.6h</td>
            <td class="status-stale">STALE</td>
        </tr>
    `;
});
```

### Refresh Rate:
```javascript
// Lines 426-427: Fetch every 1 second
fetchLiveData();
setInterval(fetchLiveData, 1000);
```

---

## COMPLETE TIMELINE

**VIX Tick Journey (Total: ~1.2 seconds)**

```
00:00.000 - Broker tick arrives at Pepperstone server
00:00.100 - Python bridge polls MT5, captures tick
00:00.110 - Tick added to batch buffer
00:02.000 - Batch sent to Flask API via HTTP POST
00:02.010 - Flask API receives batch
00:02.020 - Flask updates CURRENT table (UPDATE)
00:02.025 - Flask inserts into vix_history (INSERT)
00:02.030 - PostgreSQL commits transaction
00:03.000 - C++ backend queries CURRENT table (SELECT)
00:03.100 - C++ queries vix_history for MA50 (SELECT)
00:03.150 - C++ queries vix_history for order flow (SELECT)
00:03.200 - C++ queries vix_history for spread volatility (SELECT)
00:03.300 - C++ queries vix_history for HMM regime (SELECT)
00:03.350 - C++ calculates transaction cost (no query)
00:03.360 - C++ calculates Kelly size (no query)
00:03.370 - C++ writes live_ticks.json
00:03.400 - Browser fetches live_ticks.json
00:03.410 - Dashboard renders tick in table
```

**Total End-to-End Latency:** ~3.4 seconds (from broker to screen)
**Bottleneck:** 2-second batch interval in Python bridge

---

## DATABASE TABLES USAGE MATRIX

| Table | Type | Rows | Used By | Purpose | Update Frequency |
|-------|------|------|---------|---------|------------------|
| **current** | PostgreSQL table | 17 | Flask (WRITE), C++ (READ) | Latest tick per symbol | Every 2 seconds |
| **vix_history** | TimescaleDB hypertable | ~40,000 | Flask (WRITE), C++ (READ) | All VIX ticks archive | Every 2 seconds |
| **tsla_history** | TimescaleDB hypertable | ~50,000 | Flask (WRITE), C++ (READ) | All TSLA ticks archive | Every 2 seconds |
| **nvda_history** | TimescaleDB hypertable | ~50,000 | Flask (WRITE), C++ (READ) | All NVDA ticks archive | Every 2 seconds |
| ... (14 more _history tables) | | | | | |
| **vix_bars** | PostgreSQL table | EMPTY | NOBODY | OHLCV candles (not working) | NEVER |
| **tsla_bars** | PostgreSQL table | EMPTY | NOBODY | OHLCV candles (not working) | NEVER |
| ... (15 more _bars tables) | | | | | |

**CRITICAL FINDING:** BARS tables are **NOT USED** by any component!

---

## WHAT'S MISSING

### 1. Automatic BARS Population
**Problem:** C++ does NOT write to BARS tables
**Solution:** Deploy continuous aggregates (setup_bars_compression.sql)

### 2. Trading Engine Connection
**Problem:** `renaissance_trading_engine.py` does NOT read `live_ticks.json`
**Solution:** Connect trading engine to JSON output

### 3. Manual Override Dashboard
**Problem:** Bloomberg terminal is READ-ONLY
**Solution:** Add buttons to close positions, pause trading

---

## SUMMARY

**What Works:**
- ✅ Tick capture from broker
- ✅ HTTP API ingestion
- ✅ Database storage (CURRENT + HISTORY)
- ✅ C++ Renaissance calculations
- ✅ JSON output
- ✅ Dashboard display

**What Doesn't Work:**
- ❌ BARS tables (empty, never updated)
- ❌ Trading engine (not connected to C++ output)
- ❌ Dashboard controls (no buttons, read-only)

**Bottlenecks:**
- 2-second batching delay (Python bridge)
- Multiple SELECT queries per tick (C++ could cache)
- No database indexes on time columns (slow queries)

**Optimization Potential:**
- Reduce batch interval to 500ms → 1.5s faster
- Add indexes on vix_history(time) → 50% faster queries
- Cache last 200 ticks in C++ memory → No database reads

---

**END OF DOCUMENT**
