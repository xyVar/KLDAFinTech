#!/usr/bin/env python3
"""
KLDA-HFT Reconciler
=====================
Monitors open paper positions. Checks SL/TP conditions every 30s.
Closes positions when price hits SL or TP.
Reports daily P&L summary.

Run: python reconciler.py
Or import: from reconciler import run_reconciliation
"""

import psycopg2
import MetaTrader5 as mt5
from datetime import datetime, date
import time

from broker_adapter_mt5 import close_paper_position, ensure_paper_tables

DB_CONFIG = {
    'host': 'localhost', 'port': 5432,
    'database': 'KLDA-HFT_Database',
    'user': 'postgres', 'password': 'MyKldaTechnologies2025!'
}

POLL_INTERVAL = 30   # seconds


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] [RECONCILER] {msg}", flush=True)


def get_conn():
    return psycopg2.connect(**DB_CONFIG)


def get_current_price(symbol: str, action: str) -> float | None:
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        return None
    return tick.bid if action == 'BUY' else tick.ask


def check_sl_tp():
    """Check all open paper positions against SL/TP. Close if hit."""
    ensure_paper_tables()
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("""
        SELECT id, symbol, action, lots, entry_price, sl_price, tp_price
        FROM paper_positions
        WHERE status = 'OPEN'
    """)
    positions = cur.fetchall()
    conn.close()

    closed = 0
    for pos_id, symbol, action, lots, entry, sl, tp in positions:
        entry = float(entry)
        sl    = float(sl) if sl else None
        tp    = float(tp) if tp else None

        current = get_current_price(symbol, action)
        if current is None:
            continue

        hit_sl = sl and (current <= sl if action == 'BUY' else current >= sl)
        hit_tp = tp and (current >= tp if action == 'BUY' else current <= tp)

        if hit_sl:
            result = close_paper_position(pos_id)
            log(f"SL HIT  {symbol} pos_id={pos_id} | pnl={result.get('pnl_eur', '?'):+} EUR")
            closed += 1
        elif hit_tp:
            result = close_paper_position(pos_id)
            log(f"TP HIT  {symbol} pos_id={pos_id} | pnl={result.get('pnl_eur', '?'):+} EUR")
            closed += 1

    return closed


def daily_summary():
    """Print today's paper trading P&L."""
    ensure_paper_tables()
    conn = get_conn()
    cur  = conn.cursor()
    today = date.today().isoformat()

    cur.execute("""
        SELECT
            COUNT(*) FILTER (WHERE status = 'CLOSED')   AS closed,
            COUNT(*) FILTER (WHERE status = 'OPEN')     AS open,
            COALESCE(SUM(pnl_eur) FILTER (WHERE status = 'CLOSED'), 0) AS total_pnl,
            COALESCE(SUM(pnl_eur) FILTER (WHERE status = 'CLOSED' AND pnl_eur > 0), 0) AS gross_win,
            COALESCE(SUM(pnl_eur) FILTER (WHERE status = 'CLOSED' AND pnl_eur < 0), 0) AS gross_loss,
            COUNT(*) FILTER (WHERE status = 'CLOSED' AND pnl_eur > 0) AS wins,
            COUNT(*) FILTER (WHERE status = 'CLOSED' AND pnl_eur < 0) AS losses
        FROM paper_positions
        WHERE opened_at::date = %s
    """, (today,))
    row = cur.fetchone()
    conn.close()

    if row:
        closed, open_pos, total_pnl, gross_win, gross_loss, wins, losses = row
        win_rate = (wins / closed * 100) if closed > 0 else 0
        log(f"=== DAILY SUMMARY ({today}) ===")
        log(f"  Trades : {closed} closed, {open_pos} open")
        log(f"  P&L    : {float(total_pnl):+.4f} EUR (wins: {float(gross_win):+.4f} / losses: {float(gross_loss):+.4f})")
        log(f"  Win rate: {win_rate:.1f}% ({wins}W / {losses}L)")


def run_reconciliation():
    closed = check_sl_tp()
    return closed


def main():
    if not mt5.initialize():
        log(f"MT5 init failed: {mt5.last_error()} — SL/TP checks disabled (market closed?)")

    log("=" * 60)
    log("KLDA Reconciler — STARTING")
    log(f"  Checks SL/TP every {POLL_INTERVAL}s")
    log(f"  Daily summary every 60 cycles (~30 min)")
    log("=" * 60)

    cycle = 0
    while True:
        try:
            closed = run_reconciliation()
            if closed > 0:
                log(f"Closed {closed} position(s) via SL/TP")
            cycle += 1
            if cycle % 60 == 0:
                daily_summary()
        except Exception as e:
            log(f"ERROR: {e}")
        time.sleep(POLL_INTERVAL)


if __name__ == '__main__':
    main()
