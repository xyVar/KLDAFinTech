#!/usr/bin/env python3
"""
KLDA-HFT Bars Backfill (per-symbol tables)
Pulls all available OHLCV bars from MT5 for 51 symbols
Writes into symbol_bars tables (e.g. xauusd_bars, eurusd_bars)
Timeframes: M1, M5, M15, H1, H4, D1
"""

import MetaTrader5 as mt5
import psycopg2
from psycopg2.extras import execute_batch
from datetime import datetime
import time

DB_CONFIG = {
    'host': 'localhost', 'port': 5432,
    'database': 'KLDA-HFT_Database',
    'user': 'postgres', 'password': 'MyKldaTechnologies2025!'
}

# symbol → table prefix mapping
SYMBOLS = {
    # Commodities
    'SpotCrude': 'spotcrude',
    'SpotBrent':  'spotbrent',
    'NatGas':    'natgas',
    'XAUUSD':    'xauusd',
    'XAGUSD':    'xagusd',
    'XPTUSD':    'xptusd',
    'XPDUSD':    'xpdusd',
    'Copper':    'copper',
    'Gasoline':  'gasoline',
    'Corn':      'corn',
    'Wheat':     'wheat',
    'Soybeans':  'soybeans',
    'Coffee':    'coffee',
    'Cotton':    'cotton',
    'Sugar':     'sugar',
    # Indices
    'NAS100':    'nas100',
    'US500':     'us500',
    'US30':      'us30',
    'UK100':     'uk100',
    'GER40':     'ger40',
    'JPN225':    'jpn225',
    'FRA40':     'fra40',
    'AUS200':    'aus200',
    'HK50':      'hk50',
    'CN50':      'cn50',
    'EUSTX50':   'eustx50',
    'VIX':       'vix',
    'USDX':      'usdx',
    'EURX':      'eurx',
    'JPYX':      'jpyx',
    'US2000':    'us2000',
    # Forex
    'EURUSD':    'eurusd',
    'GBPUSD':    'gbpusd',
    'USDJPY':    'usdjpy',
    'USDCAD':    'usdcad',
    'AUDUSD':    'audusd',
    'NZDUSD':    'nzdusd',
    'USDCHF':    'usdchf',
    'USDCNH':    'usdcnh',
    'EURGBP':    'eurgbp',
    'EURJPY':    'eurjpy',
    'GBPJPY':    'gbpjpy',
    'AUDJPY':    'audjpy',
    'EURAUD':    'euraud',
    'GBPAUD':    'gbpaud',
    'CADJPY':    'cadjpy',
    'CHFJPY':    'chfjpy',
    'EURCAD':    'eurcad',
    'GBPCAD':    'gbpcad',
    'USDMXN':    'usdmxn',
    'USDZAR':    'usdzar',
}

TIMEFRAMES = {
    'M1':  mt5.TIMEFRAME_M1,
    'M5':  mt5.TIMEFRAME_M5,
    'M15': mt5.TIMEFRAME_M15,
    'H1':  mt5.TIMEFRAME_H1,
    'H4':  mt5.TIMEFRAME_H4,
    'D1':  mt5.TIMEFRAME_D1,
}

def backfill_symbol(conn, mt5_symbol, table_prefix):
    cur = conn.cursor()
    total = 0

    for tf_name, tf_const in TIMEFRAMES.items():
        rates = mt5.copy_rates_from_pos(mt5_symbol, tf_const, 0, 99999)
        if rates is None or len(rates) == 0:
            print(f"    {tf_name:4s}: no data")
            continue

        rows = [(
            datetime.fromtimestamp(r['time']),
            tf_name,
            float(r['open']), float(r['high']),
            float(r['low']),  float(r['close']),
            int(r['tick_volume']), int(r['spread'])
        ) for r in rates]

        execute_batch(cur, f"""
            INSERT INTO {table_prefix}_bars
                (time, timeframe, open, high, low, close, volume, spread)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (time, timeframe) DO NOTHING
        """, rows)
        conn.commit()
        total += len(rows)
        first = datetime.fromtimestamp(rates[0]['time']).strftime('%Y-%m-%d')
        print(f"    {tf_name:4s}: {len(rows):6,} bars from {first}")

    cur.close()
    return total

def main():
    print("=" * 60)
    print("KLDA-HFT Bars Backfill — Per-Symbol Tables")
    print("=" * 60)

    if not mt5.initialize():
        print(f"[ERROR] MT5 failed: {mt5.last_error()}")
        return

    account = mt5.account_info()
    print(f"Account: {account.login} | {account.server}\n")

    conn = psycopg2.connect(**DB_CONFIG)
    grand_total = 0
    failed = []

    symbols = list(SYMBOLS.items())
    for i, (sym, prefix) in enumerate(symbols, 1):
        print(f"[{i:2d}/{len(symbols)}] {sym} -> {prefix}_bars")

        # Subscribe to Market Watch
        info = mt5.symbol_info(sym)
        if info is None:
            print(f"  [SKIP] Symbol not found in MT5")
            failed.append(sym)
            continue
        if not info.visible:
            mt5.symbol_select(sym, True)

        bars = backfill_symbol(conn, sym, prefix)
        grand_total += bars
        print(f"  Total: {bars:,} bars\n")

    conn.close()
    mt5.shutdown()

    print("=" * 60)
    print("BACKFILL COMPLETE")
    print(f"  Total bars inserted: {grand_total:,}")
    if failed:
        print(f"  Skipped ({len(failed)}): {failed}")
    print("=" * 60)

if __name__ == '__main__':
    main()
