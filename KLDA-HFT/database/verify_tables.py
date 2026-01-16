#!/usr/bin/env python3
"""Verify database tables and row counts"""

import psycopg2

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'KLDA-HFT_Database',
    'user': 'postgres',
    'password': 'MyKldaTechnologies2025!'
}

conn = psycopg2.connect(**DB_CONFIG)
cursor = conn.cursor()

# List all tables
cursor.execute("""
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'public'
    ORDER BY table_name;
""")

print("\n[DATABASE TABLES]")
print("=" * 60)

current_tables = []
history_tables = []
bar_tables = []

for row in cursor.fetchall():
    table_name = row[0]
    if table_name == 'current':
        current_tables.append(table_name)
    elif table_name.endswith('_history'):
        history_tables.append(table_name)
    elif table_name.endswith('_bars'):
        bar_tables.append(table_name)

print(f"\n1. CURRENT table: {len(current_tables)}")
for table in current_tables:
    print(f"   - {table}")

print(f"\n2. HISTORY tables: {len(history_tables)}")
for table in sorted(history_tables)[:5]:
    print(f"   - {table}")
print(f"   ... and {len(history_tables) - 5} more")

print(f"\n3. BAR tables: {len(bar_tables)}")
for table in sorted(bar_tables)[:5]:
    print(f"   - {table}")
print(f"   ... and {len(bar_tables) - 5} more")

# Check sample data from bar tables
print("\n[SAMPLE BAR COUNTS]")
print("=" * 60)
for asset in ['tsla', 'nvda', 'aapl', 'orcl']:
    cursor.execute(f"SELECT COUNT(*) FROM {asset}_bars WHERE timeframe = 'D1';")
    d1_count = cursor.fetchone()[0]
    cursor.execute(f"SELECT MIN(time), MAX(time) FROM {asset}_bars WHERE timeframe = 'D1';")
    min_time, max_time = cursor.fetchone()
    print(f"{asset.upper()}: {d1_count} D1 bars ({min_time.date()} to {max_time.date()})")

print("\n[SUCCESS] Database verification complete!")
conn.close()
