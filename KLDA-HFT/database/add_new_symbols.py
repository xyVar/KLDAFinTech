#!/usr/bin/env python3
"""
Add 47 new symbols to KLDA-HFT Database
Creates _bars and _history tables for each new symbol
Updates the current table with all 51 symbols
"""

import psycopg2

DB_CONFIG = {
    'host': 'localhost', 'port': 5432,
    'database': 'KLDA-HFT_Database',
    'user': 'postgres', 'password': 'MyKldaTechnologies2025!'
}

# New symbols to add (existing 17 stocks already have tables)
# Symbol name → table prefix (lowercase, no special chars)
NEW_SYMBOLS = {
    # Commodities (SpotCrude and NatGas already exist)
    'SpotBrent':  'spotbrent',
    'XAUUSD':     'xauusd',
    'XAGUSD':     'xagusd',
    'XPTUSD':     'xptusd',
    'XPDUSD':     'xpdusd',
    'Copper':     'copper',
    'Gasoline':   'gasoline',
    'Corn':       'corn',
    'Wheat':      'wheat',
    'Soybeans':   'soybeans',
    'Coffee':     'coffee',
    'Cotton':     'cotton',
    'Sugar':      'sugar',
    # Indices (NAS100 and VIX already exist)
    'US500':      'us500',
    'US30':       'us30',
    'UK100':      'uk100',
    'GER40':      'ger40',
    'JPN225':     'jpn225',
    'FRA40':      'fra40',
    'AUS200':     'aus200',
    'HK50':       'hk50',
    'CN50':       'cn50',
    'EUSTX50':    'eustx50',
    'USDX':       'usdx',
    'EURX':       'eurx',
    'JPYX':       'jpyx',
    'US2000':     'us2000',
    # Forex (all new)
    'EURUSD':     'eurusd',
    'GBPUSD':     'gbpusd',
    'USDJPY':     'usdjpy',
    'USDCAD':     'usdcad',
    'AUDUSD':     'audusd',
    'NZDUSD':     'nzdusd',
    'USDCHF':     'usdchf',
    'USDCNH':     'usdcnh',
    'EURGBP':     'eurgbp',
    'EURJPY':     'eurjpy',
    'GBPJPY':     'gbpjpy',
    'AUDJPY':     'audjpy',
    'EURAUD':     'euraud',
    'GBPAUD':     'gbpaud',
    'CADJPY':     'cadjpy',
    'CHFJPY':     'chfjpy',
    'EURCAD':     'eurcad',
    'GBPCAD':     'gbpcad',
    'USDMXN':     'usdmxn',
    'USDZAR':     'usdzar',
}

def create_tables(conn, symbol, prefix):
    cur = conn.cursor()

    # _bars table (OHLCV - same schema as existing)
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {prefix}_bars (
            time      TIMESTAMPTZ(6) NOT NULL,
            timeframe VARCHAR(5)     NOT NULL,
            open      DECIMAL(18,8)  NOT NULL,
            high      DECIMAL(18,8)  NOT NULL,
            low       DECIMAL(18,8)  NOT NULL,
            close     DECIMAL(18,8)  NOT NULL,
            volume    BIGINT         DEFAULT 0,
            spread    INTEGER        DEFAULT 0,
            PRIMARY KEY (time, timeframe)
        )
    """)

    # _history table (tick data - same schema as existing)
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {prefix}_history (
            time   TIMESTAMPTZ(6) NOT NULL,
            bid    DECIMAL(18,8)  NOT NULL,
            ask    DECIMAL(18,8)  NOT NULL,
            spread DECIMAL(10,6),
            PRIMARY KEY (time)
        )
    """)

    conn.commit()
    cur.close()

def update_current_table(conn):
    cur = conn.cursor()

    # Check current table columns
    cur.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = 'current' ORDER BY ordinal_position
    """)
    cols = [r[0] for r in cur.fetchall()]

    for symbol in NEW_SYMBOLS:
        if 'symbol_id' in cols:
            cur.execute("SELECT MAX(symbol_id) FROM current")
            max_id = cur.fetchone()[0] or 17
            cur.execute(
                "INSERT INTO current (symbol_id, symbol, mt5_symbol) VALUES (%s, %s, %s) "
                "ON CONFLICT (symbol) DO NOTHING",
                (max_id + 1, symbol, symbol)
            )
        else:
            cur.execute(
                "INSERT INTO current (symbol, bid, ask, spread, last_updated) "
                "VALUES (%s, 0, 0, 0, NOW()) ON CONFLICT (symbol) DO NOTHING",
                (symbol,)
            )

    conn.commit()
    cur.close()

def main():
    print("=" * 55)
    print("KLDA-HFT: Adding 47 New Symbol Tables")
    print("=" * 55)

    conn = psycopg2.connect(**DB_CONFIG)

    created = 0
    for symbol, prefix in NEW_SYMBOLS.items():
        create_tables(conn, symbol, prefix)
        print(f"  [OK] {prefix}_bars + {prefix}_history")
        created += 1

    print(f"\n[OK] Created {created * 2} tables ({created} bars + {created} history)")

    print("\n[OK] Updating current table...")
    update_current_table(conn)
    print("[OK] All symbols added to current table")

    # Show final table count
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
    total = cur.fetchone()[0]
    print(f"\n[DB] Total tables in database: {total}")

    cur.execute("SELECT COUNT(*) FROM current")
    symbols = cur.fetchone()[0]
    print(f"[DB] Total symbols in current: {symbols}")
    cur.close()
    conn.close()

    print("\nDone.")

if __name__ == '__main__':
    main()
