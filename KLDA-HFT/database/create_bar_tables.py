#!/usr/bin/env python3
"""
KLDA-HFT Bar Tables Creation Script
Creates 17 bar tables to store historical OHLCV data
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
    print("Connecting to database...")
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    print("\n[CREATE] Creating bar tables for 17 assets...")

    for asset in ASSETS:
        table_name = f"{asset}_bars"

        # Create table
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            time TIMESTAMPTZ(6) NOT NULL,
            timeframe VARCHAR(5) NOT NULL,
            open DECIMAL(18,8) NOT NULL,
            high DECIMAL(18,8) NOT NULL,
            low DECIMAL(18,8) NOT NULL,
            close DECIMAL(18,8) NOT NULL,
            volume BIGINT DEFAULT 0,
            spread INTEGER DEFAULT 0,
            PRIMARY KEY (time, timeframe)
        );
        """

        cursor.execute(create_table_sql)
        conn.commit()
        print(f"[OK] Created {table_name}")

        # Convert to hypertable
        try:
            cursor.execute(f"""
                SELECT create_hypertable('{table_name}', 'time',
                                        if_not_exists => TRUE);
            """)
            conn.commit()
            print(f"[OK] Converted {table_name} to TimescaleDB hypertable")
        except Exception as e:
            if "already a hypertable" in str(e):
                print(f"[OK] {table_name} already a hypertable")
            else:
                print(f"[ERROR] Hypertable conversion failed: {e}")
                conn.rollback()

    # Show table structure
    print("\n[VERIFY] Checking tsla_bars structure:")
    cursor.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'tsla_bars'
        ORDER BY ordinal_position;
    """)

    for row in cursor.fetchall():
        print(f"  - {row[0]}: {row[1]}")

    print("\n[SUCCESS] All 17 bar tables created!")
    conn.close()

if __name__ == "__main__":
    main()
