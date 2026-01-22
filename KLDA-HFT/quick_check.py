#!/usr/bin/env python3
import psycopg2
import sys

try:
    conn = psycopg2.connect(
        host="localhost",
        database="KLDA-HFT_Database",
        user="postgres",
        password="MyKldaTechnologies2025!",
        connect_timeout=3
    )
    conn.set_session(readonly=True, autocommit=True)
    cursor = conn.cursor()

    # Quick check
    cursor.execute("SELECT COUNT(*) FROM timescaledb_information.continuous_aggregates WHERE view_name LIKE 'vix%';")
    count = cursor.fetchone()[0]

    if count > 0:
        print(f"DEPLOYED: {count} VIX continuous aggregates created")
        cursor.execute("SELECT view_name FROM timescaledb_information.continuous_aggregates WHERE view_name LIKE 'vix%';")
        for row in cursor.fetchall():
            print(f"  - {row[0]}")
    else:
        print("STILL DEPLOYING: No continuous aggregates yet")

    cursor.close()
    conn.close()

except Exception as e:
    print(f"DATABASE BUSY: {e}")
    print("Deployment still processing (heavy tick load)")
    sys.exit(1)
