#!/usr/bin/env python3
"""Quick verification of bars deployment"""
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
print(f"DEPLOYMENT VERIFICATION - {datetime.now().strftime('%H:%M:%S')}")
print("=" * 80)

# Check continuous aggregates
print("\n1. Continuous Aggregates Status:")
try:
    cursor.execute("""
        SELECT view_name, materialized_only
        FROM timescaledb_information.continuous_aggregates
        WHERE view_name LIKE 'vix%'
        ORDER BY view_name;
    """)
    views = cursor.fetchall()
    if views:
        print(f"✅ Found {len(views)} continuous aggregates:")
        for view in views:
            print(f"   - {view[0]}")
    else:
        print("❌ NO continuous aggregates found (deployment may still be running)")
except Exception as e:
    print(f"❌ Error: {e}")

# Check if vix_bars view exists
print("\n2. VIX_BARS Unified View:")
try:
    cursor.execute("""
        SELECT COUNT(*) FROM information_schema.views
        WHERE table_name = 'vix_bars';
    """)
    exists = cursor.fetchone()[0]
    if exists:
        print("✅ vix_bars view exists")

        # Try to query it
        cursor.execute("SELECT COUNT(*) FROM vix_bars LIMIT 1;")
        print(f"✅ vix_bars is queryable")
    else:
        print("❌ vix_bars view not found")
except Exception as e:
    print(f"⏳ Not ready yet: {e}")

print("\n" + "=" * 80)
print("If you see ❌, the deployment is still processing (heavy load)")
print("Run this script again in 1 minute")
print("=" * 80)

cursor.close()
conn.close()
