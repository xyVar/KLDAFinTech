#!/usr/bin/env python3
"""
KLDA-HFT Risk Gate — Limits Enforcer
=====================================
Called by klda_engine.py before every order attempt.
Returns (allowed: bool, reason: str).

Limits (tuned for ~€50-200 account in Phase 0/1):
  - Daily loss cap: absolute EUR
  - Max open positions
  - Max lot size per symbol
  - Max total lots across all positions
  - Min margin level before new trades blocked
"""

import psycopg2
import MetaTrader5 as mt5
from datetime import datetime, date

DB_CONFIG = {
    'host': 'localhost', 'port': 5432,
    'database': 'KLDA-HFT_Database',
    'user': 'postgres', 'password': 'MyKldaTechnologies2025!'
}

# ── HARD LIMITS ───────────────────────────────────────────────────────────────
MAX_DAILY_LOSS_EUR   = 10.0    # stop opening new trades if day P&L < -10 EUR
MAX_OPEN_POSITIONS   = 3       # never hold more than 3 simultaneous positions
MAX_LOT_PER_SYMBOL   = 0.01    # micro lot only — smallest available
MAX_TOTAL_LOTS       = 0.03    # total exposure cap across all symbols
MIN_MARGIN_LEVEL_PCT = 200.0   # block new trades below 200% margin level
MIN_FREE_MARGIN_EUR  = 10.0    # block if free margin < €10


def get_conn():
    return psycopg2.connect(**DB_CONFIG)


def _mt5_init() -> bool:
    """Initialize MT5 if not already running."""
    info = mt5.account_info()
    if info is not None:
        return True
    return mt5.initialize()


def check_daily_loss() -> tuple[bool, str]:
    """
    Compute today's realized + unrealized P&L.
    Uses account_snapshots for start-of-day equity baseline.
    """
    try:
        conn = get_conn()
        cur  = conn.cursor()

        # Start-of-day equity (first snapshot today)
        today = date.today().isoformat()
        cur.execute("""
            SELECT equity FROM account_snapshots
            WHERE time::date = %s
            ORDER BY time ASC LIMIT 1
        """, (today,))
        row = cur.fetchone()
        conn.close()

        if row is None:
            # No snapshot yet today — can't enforce, allow
            return True, "no_snapshot_yet"

        start_equity = float(row[0])
        info = mt5.account_info()
        if info is None:
            return False, "mt5_account_unavailable"

        current_equity = info.equity
        day_pnl = current_equity - start_equity

        if day_pnl < -MAX_DAILY_LOSS_EUR:
            return False, f"daily_loss_limit: day_pnl={day_pnl:.2f} EUR < -{MAX_DAILY_LOSS_EUR}"

        return True, f"daily_pnl={day_pnl:+.2f}"

    except Exception as e:
        return False, f"daily_loss_check_error: {e}"


def check_positions(symbol: str, paper_mode: bool = False) -> tuple[bool, str]:
    """
    Check open position count and total lots.
    In paper_mode: checks paper_positions table.
    In live mode: checks real MT5 positions.
    """
    if paper_mode:
        try:
            conn = get_conn()
            cur  = conn.cursor()
            cur.execute("SELECT COUNT(*), COALESCE(SUM(lots),0) FROM paper_positions WHERE status='OPEN'")
            open_count, total_lots = cur.fetchone()
            open_count = int(open_count)
            total_lots = float(total_lots)
            cur.execute("SELECT COUNT(*) FROM paper_positions WHERE status='OPEN' AND symbol=%s", (symbol,))
            sym_count = int(cur.fetchone()[0])
            conn.close()

            if open_count >= MAX_OPEN_POSITIONS:
                return False, f"max_positions: {open_count}/{MAX_OPEN_POSITIONS} paper positions open"
            if total_lots + MAX_LOT_PER_SYMBOL > MAX_TOTAL_LOTS:
                return False, f"max_total_lots: {total_lots:.2f}+{MAX_LOT_PER_SYMBOL} > {MAX_TOTAL_LOTS}"
            if sym_count > 0:
                return False, f"already_in_{symbol}: {sym_count} paper position(s) open"
            return True, f"positions_ok: {open_count} open, {total_lots:.2f} total lots"
        except Exception as e:
            return False, f"paper_position_check_error: {e}"

    if not _mt5_init():
        return False, "mt5_account_unavailable"
    positions = mt5.positions_get()
    if positions is None:
        return False, "mt5_positions_unavailable"

    open_count = len(positions)
    total_lots = sum(p.volume for p in positions)
    sym_lots   = sum(p.volume for p in positions if p.symbol == symbol)

    if open_count >= MAX_OPEN_POSITIONS:
        return False, f"max_positions: {open_count}/{MAX_OPEN_POSITIONS} open"
    if total_lots + MAX_LOT_PER_SYMBOL > MAX_TOTAL_LOTS:
        return False, f"max_total_lots: {total_lots:.2f}+{MAX_LOT_PER_SYMBOL} > {MAX_TOTAL_LOTS}"
    if sym_lots > 0:
        return False, f"already_in_{symbol}: {sym_lots} lots open"

    return True, f"positions_ok: {open_count} open, {total_lots:.2f} total lots"


def check_margin() -> tuple[bool, str]:
    """
    Check account margin level and free margin.
    """
    if not _mt5_init():
        return False, "mt5_account_unavailable"
    info = mt5.account_info()
    if info is None:
        return False, "mt5_account_unavailable"

    if info.margin_level < MIN_MARGIN_LEVEL_PCT and info.margin > 0:
        return False, f"margin_level: {info.margin_level:.1f}% < {MIN_MARGIN_LEVEL_PCT}%"

    if info.margin_free < MIN_FREE_MARGIN_EUR:
        return False, f"free_margin: {info.margin_free:.2f} EUR < {MIN_FREE_MARGIN_EUR}"

    return True, f"margin_ok: level={info.margin_level:.1f}%, free={info.margin_free:.2f}"


def is_kill_switch_active() -> bool:
    """Check if kill_switch.py has written a KILL flag to DB."""
    try:
        conn = get_conn()
        cur  = conn.cursor()
        cur.execute("""
            SELECT COUNT(*) FROM system_flags
            WHERE flag = 'KILL_SWITCH' AND active = TRUE
        """)
        count = cur.fetchone()[0]
        conn.close()
        return count > 0
    except Exception:
        return False  # table may not exist yet — don't block


def allow_trade(symbol: str, paper_mode: bool = False) -> tuple[bool, str]:
    """
    Master gate. Call this before every order.
    paper_mode=True: skips live account margin/daily-loss checks
                     (paper positions don't use real margin).
    Returns (True, reason) to proceed, (False, reason) to block.
    """
    if is_kill_switch_active():
        return False, "KILL_SWITCH_ACTIVE"

    if not paper_mode:
        ok, reason = check_margin()
        if not ok:
            return False, reason

        ok, reason = check_daily_loss()
        if not ok:
            return False, reason

    ok, reason = check_positions(symbol, paper_mode=paper_mode)
    if not ok:
        return False, reason

    return True, f"all_checks_passed | {reason}"


def get_lot_size(symbol: str) -> float:
    """
    Returns approved lot size for this trade.
    Always returns MAX_LOT_PER_SYMBOL in Phase 0/1 — no Kelly sizing yet.
    """
    return MAX_LOT_PER_SYMBOL


if __name__ == '__main__':
    # Self-test
    mt5.initialize()
    print("=== LIMITS ENFORCER SELF-TEST ===")
    allowed, reason = allow_trade('NAS100')
    print(f"allow_trade('NAS100'): {allowed} | {reason}")
    print(f"lot_size: {get_lot_size('NAS100')}")
    mt5.shutdown()
