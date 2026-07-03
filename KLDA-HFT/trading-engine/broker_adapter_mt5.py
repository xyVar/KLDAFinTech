#!/usr/bin/env python3
"""
KLDA-HFT Broker Adapter — MT5
================================
Single interface between the OMS and MT5.
PAPER_MODE = True  → logs the order, writes to paper_positions table, no MT5 call
PAPER_MODE = False → sends real MT5 order_send()

All callers use: adapter.send_order(signal) and adapter.close_position(pos_id)
"""

import MetaTrader5 as mt5
import psycopg2
from datetime import datetime

DB_CONFIG = {
    'host': 'localhost', 'port': 5432,
    'database': 'KLDA-HFT_Database',
    'user': 'postgres', 'password': 'MyKldaTechnologies2025!'
}

MAGIC     = 234000
DEVIATION = 20
PAPER_MODE = True   # flip to False for live execution


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] [ADAPTER] {msg}", flush=True)


def get_conn():
    return psycopg2.connect(**DB_CONFIG)


def ensure_paper_tables():
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS paper_positions (
            id           SERIAL PRIMARY KEY,
            opened_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            closed_at    TIMESTAMPTZ,
            symbol       VARCHAR(30)  NOT NULL,
            action       VARCHAR(10)  NOT NULL,
            lots         NUMERIC(10,4) NOT NULL,
            entry_price  NUMERIC(18,8) NOT NULL,
            exit_price   NUMERIC(18,8),
            sl_price     NUMERIC(18,8),
            tp_price     NUMERIC(18,8),
            pnl_points   NUMERIC(18,8),
            pnl_eur      NUMERIC(12,4),
            status       VARCHAR(20) NOT NULL DEFAULT 'OPEN',
            signal_id    BIGINT,
            notes        TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS paper_orders (
            id           SERIAL PRIMARY KEY,
            time         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            symbol       VARCHAR(30)  NOT NULL,
            action       VARCHAR(10)  NOT NULL,
            lots         NUMERIC(10,4) NOT NULL,
            requested_price NUMERIC(18,8),
            fill_price   NUMERIC(18,8),
            status       VARCHAR(20) NOT NULL,
            position_id  INT,
            notes        TEXT
        )
    """)
    conn.commit()
    conn.close()


def _get_current_price(symbol: str, action: str) -> float | None:
    """Get MT5 ask (BUY) or bid (SELL) for fill simulation."""
    if not mt5.initialize():
        return None
    tick = mt5.symbol_info_tick(symbol)
    mt5.shutdown()
    if tick is None:
        return None
    return tick.ask if action == 'BUY' else tick.bid


def send_order(signal_id: int, symbol: str, action: str, lots: float,
               sl_pct: float = 0.5, tp_pct: float = 1.0) -> dict:
    """
    Route an order. Returns result dict with position_id and fill_price.
    sl_pct / tp_pct: stop loss / take profit as % from entry.
    """
    ensure_paper_tables()

    fill_price = _get_current_price(symbol, action)
    if fill_price is None:
        # Market closed — use last known price from current table
        try:
            conn = get_conn()
            cur  = conn.cursor()
            cur.execute("SELECT ask FROM current WHERE symbol = %s", (symbol,))
            row = cur.fetchone()
            conn.close()
            fill_price = float(row[0]) if row else None
        except Exception:
            fill_price = None

    if fill_price is None:
        log(f"REJECT {symbol}: no price available")
        return {'ok': False, 'reason': 'no_price'}

    # Calculate SL / TP
    if action == 'BUY':
        sl = fill_price * (1 - sl_pct / 100)
        tp = fill_price * (1 + tp_pct / 100)
    else:
        sl = fill_price * (1 + sl_pct / 100)
        tp = fill_price * (1 - tp_pct / 100)

    if PAPER_MODE:
        conn = get_conn()
        cur  = conn.cursor()
        cur.execute("""
            INSERT INTO paper_positions
                (symbol, action, lots, entry_price, sl_price, tp_price, signal_id, status, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'OPEN', 'PAPER')
            RETURNING id
        """, (symbol, action, lots, fill_price, round(sl, 8), round(tp, 8), signal_id))
        pos_id = cur.fetchone()[0]
        cur.execute("""
            INSERT INTO paper_orders
                (symbol, action, lots, requested_price, fill_price, status, position_id, notes)
            VALUES (%s, %s, %s, %s, %s, 'FILLED', %s, 'PAPER')
        """, (symbol, action, lots, fill_price, fill_price, pos_id))
        conn.commit()
        conn.close()
        log(f"[PAPER] OPEN  {action} {symbol} {lots} lots @ {fill_price:.5f} | SL {sl:.5f} | TP {tp:.5f} | pos_id={pos_id}")
        return {'ok': True, 'paper': True, 'position_id': pos_id, 'fill_price': fill_price}

    else:
        # LIVE — real MT5 execution
        if not mt5.initialize():
            return {'ok': False, 'reason': f'mt5_init_failed: {mt5.last_error()}'}

        order_type = mt5.ORDER_TYPE_BUY if action == 'BUY' else mt5.ORDER_TYPE_SELL
        request = {
            'action':    mt5.TRADE_ACTION_DEAL,
            'symbol':    symbol,
            'volume':    lots,
            'type':      order_type,
            'price':     fill_price,
            'sl':        round(sl, 8),
            'tp':        round(tp, 8),
            'deviation': DEVIATION,
            'magic':     MAGIC,
            'comment':   f'KLDA_SIG_{signal_id}',
            'type_time': mt5.ORDER_TIME_GTC,
            'type_filling': mt5.ORDER_FILLING_IOC,
        }
        result = mt5.order_send(request)
        mt5.shutdown()

        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
            log(f"[LIVE]  OPEN  {action} {symbol} {lots} lots @ {result.price} | ticket={result.order}")
            return {'ok': True, 'paper': False, 'ticket': result.order, 'fill_price': result.price}
        else:
            retcode = result.retcode if result else 'None'
            log(f"[LIVE]  FAIL  {symbol}: retcode={retcode}")
            return {'ok': False, 'reason': f'mt5_retcode={retcode}'}


def close_paper_position(position_id: int) -> dict:
    """Close a paper position, calculate P&L."""
    ensure_paper_tables()
    conn = get_conn()
    cur  = conn.cursor()

    cur.execute("SELECT symbol, action, lots, entry_price FROM paper_positions WHERE id = %s AND status = 'OPEN'", (position_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return {'ok': False, 'reason': 'position_not_found_or_closed'}

    symbol, action, lots, entry_price = row[0], row[1], float(row[2]), float(row[3])
    exit_price = _get_current_price(symbol, 'SELL' if action == 'BUY' else 'BUY')
    if exit_price is None:
        conn.close()
        return {'ok': False, 'reason': 'no_exit_price'}

    pnl_points = (exit_price - entry_price) if action == 'BUY' else (entry_price - exit_price)
    pnl_eur = round(pnl_points * lots * 1000, 4)  # approximate for CFDs

    cur.execute("""
        UPDATE paper_positions SET
            closed_at = NOW(), exit_price = %s,
            pnl_points = %s, pnl_eur = %s, status = 'CLOSED'
        WHERE id = %s
    """, (exit_price, round(pnl_points, 8), pnl_eur, position_id))
    conn.commit()
    conn.close()

    log(f"[PAPER] CLOSE {symbol} pos_id={position_id} @ {exit_price:.5f} | PnL {pnl_eur:+.4f} EUR")
    return {'ok': True, 'pnl_eur': pnl_eur, 'exit_price': exit_price}
