#!/usr/bin/env python3
"""
KLDA-HFT Historical Backfill
Pulls ALL historical data (ticks + bars) for 51 symbols from MT5
Stores in PostgreSQL ticks + bars tables
"""

import MetaTrader5 as mt5
import psycopg2
from psycopg2.extras import execute_batch
from datetime import datetime, timedelta
import time

DB_CONFIG = {
    'host': 'localhost', 'port': 5432,
    'database': 'KLDA-HFT_Database',
    'user': 'postgres', 'password': 'MyKldaTechnologies2025!'
}

SYMBOLS = {
    'commodities': [
        'SpotCrude','SpotBrent','NatGas','XAUUSD','XAGUSD',
        'XPTUSD','XPDUSD','Copper','Gasoline','Corn',
        'Wheat','Soybeans','Coffee','Cotton','Sugar'
    ],
    'indices': [
        'NAS100','US500','US30','UK100','GER40',
        'JPN225','FRA40','AUS200','HK50','CN50',
        'EUSTX50','VIX','USDX','EURX','JPYX','US2000'
    ],
    'forex': [
        'EURUSD','GBPUSD','USDJPY','USDCAD','AUDUSD',
        'NZDUSD','USDCHF','USDCNH','EURGBP','EURJPY',
        'GBPJPY','AUDJPY','EURAUD','GBPAUD','CADJPY',
        'CHFJPY','EURCAD','GBPCAD','USDMXN','USDZAR'
    ]
}

ALL_SYMBOLS = SYMBOLS['commodities'] + SYMBOLS['indices'] + SYMBOLS['forex']

TIMEFRAMES = {
    'M1':  mt5.TIMEFRAME_M1,
    'M5':  mt5.TIMEFRAME_M5,
    'M15': mt5.TIMEFRAME_M15,
    'H1':  mt5.TIMEFRAME_H1,
    'H4':  mt5.TIMEFRAME_H4,
    'D1':  mt5.TIMEFRAME_D1,
}

def get_db():
    return psycopg2.connect(**DB_CONFIG)

def setup_bars_table(conn):
    """Create bars table if not exists"""
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS bars (
            time      TIMESTAMPTZ(0) NOT NULL,
            symbol    VARCHAR(30)    NOT NULL,
            timeframe VARCHAR(5)     NOT NULL,
            open      DECIMAL(18,8)  NOT NULL,
            high      DECIMAL(18,8)  NOT NULL,
            low       DECIMAL(18,8)  NOT NULL,
            close     DECIMAL(18,8)  NOT NULL,
            volume    BIGINT         DEFAULT 0,
            spread    INTEGER        DEFAULT 0,
            PRIMARY KEY (time, symbol, timeframe)
        )
    """)
    # Index for fast symbol+timeframe queries
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_bars_symbol_tf
        ON bars (symbol, timeframe, time DESC)
    """)
    conn.commit()
    cur.close()
    print("[OK] bars table ready")

def subscribe_all(symbols):
    """Subscribe all symbols to Market Watch"""
    ok, fail = [], []
    for sym in symbols:
        info = mt5.symbol_info(sym)
        if info is None:
            fail.append(sym)
            continue
        if not info.visible:
            mt5.symbol_select(sym, True)
        ok.append(sym)
    print(f"[SYMBOLS] Subscribed: {len(ok)} | Not found: {len(fail)}")
    if fail:
        print(f"  Missing: {fail}")
    return ok

def backfill_bars(conn, symbol):
    """Pull all historical OHLCV bars for all timeframes"""
    cur = conn.cursor()
    total = 0

    for tf_name, tf_const in TIMEFRAMES.items():
        # Pull maximum bars (99999 = MT5 max)
        rates = mt5.copy_rates_from_pos(symbol, tf_const, 0, 99999)
        if rates is None or len(rates) == 0:
            continue

        rows = []
        for r in rates:
            rows.append((
                datetime.fromtimestamp(r['time']),
                symbol, tf_name,
                float(r['open']), float(r['high']),
                float(r['low']), float(r['close']),
                int(r['tick_volume']), int(r['spread'])
            ))

        execute_batch(cur, """
            INSERT INTO bars (time, symbol, timeframe, open, high, low, close, volume, spread)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (time, symbol, timeframe) DO NOTHING
        """, rows)

        conn.commit()
        total += len(rows)
        first = datetime.fromtimestamp(rates[0]['time']).strftime('%Y-%m-%d')
        print(f"  {tf_name:4s}: {len(rows):6,} bars from {first}")

    cur.close()
    return total

def backfill_ticks(conn, symbol):
    """Pull ALL historical ticks going back as far as MT5 has"""
    cur = conn.cursor()
    total = 0

    # Start 3 years back, pull forward in 1-day chunks
    date_from = datetime.now() - timedelta(days=365 * 3)
    date_to   = datetime.now()
    chunk     = timedelta(days=1)

    current = date_from
    while current < date_to:
        chunk_end = min(current + chunk, date_to)

        ticks_raw = mt5.copy_ticks_range(symbol, current, chunk_end, mt5.COPY_TICKS_ALL)

        if ticks_raw is not None and len(ticks_raw) > 0:
            rows = []
            for t in ticks_raw:
                dt = datetime.fromtimestamp(t['time'])
                us = t['time_msc'] % 1000 * 1000
                ts = dt.strftime('%Y-%m-%d %H:%M:%S') + f'.{us:06d}'
                flags = int(t['flags'])
                rows.append((
                    ts, symbol,
                    float(t['bid']), float(t['ask']),
                    0.0,
                    int(t['volume']),
                    int(t['volume']) if (flags & 32) else 0,
                    int(t['volume']) if (flags & 64) else 0,
                    flags
                ))

            execute_batch(cur, """
                INSERT INTO ticks (time, symbol, bid, ask, spread, volume, buy_volume, sell_volume, flags)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, rows)
            conn.commit()
            total += len(rows)

        current = chunk_end

    cur.close()
    return total

def main():
    print("=" * 60)
    print("KLDA-HFT Historical Backfill")
    print("=" * 60)

    if not mt5.initialize():
        print(f"[ERROR] MT5 failed: {mt5.last_error()}")
        return

    account = mt5.account_info()
    print(f"Account: {account.login} | {account.server}")

    conn = get_db()
    setup_bars_table(conn)

    symbols = subscribe_all(ALL_SYMBOLS)
    print(f"\nStarting backfill for {len(symbols)} symbols...\n")

    grand_total_bars  = 0
    grand_total_ticks = 0

    for i, symbol in enumerate(symbols, 1):
        print(f"[{i:2d}/{len(symbols)}] {symbol}")

        # BARS (deep history - up to 20 years)
        print(f"  Pulling bars...")
        bars = backfill_bars(conn, symbol)
        grand_total_bars += bars
        print(f"  Total bars: {bars:,}")

        # TICKS (last 3 years)
        print(f"  Pulling ticks (3 years)...")
        ticks = backfill_ticks(conn, symbol)
        grand_total_ticks += ticks
        print(f"  Total ticks: {ticks:,}")
        print()

    conn.close()
    mt5.shutdown()

    print("=" * 60)
    print("BACKFILL COMPLETE")
    print(f"  Total bars:  {grand_total_bars:,}")
    print(f"  Total ticks: {grand_total_ticks:,}")
    print("=" * 60)

if __name__ == '__main__':
    main()
