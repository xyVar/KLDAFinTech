#!/usr/bin/env python3
"""
KLDA-HFT Database Setup Script
Connects to PostgreSQL and creates all tables automatically
"""

import psycopg2
from psycopg2 import sql

# Database connection parameters
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'KLDA-HFT_Database',
    'user': 'postgres',
    'password': 'MyKldaTechnologies2025!'
}

def connect_db():
    """Connect to PostgreSQL database"""
    print("Connecting to database...")
    conn = psycopg2.connect(**DB_CONFIG)
    print("[OK] Connected successfully!")
    return conn

def execute_sql(conn, sql_statement, description):
    """Execute SQL and print result"""
    try:
        cursor = conn.cursor()
        cursor.execute(sql_statement)
        conn.commit()
        print(f"[OK] {description}")
        return True
    except Exception as e:
        print(f"[ERROR] {description} - Error: {e}")
        conn.rollback()
        return False

def main():
    print("="*60)
    print("KLDA-HFT DATABASE SETUP")
    print("="*60)

    # Connect
    conn = connect_db()

    # 1. Enable TimescaleDB
    print("\n[1/4] Installing TimescaleDB extension...")
    execute_sql(conn, "CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;",
                "TimescaleDB extension enabled")

    # 2. Create CURRENT table
    print("\n[2/4] Creating CURRENT table (17 assets)...")
    execute_sql(conn, """
        CREATE TABLE IF NOT EXISTS current (
            symbol_id INTEGER PRIMARY KEY,
            symbol VARCHAR(20) NOT NULL UNIQUE,
            mt5_symbol VARCHAR(50),
            bid DECIMAL(18,8) NOT NULL DEFAULT 0,
            ask DECIMAL(18,8) NOT NULL DEFAULT 0,
            spread DECIMAL(10,6) DEFAULT 0,
            last_updated TIMESTAMPTZ(6) NOT NULL DEFAULT NOW()
        );
    """, "CURRENT table created")

    # Insert 17 assets
    execute_sql(conn, """
        INSERT INTO current (symbol_id, symbol, mt5_symbol) VALUES
        (1, 'TSLA', 'TSLA.US-24'),
        (2, 'NVDA', 'NVDA.US-24'),
        (3, 'PLTR', 'PLTR.US-24'),
        (4, 'AMD', 'AMD.US-24'),
        (5, 'AVGO', 'AVGO.US-24'),
        (6, 'META', 'META.US-24'),
        (7, 'AAPL', 'AAPL.US-24'),
        (8, 'MSFT', 'MSFT.US-24'),
        (9, 'ORCL', 'ORCL.US-24'),
        (10, 'AMZN', 'AMZN.US-24'),
        (11, 'CSCO', 'CSCO.US-24'),
        (12, 'GOOG', 'GOOG.US-24'),
        (13, 'INTC', 'INTC.US-24'),
        (14, 'VIX', 'VIX'),
        (15, 'NAS100', 'NAS100'),
        (16, 'NatGas', 'NatGas'),
        (17, 'SpotCrude', 'SpotCrude')
        ON CONFLICT (symbol_id) DO NOTHING;
    """, "17 assets inserted")

    # 3. Create 17 history tables
    print("\n[3/4] Creating 17 HISTORY tables...")

    assets = ['tsla', 'nvda', 'pltr', 'amd', 'avgo', 'meta', 'aapl', 'msft',
              'orcl', 'amzn', 'csco', 'goog', 'intc', 'vix', 'nas100',
              'natgas', 'spotcrude']

    for asset in assets:
        table_name = f"{asset}_history"
        execute_sql(conn, f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                time TIMESTAMPTZ(6) NOT NULL,
                bid DECIMAL(18,8) NOT NULL,
                ask DECIMAL(18,8) NOT NULL,
                spread DECIMAL(10,6),
                PRIMARY KEY (time)
            );
        """, f"{asset.upper()} history table created")

    # 4. Convert to hypertables
    print("\n[4/4] Converting to TimescaleDB hypertables...")

    for asset in assets:
        table_name = f"{asset}_history"
        execute_sql(conn,
                   f"SELECT create_hypertable('{table_name}', 'time', if_not_exists => TRUE);",
                   f"{asset.upper()} converted to hypertable")

    # Verification
    print("\n" + "="*60)
    print("VERIFICATION")
    print("="*60)

    cursor = conn.cursor()

    # Check current table
    cursor.execute("SELECT COUNT(*) FROM current;")
    asset_count = cursor.fetchone()[0]
    print(f"[OK] CURRENT table: {asset_count} assets")

    # Check history tables
    cursor.execute("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name LIKE '%_history'
        ORDER BY table_name;
    """)
    history_tables = cursor.fetchall()
    print(f"[OK] HISTORY tables: {len(history_tables)} tables created")

    for table in history_tables:
        print(f"  - {table[0]}")

    print("\n" + "="*60)
    print("DATABASE SETUP COMPLETE!")
    print("="*60)
    print("\nArchitecture:")
    print("  Broker → CURRENT (17 rows) → HISTORY (17 tables)")
    print("\nReady for tick data ingestion.")

    conn.close()

if __name__ == "__main__":
    main()
