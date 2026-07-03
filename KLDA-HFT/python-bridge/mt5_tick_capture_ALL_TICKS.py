#!/usr/bin/env python3
"""
KLDA-HFT MT5 Tick Capture - UNIVERSAL (all Market Watch symbols)
Captures ALL ticks from every symbol visible in MT5 Market Watch.
No hardcoded symbols - fully dynamic.
"""

import logging
import os
import sys
import threading
import time
import traceback
from datetime import datetime, timedelta, timezone
from logging.handlers import RotatingFileHandler

import MetaTrader5 as mt5
import psycopg2
from psycopg2.extras import execute_batch

# Rotating file log next to this script + mirror to stdout.
LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bridge.log')
log = logging.getLogger('klda.bridge')
log.setLevel(logging.INFO)
_fmt = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
_fh = RotatingFileHandler(LOG_PATH, maxBytes=10 * 1024 * 1024, backupCount=5, encoding='utf-8')
_fh.setFormatter(_fmt)
_sh = logging.StreamHandler(sys.stdout)
_sh.setFormatter(_fmt)
log.addHandler(_fh)
log.addHandler(_sh)

DB_CONFIG = {
    'host': '127.0.0.1',  # not 'localhost': ::1 is claimed by a WSL postgres relay with different creds
    'port': 5432,
    'database': 'KLDA-HFT_Database',
    'user': 'postgres',
    'password': 'MyKldaTechnologies2025!'
}

# Per-symbol last captured tick, keyed by tick['time_msc'] (epoch ms, timezone-agnostic).
last_msc = {}
stats = {'ticks': 0, 'errors': 0, 'symbols': 0, 'reconnects': 0}

# How far back to ask MT5 for ticks each poll. Must exceed the loop period (and any
# transient stall) so no ticks are skipped; the time_msc filter discards duplicates.
LOOKBACK_SEC = 10


def get_db():
    return psycopg2.connect(**DB_CONFIG)


def get_market_watch_symbols():
    """Get all symbols currently visible in MT5 Market Watch"""
    symbols = mt5.symbols_get()
    if not symbols:
        return []
    return [s.name for s in symbols if s.visible]


def init_symbol_timestamps(symbols):
    """Seed each symbol's last-seen tick (time_msc) so we only capture ticks from now on."""
    for symbol in symbols:
        tick = mt5.symbol_info_tick(symbol)
        last_msc[symbol] = tick.time_msc if tick else 0


def mt5_connect():
    """Initialize MT5. Returns True on success."""
    if not mt5.initialize():
        log.error(f"MT5 initialize failed: {mt5.last_error()}")
        return False
    acct = mt5.account_info()
    if acct:
        log.info(f"MT5 connected. Account={acct.login} Server={acct.server} Balance=${acct.balance:,.2f}")
    else:
        log.warning("MT5 initialized but account_info() returned None")
    return True


def mt5_reconnect():
    """Tear down and re-initialize MT5 after a drop. Re-seeds symbol timestamps."""
    stats['reconnects'] += 1
    log.warning(f"MT5 reconnect attempt #{stats['reconnects']}")
    try:
        mt5.shutdown()
    except Exception:
        pass
    time.sleep(2)
    if not mt5_connect():
        return None
    symbols = get_market_watch_symbols()
    stats['symbols'] = len(symbols)
    init_symbol_timestamps(symbols)
    log.info(f"Reconnected. {len(symbols)} symbols in Market Watch.")
    return symbols


def capture_all_ticks(symbols):
    """Capture all new ticks since last check for every symbol.

    Pulls a short trailing window via copy_ticks_from and keeps only ticks whose
    time_msc is newer than the last we stored. time_msc is epoch-ms (timezone-agnostic),
    so this avoids the server/UTC/local mismatch that froze the old window logic.
    """
    all_ticks = []
    start = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(seconds=LOOKBACK_SEC)

    for symbol in symbols:
        ticks_raw = mt5.copy_ticks_from(symbol, start, 100000, mt5.COPY_TICKS_ALL)
        if ticks_raw is None or len(ticks_raw) == 0:
            continue

        seen = last_msc.get(symbol, 0)
        new_ticks = [t for t in ticks_raw if t['time_msc'] > seen]
        if not new_ticks:
            continue

        last_msc[symbol] = max(t['time_msc'] for t in ticks_raw)

        sym_info = mt5.symbol_info(symbol)
        point = sym_info.point if sym_info and sym_info.point > 0 else 0.00001

        for tick in new_ticks:
            dt = datetime.fromtimestamp(tick['time'])
            microseconds = tick['time_msc'] % 1000 * 1000
            timestamp = dt.strftime('%Y-%m-%d %H:%M:%S') + f'.{microseconds:06d}'

            spread = (tick['ask'] - tick['bid']) / point if point > 0 else 0
            flags = int(tick['flags'])
            buy_vol = int(tick['volume']) if (flags & 32) else 0
            sell_vol = int(tick['volume']) if (flags & 64) else 0

            all_ticks.append((
                timestamp,
                symbol,
                float(tick['bid']),
                float(tick['ask']),
                float(spread),
                int(tick['volume']),
                buy_vol,
                sell_vol,
                flags
            ))

    return all_ticks


def write_to_db(ticks):
    """Write ticks to universal ticks table + update current"""
    if not ticks:
        return

    try:
        conn = get_db()
        cur = conn.cursor()

        execute_batch(cur, """
            INSERT INTO ticks (time, symbol, bid, ask, spread, volume, buy_volume, sell_volume, flags)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
        """, ticks)

        latest = {}
        for t in ticks:
            sym = t[1]
            if sym not in latest or t[0] > latest[sym][0]:
                latest[sym] = t

        for sym, t in latest.items():
            cur.execute("""
                INSERT INTO current (symbol, bid, ask, spread, volume, flags, last_updated)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (symbol) DO UPDATE SET
                    bid = EXCLUDED.bid,
                    ask = EXCLUDED.ask,
                    spread = EXCLUDED.spread,
                    volume = EXCLUDED.volume,
                    flags = EXCLUDED.flags,
                    last_updated = EXCLUDED.last_updated
            """, (sym, t[2], t[3], t[4], t[5], t[8], t[0]))

        conn.commit()
        cur.close()
        conn.close()

        stats['ticks'] += len(ticks)

    except Exception as e:
        stats['errors'] += 1
        log.error(f"DB write failed: {e}")


def print_stats():
    while True:
        time.sleep(30)
        log.info(
            f"Ticks: {stats['ticks']:,} | Symbols: {stats['symbols']} | "
            f"Errors: {stats['errors']} | Reconnects: {stats['reconnects']}"
        )


def main():
    log.info("=" * 60)
    log.info("KLDA-HFT Universal Tick Capture")
    log.info("Captures ALL Market Watch symbols dynamically")
    log.info("=" * 60)

    if not mt5_connect():
        return

    symbols = get_market_watch_symbols()
    stats['symbols'] = len(symbols)
    log.info(f"Market Watch symbols ({len(symbols)}): {', '.join(symbols)}")

    init_symbol_timestamps(symbols)

    threading.Thread(target=print_stats, daemon=True).start()

    log.info(f"[START] Capturing ticks every 1s (lookback {LOOKBACK_SEC}s)... Press Ctrl+C to stop")

    while True:
        try:
            ticks = capture_all_ticks(symbols)
            if ticks:
                write_to_db(ticks)
            time.sleep(1.0)
        except KeyboardInterrupt:
            raise
        except Exception:
            stats['errors'] += 1
            log.error("Capture loop exception:\n" + traceback.format_exc())
            new_symbols = mt5_reconnect()
            if new_symbols:
                symbols = new_symbols
            else:
                time.sleep(5)


if __name__ == '__main__':
    # Outer restart wrapper: any unhandled exit re-enters main() with backoff.
    backoff = 1
    while True:
        try:
            main()
            log.warning(f"main() returned; restarting in {backoff}s")
        except KeyboardInterrupt:
            log.info(f"[STOP] Total ticks captured: {stats['ticks']:,}")
            try:
                mt5.shutdown()
            except Exception:
                pass
            break
        except Exception:
            log.critical(f"Fatal in main(); restarting in {backoff}s:\n{traceback.format_exc()}")
        try:
            mt5.shutdown()
        except Exception:
            pass
        time.sleep(backoff)
        backoff = min(backoff * 2, 60)
