# MT5 BRIDGE MANUAL MANAGEMENT GUIDE
## How to Keep MT5 Bridge Running 24/7

**Date:** 2026-01-30
**Purpose:** Manual control and monitoring of MT5 tick capture bridge

---

## QUICK REFERENCE COMMANDS

### Check if Bridge is Working
```bash
# 1. Check Python processes
tasklist | findstr python.exe

# 2. Check Flask API stats
curl http://localhost:5000/stats

# 3. Check database last update
psql -U postgres -d KLDA-HFT_Database -c "SELECT MAX(last_updated), NOW() - MAX(last_updated) AS age FROM current;"
```

### Restart the Bridge
```bash
# 1. Kill all Python processes
taskkill /F /IM python.exe

# 2. Restart Flask API (in new terminal)
cd C:\Users\PC\Desktop\KLDAFinTech\KLDA-HFT\api
python tick_receiver.py

# 3. Restart MT5 Bridge (in new terminal)
cd C:\Users\PC\Desktop\KLDAFinTech\KLDA-HFT\python-bridge
python mt5_tick_capture_ALL_TICKS.py
```

---

## PROBLEM: WHY DID IT STOP?

**Possible Reasons:**

1. **MT5 Terminal Disconnected from Broker**
   - Internet connection dropped
   - Broker server maintenance
   - MT5 terminal crashed

2. **MT5 API Connection Lost**
   - Python lost connection to MT5
   - MT5 terminal needs restart
   - No automatic reconnect

3. **Broker Returned No Ticks**
   - Market was closed (weekends, holidays)
   - Asset temporarily unavailable
   - Python bridge waiting for ticks that never came

4. **Python Script Crashed Silently**
   - Exception not caught
   - Memory issue
   - Loop stopped

---

## SOLUTION 1: ADD AUTO-RECONNECT TO BRIDGE

**File:** `python-bridge/mt5_tick_capture_ALL_TICKS.py`

Add reconnect logic after line 32 (connect_mt5 function):

```python
import time
import sys

def connect_mt5_with_retry(max_retries=5):
    """Connect to MT5 with automatic retries"""
    for attempt in range(max_retries):
        print(f"[ATTEMPT {attempt+1}/{max_retries}] Connecting to MT5...")

        if not mt5.initialize():
            error = mt5.last_error()
            print(f"[ERROR] MT5 initialization failed: {error}")

            if attempt < max_retries - 1:
                print(f"[RETRY] Waiting 10 seconds before retry...")
                time.sleep(10)
                continue
            else:
                print(f"[FATAL] Failed after {max_retries} attempts. Exiting.")
                return False

        # Test connection
        account_info = mt5.account_info()
        if account_info is None:
            print("[ERROR] Failed to get account info")
            if attempt < max_retries - 1:
                mt5.shutdown()
                time.sleep(10)
                continue
            else:
                return False

        print(f"[OK] Connected to MT5")
        print(f"  Account: {account_info.login}")
        print(f"  Server: {account_info.server}")
        print(f"  Balance: ${account_info.balance:.2f}")
        return True

    return False

# Replace line 38 in main script
if not connect_mt5_with_retry():
    sys.exit(1)
```

**Add reconnect check in main loop** (after line 190):

```python
# Main loop
tick_count_since_last_check = 0
last_reconnect_check = time.time()

while True:
    try:
        # Capture ticks
        ticks = capture_all_ticks(available_symbols)

        # Send to API
        send_to_api(ticks)

        # Track tick count
        tick_count_since_last_check += len(ticks)

        # Every 60 seconds, check if MT5 is still connected
        if time.time() - last_reconnect_check > 60:
            # Check if we got any ticks in last 60 seconds
            if tick_count_since_last_check == 0:
                print("[WARNING] No ticks received in 60 seconds. Checking MT5 connection...")

                # Test if MT5 is responsive
                test_tick = mt5.symbol_info_tick('NAS100')
                if test_tick is None:
                    print("[ERROR] MT5 not responding. Attempting reconnect...")
                    mt5.shutdown()
                    time.sleep(5)

                    if not connect_mt5_with_retry():
                        print("[FATAL] Reconnect failed. Exiting.")
                        sys.exit(1)

                    # Re-subscribe to symbols
                    available_symbols = subscribe_symbols()
                    print("[OK] Reconnected successfully!")

            # Reset counters
            tick_count_since_last_check = 0
            last_reconnect_check = time.time()

        # Sleep
        time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n[STOP] Shutting down gracefully...")
        mt5.shutdown()
        sys.exit(0)

    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        print(f"[RETRY] Attempting to recover...")
        time.sleep(5)
        # Don't exit - try to continue
```

---

## SOLUTION 2: CREATE WATCHDOG SCRIPT

**File:** `python-bridge/watchdog.py`

```python
#!/usr/bin/env python3
"""
Watchdog script to monitor and restart MT5 bridge if it fails
Run this in a separate terminal
"""

import subprocess
import time
import requests
import psycopg2
from datetime import datetime

# Configuration
FLASK_STATS_URL = "http://localhost:5000/stats"
DB_CONFIG = {
    'host': 'localhost',
    'database': 'KLDA-HFT_Database',
    'user': 'postgres',
    'password': 'MyKldaTechnologies2025!'
}

# Process references
flask_process = None
bridge_process = None

def check_flask_api():
    """Check if Flask API is responding"""
    try:
        response = requests.get(FLASK_STATS_URL, timeout=5)
        if response.status_code == 200:
            return True
    except:
        pass
    return False

def check_database_freshness():
    """Check if database received ticks in last 5 minutes"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT EXTRACT(EPOCH FROM (NOW() - MAX(last_updated))) AS seconds_ago
            FROM current;
        """)

        seconds_ago = cursor.fetchone()[0]
        cursor.close()
        conn.close()

        # Data is fresh if < 5 minutes old
        return seconds_ago < 300
    except:
        return False

def start_flask_api():
    """Start Flask API process"""
    global flask_process
    print(f"[{datetime.now()}] Starting Flask API...")

    flask_process = subprocess.Popen(
        ['python', 'tick_receiver.py'],
        cwd='C:\\Users\\PC\\Desktop\\KLDAFinTech\\KLDA-HFT\\api',
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    time.sleep(5)  # Wait for Flask to start

def start_mt5_bridge():
    """Start MT5 bridge process"""
    global bridge_process
    print(f"[{datetime.now()}] Starting MT5 Bridge...")

    bridge_process = subprocess.Popen(
        ['python', 'mt5_tick_capture_ALL_TICKS.py'],
        cwd='C:\\Users\\PC\\Desktop\\KLDAFinTech\\KLDA-HFT\\python-bridge',
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    time.sleep(5)  # Wait for bridge to connect

def restart_system():
    """Kill and restart both processes"""
    global flask_process, bridge_process

    print(f"[{datetime.now()}] RESTARTING SYSTEM...")

    # Kill existing processes
    if flask_process:
        flask_process.kill()
    if bridge_process:
        bridge_process.kill()

    # Also kill any orphaned python processes
    subprocess.run(['taskkill', '/F', '/IM', 'python.exe'],
                   stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL)

    time.sleep(3)

    # Restart
    start_flask_api()
    start_mt5_bridge()

    print(f"[{datetime.now()}] System restarted successfully!")

def main():
    """Main watchdog loop"""
    print("=" * 60)
    print("KLDA-HFT WATCHDOG - 24/7 Monitoring")
    print("=" * 60)
    print("Checking system every 60 seconds...")
    print("Press Ctrl+C to stop")
    print()

    # Initial start
    restart_system()

    consecutive_failures = 0

    while True:
        try:
            time.sleep(60)  # Check every 60 seconds

            # Check Flask API
            flask_ok = check_flask_api()

            # Check database freshness
            db_fresh = check_database_freshness()

            if flask_ok and db_fresh:
                print(f"[{datetime.now()}] ✓ System healthy")
                consecutive_failures = 0
            else:
                consecutive_failures += 1

                if not flask_ok:
                    print(f"[{datetime.now()}] ✗ Flask API not responding")
                if not db_fresh:
                    print(f"[{datetime.now()}] ✗ Database not receiving ticks")

                # Restart after 2 consecutive failures (2 minutes)
                if consecutive_failures >= 2:
                    print(f"[{datetime.now()}] !! FAILURE DETECTED - Restarting...")
                    restart_system()
                    consecutive_failures = 0

        except KeyboardInterrupt:
            print("\n[STOP] Watchdog shutting down...")
            if flask_process:
                flask_process.kill()
            if bridge_process:
                bridge_process.kill()
            break

        except Exception as e:
            print(f"[{datetime.now()}] ERROR: {e}")

if __name__ == '__main__':
    main()
```

**How to use:**
```bash
# Open new terminal
cd C:\Users\PC\Desktop\KLDAFinTech\KLDA-HFT\python-bridge
python watchdog.py

# Leave this running 24/7
# It will auto-restart Flask + Bridge if they fail
```

---

## SOLUTION 3: WINDOWS TASK SCHEDULER (Auto-Start on Boot)

### Step 1: Create Startup Batch File

**File:** `C:\Users\PC\Desktop\KLDAFinTech\KLDA-HFT\start_all.bat`

```batch
@echo off
echo Starting KLDA-HFT System...

REM Start PostgreSQL (if not already running)
net start postgresql-x64-16

REM Wait for PostgreSQL
timeout /t 5

REM Start Flask API in background
start "KLDA-HFT Flask API" /MIN cmd /c "cd C:\Users\PC\Desktop\KLDAFinTech\KLDA-HFT\api && python tick_receiver.py"

REM Wait for Flask to start
timeout /t 10

REM Start MT5 Bridge in background
start "KLDA-HFT MT5 Bridge" /MIN cmd /c "cd C:\Users\PC\Desktop\KLDAFinTech\KLDA-HFT\python-bridge && python mt5_tick_capture_ALL_TICKS.py"

REM Start Watchdog in background
timeout /t 10
start "KLDA-HFT Watchdog" /MIN cmd /c "cd C:\Users\PC\Desktop\KLDAFinTech\KLDA-HFT\python-bridge && python watchdog.py"

echo KLDA-HFT System Started!
echo Flask API: http://localhost:5000
echo Check status: curl http://localhost:5000/stats
pause
```

### Step 2: Add to Windows Startup

1. Press `Win + R`
2. Type `shell:startup`
3. Right-click → New → Shortcut
4. Target: `C:\Users\PC\Desktop\KLDAFinTech\KLDA-HFT\start_all.bat`
5. Name: "KLDA-HFT Auto Start"

Now it starts automatically when Windows boots!

---

## MANUAL MONITORING COMMANDS

### Check System Health
```bash
# 1. Check if processes are running
tasklist | findstr python.exe

# 2. Check Flask API
curl http://localhost:5000/stats

# 3. Check database age
psql -U postgres -d KLDA-HFT_Database -c "SELECT symbol, last_updated, NOW() - last_updated AS age FROM current ORDER BY last_updated DESC LIMIT 5;"

# 4. Check MT5 bridge stats (if you keep the window open)
# Look for "Ticks sent" increasing
```

### Check MT5 Terminal Connection

**Open MT5 Terminal manually:**
1. Check bottom-right corner: Should show connection bars (green)
2. Tools → Options → Server → Check "Enable news"
3. View → Toolbox → Trade tab → Check account info

**If disconnected:**
1. File → Login to Trade Account
2. Re-enter credentials
3. MT5 bridge should auto-reconnect in 60 seconds

---

## WHAT TO DO WHEN IT STOPS

### Scenario 1: No ticks for > 5 minutes

```bash
# Step 1: Check database
psql -U postgres -d KLDA-HFT_Database -c "SELECT MAX(last_updated), NOW() - MAX(last_updated) FROM current;"

# Step 2: Check Flask API
curl http://localhost:5000/stats

# Step 3: Restart MT5 bridge only
taskkill /F /PID <MT5_BRIDGE_PID>
cd C:\Users\PC\Desktop\KLDAFinTech\KLDA-HFT\python-bridge
python mt5_tick_capture_ALL_TICKS.py
```

### Scenario 2: Flask API not responding

```bash
# Step 1: Kill Flask
taskkill /F /PID <FLASK_PID>

# Step 2: Restart Flask
cd C:\Users\PC\Desktop\KLDAFinTech\KLDA-HFT\api
python tick_receiver.py
```

### Scenario 3: Both broken

```bash
# Full restart
taskkill /F /IM python.exe
C:\Users\PC\Desktop\KLDAFinTech\KLDA-HFT\start_all.bat
```

---

## DASHBOARD FOR MONITORING

Create simple monitoring page:

**File:** `KLDA-HFT/monitor.html`

```html
<!DOCTYPE html>
<html>
<head>
    <title>KLDA-HFT Monitor</title>
    <style>
        body { font-family: monospace; background: #000; color: #0f0; padding: 20px; }
        .status { padding: 10px; margin: 10px 0; border: 1px solid #0f0; }
        .healthy { background: #002200; }
        .unhealthy { background: #220000; color: #f00; }
    </style>
</head>
<body>
    <h1>KLDA-HFT System Monitor</h1>

    <div id="flask-status" class="status">
        <strong>Flask API:</strong> <span id="flask-text">Checking...</span>
    </div>

    <div id="db-status" class="status">
        <strong>Database:</strong> <span id="db-text">Checking...</span>
    </div>

    <div id="ticks-status" class="status">
        <strong>Last Tick:</strong> <span id="ticks-text">Checking...</span>
    </div>

    <script>
        async function checkSystem() {
            // Check Flask
            try {
                const response = await fetch('http://localhost:5000/stats');
                const data = await response.json();

                document.getElementById('flask-text').textContent = `OK (${data.ticks_processed} ticks processed)`;
                document.getElementById('flask-status').className = 'status healthy';

                // Check last flush time
                const lastFlush = new Date(data.last_flush);
                const ageSeconds = (new Date() - lastFlush) / 1000;

                if (ageSeconds < 300) {
                    document.getElementById('ticks-text').textContent = `${Math.floor(ageSeconds)}s ago (FRESH)`;
                    document.getElementById('ticks-status').className = 'status healthy';
                } else {
                    document.getElementById('ticks-text').textContent = `${Math.floor(ageSeconds/60)}min ago (STALE!)`;
                    document.getElementById('ticks-status').className = 'status unhealthy';
                }
            } catch (e) {
                document.getElementById('flask-text').textContent = 'OFFLINE';
                document.getElementById('flask-status').className = 'status unhealthy';
            }
        }

        // Check every 5 seconds
        setInterval(checkSystem, 5000);
        checkSystem();
    </script>
</body>
</html>
```

**Open:** `http://localhost:8082/monitor.html`

---

## SUMMARY

**For 24/7 Operation:**

1. ✅ Use `watchdog.py` to auto-restart on failure
2. ✅ Add auto-reconnect logic to MT5 bridge
3. ✅ Use Windows Task Scheduler to start on boot
4. ✅ Monitor with `monitor.html` dashboard

**Current Issue:**
Your bridge has been stuck for 9 days. You need to restart it NOW.

**Quick Fix:**
```bash
taskkill /F /IM python.exe
C:\Users\PC\Desktop\KLDAFinTech\KLDA-HFT\start_all.bat
```

Then implement watchdog for future.
