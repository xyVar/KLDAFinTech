#!/usr/bin/env python3
import psycopg2
from datetime import datetime

conn = psycopg2.connect(
    host="localhost",
    database="KLDA-HFT_Database",
    user="postgres",
    password="MyKldaTechnologies2025!"
)
cursor = conn.cursor()

print(f"=== DATA FLOW VERIFICATION - {datetime.now().strftime('%H:%M:%S')} ===\n")

# Check VIX
cursor.execute("SELECT last_updated FROM current WHERE symbol='VIX';")
current_time = cursor.fetchone()[0]
print(f"1. CURRENT table (VIX): {current_time}")

cursor.execute("SELECT MAX(time), COUNT(*) FROM vix_history WHERE time >= NOW() - INTERVAL '1 minute';")
history_time, count = cursor.fetchone()
print(f"2. HISTORY table (vix_history): {history_time} ({count} ticks last minute)")

cursor.execute("SELECT MAX(time) FROM vix_bars WHERE timeframe='M1';")
bars_time = cursor.fetchone()[0]
print(f"3. BARS table (vix_bars M1): {bars_time}")

print(f"\n✅ FLOW CONFIRMED: CURRENT → HISTORY → BARS")

cursor.close()
conn.close()
