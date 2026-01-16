#!/usr/bin/env python3
"""Check all data in database - BARS vs HISTORY"""

import psycopg2

conn = psycopg2.connect(
    host='localhost',
    port=5432,
    database='KLDA-HFT_Database',
    user='postgres',
    password='MyKldaTechnologies2025!'
)
cursor = conn.cursor()

print('=' * 80)
print('BARS TABLES - Historical OHLCV Data (16+ years)')
print('=' * 80)

assets = ['TSLA', 'NVDA', 'AAPL', 'MSFT', 'ORCL', 'PLTR', 'AMD']

for asset in assets:
    table = f'{asset.lower()}_bars'
    cursor.execute(f"""
        SELECT
            MIN(time) as earliest,
            MAX(time) as latest,
            COUNT(*) as total_bars
        FROM {table};
    """)
    row = cursor.fetchone()
    if row and row[2] > 0:
        earliest = str(row[0])[:10]
        latest = str(row[1])[:10]
        years = int(latest[:4]) - int(earliest[:4])
        print(f'{asset:8} | {earliest} to {latest} | {years:2} years | {row[2]:,} bars')

print()
print('=' * 80)
print('HISTORY TABLES - Live Tick Data (captured since today)')
print('=' * 80)

for asset in assets:
    table = f'{asset.lower()}_history'
    cursor.execute(f"""
        SELECT
            MIN(time) as earliest,
            MAX(time) as latest,
            COUNT(*) as total_ticks
        FROM {table};
    """)
    row = cursor.fetchone()
    if row and row[2] > 0:
        earliest = str(row[0])[:19]
        latest = str(row[1])[:19]
        print(f'{asset:8} | {earliest} to {latest} | {row[2]:,} ticks')
    else:
        print(f'{asset:8} | NO DATA YET')

conn.close()
