#!/usr/bin/env python3
"""
Diagnose database write issue
Real-time monitoring to see if database is receiving updates
"""
import psycopg2
from datetime import datetime
import time

conn = psycopg2.connect(
    host="localhost",
    database="KLDA-HFT_Database",
    user="postgres",
    password="MyKldaTechnologies2025!"
)
cursor = conn.cursor()

print("=" * 80)
print("REAL-TIME DATABASE WRITE MONITORING")
print("=" * 80)
print(f"Current time: {datetime.now()}")
print("\nMonitoring CURRENT table for 30 seconds...")
print("-" * 80)

# Get initial state
cursor.execute("SELECT symbol, last_updated FROM current WHERE symbol = 'VIX';")
initial = cursor.fetchone()
initial_time = initial[1] if initial else None
print(f"INITIAL STATE (VIX): {initial_time}")

# Monitor for 30 seconds
for i in range(6):  # 6 iterations x 5 seconds = 30 seconds
    time.sleep(5)

    cursor.execute("SELECT symbol, last_updated FROM current WHERE symbol = 'VIX';")
    current = cursor.fetchone()
    current_time = current[1] if current else None

    if current_time != initial_time:
        print(f"[+5s] UPDATE DETECTED! New timestamp: {current_time}")
        initial_time = current_time
    else:
        print(f"[+5s] NO CHANGE - Still: {current_time}")

print("-" * 80)
print("\nCONCLUSION:")
cursor.execute("SELECT symbol, last_updated, NOW() - last_updated AS age FROM current WHERE symbol = 'VIX';")
final = cursor.fetchone()
print(f"VIX last_updated: {final[1]}")
print(f"Age: {final[2]}")

if final[2].total_seconds() < 60:
    print("\nDATABASE IS RECEIVING UPDATES (data less than 1 minute old)")
else:
    print(f"\nDATABASE IS STALE (data is {int(final[2].total_seconds()/3600)} hours old)")
    print("\nPOSSIBLE CAUSES:")
    print("1. Flask API is writing to WRONG database")
    print("2. Flask API connection is stale/disconnected")
    print("3. Transaction not committing properly")
    print("4. Permission issue preventing writes")

cursor.close()
conn.close()
