#!/usr/bin/env python3
"""
KLDA-HFT Bars Backfill - 13 Stocks
Pulls OHLCV bars from MT5 into per-symbol _bars tables
Tries .US-24 suffix first, then plain name
"""

import MetaTrader5 as mt5
import psycopg2
from psycopg2.extras import execute_batch
from datetime import datetime

DB_CONFIG = {
    'host': 'localhost', 'port': 5432,
    'database': 'KLDA-HFT_Database',
    'user': 'postgres', 'password': 'MyKldaTechnologies2025!'
}

# table_prefix -> MT5 symbol candidates (try in order)
STOCKS = {
    'aapl':  ['AAPL.US-24', 'AAPL.US', 'AAPL'],
    'amd':   ['AMD.US-24',  'AMD.US',  'AMD'],
    'amzn':  ['AMZN.US-24', 'AMZN.US', 'AMZN'],
    'avgo':  ['AVGO.US-24', 'AVGO.US', 'AVGO'],
    'csco':  ['CSCO.US-24', 'CSCO.US', 'CSCO'],
    'goog':  ['GOOG.US-24', 'GOOGL.US-24', 'GOOG.US', 'GOOG'],
    'intc':  ['INTC.US-24', 'INTC.US', 'INTC'],
    'meta':  ['META.US-24', 'META.US', 'META'],
    'msft':  ['MSFT.US-24', 'MSFT.US', 'MSFT'],
    'nvda':  ['NVDA.US-24', 'NVDA.US', 'NVDA'],
    'orcl':  ['ORCL.US-24', 'ORCL.US', 'ORCL'],
    'pltr':  ['PLTR.US-24', 'PLTR.US', 'PLTR'],
    'tsla':  ['TSLA.US-24', 'TSLA.US', 'TSLA'],
}

TIMEFRAMES = {
    'M1':  mt5.TIMEFRAME_M1,
    'M5':  mt5.TIMEFRAME_M5,
    'M15': mt5.TIMEFRAME_M15,
    'H1':  mt5.TIMEFRAME_H1,
    'H4':  mt5.TIMEFRAME_H4,
    'D1':  mt5.TIMEFRAME_D1,
}

def find_symbol(candidates):
    for sym in candidates:
        info = mt5.symbol_info(sym)
        if info is not None:
            if not info.visible:
                mt5.symbol_select(sym, True)
            return sym
    return None

def backfill_symbol(conn, mt5_symbol, prefix):
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
            INSERT INTO {prefix}_bars
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
    print("=" * 55)
    print("KLDA-HFT Bars Backfill - 13 Stocks")
    print("=" * 55)

    if not mt5.initialize():
        print(f"[ERROR] MT5 failed: {mt5.last_error()}")
        return

    account = mt5.account_info()
    print(f"Account: {account.login} | {account.server}\n")

    conn = psycopg2.connect(**DB_CONFIG)
    grand_total = 0
    skipped = []

    for i, (prefix, candidates) in enumerate(STOCKS.items(), 1):
        print(f"[{i:2d}/13] {prefix}_bars")

        sym = find_symbol(candidates)
        if sym is None:
            print(f"  [SKIP] Not found: {candidates}")
            skipped.append(prefix)
            continue

        print(f"  MT5 symbol: {sym}")
        bars = backfill_symbol(conn, sym, prefix)
        grand_total += bars
        print(f"  Total: {bars:,} bars\n")

    conn.close()
    mt5.shutdown()

    print("=" * 55)
    print("COMPLETE")
    print(f"  Total bars: {grand_total:,}")
    if skipped:
        print(f"  Skipped:    {skipped}")
    print("=" * 55)

if __name__ == '__main__':
    main()
