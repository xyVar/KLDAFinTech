#!/usr/bin/env python3
"""
Add order flow columns to database
Separates buy-side and sell-side volume for market microstructure analysis
"""

import psycopg2

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'KLDA-HFT_Database',
    'user': 'postgres',
    'password': 'MyKldaTechnologies2025!'
}

ASSETS = ['tsla', 'nvda', 'pltr', 'amd', 'avgo', 'meta', 'aapl', 'msft',
          'orcl', 'amzn', 'csco', 'goog', 'intc', 'vix', 'nas100',
          'natgas', 'spotcrude']

def main():
    print("[START] Adding order flow columns for Renaissance-style analysis")
    print("=" * 60)

    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # Add columns to CURRENT table
    print("\n[CURRENT TABLE]")
    cursor.execute("""
        ALTER TABLE current
        ADD COLUMN IF NOT EXISTS buy_volume BIGINT DEFAULT 0,
        ADD COLUMN IF NOT EXISTS sell_volume BIGINT DEFAULT 0,
        ADD COLUMN IF NOT EXISTS flags INTEGER DEFAULT 0;
    """)
    conn.commit()
    print("[OK] Added: buy_volume, sell_volume, flags")

    # Add columns to all 17 HISTORY tables
    print("\n[HISTORY TABLES]")
    for asset in ASSETS:
        table_name = f"{asset}_history"
        cursor.execute(f"""
            ALTER TABLE {table_name}
            ADD COLUMN IF NOT EXISTS buy_volume BIGINT DEFAULT 0,
            ADD COLUMN IF NOT EXISTS sell_volume BIGINT DEFAULT 0,
            ADD COLUMN IF NOT EXISTS flags INTEGER DEFAULT 0;
        """)
        conn.commit()
        print(f"[OK] {asset.upper()}_history updated")

    # Show structure
    print("\n[VERIFY] CURRENT table columns:")
    cursor.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'current'
        ORDER BY ordinal_position;
    """)
    for row in cursor.fetchall():
        print(f"  - {row[0]}: {row[1]}")

    print("\n[SUCCESS] Order flow columns added!")
    print("\nNow you can track:")
    print("  - Buy-side volume (aggressive buyers)")
    print("  - Sell-side volume (aggressive sellers)")
    print("  - Order flow imbalance (buy - sell)")
    print("  - Market microstructure signals")

    conn.close()

if __name__ == "__main__":
    main()
