#!/usr/bin/env python3
"""Quick examination of current database state"""
import psycopg2

conn = psycopg2.connect(
    host="localhost",
    database="KLDA-HFT_Database",
    user="postgres",
    password="MyKldaTechnologies2025!"
)
cursor = conn.cursor()

print("=" * 80)
print("CURRENT DATABASE STATE EXAMINATION")
print("=" * 80)

# 1. Check if bars tables exist
print("\n1. BARS TABLES (current state):")
print("-" * 80)
cursor.execute("""
    SELECT tablename
    FROM pg_tables
    WHERE schemaname='public' AND tablename LIKE '%bars'
    ORDER BY tablename;
""")
bars_tables = cursor.fetchall()
print(f"Found {len(bars_tables)} bars tables:")
for table in bars_tables[:5]:
    print(f"  - {table[0]}")
if len(bars_tables) > 5:
    print(f"  ... and {len(bars_tables)-5} more")

# 2. Check if continuous aggregates exist
print("\n2. CONTINUOUS AGGREGATES (auto-compression mechanism):")
print("-" * 80)
cursor.execute("""
    SELECT view_name
    FROM timescaledb_information.continuous_aggregates
    ORDER BY view_name;
""")
cont_aggs = cursor.fetchall()
if cont_aggs:
    print(f"Found {len(cont_aggs)} continuous aggregates:")
    for view in cont_aggs[:10]:
        print(f"  - {view[0]}")
else:
    print("NO continuous aggregates found!")
    print("This means: Bars are NOT auto-updating from history")

# 3. Check vix_bars structure
print("\n3. VIX_BARS TABLE STRUCTURE:")
print("-" * 80)
try:
    cursor.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'vix_bars'
        ORDER BY ordinal_position;
    """)
    columns = cursor.fetchall()
    print("Columns:")
    for col in columns:
        print(f"  - {col[0]:<20} {col[1]}")

    # Check if it's a regular table or view
    cursor.execute("""
        SELECT
            CASE
                WHEN relkind = 'r' THEN 'Regular Table'
                WHEN relkind = 'v' THEN 'View'
                WHEN relkind = 'm' THEN 'Materialized View'
            END as type
        FROM pg_class
        WHERE relname = 'vix_bars';
    """)
    table_type = cursor.fetchone()
    print(f"\nType: {table_type[0]}")

except Exception as e:
    print(f"Error: {e}")

# 4. Sample vix_bars data (quick check)
print("\n4. VIX_BARS SAMPLE DATA (last 3 rows):")
print("-" * 80)
try:
    cursor.execute("""
        SELECT time, timeframe, open, close
        FROM vix_bars
        ORDER BY time DESC
        LIMIT 3;
    """)
    rows = cursor.fetchall()
    for row in rows:
        print(f"  {row[0]} | {row[1]:<5} | O:{row[2]:.2f} C:{row[3]:.2f}")
except Exception as e:
    print(f"Error: {e}")

# 5. Check how bars are populated
print("\n5. HOW ARE BARS POPULATED?")
print("-" * 80)
cursor.execute("""
    SELECT tgname, proname
    FROM pg_trigger
    JOIN pg_proc ON pg_trigger.tgfoid = pg_proc.oid
    WHERE tgrelid = 'vix_bars'::regclass;
""")
triggers = cursor.fetchall()
if triggers:
    print("Triggers found:")
    for trig in triggers:
        print(f"  - {trig[0]} → {trig[1]}")
else:
    print("NO triggers found on vix_bars")

if not cont_aggs:
    print("\nCONCLUSION: Bars are populated MANUALLY, not automatically!")
else:
    print("\nCONCLUSION: Bars are populated by continuous aggregates")

print("\n" + "=" * 80)
print("EXAMINATION COMPLETE")
print("=" * 80)

cursor.close()
conn.close()
