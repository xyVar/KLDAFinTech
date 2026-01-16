#!/usr/bin/env python3
"""Add volume column to all tables"""

import psycopg2

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'KLDA-HFT_Database',
    'user': 'postgres',
    'password': 'MyKldaTechnologies2025!'
}

def main():
    print("Connecting to database...")
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # Add volume to CURRENT table
    print("Adding volume to CURRENT table...")
    cursor.execute("ALTER TABLE current ADD COLUMN IF NOT EXISTS volume BIGINT DEFAULT 0;")
    conn.commit()
    print("[OK] CURRENT table updated")

    # Add volume to all 17 HISTORY tables
    print("\nAdding volume to HISTORY tables...")
    assets = ['tsla', 'nvda', 'pltr', 'amd', 'avgo', 'meta', 'aapl', 'msft',
              'orcl', 'amzn', 'csco', 'goog', 'intc', 'vix', 'nas100',
              'natgas', 'spotcrude']

    for asset in assets:
        table_name = f"{asset}_history"
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS volume BIGINT DEFAULT 0;")
        conn.commit()
        print(f"[OK] {asset.upper()} history updated")

    # Show CURRENT table structure
    print("\nCURRENT table columns:")
    cursor.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'current'
        ORDER BY ordinal_position;
    """)
    for row in cursor.fetchall():
        print(f"  - {row[0]}: {row[1]}")

    print("\n[SUCCESS] Volume column added to all tables!")
    conn.close()

if __name__ == "__main__":
    main()
