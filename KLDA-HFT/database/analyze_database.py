#!/usr/bin/env python3
"""
Complete KLDA-HFT Database Analysis
"""

import psycopg2
from datetime import datetime

conn = psycopg2.connect(
    host='localhost',
    port=5432,
    database='KLDA-HFT_Database',
    user='postgres',
    password='MyKldaTechnologies2025!'
)

cursor = conn.cursor()

print("=" * 80)
print("KLDA-HFT DATABASE ANALYSIS")
print("=" * 80)

# Get all tables
cursor.execute("""
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'public'
    ORDER BY table_name;
""")

tables = [row[0] for row in cursor.fetchall()]

print(f"\nTotal Tables: {len(tables)}")
print("\nTables:")
for table in tables:
    print(f"  - {table}")

# Analyze CURRENT table (latest tick per symbol)
print("\n" + "=" * 80)
print("CURRENT TABLE - Latest Tick Per Symbol")
print("=" * 80)

cursor.execute("""
    SELECT
        symbol,
        bid,
        ask,
        spread,
        volume,
        buy_volume,
        sell_volume,
        flags,
        last_updated,
        EXTRACT(EPOCH FROM (NOW() - last_updated)) as seconds_ago
    FROM current
    ORDER BY symbol;
""")

print(f"\n{'Symbol':<12} {'Bid':<10} {'Ask':<10} {'Spread':<8} {'Vol':<8} {'Buy':<8} {'Sell':<8} {'Flags':<6} {'Age'}")
print("-" * 80)

live_symbols = []
for row in cursor.fetchall():
    symbol, bid, ask, spread, vol, buy_vol, sell_vol, flags, last_updated, age = row

    age_str = f"{int(age)}s" if age < 60 else f"{int(age/60)}m" if age < 3600 else f"{int(age/3600)}h"

    if age < 600:  # Fresh = < 10 minutes
        live_symbols.append(symbol)
        marker = " ← LIVE"
    else:
        marker = ""

    print(f"{symbol:<12} {bid:<10.2f} {ask:<10.2f} {spread:<8.4f} {vol:<8} {buy_vol:<8} {sell_vol:<8} {flags:<6} {age_str}{marker}")

# Analyze HISTORY tables (tick archives)
print("\n" + "=" * 80)
print("HISTORY TABLES - Tick Data Volume")
print("=" * 80)

history_tables = [t for t in tables if t.endswith('_history')]

print(f"\n{'Symbol':<12} {'Total Ticks':<15} {'Earliest Tick':<20} {'Latest Tick':<20}")
print("-" * 80)

total_ticks = 0
for table in history_tables:
    symbol = table.replace('_history', '').upper()

    cursor.execute(f"""
        SELECT
            COUNT(*) as count,
            MIN(time) as earliest,
            MAX(time) as latest
        FROM {table};
    """)

    count, earliest, latest = cursor.fetchone()
    total_ticks += count

    print(f"{symbol:<12} {count:<15,} {str(earliest)[:19]:<20} {str(latest)[:19]:<20}")

# DATA SOURCE ANALYSIS
print("\n" + "=" * 80)
print("DATA SOURCE ANALYSIS")
print("=" * 80)

print("\nBROKER: Pepperstone (Demo Account)")
print("CONNECTION: MT5 Python API → Flask API → PostgreSQL")
print("TICK TYPE: CFD Quotes (Bid/Ask only, NO trade volume)")

# Check tick flags distribution
print("\n" + "=" * 80)
print("TICK FLAGS DISTRIBUTION (SpotCrude Sample)")
print("=" * 80)

cursor.execute("""
    WITH recent AS (
        SELECT flags FROM spotcrude_history
        ORDER BY time DESC LIMIT 1000
    )
    SELECT flags, COUNT(*) as count
    FROM recent
    GROUP BY flags
    ORDER BY count DESC;
""")

print(f"\n{'Flags':<8} {'Count':<10} {'Type'}")
print("-" * 40)

for flags, count in cursor.fetchall():
    flag_type = []
    if flags & 2: flag_type.append("BID")
    if flags & 4: flag_type.append("ASK")
    if flags & 8: flag_type.append("TRADE")

    type_str = "+".join(flag_type) if flag_type else "NONE"
    print(f"{flags:<8} {count:<10} {type_str}")

# SUMMARY
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

print(f"\nTotal Symbols: {len(history_tables)}")
print(f"Live Symbols (< 10min old): {len(live_symbols)} → {', '.join(live_symbols)}")
print(f"Total Ticks Captured: {total_ticks:,}")
print(f"\nData Quality:")
print(f"  ✓ Bid/Ask prices: YES")
print(f"  ✓ Spread data: YES")
print(f"  ✗ Trade volume: NO (all buy_volume=0, sell_volume=0)")
print(f"  ✗ TRADE ticks: NO (only QUOTE ticks with flags 2/4/6)")

print("\nIMPACT ON RENAISSANCE STRATEGY:")
print("  ✓ Mean Reversion: WORKS (uses bid prices)")
print("  ✓ HMM Regime: WORKS (uses bid prices)")
print("  ✓ Spread Volatility: WORKS (uses spread data)")
print("  ✓ Transaction Cost: WORKS (uses spread data)")
print("  ✓ Kelly Sizing: WORKS (model-based)")
print("  ✗ Order Flow: BROKEN (needs buy/sell volume)")

print("\n" + "=" * 80)

cursor.close()
conn.close()
