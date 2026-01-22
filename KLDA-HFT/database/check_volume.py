#!/usr/bin/env python3
"""
Check which symbols have volume data and fresh ticks
"""

import psycopg2
from datetime import datetime, timedelta

conn = psycopg2.connect(
    host='localhost',
    port=5432,
    database='KLDA-HFT_Database',
    user='postgres',
    password='MyKldaTechnologies2025!'
)

cursor = conn.cursor()

print("=" * 80)
print("VOLUME DATA CHECK - All Symbols")
print("=" * 80)

# Check current table for all symbols
cursor.execute("""
    SELECT
        symbol,
        last_updated,
        volume,
        buy_volume,
        sell_volume,
        EXTRACT(EPOCH FROM (NOW() - last_updated)) as seconds_ago
    FROM current
    ORDER BY last_updated DESC;
""")

print("\n{:<12} {:<20} {:<10} {:<10} {:<10} {:<15}".format(
    "Symbol", "Last Update", "Volume", "Buy Vol", "Sell Vol", "Age (seconds)"))
print("-" * 80)

fresh_symbols = []
symbols_with_volume = []

for row in cursor.fetchall():
    symbol = row[0]
    last_updated = row[1]
    volume = row[2]
    buy_vol = row[3]
    sell_vol = row[4]
    age = int(row[5])

    # Check if fresh (< 10 minutes)
    if age < 600:
        fresh_symbols.append(symbol)

    # Check if has volume
    if buy_vol > 0 or sell_vol > 0:
        symbols_with_volume.append(symbol)
        marker = " <-- HAS VOLUME!"
    else:
        marker = ""

    # Color code by age
    if age < 60:
        age_str = f"{age}s (LIVE)"
    elif age < 600:
        age_str = f"{age//60}m (FRESH)"
    else:
        age_str = f"{age//3600}h (OLD)"

    print("{:<12} {:<20} {:<10} {:<10} {:<10} {:<15}{}".format(
        symbol,
        str(last_updated)[:19],
        volume,
        buy_vol,
        sell_vol,
        age_str,
        marker
    ))

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Fresh symbols (< 10 min): {len(fresh_symbols)} - {', '.join(fresh_symbols) if fresh_symbols else 'NONE'}")
print(f"Symbols with volume: {len(symbols_with_volume)} - {', '.join(symbols_with_volume) if symbols_with_volume else 'NONE'}")

if not symbols_with_volume:
    print("\n[!] NO VOLUME DATA DETECTED")
    print("    Possible reasons:")
    print("    1. MT5 is not sending volume (tick flags issue)")
    print("    2. Broker doesn't provide volume for these instruments")
    print("    3. Python bridge not capturing volume field")

cursor.close()
conn.close()
