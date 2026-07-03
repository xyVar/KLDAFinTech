#!/usr/bin/env python3
"""
KLDA-HFT Kill Switch
=====================
Emergency stop. Does three things:
  1. Closes ALL open MT5 positions at market
  2. Writes KILL_SWITCH flag to DB (blocks limits_enforcer)
  3. Cancels all pending signals in DB

Run directly:
    python kill_switch.py [--reason "manual override"]

Or import:
    from kill_switch import trigger_kill_switch
    trigger_kill_switch("drawdown_limit_breached")
"""

import MetaTrader5 as mt5
import psycopg2
from datetime import datetime
import argparse
import sys

DB_CONFIG = {
    'host': 'localhost', 'port': 5432,
    'database': 'KLDA-HFT_Database',
    'user': 'postgres', 'password': 'MyKldaTechnologies2025!'
}

MAGIC    = 234000
DEVIATION = 20


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] [KILL] {msg}", flush=True)


def get_conn():
    return psycopg2.connect(**DB_CONFIG)


def ensure_flags_table():
    """Create system_flags table if it doesn't exist."""
    try:
        conn = get_conn()
        cur  = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS system_flags (
                flag        VARCHAR(50) PRIMARY KEY,
                active      BOOLEAN     NOT NULL DEFAULT TRUE,
                reason      TEXT,
                triggered_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)
        conn.commit()
        conn.close()
    except Exception as e:
        log(f"WARNING: could not create system_flags table: {e}")


def close_all_positions() -> int:
    """Close every open position at market. Returns count closed."""
    positions = mt5.positions_get()
    if not positions:
        log("No open positions to close.")
        return 0

    closed = 0
    for pos in positions:
        symbol   = pos.symbol
        lot      = pos.volume
        order_type = mt5.ORDER_TYPE_SELL if pos.type == mt5.POSITION_TYPE_BUY else mt5.ORDER_TYPE_BUY

        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            log(f"WARN: no tick for {symbol} — skipping")
            continue

        price = tick.bid if order_type == mt5.ORDER_TYPE_SELL else tick.ask

        request = {
            'action':    mt5.TRADE_ACTION_DEAL,
            'symbol':    symbol,
            'volume':    lot,
            'type':      order_type,
            'position':  pos.ticket,
            'price':     price,
            'deviation': DEVIATION,
            'magic':     MAGIC,
            'comment':   'KILL_SWITCH',
            'type_time': mt5.ORDER_TIME_GTC,
            'type_filling': mt5.ORDER_FILLING_IOC,
        }

        result = mt5.order_send(request)
        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
            log(f"CLOSED {symbol} {lot} lots @ {price:.5f} | ticket {pos.ticket}")
            closed += 1
        else:
            retcode = result.retcode if result else 'None'
            log(f"FAILED to close {symbol}: retcode={retcode}")

    return closed


def set_kill_flag(reason: str):
    """Write KILL_SWITCH = TRUE to system_flags."""
    ensure_flags_table()
    try:
        conn = get_conn()
        cur  = conn.cursor()
        cur.execute("""
            INSERT INTO system_flags (flag, active, reason, triggered_at)
            VALUES ('KILL_SWITCH', TRUE, %s, NOW())
            ON CONFLICT (flag) DO UPDATE SET
                active       = TRUE,
                reason       = EXCLUDED.reason,
                triggered_at = EXCLUDED.triggered_at
        """, (reason,))
        conn.commit()
        conn.close()
        log(f"Kill flag SET in DB. Reason: {reason}")
    except Exception as e:
        log(f"ERROR writing kill flag: {e}")


def cancel_pending_signals():
    """Mark all PENDING/EXECUTING signals as CANCELLED."""
    try:
        conn = get_conn()
        cur  = conn.cursor()
        cur.execute("""
            UPDATE signals SET status = 'CANCELLED'
            WHERE status IN ('PENDING', 'EXECUTING')
        """)
        rows = cur.rowcount
        conn.commit()
        conn.close()
        log(f"Cancelled {rows} pending signals.")
    except Exception as e:
        log(f"ERROR cancelling signals: {e}")


def clear_kill_switch():
    """Re-enable trading after manual review. Call when ready to resume."""
    ensure_flags_table()
    try:
        conn = get_conn()
        cur  = conn.cursor()
        cur.execute("""
            UPDATE system_flags SET active = FALSE
            WHERE flag = 'KILL_SWITCH'
        """)
        conn.commit()
        conn.close()
        log("Kill switch CLEARED. Trading re-enabled.")
    except Exception as e:
        log(f"ERROR clearing kill switch: {e}")


def trigger_kill_switch(reason: str = "manual"):
    """Full emergency stop sequence."""
    log("=" * 50)
    log(f"KILL SWITCH TRIGGERED — reason: {reason}")
    log("=" * 50)

    if not mt5.initialize():
        log(f"MT5 init failed: {mt5.last_error()}")
    else:
        closed = close_all_positions()
        log(f"Positions closed: {closed}")
        mt5.shutdown()

    set_kill_flag(reason)
    cancel_pending_signals()

    log("Kill switch complete. Trading halted.")
    log("To resume: python kill_switch.py --clear")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='KLDA-HFT Kill Switch')
    parser.add_argument('--reason', default='manual_trigger', help='Reason for kill')
    parser.add_argument('--clear',  action='store_true', help='Clear kill switch and re-enable trading')
    args = parser.parse_args()

    if args.clear:
        clear_kill_switch()
    else:
        trigger_kill_switch(args.reason)
