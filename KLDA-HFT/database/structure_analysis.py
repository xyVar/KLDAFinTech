#!/usr/bin/env python3
"""
KLDA-HFT Database Structure Analysis
Quick analysis of table relationships and data flow
"""

import psycopg2
from datetime import datetime

conn = psycopg2.connect(
    host="localhost",
    database="KLDA-HFT_Database",
    user="postgres",
    password="MyKldaTechnologies2025!"
)
cursor = conn.cursor()

print("=" * 80)
print("KLDA-HFT DATABASE STRUCTURE ANALYSIS")
print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)

# 1. List all tables
print("\n1. ALL TABLES IN DATABASE")
print("-" * 80)
cursor.execute("""
    SELECT tablename
    FROM pg_tables
    WHERE schemaname='public'
    ORDER BY tablename;
""")
tables = cursor.fetchall()
print(f"Total tables: {len(tables)}\n")

current_tables = []
history_tables = []
bars_tables = []
other_tables = []

for table in tables:
    table_name = table[0]
    if table_name == 'current':
        current_tables.append(table_name)
    elif '_history' in table_name:
        history_tables.append(table_name)
    elif '_bars' in table_name:
        bars_tables.append(table_name)
    else:
        other_tables.append(table_name)

print(f"CURRENT TABLE (Entry Point): {len(current_tables)}")
for t in current_tables:
    print(f"  - {t}")

print(f"\nHISTORY TABLES (Tick Storage): {len(history_tables)}")
for t in history_tables[:5]:
    print(f"  - {t}")
if len(history_tables) > 5:
    print(f"  ... and {len(history_tables) - 5} more")

print(f"\nBARS TABLES (OHLCV Data): {len(bars_tables)}")
for t in bars_tables[:5]:
    print(f"  - {t}")
if len(bars_tables) > 5:
    print(f"  ... and {len(bars_tables) - 5} more")

print(f"\nOTHER TABLES: {len(other_tables)}")
for t in other_tables:
    print(f"  - {t}")

# 2. CURRENT table structure
print("\n2. CURRENT TABLE (Entry Point)")
print("-" * 80)
cursor.execute("SELECT COUNT(*) FROM current;")
print(f"Rows: {cursor.fetchone()[0]}")

cursor.execute("""
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_name = 'current'
    ORDER BY ordinal_position;
""")
columns = cursor.fetchall()
print("\nColumns:")
for col in columns:
    print(f"  - {col[0]:<20} {col[1]}")

# 3. Sample HISTORY table structure
print("\n3. HISTORY TABLE STRUCTURE (Example: tsla_history)")
print("-" * 80)
try:
    cursor.execute("SELECT COUNT(*) FROM tsla_history;")
    print(f"Total ticks: {cursor.fetchone()[0]:,}")

    cursor.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'tsla_history'
        ORDER BY ordinal_position;
    """)
    columns = cursor.fetchall()
    print("\nColumns:")
    for col in columns:
        print(f"  - {col[0]:<20} {col[1]}")
except Exception as e:
    print(f"Error: {e}")

# 4. Sample BARS table structure
print("\n4. BARS TABLE STRUCTURE (Example: tsla_bars)")
print("-" * 80)
try:
    cursor.execute("SELECT COUNT(*) FROM tsla_bars;")
    print(f"Total bars: {cursor.fetchone()[0]:,}")

    cursor.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'tsla_bars'
        ORDER BY ordinal_position;
    """)
    columns = cursor.fetchall()
    print("\nColumns:")
    for col in columns:
        print(f"  - {col[0]:<20} {col[1]}")

    # Show timeframe distribution
    cursor.execute("""
        SELECT timeframe, COUNT(*)
        FROM tsla_bars
        GROUP BY timeframe
        ORDER BY timeframe;
    """)
    timeframes = cursor.fetchall()
    print("\nTimeframe Distribution:")
    for tf in timeframes:
        print(f"  - {tf[0]}: {tf[1]:,} bars")
except Exception as e:
    print(f"Error: {e}")

# 5. Data Flow Verification
print("\n5. DATA FLOW VERIFICATION")
print("-" * 80)

symbols = ['TSLA', 'VIX', 'NAS100']
for symbol in symbols:
    symbol_lower = symbol.lower()
    try:
        # Check CURRENT
        cursor.execute(f"""
            SELECT last_updated,
                   EXTRACT(EPOCH FROM (NOW() - last_updated)) as seconds_ago
            FROM current
            WHERE symbol = '{symbol}';
        """)
        result = cursor.fetchone()
        if result:
            last_update, seconds_ago = result
            status = "LIVE" if seconds_ago < 60 else "STALE"
            print(f"\n{symbol}:")
            print(f"  CURRENT:  Last update {int(seconds_ago)}s ago [{status}]")

        # Check HISTORY (last 5 minutes)
        cursor.execute(f"""
            SELECT COUNT(*)
            FROM {symbol_lower}_history
            WHERE time >= NOW() - INTERVAL '5 minutes';
        """)
        count = cursor.fetchone()[0]
        print(f"  HISTORY:  {count} ticks in last 5 minutes")

        # Check BARS
        cursor.execute(f"SELECT COUNT(*) FROM {symbol_lower}_bars;")
        count = cursor.fetchone()[0]
        print(f"  BARS:     {count:,} total bars")

    except Exception as e:
        print(f"\n{symbol}: Error - {e}")

# 6. TimescaleDB Integration
print("\n6. TIMESCALEDB INTEGRATION")
print("-" * 80)
cursor.execute("""
    SELECT hypertable_name, num_chunks, compression_enabled
    FROM timescaledb_information.hypertables
    WHERE hypertable_name LIKE '%history'
    ORDER BY hypertable_name
    LIMIT 5;
""")
results = cursor.fetchall()
for row in results:
    comp_status = "ENABLED" if row[2] else "DISABLED"
    print(f"  {row[0]:<25} Chunks: {row[1]:<5} Compression: {comp_status}")

print("\n" + "=" * 80)
print("STRUCTURE ANALYSIS COMPLETE")
print("=" * 80)

cursor.close()
conn.close()
