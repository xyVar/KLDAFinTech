#!/usr/bin/env python3
"""Check if ticks are being stored in database"""

import psycopg2
from datetime import datetime

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'KLDA-HFT_Database',
    'user': 'postgres',
    'password': 'MyKldaTechnologies2025!'
}

conn = psycopg2.connect(**DB_CONFIG)
cursor = conn.cursor()

print("=" * 60)
print("DATABASE TICK VERIFICATION")
print("=" * 60)

# Check CURRENT table
print("\n[CURRENT TABLE] - Latest tick for each asset:")
cursor.execute("""
    SELECT symbol, bid, ask, buy_volume, sell_volume, last_updated
    FROM current
    ORDER BY last_updated DESC;
""")

rows = cursor.fetchall()
if rows:
    for row in rows:
        symbol, bid, ask, buy_vol, sell_vol, updated = row
        print(f"  {symbol.upper():6} | Bid: {bid:8.2f} | Ask: {ask:8.2f} | Buy: {buy_vol:6} | Sell: {sell_vol:6} | {updated}")
else:
    print("  [EMPTY] No data in CURRENT table")

# Check HISTORY tables for recent ticks
print("\n[HISTORY TABLES] - Tick counts (last 5 minutes):")
assets = ['tsla', 'nvda', 'aapl', 'pltr', 'amd']

for asset in assets:
    cursor.execute(f"""
        SELECT COUNT(*), MIN(time), MAX(time)
        FROM {asset}_history
        WHERE time >= NOW() - INTERVAL '5 minutes';
    """)

    count, min_time, max_time = cursor.fetchone()

    if count > 0:
        print(f"  {asset.upper():6} | {count:4} ticks | {min_time} -> {max_time}")
    else:
        print(f"  {asset.upper():6} | No ticks in last 5 minutes")

# Total ticks in history
print("\n[TOTAL TICKS] - All time:")
for asset in assets:
    cursor.execute(f"SELECT COUNT(*) FROM {asset}_history;")
    total = cursor.fetchone()[0]
    print(f"  {asset.upper():6} | {total:,} ticks")

print("\n" + "=" * 60)
print("[SUCCESS] Database check complete!")
print("=" * 60)

conn.close()
