# KLDA-HFT Morning Startup Guide

**Scenario:** You arrive at the office and want to check ticks and prices.

---

## 🔍 **STEP 1: CHECK IF DATA IS ALREADY FLOWING**

Before starting anything, check if systems are already running from yesterday:

### Check PostgreSQL Database:
```bash
"C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -d KLDA-HFT_Database -c "SELECT symbol, bid, ask, last_updated, NOW() - last_updated AS ago FROM current ORDER BY symbol;"
```

**What you'll see:**
- If `ago` is < 5 seconds → Data is LIVE, systems running ✅
- If `ago` is hours → Systems stopped, need to start ❌

---

## 🚀 **STEP 2: START THE DATA PIPELINE** (if stopped)

**You need 2 things running to get live data:**

### 2A. Start Flask API (receives ticks)
```bash
cd C:\Users\PC\Desktop\KLDAFinTech\KLDA-HFT\api
python tick_receiver.py
```

**Leave this window open! You'll see:**
```
* Running on http://127.0.0.1:5000
[FLUSH] Processed 15 ticks | Total: 850000
[FLUSH] Processed 15 ticks | Total: 850015
```

### 2B. Start Python Bridge (captures ticks from MT5)

**Open NEW command window:**
```bash
cd C:\Users\PC\Desktop\KLDAFinTech\KLDA-HFT\python-bridge
python mt5_tick_capture_ALL_TICKS.py
```

**You'll see:**
```
[OK] Connected to MT5
[OK] Subscribed to 15 symbols
[OK] Sent batch #10 | 45 ticks | Total: 450
```

**Now ticks are flowing:** MT5 → Python → API → PostgreSQL ✅

---

## 📊 **STEP 3: VIEW LIVE TICKS** (3 options)

### **Option A: Direct Database Query (Fastest)**

**See live prices right now:**
```bash
"C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -d KLDA-HFT_Database -c "SELECT symbol, bid, ask, spread, last_updated FROM current ORDER BY symbol;"
```

**Repeat to see updates:**
```bash
# Run again after 1 second - prices will change
"C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -d KLDA-HFT_Database -c "SELECT symbol, bid, ask, spread, last_updated FROM current ORDER BY symbol;"
```

---

### **Option B: pgAdmin (GUI)**

1. Open **pgAdmin 4**
2. Connect to `KLDA-HFT_Database`
3. Open Query Tool
4. Run:
```sql
SELECT symbol, bid, ask, spread, volume, last_updated
FROM current
ORDER BY symbol;
```
5. Click **Execute/Refresh** button (F5) to see updates

---

### **Option C: Live Ticker Dashboard (Bloomberg-style)**

**Start C++ backend + web server:**

**Terminal 1 - Start Docker C++ backend:**
```bash
cd C:\Users\PC\Desktop\KLDAFinTech\KLDA-HFT\cpp-backend
docker-compose up
```

**Terminal 2 - Start web server:**
```bash
cd C:\Users\PC\Desktop\KLDAFinTech\KLDA-HFT\cpp-backend
python -m http.server 9000
```

**Open browser:**
```
http://localhost:9000/live_ticker.html
```

**You'll see:** 17 asset cards with bid/ask/spread updating every second

---

## 🛑 **STEP 4: SHUTDOWN** (end of day)

### Stop Python Bridge:
- Go to terminal running `mt5_tick_capture_ALL_TICKS.py`
- Press **Ctrl+C**

### Stop Flask API:
- Go to terminal running `tick_receiver.py`
- Press **Ctrl+C**

### Stop Docker (if running):
```bash
cd C:\Users\PC\Desktop\KLDAFinTech\KLDA-HFT\cpp-backend
docker-compose down
```

### Stop web server (if running):
- Go to terminal running `http.server`
- Press **Ctrl+C**

---

## 📋 **QUICK REFERENCE CARD**

```
┌─────────────────────────────────────────────────────┐
│ KLDA-HFT QUICK START                                │
├─────────────────────────────────────────────────────┤
│                                                     │
│ 1. CHECK DATA:                                      │
│    psql → SELECT * FROM current;                    │
│                                                     │
│ 2. START DATA FLOW:                                 │
│    Terminal 1: python tick_receiver.py              │
│    Terminal 2: python mt5_tick_capture_ALL_TICKS.py │
│                                                     │
│ 3. VIEW TICKS:                                      │
│    • pgAdmin (refresh query)                        │
│    • OR: docker-compose up + browser dashboard      │
│                                                     │
│ 4. SHUTDOWN:                                        │
│    Ctrl+C on all terminals                          │
│    docker-compose down                              │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## 🔧 **TROUBLESHOOTING**

### "No ticks coming in"
**Check:**
1. Is MT5 terminal open and logged in?
2. Is Python bridge showing errors?
3. Is Flask API receiving requests?

**Fix:**
- Restart Python bridge (Ctrl+C, then run again)

### "Old prices in database"
**Cause:** Market closed (stocks trade 09:30-16:00 EST)

**Check:** NAS100, VIX should update 24/7

### "Docker won't start"
**Check:**
```bash
docker ps
```
If shows `klda-hft-cpp-backend`, it's running.

---

## 📁 **FILE LOCATIONS**

```
C:\Users\PC\Desktop\KLDAFinTech\KLDA-HFT\
├── python-bridge/
│   └── mt5_tick_capture_ALL_TICKS.py  ← Start this
├── api/
│   └── tick_receiver.py               ← Start this
└── cpp-backend/
    ├── docker-compose.yml             ← docker-compose up
    └── live_ticker.html               ← Open in browser
```

---

## ⚡ **MINIMAL STARTUP** (just check prices)

**If you just want to see current prices quickly:**

```bash
# One command - shows all 17 assets
"C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -d KLDA-HFT_Database -c "SELECT symbol, bid, ask, last_updated FROM current ORDER BY symbol;"
```

**If data is old (systems stopped):**
1. Start API: `python tick_receiver.py`
2. Start bridge: `python mt5_tick_capture_ALL_TICKS.py`
3. Wait 5 seconds
4. Run query again → Fresh data!

---

**Created:** 2026-01-15
**Purpose:** Manual control of KLDA-HFT infrastructure
