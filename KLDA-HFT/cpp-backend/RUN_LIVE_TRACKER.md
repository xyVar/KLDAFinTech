# KLDA-HFT Live Tick Tracker - How to Run

## What This Does

**C++ Backend:**
- Connects to your PostgreSQL database
- Reads `CURRENT` table every 1 second
- Outputs live data to `live_ticks.json`

**HTML Frontend:**
- Beautiful dashboard showing all 17 assets
- Updates every second automatically
- Color-coded: BID (red), ASK (cyan), SPREAD (yellow)
- Shows time since last update (green = recent, red = stale)

---

## Option 1: Run Locally (Windows)

### Step 1: Compile C++ Live Tracker

```bash
cd C:\Users\PC\Desktop\KLDAFinTech\KLDA-HFT\cpp-backend

# Compile with g++
g++ -std=c++17 src/main_live.cpp src/database/connection.cpp ^
    -I"C:/Program Files/PostgreSQL/16/include" ^
    -L"C:/Program Files/PostgreSQL/16/lib" ^
    -lpq -o live_tracker.exe
```

### Step 2: Run the C++ Backend

```bash
# Make sure config.json exists in cpp-backend folder
live_tracker.exe
```

**You should see:**
```
======================================
KLDA-HFT Live Tick Tracker
======================================

[1] Loading configuration...
[OK] Configuration loaded

[2] Connecting to PostgreSQL...
[OK] Connected to database

[3] Starting live tick tracking...
Writing to: live_ticks.json
Press Ctrl+C to stop

[10] Updated 17 assets
[20] Updated 17 assets
[30] Updated 17 assets
...
```

### Step 3: Open Frontend

1. Open File Explorer
2. Navigate to: `C:\Users\PC\Desktop\KLDAFinTech\KLDA-HFT\cpp-backend\`
3. Double-click: **`live_ticker.html`**

**Your browser will show:**
- 17 asset cards updating every second
- Green "CONNECTED" status
- Live bid/ask prices
- Volume data

---

## Option 2: Run in Docker (Recommended)

### Step 1: Add main_live.cpp to Dockerfile

Edit `Dockerfile`, change line 41:
```dockerfile
# OLD:
CMD ["./build/klda-hft-engine"]

# NEW:
CMD ["./build/live_tracker"]
```

### Step 2: Update CMakeLists.txt

Edit `CMakeLists.txt`, add after line 26:
```cmake
# Live tracker executable
add_executable(live_tracker src/main_live.cpp src/database/connection.cpp)
target_link_libraries(live_tracker PRIVATE ${PostgreSQL_LIBRARIES})
```

### Step 3: Rebuild Docker Image

```bash
cd C:\Users\PC\Desktop\KLDAFinTech\KLDA-HFT\cpp-backend
docker-compose build
docker-compose up -d
```

### Step 4: Open Frontend

Open `live_ticker.html` in browser (same as Option 1, Step 3)

---

## Troubleshooting

### "Failed to connect to database"

**Check PostgreSQL is running:**
```bash
"C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -d KLDA-HFT_Database -c "\l"
```

**Check config.json has correct password:**
```json
{
  "database": {
    "host": "localhost",
    "port": 5432,
    "name": "KLDA-HFT_Database",
    "user": "postgres",
    "password": "MyKldaTechnologies2025!"
  }
}
```

### "ERROR: Failed to fetch data" in browser

**Make sure C++ backend is running!**

Check if `live_ticks.json` file exists and is being updated:
```bash
dir live_ticks.json
```

If file doesn't exist or isn't updating = C++ backend not running

### Browser shows "Waiting for data..."

**C++ backend needs a few seconds to start writing data.**

Wait 5 seconds and refresh the page.

### Prices stuck at yesterday's close

**Normal! Market is closed.**

Your system is working correctly. Prices will update when:
- Stock market opens: 16:30 CET+1 (09:30 EST)
- Futures trading: 24/7 (NAS100, VIX should update now)

---

## What You're Seeing

### Ticker Card Colors:

- **BID** (Red): Selling price
- **ASK** (Cyan): Buying price
- **SPREAD** (Yellow): Difference (ask - bid)

### Time Indicators:

- **Green** = Updated < 5 seconds ago (live!)
- **Gray** = Updated 5 sec - 5 min ago (recent)
- **Red** = Updated > 5 min ago (stale/market closed)

### Volume:

- **Volume**: Total tick volume
- **Buy**: Buy-side volume (BUY trades)
- **Sell**: Sell-side volume (SELL trades)

---

## Next Steps

Once this works, we can add:

1. **Historical Charts**: Show price movement over time
2. **Tick Archive View**: Browse historical ticks
3. **Timeframe Bars**: Display M5, H1, D1 bars
4. **Alerts**: Price threshold notifications
5. **WebSocket**: Real-time push (no polling)

---

## File Structure

```
cpp-backend/
├── src/
│   ├── main.cpp           (test program)
│   ├── main_live.cpp      (continuous live tracker) ✅ NEW
│   └── database/
│       ├── connection.h
│       └── connection.cpp
├── config.json            (database credentials)
├── live_tracker.exe       (compiled binary) ✅ NEW
├── live_ticks.json        (output data) ✅ NEW
└── live_ticker.html       (frontend dashboard) ✅ NEW
```

---

**Created:** 2026-01-15
**Status:** Ready to run!
