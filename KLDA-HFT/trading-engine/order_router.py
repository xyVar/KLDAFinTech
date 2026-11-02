#!/usr/bin/env python3
"""
KLDA-HFT Order Router
======================
Sits between signals table and broker_adapter_mt5.
Lifecycle per signal:
  PENDING → check limits → send order → EXECUTING → fill confirmed → FILLED
                         ↘ blocked by risk gate → REJECTED

Safety gates (before the risk gate):
  - LIVE orders only for symbols in config/validated_patterns.json
  - no new entries at/after intraday.no_new_entries_after (broker time)
Exit geometry (SL/TP) comes from the per-symbol config — see thresholds_for().

Run continuously:
  python order_router.py

Or import:
  from order_router import process_pending_signals
"""

import psycopg2
import time
from datetime import datetime

from limits_enforcer import allow_trade, get_lot_size
from broker_adapter_mt5 import send_order, PAPER_MODE
from config_loader import thresholds_for, is_validated, broker_now, intraday_times

DB_CONFIG = {
    'host': '127.0.0.1', 'port': 5432,
    'database': 'KLDA-HFT_Database',
    'user': 'postgres', 'password': 'MyKldaTechnologies2025!'
}

POLL_INTERVAL = 5   # seconds between signal table scans


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] [ROUTER] {msg}", flush=True)


def get_conn():
    return psycopg2.connect(**DB_CONFIG)


def fetch_pending_signals(cur) -> list:
    cur.execute("""
        SELECT id, symbol, action, price, confidence, pattern_name
        FROM signals
        WHERE status = 'PENDING'
        ORDER BY time ASC
        LIMIT 10
    """)
    return cur.fetchall()


def mark_signal(cur, conn, signal_id: int, status: str, notes: str = ''):
    cur.execute("""
        UPDATE signals SET status = %s
        WHERE id = %s
    """, (status, signal_id))
    conn.commit()


def process_pending_signals():
    conn = get_conn()
    cur  = conn.cursor()
    signals = fetch_pending_signals(cur)

    if not signals:
        conn.close()
        return 0

    processed = 0
    no_entries_after, _ = intraday_times()
    for sig_id, symbol, action, price, confidence, pattern in signals:

        # 0 — Safety gates: validated-only live trading, intraday entry cutoff
        if not PAPER_MODE:
            ok, why = is_validated(symbol, pattern)
            if not ok:
                log(f"REJECTED sig_id={sig_id} {symbol}: live order refused — {why}")
                mark_signal(cur, conn, sig_id, 'REJECTED', why)
                processed += 1
                continue
        bnow = broker_now()
        if bnow.time() >= no_entries_after:
            why = f"intraday cutoff: broker {bnow:%H:%M} >= {no_entries_after:%H:%M}"
            log(f"REJECTED sig_id={sig_id} {symbol}: {why}")
            mark_signal(cur, conn, sig_id, 'REJECTED', why)
            processed += 1
            continue

        # 1 — Risk gate check
        allowed, reason = allow_trade(symbol, paper_mode=PAPER_MODE)
        if not allowed:
            log(f"REJECTED sig_id={sig_id} {symbol}: {reason}")
            mark_signal(cur, conn, sig_id, 'REJECTED', reason)
            processed += 1
            continue

        lots = get_lot_size(symbol)
        th   = thresholds_for(symbol)

        # 2 — Mark as executing
        mark_signal(cur, conn, sig_id, 'EXECUTING')

        # 3 — Send order via adapter
        result = send_order(
            signal_id=sig_id,
            symbol=symbol,
            action=action,
            lots=lots,
            sl_pct=th['sl_pct'],
            tp_pct=th['tp_pct'],
        )

        # 4 — Update signal status
        if result['ok']:
            mark_signal(cur, conn, sig_id, 'FILLED')
            mode_tag = '[PAPER]' if PAPER_MODE else '[LIVE]'
            log(f"FILLED {mode_tag} sig_id={sig_id} {action} {symbol} {lots} lots @ {result['fill_price']:.5f}")
        else:
            mark_signal(cur, conn, sig_id, 'FAILED')
            log(f"FAILED sig_id={sig_id} {symbol}: {result.get('reason')}")

        processed += 1

    conn.close()
    return processed


def main():
    log("=" * 60)
    log("KLDA Order Router — STARTING")
    log(f"  Mode    : {'PAPER' if PAPER_MODE else 'LIVE'}")
    th = thresholds_for('default')
    no_entries_after, _ = intraday_times()
    log(f"  SL/TP   : {th['sl_pct']}% / {th['tp_pct']}% default (per-symbol: config/trading_config.json)")
    log(f"  Live    : only symbols in config/validated_patterns.json")
    log(f"  Entries : none at/after {no_entries_after:%H:%M} broker time (now {broker_now():%H:%M})")
    log(f"  Poll    : every {POLL_INTERVAL}s")
    log("=" * 60)

    while True:
        try:
            n = process_pending_signals()
            if n > 0:
                log(f"Processed {n} signal(s)")
        except Exception as e:
            log(f"ERROR: {e}")
        time.sleep(POLL_INTERVAL)


if __name__ == '__main__':
    main()
