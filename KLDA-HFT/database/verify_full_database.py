#!/usr/bin/env python3
"""Complete database verification - all tables and data"""

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

print("=" * 60)
print("COMPLETE DATABASE VERIFICATION")
print("=" * 60)

# 1. List ALL tables
print("\n[1] ALL TABLES IN DATABASE:")
cursor.execute("""
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'public'
    ORDER BY table_name;
""")
all_tables = cursor.fetchall()
for i, (table,) in enumerate(all_tables, 1):
    print(f"  {i:2}. {table}")

print(f"\nTotal tables: {len(all_tables)}")

# 2. CURRENT table structure and data
print("\n" + "=" * 60)
print("[2] CURRENT TABLE:")
cursor.execute("SELECT * FROM current ORDER BY symbol_id;")
rows = cursor.fetchall()
print(f"Rows: {len(rows)}")
print("\nID | Symbol     | MT5 Symbol      | Bid      | Ask      | Updated")
print("-" * 60)
for row in rows[:5]:  # First 5
    print(f"{row[0]:2} | {row[1]:10} | {row[2]:15} | {row[3]:8.2f} | {row[4]:8.2f} | {str(row[6])[:19]}")
print(f"... ({len(rows)} total rows)")

# 3. HISTORY tables - row counts
print("\n" + "=" * 60)
print("[3] HISTORY TABLES (tick archives):")
history_tables = [t[0] for t in all_tables if t[0].endswith('_history')]
print(f"Total history tables: {len(history_tables)}")
for table in history_tables[:5]:
    cursor.execute(f"SELECT COUNT(*) FROM {table};")
    count = cursor.fetchone()[0]
    print(f"  {table:20} | {count:,} ticks")
print(f"... ({len(history_tables)} total)")

# 4. BARS tables - row counts
print("\n" + "=" * 60)
print("[4] BARS TABLES (historical OHLCV):")
bar_tables = [t[0] for t in all_tables if t[0].endswith('_bars')]
print(f"Total bar tables: {len(bar_tables)}")
total_bars = 0
for table in bar_tables[:5]:
    cursor.execute(f"SELECT COUNT(*) FROM {table};")
    count = cursor.fetchone()[0]
    total_bars += count
    print(f"  {table:20} | {count:,} bars")
print(f"... ({len(bar_tables)} total)")
print(f"Total historical bars: {total_bars:,}")

# 5. Sample recent tick data
print("\n" + "=" * 60)
print("[5] SAMPLE RECENT TICK DATA (tsla_history):")
cursor.execute("""
    SELECT time, bid, ask, volume, buy_volume, sell_volume, flags
    FROM tsla_history
    ORDER BY time DESC
    LIMIT 5;
""")
print("\nTime                      | Bid      | Ask      | Vol | BuyVol | SellVol | Flags")
print("-" * 80)
for row in cursor.fetchall():
    print(f"{str(row[0])[:26]} | {row[1]:8.2f} | {row[2]:8.2f} | {row[3]:3} | {row[4]:6} | {row[5]:7} | {row[6]}")

# 6. Database size
cursor.execute("""
    SELECT pg_size_pretty(pg_database_size('KLDA-HFT_Database'));
""")
db_size = cursor.fetchone()[0]

print("\n" + "=" * 60)
print("[SUMMARY]")
print(f"Total tables: {len(all_tables)}")
print(f"CURRENT table: {len(rows)} rows")
print(f"HISTORY tables: {len(history_tables)} tables")
print(f"BARS tables: {len(bar_tables)} tables ({total_bars:,} bars)")
print(f"Database size: {db_size}")
print("=" * 60)

conn.close()
