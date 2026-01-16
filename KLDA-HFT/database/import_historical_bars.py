#!/usr/bin/env python3
"""
KLDA-HFT Historical Bar Data Import Script
Imports 575,816+ bars from CSV files into PostgreSQL
"""

import psycopg2
import csv
import os
from datetime import datetime
from pathlib import Path

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'KLDA-HFT_Database',
    'user': 'postgres',
    'password': 'MyKldaTechnologies2025!'
}

# Asset folder name to database table mapping
ASSET_MAPPING = {
    'TSLA.US-24': 'tsla',
    'NVDA.US-24': 'nvda',
    'PLTR.US-24': 'pltr',
    'AMD.US-24': 'amd',
    'AVGO.US-24': 'avgo',
    'META.US-24': 'meta',
    'AAPL.US-24': 'aapl',
    'MSFT.US-24': 'msft',
    'ORCL.US-24': 'orcl',
    'AMZN.US-24': 'amzn',
    'CSCO.US-24': 'csco',
    'GOOG.US-24': 'goog',
    'INTC.US-24': 'intc',
    'VIX': 'vix',
    'NAS100': 'nas100',
    'NatGas': 'natgas',
    'SpotCrude': 'spotcrude'
}

TIMEFRAMES = ['M1', 'M5', 'M15', 'M30', 'H1', 'H4', 'D1', 'W1', 'MN']

def parse_mt5_datetime(dt_str):
    """Convert MT5 datetime string to Python datetime"""
    # Format: "2025.12.23 00:20"
    return datetime.strptime(dt_str, '%Y.%m.%d %H:%M')

def import_csv_file(cursor, csv_path, asset_table, timeframe):
    """Import single CSV file into database"""
    bars_imported = 0
    bars_skipped = 0

    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)

        # Prepare batch insert
        insert_sql = f"""
            INSERT INTO {asset_table}_bars (time, timeframe, open, high, low, close, volume, spread)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (time, timeframe) DO NOTHING;
        """

        batch = []
        for row in reader:
            try:
                time = parse_mt5_datetime(row['DateTime'])
                open_price = float(row['Open'])
                high_price = float(row['High'])
                low_price = float(row['Low'])
                close_price = float(row['Close'])
                volume = int(row['Volume'])
                spread = int(row['Spread'])

                batch.append((time, timeframe, open_price, high_price, low_price,
                            close_price, volume, spread))

                # Batch insert every 1000 rows
                if len(batch) >= 1000:
                    cursor.executemany(insert_sql, batch)
                    bars_imported += len(batch)
                    batch = []

            except Exception as e:
                bars_skipped += 1
                continue

        # Insert remaining rows
        if batch:
            cursor.executemany(insert_sql, batch)
            bars_imported += len(batch)

    return bars_imported, bars_skipped

def main():
    print("[START] KLDA-HFT Historical Bar Import")
    print("=" * 60)

    data_dir = Path(r'C:\Users\PC\Desktop\KLDAFinTech\data\raw')

    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    total_bars = 0
    total_skipped = 0
    files_processed = 0

    # Iterate through each asset folder
    for folder_name, asset_name in ASSET_MAPPING.items():
        asset_dir = data_dir / folder_name

        if not asset_dir.exists():
            print(f"[SKIP] {folder_name} - Directory not found")
            continue

        print(f"\n[ASSET] {asset_name.upper()}")
        print("-" * 60)

        asset_bars = 0

        # Import each timeframe CSV
        for timeframe in TIMEFRAMES:
            csv_file = asset_dir / f"{timeframe}.csv"

            if not csv_file.exists():
                continue

            try:
                bars_imported, bars_skipped = import_csv_file(
                    cursor, csv_file, asset_name, timeframe
                )

                conn.commit()

                print(f"  [{timeframe:>4}] {bars_imported:>6} bars imported, "
                      f"{bars_skipped:>3} skipped")

                total_bars += bars_imported
                total_skipped += bars_skipped
                asset_bars += bars_imported
                files_processed += 1

            except Exception as e:
                print(f"  [ERROR] {timeframe} - {e}")
                conn.rollback()

        print(f"  [TOTAL] {asset_bars} bars for {asset_name.upper()}")

    # Summary
    print("\n" + "=" * 60)
    print(f"[SUMMARY] Import Complete")
    print(f"  Files processed: {files_processed}")
    print(f"  Bars imported: {total_bars:,}")
    print(f"  Bars skipped: {total_skipped:,}")
    print("=" * 60)

    # Verify data
    print("\n[VERIFY] Checking data in database...")
    for asset in ['tsla', 'nvda', 'pltr', 'aapl', 'orcl']:
        cursor.execute(f"SELECT COUNT(*) FROM {asset}_bars;")
        count = cursor.fetchone()[0]
        print(f"  {asset.upper()}_bars: {count:,} rows")

    print("\n[SUCCESS] Historical data import complete!")
    conn.close()

if __name__ == "__main__":
    main()
