#!/usr/bin/env python3
"""
Watchdog script to monitor and restart MT5 bridge if it fails
Run this in a separate terminal: python watchdog.py
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
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting Flask API...")

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
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting MT5 Bridge...")

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

    print(f"[{datetime.now().strftime('%H:%M:%S')}] RESTARTING SYSTEM...")

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

    print(f"[{datetime.now().strftime('%H:%M:%S')}] System restarted successfully!")

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
                print(f"[{datetime.now().strftime('%H:%M:%S')}] OK - System healthy")
                consecutive_failures = 0
            else:
                consecutive_failures += 1

                if not flask_ok:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR - Flask API not responding")
                if not db_fresh:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR - Database not receiving ticks")

                # Restart after 2 consecutive failures (2 minutes)
                if consecutive_failures >= 2:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] FAILURE DETECTED - Restarting...")
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
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR: {e}")

if __name__ == '__main__':
    main()
