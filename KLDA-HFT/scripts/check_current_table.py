#!/usr/bin/env python3
"""Check CURRENT table contents"""

import psycopg2

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'KLDA-HFT_Database',
    'user': 'postgres',
    'password': 'MyKldaTechnologies2025!'
}

conn = psycopg2.connect(**DB_CONFIG)
cursor = conn.cursor()

print("=" * 60)
print("CURRENT TABLE CONTENTS")
print("=" * 60)

cursor.execute("""
    SELECT symbol_id, symbol, mt5_symbol, bid, ask
    FROM current
    ORDER BY symbol_id;
""")

print("\nID | Symbol     | MT5 Symbol      | Bid      | Ask")
print("-" * 60)

rows = cursor.fetchall()
if rows:
    for row in rows:
        symbol_id, symbol, mt5_symbol, bid, ask = row
        mt5_sym = mt5_symbol if mt5_symbol else "NULL"
        sym = symbol if symbol else "NULL"
        print(f"{symbol_id:2} | {sym:10} | {mt5_sym:15} | {bid:8.2f} | {ask:8.2f}")
else:
    print("[EMPTY] No rows in CURRENT table!")

print("\n" + "=" * 60)
conn.close()
