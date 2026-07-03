#!/usr/bin/env python3
"""
KLDA-HFT Trading Engine
Renaissance / Medallion Fund style — fully automated

Runs 3 loops simultaneously:
  1. Signal Executor   — watches signals table, fires orders via MT5
  2. Position Monitor  — tracks open trades, updates DB
  3. Account Snapshot  — saves equity/balance every 5s
"""

import MetaTrader5 as mt5
import psycopg2
import psycopg2.extras
from datetime import datetime, timedelta, timezone
import time
import threading

DB_CONFIG = {
    'host': 'localhost', 'port': 5432,
    'database': 'KLDA-HFT_Database',
    'user': 'postgres', 'password': 'MyKldaTechnologies2025!'
}

MAGIC         = 234000       # EA magic number
MAX_POSITIONS = 10           # max simultaneous open trades
MAX_RISK_PCT  = 2.0          # max % account per trade (Kelly cap)
MIN_LOT       = 0.01         # minimum lot size
DEVIATION     = 20           # max price deviation (slippage)
CLOSE_PROFIT_PCT = 1.0       # close trade at +1% profit
CLOSE_LOSS_PCT   = 0.5       # close trade at -0.5% loss (stop)

running = True

def get_conn():
    return psycopg2.connect(**DB_CONFIG)

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:12]}] {msg}", flush=True)

# ── ACCOUNT SNAPSHOT LOOP ────────────────────────────────────
def account_snapshot_loop():
    log("[ACCOUNT] Snapshot loop started")
    while running:
        try:
            info = mt5.account_info()
            if info:
                conn = get_conn()
                cur  = conn.cursor()
                cur.execute("""
                    INSERT INTO account_snapshots
                        (login, server, balance, equity, margin,
                         free_margin, margin_level, profit)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (time) DO NOTHING
                """, (
                    info.login, info.server,
                    info.balance, info.equity,
                    info.margin, info.margin_free,
                    info.margin_level, info.profit
                ))
                conn.commit()
                conn.close()
        except Exception as e:
            log(f"[ACCOUNT] Error: {e}")
        time.sleep(5)

# ── CALC LOT SIZE ────────────────────────────────────────────
def calc_lot(symbol, kelly_pct, price):
    try:
        info    = mt5.symbol_info(symbol)
        account = mt5.account_info()
        if not info or not account: return MIN_LOT

        risk_amount = account.balance * (min(kelly_pct, MAX_RISK_PCT) / 100.0)
        tick_val    = info.trade_tick_value
        tick_size   = info.trade_tick_size
        contract    = info.trade_contract_size

        if price > 0 and contract > 0:
            lot = risk_amount / (price * contract * 0.01)
        else:
            lot = MIN_LOT

        # Round to broker's step
        step = info.volume_step
        lot  = round(round(lot / step) * step, 8)
        lot  = max(info.volume_min, min(lot, info.volume_max))
        return lot
    except:
        return MIN_LOT

# ── EXECUTE ONE SIGNAL ───────────────────────────────────────
def execute_signal(signal):
    symbol    = signal['symbol']
    action    = signal['action']   # BUY or SELL
    price_sig = float(signal['price'])
    kelly_pct = float(signal['kelly_pct'] or MAX_RISK_PCT)
    sig_id    = signal['id']

    # Subscribe symbol
    if not mt5.symbol_select(symbol, True):
        return False, f"Cannot select {symbol}"

    tick = mt5.symbol_info_tick(symbol)
    if not tick:
        return False, f"No tick for {symbol}"

    order_type = mt5.ORDER_TYPE_BUY  if action == 'BUY'  else mt5.ORDER_TYPE_SELL
    price      = tick.ask            if action == 'BUY'  else tick.bid
    lot        = calc_lot(symbol, kelly_pct, price)

    request = {
        "action":      mt5.TRADE_ACTION_DEAL,
        "symbol":      symbol,
        "volume":      lot,
        "type":        order_type,
        "price":       price,
        "deviation":   DEVIATION,
        "magic":       MAGIC,
        "comment":     f"KLDA-SIG-{sig_id}",
        "type_time":   mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    result = mt5.order_send(request)

    if result and result.retcode == mt5.TRADE_RETCODE_DONE:
        return True, result.order
    else:
        err = result.comment if result else mt5.last_error()
        return False, str(err)

# ── SIGNAL EXECUTOR LOOP ─────────────────────────────────────
def signal_executor_loop():
    log("[EXECUTOR] Signal executor started")
    while running:
        try:
            conn = get_conn()
            cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

            # Count open positions (ours)
            mt5_positions = mt5.positions_get(magic=MAGIC)
            open_count    = len(mt5_positions) if mt5_positions else 0

            if open_count >= MAX_POSITIONS:
                conn.close()
                time.sleep(1)
                continue

            # Get pending signals
            cur.execute("""
                SELECT id, symbol, action, price, confidence, kelly_pct
                FROM signals
                WHERE status = 'PENDING'
                ORDER BY time DESC
                LIMIT %s
            """, (MAX_POSITIONS - open_count,))
            signals = cur.fetchall()
            conn.close()

            for sig in signals:
                # Mark as processing
                conn2 = get_conn()
                cur2  = conn2.cursor()
                cur2.execute("UPDATE signals SET status='EXECUTING' WHERE id=%s", (sig['id'],))
                conn2.commit()

                ok, result = execute_signal(sig)

                if ok:
                    ticket = result
                    cur2.execute("UPDATE signals SET status='EXECUTED' WHERE id=%s", (sig['id'],))
                    log(f"[TRADE] {sig['action']} {sig['symbol']} ticket={ticket} conf={sig['confidence']}%")

                    # Save to trades table
                    tick = mt5.symbol_info_tick(sig['symbol'])
                    price = tick.ask if sig['action'] == 'BUY' else tick.bid if tick else sig['price']
                    lot   = calc_lot(sig['symbol'], float(sig['kelly_pct'] or MAX_RISK_PCT), price)
                    cur2.execute("""
                        INSERT INTO trades (ticket, symbol, type, volume, open_price,
                                           open_time, signal_id, magic, comment, status)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,'OPEN')
                        ON CONFLICT (ticket) DO NOTHING
                    """, (ticket, sig['symbol'], sig['action'], lot, price,
                          datetime.now(), sig['id'], MAGIC, f"KLDA-SIG-{sig['id']}"))

                    # Log execution
                    cur2.execute("""
                        INSERT INTO execution_log (signal_id, symbol, action, volume, price, ticket, status)
                        VALUES (%s,%s,%s,%s,%s,%s,'OK')
                    """, (sig['id'], sig['symbol'], sig['action'], lot, price, ticket))
                else:
                    cur2.execute("UPDATE signals SET status='FAILED' WHERE id=%s", (sig['id'],))
                    cur2.execute("""
                        INSERT INTO execution_log (signal_id, symbol, action, price, status, error)
                        VALUES (%s,%s,%s,%s,'FAILED',%s)
                    """, (sig['id'], sig['symbol'], sig['action'], sig['price'], str(result)))
                    log(f"[FAIL] {sig['symbol']} error: {result}")

                conn2.commit()
                conn2.close()

        except Exception as e:
            log(f"[EXECUTOR] Error: {e}")

        time.sleep(1)

# ── POSITION MONITOR LOOP ────────────────────────────────────
def position_monitor_loop():
    log("[POSITIONS] Monitor started")
    while running:
        try:
            positions = mt5.positions_get(magic=MAGIC)
            if not positions:
                time.sleep(2)
                continue

            conn = get_conn()
            cur  = conn.cursor()

            for pos in positions:
                profit_pct = (pos.profit / (pos.price_open * pos.volume)) * 100 if pos.price_open > 0 else 0

                # Update trade record
                cur.execute("""
                    UPDATE trades SET
                        close_price = %s,
                        profit      = %s,
                        status      = 'OPEN'
                    WHERE ticket = %s
                """, (pos.price_current, pos.profit, pos.ticket))

                # Close if profit/loss target hit
                should_close = False
                if profit_pct >= CLOSE_PROFIT_PCT:
                    log(f"[CLOSE] {pos.symbol} profit={profit_pct:.2f}% TARGET HIT")
                    should_close = True
                elif profit_pct <= -CLOSE_LOSS_PCT:
                    log(f"[STOP]  {pos.symbol} loss={profit_pct:.2f}% STOP HIT")
                    should_close = True

                if should_close:
                    close_type = mt5.ORDER_TYPE_SELL if pos.type == 0 else mt5.ORDER_TYPE_BUY
                    tick       = mt5.symbol_info_tick(pos.symbol)
                    close_price = tick.bid if pos.type == 0 else tick.ask

                    req = {
                        "action":      mt5.TRADE_ACTION_DEAL,
                        "symbol":      pos.symbol,
                        "volume":      pos.volume,
                        "type":        close_type,
                        "position":    pos.ticket,
                        "price":       close_price,
                        "deviation":   DEVIATION,
                        "magic":       MAGIC,
                        "comment":     "KLDA-CLOSE",
                        "type_time":   mt5.ORDER_TIME_GTC,
                        "type_filling": mt5.ORDER_FILLING_IOC,
                    }
                    res = mt5.order_send(req)
                    if res and res.retcode == mt5.TRADE_RETCODE_DONE:
                        cur.execute("""
                            UPDATE trades SET
                                close_price = %s,
                                close_time  = %s,
                                profit      = %s,
                                net_profit  = %s,
                                status      = 'CLOSED'
                            WHERE ticket = %s
                        """, (close_price, datetime.now(), pos.profit, pos.profit, pos.ticket))
                        log(f"[CLOSED] {pos.symbol} P&L={pos.profit:.2f}")

            conn.commit()
            conn.close()

        except Exception as e:
            log(f"[POSITIONS] Error: {e}")

        time.sleep(2)

# ── DAILY P&L UPDATER ────────────────────────────────────────
def daily_pnl_loop():
    log("[PNL] Daily P&L tracker started")
    while running:
        try:
            today = datetime.now().date()
            conn  = get_conn()
            cur   = conn.cursor()
            cur.execute("""
                SELECT
                    COUNT(*) as cnt,
                    COALESCE(SUM(CASE WHEN profit > 0 THEN profit ELSE 0 END), 0) as gross_profit,
                    COALESCE(SUM(CASE WHEN profit < 0 THEN profit ELSE 0 END), 0) as gross_loss,
                    COALESCE(SUM(profit), 0) as net_profit,
                    COALESCE(SUM(CASE WHEN profit > 0 THEN 1.0 ELSE 0 END) / NULLIF(COUNT(*),0), 0) as win_rate
                FROM trades
                WHERE status = 'CLOSED'
                AND DATE(close_time) = %s
            """, (today,))
            row = cur.fetchone()

            acct = mt5.account_info()
            balance = acct.balance if acct else 0

            cur.execute("""
                INSERT INTO daily_pnl (date, trades_count, gross_profit, gross_loss,
                                       net_profit, win_rate, balance_eod)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (date) DO UPDATE SET
                    trades_count = EXCLUDED.trades_count,
                    gross_profit = EXCLUDED.gross_profit,
                    gross_loss   = EXCLUDED.gross_loss,
                    net_profit   = EXCLUDED.net_profit,
                    win_rate     = EXCLUDED.win_rate,
                    balance_eod  = EXCLUDED.balance_eod
            """, (today, row[0], row[1], row[2], row[3], row[4], balance))

            conn.commit()
            conn.close()
        except Exception as e:
            log(f"[PNL] Error: {e}")
        time.sleep(60)

# ── DEPOSIT/WITHDRAWAL SYNC ──────────────────────────────────
def sync_balance_ops():
    try:
        now  = datetime.now()
        from_date = datetime(now.year - 1, 1, 1)
        deals = mt5.history_deals_get(from_date, now)
        if not deals:
            return

        conn = get_conn()
        cur  = conn.cursor()
        for d in deals:
            if d.type == 2:  # DEAL_TYPE_BALANCE
                dtype = 'DEPOSIT' if d.profit > 0 else 'WITHDRAWAL'
                cur.execute("""
                    INSERT INTO transactions (time, type, amount, balance_after, note)
                    VALUES (%s,%s,%s,%s,%s)
                    ON CONFLICT DO NOTHING
                """, (datetime.fromtimestamp(d.time), dtype,
                      abs(d.profit), d.profit, d.comment or ''))
        conn.commit()
        conn.close()
        log(f"[SYNC] Balance operations synced")
    except Exception as e:
        log(f"[SYNC] Error: {e}")

# ── MAIN ─────────────────────────────────────────────────────
def main():
    global running
    print("=" * 60)
    print("KLDA-HFT Trading Engine — Renaissance / Medallion Style")
    print("=" * 60)

    if not mt5.initialize():
        print(f"[ERROR] MT5 init failed: {mt5.last_error()}")
        return

    acct = mt5.account_info()
    print(f"[OK] Account: {acct.login} | {acct.server}")
    print(f"[OK] Balance: ${acct.balance:,.2f} | Equity: ${acct.equity:,.2f}")
    print(f"[OK] Margin Level: {acct.margin_level:.1f}%")
    print()

    # Sync historical balance ops
    sync_balance_ops()

    # Start all loops in threads
    threads = [
        threading.Thread(target=account_snapshot_loop,  daemon=True, name="AccountSnap"),
        threading.Thread(target=signal_executor_loop,    daemon=True, name="Executor"),
        threading.Thread(target=position_monitor_loop,   daemon=True, name="Positions"),
        threading.Thread(target=daily_pnl_loop,          daemon=True, name="DailyPnL"),
    ]
    for t in threads:
        t.start()
        log(f"[START] {t.name} thread started")

    print()
    log("[READY] All systems running. Watching for signals...")

    try:
        while True:
            time.sleep(10)
            acct = mt5.account_info()
            pos  = mt5.positions_get(magic=MAGIC)
            n    = len(pos) if pos else 0
            if acct:
                log(f"[STATUS] Balance=${acct.balance:,.2f} Equity=${acct.equity:,.2f} "
                    f"Profit=${acct.profit:,.2f} Positions={n}")
    except KeyboardInterrupt:
        running = False
        print("\n[STOP] Engine shutting down...")
        mt5.shutdown()

if __name__ == '__main__':
    main()
