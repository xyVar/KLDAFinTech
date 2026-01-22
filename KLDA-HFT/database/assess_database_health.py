#!/usr/bin/env python3
"""
KLDA-HFT Database Health Assessment
Comprehensive check of PostgreSQL + TimescaleDB data pipeline
"""

import psycopg2
from datetime import datetime, timedelta
import sys

# Database connection
conn = psycopg2.connect(
    host="localhost",
    database="KLDA-HFT_Database",
    user="postgres",
    password="MyKldaTechnologies2025!"
)
cursor = conn.cursor()

print("=" * 80)
print("KLDA-HFT DATABASE HEALTH ASSESSMENT")
print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)

# 1. Check TimescaleDB Extension
print("\n1. TIMESCALEDB STATUS")
print("-" * 80)
cursor.execute("SELECT extname, extversion FROM pg_extension WHERE extname = 'timescaledb';")
result = cursor.fetchone()
if result:
    print(f"[OK] TimescaleDB installed: Version {result[1]}")
else:
    print("[ERROR] TimescaleDB NOT installed!")

# 2. Check Hypertables and Compression
print("\n2. HYPERTABLES & COMPRESSION")
print("-" * 80)
cursor.execute("""
    SELECT hypertable_name, compression_enabled, num_chunks
    FROM timescaledb_information.hypertables
    ORDER BY hypertable_name;
""")
hypertables = cursor.fetchall()
if hypertables:
    for ht in hypertables:
        compression_status = "ENABLED" if ht[1] else "DISABLED"
        print(f"{ht[0]:<25} Compression: {compression_status:<10} Chunks: {ht[2]}")
else:
    print("[WARNING] No hypertables found! History tables may not be optimized.")

# 3. Check Current Table (Entry Point)
print("\n3. CURRENT TABLE (Live Broker Feed Entry Point)")
print("-" * 80)
cursor.execute("""
    SELECT symbol, bid, ask, spread,
           TO_CHAR(last_updated, 'YYYY-MM-DD HH24:MI:SS') as last_updated,
           EXTRACT(EPOCH FROM (NOW() - last_updated)) as seconds_ago
    FROM current
    ORDER BY symbol;
""")
current_data = cursor.fetchall()
live_count = 0
stale_count = 0
for row in current_data:
    symbol, bid, ask, spread, last_updated, seconds_ago = row
    status = "LIVE" if seconds_ago < 60 else ("DELAYED" if seconds_ago < 600 else "STALE")
    if status == "LIVE":
        live_count += 1
    else:
        stale_count += 1

    time_str = f"{int(seconds_ago)}s ago" if seconds_ago < 60 else f"{int(seconds_ago/60)}m ago" if seconds_ago < 3600 else f"{int(seconds_ago/3600)}h ago"
    print(f"{symbol:<10} Bid: {bid:>10.2f} Ask: {ask:>10.2f} [{status}] Last: {last_updated} ({time_str})")

print(f"\nSummary: {live_count} LIVE, {stale_count} STALE (>10 min old)")

# 4. Check History Tables (Tick Storage)
print("\n4. HISTORY TABLES (Tick Storage)")
print("-" * 80)
symbols = ['tsla', 'nvda', 'pltr', 'amd', 'avgo', 'meta', 'aapl', 'msft',
           'orcl', 'amzn', 'csco', 'goog', 'intc', 'vix', 'nas100', 'natgas', 'spotcrude']

total_ticks = 0
for symbol in symbols:
    try:
        cursor.execute(f"""
            SELECT COUNT(*) as total,
                   MIN(time) as earliest,
                   MAX(time) as latest,
                   EXTRACT(EPOCH FROM (NOW() - MAX(time))) as seconds_ago
            FROM {symbol}_history;
        """)
        result = cursor.fetchone()
        count, earliest, latest, seconds_ago = result
        total_ticks += count

        if count > 0:
            time_str = f"{int(seconds_ago)}s ago" if seconds_ago < 60 else f"{int(seconds_ago/60)}m ago" if seconds_ago < 3600 else f"{int(seconds_ago/3600)}h ago"
            status = "LIVE" if seconds_ago < 300 else "STALE"
            print(f"{symbol.upper():<12} Ticks: {count:>8,} | Latest: {latest.strftime('%Y-%m-%d %H:%M:%S')} ({time_str}) [{status}]")
        else:
            print(f"{symbol.upper():<12} Ticks: {count:>8,} | [NO DATA]")
    except Exception as e:
        print(f"{symbol.upper():<12} [ERROR] {str(e)}")

print(f"\nTotal ticks across all history tables: {total_ticks:,}")

# 5. Check Continuous Aggregates (Bars)
print("\n5. CONTINUOUS AGGREGATES (OHLCV Bars)")
print("-" * 80)
cursor.execute("""
    SELECT view_name, materialized_only
    FROM timescaledb_information.continuous_aggregates
    ORDER BY view_name
    LIMIT 10;
""")
aggs = cursor.fetchall()
if aggs:
    for agg in aggs:
        print(f"  - {agg[0]}")
    print(f"\nTotal continuous aggregates: {len(aggs)}")
else:
    print("[WARNING] No continuous aggregates found! Bars are NOT pre-computed.")
    print("Dashboard is doing on-the-fly aggregation (slower performance).")

# 6. Check Positions Table
print("\n6. POSITIONS TABLE (Trading Positions)")
print("-" * 80)
try:
    cursor.execute("""
        SELECT COUNT(*) as total,
               COUNT(*) FILTER (WHERE status = 'OPEN') as open_positions,
               COUNT(*) FILTER (WHERE status = 'CLOSED') as closed_positions
        FROM positions;
    """)
    result = cursor.fetchone()
    print(f"Total positions: {result[0]}")
    print(f"  - Open: {result[1]}")
    print(f"  - Closed: {result[2]}")
except Exception as e:
    print(f"[ERROR] {str(e)}")

# 7. Data Ingestion Rate (Last Hour)
print("\n7. DATA INGESTION RATE (Last Hour)")
print("-" * 80)
try:
    cursor.execute("""
        SELECT COUNT(*) as ticks_last_hour
        FROM tsla_history
        WHERE time >= NOW() - INTERVAL '1 hour';
    """)
    result = cursor.fetchone()
    ticks_per_hour = result[0]
    ticks_per_min = ticks_per_hour / 60
    print(f"TSLA ticks in last hour: {ticks_per_hour:,} ({ticks_per_min:.1f} ticks/min)")

    if ticks_per_hour > 0:
        print("[OK] Data is flowing into the database")
    else:
        print("[WARNING] NO new ticks in the last hour!")
except Exception as e:
    print(f"[ERROR] {str(e)}")

# 8. Database Size
print("\n8. DATABASE SIZE")
print("-" * 80)
cursor.execute("""
    SELECT pg_size_pretty(pg_database_size('KLDA-HFT_Database'));
""")
size = cursor.fetchone()[0]
print(f"Total database size: {size}")

# 9. Recommendations
print("\n9. RECOMMENDATIONS")
print("-" * 80)
issues = []

if stale_count > 0:
    issues.append(f"- {stale_count} symbols have STALE data (> 10 min old) - Check MT5 connection")

if not hypertables:
    issues.append("- History tables are NOT hypertables - Enable TimescaleDB for better performance")

if not aggs:
    issues.append("- NO continuous aggregates - Create them for faster chart rendering")

if ticks_per_hour == 0:
    issues.append("- NO new ticks in last hour - Restart tick capture script")

if issues:
    for issue in issues:
        print(issue)
else:
    print("[OK] All systems operational!")

print("\n" + "=" * 80)
print("ASSESSMENT COMPLETE")
print("=" * 80)

cursor.close()
conn.close()
