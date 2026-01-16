# Python Bridge - MT5 to API Data Capture

**Role:** "Electricity Provider" - Connects MT5 terminal to API server
**Status:** ✅ RUNNING (Task ID: b796f34)

---

## Purpose

This component captures live tick data from MT5 broker terminal and sends it to the API server for storage. It acts as a bridge between the broker and the database.

---

## Files

### Main Script
**`mt5_tick_capture.py`** - Main data capture script
- Connects to MT5 terminal via MetaTrader5 Python library
- Polls 17 assets every 1 second
- Captures: bid, ask, spread, volume, flags, timestamp
- Sends batch HTTP POST to API server
- Runs continuously in background

**Running:** Currently active (check with `/tasks` command)

### Testing & Utilities
**`test_mt5_connection.py`** - Test MT5 connection
- Verifies MT5 terminal is accessible
- Shows available symbols
- Tests tick retrieval

**`debug_mt5_tick.py`** - Debug tick structure
- Shows raw MT5 tick data
- Explains MT5 flag values
- Useful for understanding tick format

### Configuration Fixes
**`fix_mt5_config.py`** - Fix MT5 WebRequest config
- Directly edits MT5 config file (common.ini)
- Adds WebRequest URL permissions
- Required UTF-16 LE encoding

**`fix_mt5_webrequest.bat`** - Windows batch script
- Alternative method to fix WebRequest
- Opens config file in notepad

---

## How It Works

```
┌──────────────────────────────────────┐
│     MT5 Terminal (Broker Server)    │
│  - Connected to broker               │
│  - Real-time tick stream             │
└────────────┬─────────────────────────┘
             │
             │ MetaTrader5.symbol_info_tick()
             │ Polls every 1 second
             ↓
┌──────────────────────────────────────┐
│   mt5_tick_capture.py (This Script) │
│                                      │
│  1. Initialize MT5 connection        │
│  2. Loop every 1 second:             │
│     - Get ticks for 17 assets        │
│     - Format timestamps (μs)         │
│     - Calculate spread               │
│     - Build JSON payload             │
│  3. HTTP POST to API server          │
└────────────┬─────────────────────────┘
             │
             │ HTTP POST /tick/batch
             │ JSON: {ticks: [...]}
             ↓
┌──────────────────────────────────────┐
│     API Server (tick_receiver.py)    │
│  Receives and stores to PostgreSQL   │
└──────────────────────────────────────┘
```

---

## Configuration

### MT5 Symbols (17 assets)
```python
SYMBOLS = [
    'TSLA.US', 'NVDA.US', 'AAPL.US', 'MSFT.US',
    'ORCL.US', 'PLTR.US', 'AMD.US', 'AVGO.US',
    'META.US', 'AMZN.US', 'CSCO.US', 'GOOG.US',
    'INTC.US', 'VIX', 'NAS100', 'NATGAS', 'CRUDEOIL'
]
```

### API Endpoint
```python
API_URL = 'http://localhost:5000/tick/batch'
```

### Capture Frequency
- **Interval:** 1 second per batch
- **Assets per batch:** 17
- **Ticks per second:** ~17 (one per asset)
- **Ticks per day:** ~1.5 million

---

## Data Format

### Tick JSON Structure
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
    ...
  ]
}
```

### Timestamp Precision
- **Format:** `YYYY-MM-DD HH:MM:SS.ffffff`
- **Precision:** Microseconds (6 decimal places)
- **Timezone:** Local (CET +01:00)

---

## Running the Script

### Start Capture
```bash
cd KLDA-HFT/python-bridge
python mt5_tick_capture.py
```

### Check if Running
```bash
# In Claude Code
/tasks
```

Look for task ID: `b796f34`

### Stop Capture
```bash
# Kill the background task
Ctrl+C (if running in foreground)
# Or kill the task ID in Claude Code
```

---

## Requirements

### Python Libraries
```bash
pip install MetaTrader5
pip install requests
```

### MT5 Terminal
- Must be installed and logged in
- Demo or live account (currently: PepperstoneUK-Demo)
- MT5 must be running (terminal open)

---

## Troubleshooting

### Error: "MT5 initialization failed"
**Solution:**
1. Check MT5 terminal is running
2. Try logging in again in MT5
3. Restart MT5 terminal

### Error: "Symbol not found"
**Solution:**
1. Check symbol name in MT5 Market Watch
2. Right-click Market Watch → Show All
3. Verify spelling (e.g., 'TSLA.US' not 'TSLA')

### Error: "Connection refused to API"
**Solution:**
1. Check API server is running (task bd8a243)
2. Verify API port: `http://localhost:5000`
3. Test: `curl http://localhost:5000/health`

### No ticks captured (volume always 0)
**This is NORMAL!**
- Markets closed/after-hours → Only quote updates (flags=6)
- volume=0 is correct for quotes
- Wait for market open (9:30 AM ET) for trades with volume >0

---

## Statistics

**Current Status (2026-01-13 17:54):**
- Ticks captured: 14,715
- Assets monitored: 17
- Running since: 17:31 (2.5 hours)
- Average: ~98 ticks per asset per hour

**Expected at Market Open:**
- ~100-1,000 quote ticks per second per asset
- ~1-50 trade ticks per second per asset
- ~300,000 ticks per day per asset (during trading hours)

---

## MT5 Tick Flags Reference

| Flags | Meaning | Volume | Description |
|-------|---------|--------|-------------|
| 6     | BID+ASK | 0      | Quote update (most common) |
| 40    | BUY TRADE | >0   | Buyer-initiated trade |
| 72    | SELL TRADE | >0  | Seller-initiated trade |

**Flag Bits:**
- BIT 2 = Bid changed
- BIT 4 = Ask changed
- BIT 8 = Trade occurred (LAST price)
- BIT 32 = BUY trade
- BIT 64 = SELL trade

---

## Important Notes

1. **This script does NOT perform analysis** - only captures data
2. **No database access** - only sends HTTP requests to API
3. **Runs continuously** - never stops unless killed
4. **Lightweight** - ~1% CPU usage, minimal memory
5. **Resilient** - Automatically retries on HTTP errors

---

**Last Updated:** 2026-01-13
