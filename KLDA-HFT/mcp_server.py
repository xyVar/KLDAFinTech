#!/usr/bin/env python3
"""
KLDA-HFT MCP Server
====================
Exposes the trading system as MCP tools for Claude Code.
Claude can query live state, positions, signals, P&L, and run
read-only SQL — without re-establishing context every session.

Run: python mcp_server.py
Configure in .mcp.json (project root)
"""

from mcp.server.fastmcp import FastMCP
import psycopg2
import psycopg2.extras
import json
import subprocess
from datetime import date, datetime

mcp = FastMCP("klda-hft")

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'KLDA-HFT_Database',
    'user': 'postgres',
    'password': 'MyKldaTechnologies2025!',
}


def get_conn():
    return psycopg2.connect(**DB_CONFIG)


def _json(obj):
    return json.dumps(obj, indent=2, default=str)


# ── ACCOUNT ───────────────────────────────────────────────────────────────────

@mcp.tool()
def account_status() -> str:
    """
    Live MT5 account: balance, equity, margin level, free margin.
    Works even when markets are closed (reads cached data).
    """
    try:
        import MetaTrader5 as mt5
        if not mt5.initialize():
            return f"MT5 unavailable: {mt5.last_error()}"
        info = mt5.account_info()
        mt5.shutdown()
        if info is None:
            return "MT5 account info unavailable"
        return _json({
            'login':           info.login,
            'server':          info.server,
            'currency':        info.currency,
            'balance':         round(info.balance, 2),
            'equity':          round(info.equity, 2),
            'margin':          round(info.margin, 2),
            'free_margin':     round(info.margin_free, 2),
            'margin_level_pct': round(info.margin_level, 2),
            'leverage':        info.leverage,
        })
    except Exception as e:
        return f"Error: {e}"


# ── POSITIONS ─────────────────────────────────────────────────────────────────

@mcp.tool()
def open_positions(mode: str = "paper") -> str:
    """
    Get open positions.
    mode='paper' → paper_positions table (default)
    mode='live'  → real MT5 positions
    mode='both'  → both sources
    """
    result = {}

    if mode in ("paper", "both"):
        try:
            conn = get_conn()
            cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute("""
                SELECT id, symbol, action, lots, entry_price, sl_price, tp_price,
                       opened_at, pnl_eur, status
                FROM paper_positions WHERE status = 'OPEN'
                ORDER BY opened_at DESC
            """)
            result['paper'] = [dict(r) for r in cur.fetchall()]
            conn.close()
        except Exception as e:
            result['paper'] = f"Error: {e}"

    if mode in ("live", "both"):
        try:
            import MetaTrader5 as mt5
            if mt5.initialize():
                positions = mt5.positions_get()
                mt5.shutdown()
                result['live'] = [{
                    'ticket':     p.ticket,
                    'symbol':     p.symbol,
                    'type':       'BUY' if p.type == 0 else 'SELL',
                    'volume':     p.volume,
                    'price_open': p.price_open,
                    'sl':         p.sl,
                    'tp':         p.tp,
                    'profit':     round(p.profit, 2),
                    'swap':       round(p.swap, 2),
                } for p in (positions or [])]
            else:
                result['live'] = f"MT5 unavailable: {mt5.last_error()}"
        except Exception as e:
            result['live'] = f"Error: {e}"

    if mode == "paper":
        return _json(result.get('paper', []))
    if mode == "live":
        return _json(result.get('live', []))
    return _json(result)


@mcp.tool()
def closed_positions(days: int = 7, limit: int = 50) -> str:
    """
    Recent closed paper positions with P&L.
    days: how many days back to look (default 7)
    limit: max rows (default 50)
    """
    try:
        conn = get_conn()
        cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT id, symbol, action, lots,
                   entry_price, exit_price, sl_price, tp_price,
                   opened_at, closed_at,
                   pnl_points, pnl_eur, status, notes
            FROM paper_positions
            WHERE status = 'CLOSED'
              AND opened_at >= NOW() - INTERVAL '%s days'
            ORDER BY closed_at DESC
            LIMIT %s
        """, (days, limit))
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return _json(rows)
    except Exception as e:
        return f"Error: {e}"


# ── SIGNALS ───────────────────────────────────────────────────────────────────

@mcp.tool()
def recent_signals(limit: int = 30, status_filter: str = "all") -> str:
    """
    Recent trading signals.
    status_filter: 'all' | 'PENDING' | 'FILLED' | 'REJECTED' | 'FAILED'
    """
    try:
        conn = get_conn()
        cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        if status_filter == "all":
            cur.execute("""
                SELECT id, time, symbol, action, price, confidence,
                       mean_rev, regime, status
                FROM signals
                ORDER BY time DESC LIMIT %s
            """, (limit,))
        else:
            cur.execute("""
                SELECT id, time, symbol, action, price, confidence,
                       mean_rev, regime, status
                FROM signals
                WHERE status = %s
                ORDER BY time DESC LIMIT %s
            """, (status_filter, limit))
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return _json(rows)
    except Exception as e:
        return f"Error: {e}"


# ── P&L ───────────────────────────────────────────────────────────────────────

@mcp.tool()
def daily_pnl(target_date: str = "today") -> str:
    """
    Paper trading P&L summary for a given day.
    target_date: 'today' or ISO date string 'YYYY-MM-DD'
    """
    try:
        d = date.today().isoformat() if target_date == "today" else target_date
        conn = get_conn()
        cur  = conn.cursor()
        cur.execute("""
            SELECT
                COUNT(*) FILTER (WHERE status = 'CLOSED')               AS closed,
                COUNT(*) FILTER (WHERE status = 'OPEN')                 AS open_pos,
                COALESCE(SUM(pnl_eur) FILTER (WHERE status='CLOSED'),0) AS total_pnl,
                COALESCE(SUM(pnl_eur) FILTER (WHERE status='CLOSED' AND pnl_eur > 0), 0) AS gross_win,
                COALESCE(SUM(pnl_eur) FILTER (WHERE status='CLOSED' AND pnl_eur < 0), 0) AS gross_loss,
                COUNT(*) FILTER (WHERE status='CLOSED' AND pnl_eur > 0) AS wins,
                COUNT(*) FILTER (WHERE status='CLOSED' AND pnl_eur < 0) AS losses
            FROM paper_positions
            WHERE opened_at::date = %s
        """, (d,))
        r = cur.fetchone()
        conn.close()
        closed, open_pos, total_pnl, gross_win, gross_loss, wins, losses = r
        win_rate = (wins / closed * 100) if closed > 0 else 0
        return _json({
            'date':           d,
            'closed_trades':  closed,
            'open_trades':    open_pos,
            'total_pnl_eur':  float(total_pnl),
            'gross_win_eur':  float(gross_win),
            'gross_loss_eur': float(gross_loss),
            'wins':           wins,
            'losses':         losses,
            'win_rate_pct':   round(win_rate, 1),
        })
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def pnl_summary(days: int = 30) -> str:
    """
    Aggregate paper trading stats over N days.
    Returns total trades, win rate, total P&L, avg win/loss, best/worst day.
    """
    try:
        conn = get_conn()
        cur  = conn.cursor()
        cur.execute("""
            SELECT
                COUNT(*)                                                  AS total_trades,
                COUNT(*) FILTER (WHERE pnl_eur > 0)                      AS wins,
                COUNT(*) FILTER (WHERE pnl_eur < 0)                      AS losses,
                COALESCE(SUM(pnl_eur), 0)                                AS total_pnl,
                COALESCE(AVG(pnl_eur) FILTER (WHERE pnl_eur > 0), 0)    AS avg_win,
                COALESCE(AVG(pnl_eur) FILTER (WHERE pnl_eur < 0), 0)    AS avg_loss,
                COALESCE(MAX(pnl_eur), 0)                                AS best_trade,
                COALESCE(MIN(pnl_eur), 0)                                AS worst_trade
            FROM paper_positions
            WHERE status = 'CLOSED'
              AND opened_at >= NOW() - INTERVAL '%s days'
        """, (days,))
        r = cur.fetchone()
        conn.close()
        total, wins, losses, total_pnl, avg_win, avg_loss, best, worst = r
        win_rate = (wins / total * 100) if total > 0 else 0
        return _json({
            'period_days':    days,
            'total_trades':   total,
            'wins':           wins,
            'losses':         losses,
            'win_rate_pct':   round(float(win_rate), 1),
            'total_pnl_eur':  round(float(total_pnl), 4),
            'avg_win_eur':    round(float(avg_win), 4),
            'avg_loss_eur':   round(float(avg_loss), 4),
            'best_trade_eur': round(float(best), 4),
            'worst_trade_eur':round(float(worst), 4),
        })
    except Exception as e:
        return f"Error: {e}"


# ── SYSTEM ────────────────────────────────────────────────────────────────────

@mcp.tool()
def system_status() -> str:
    """
    Full pipeline health check:
    - Kill switch state
    - Open paper positions count
    - Signals today (by status)
    - Latest tick timestamps per symbol
    - cagg_bars_m5 latest bar timestamps
    """
    try:
        conn = get_conn()
        cur  = conn.cursor()

        # Kill switch
        try:
            cur.execute("SELECT COUNT(*) FROM system_flags WHERE flag='KILL_SWITCH' AND active=TRUE")
            kill_active = cur.fetchone()[0] > 0
        except Exception:
            kill_active = "table_missing"

        # Open paper positions
        try:
            cur.execute("SELECT COUNT(*), COALESCE(SUM(lots),0) FROM paper_positions WHERE status='OPEN'")
            open_count, total_lots = cur.fetchone()
        except Exception:
            open_count, total_lots = 0, 0

        # Signals today
        today = date.today().isoformat()
        try:
            cur.execute("""
                SELECT status, COUNT(*) FROM signals
                WHERE time::date = %s GROUP BY status
            """, (today,))
            signal_counts = dict(cur.fetchall())
        except Exception:
            signal_counts = {}

        # Latest ticks
        try:
            cur.execute("""
                SELECT symbol, MAX(time) as latest
                FROM ticks GROUP BY symbol
                ORDER BY latest DESC LIMIT 10
            """)
            latest_ticks = [{'symbol': r[0], 'latest': str(r[1])} for r in cur.fetchall()]
        except Exception:
            latest_ticks = []

        # Latest cagg bar
        try:
            cur.execute("""
                SELECT symbol, MAX(time) as latest
                FROM cagg_bars_m5 GROUP BY symbol
                ORDER BY latest DESC LIMIT 6
            """)
            latest_bars = [{'symbol': r[0], 'latest': str(r[1])} for r in cur.fetchall()]
        except Exception:
            latest_bars = []

        conn.close()
        return _json({
            'kill_switch_active':    kill_active,
            'open_paper_positions':  int(open_count),
            'total_paper_lots':      float(total_lots),
            'signals_today':         signal_counts,
            'latest_ticks':          latest_ticks,
            'latest_cagg_bars_m5':   latest_bars,
        })
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def price_snapshot(symbols: str = "all") -> str:
    """
    Latest bid/ask prices from the current table.
    symbols: 'all' or comma-separated list e.g. 'NatGas,NAS100,GER40'
    """
    try:
        conn = get_conn()
        cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        if symbols == "all":
            cur.execute("SELECT symbol, bid, ask, spread, last_updated FROM current ORDER BY symbol")
        else:
            sym_list = [s.strip() for s in symbols.split(',')]
            cur.execute("""
                SELECT symbol, bid, ask, spread, last_updated
                FROM current WHERE symbol = ANY(%s) ORDER BY symbol
            """, (sym_list,))
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return _json(rows)
    except Exception as e:
        return f"Error: {e}"


# ── RISK ──────────────────────────────────────────────────────────────────────

@mcp.tool()
def risk_state() -> str:
    """
    Current risk gate state: limits vs actual exposure.
    Shows how close the system is to each hard limit.
    """
    try:
        conn = get_conn()
        cur  = conn.cursor()
        cur.execute("""
            SELECT COUNT(*), COALESCE(SUM(lots), 0)
            FROM paper_positions WHERE status = 'OPEN'
        """)
        open_count, total_lots = cur.fetchone()
        conn.close()

        limits = {
            'MAX_OPEN_POSITIONS':   3,
            'MAX_LOT_PER_SYMBOL':   0.01,
            'MAX_TOTAL_LOTS':       0.03,
            'MIN_MARGIN_LEVEL_PCT': 200.0,
            'MIN_FREE_MARGIN_EUR':  10.0,
            'MAX_DAILY_LOSS_EUR':   10.0,
        }
        actual = {
            'open_positions':  int(open_count),
            'total_lots':      float(total_lots),
        }
        return _json({'limits': limits, 'actual': actual})
    except Exception as e:
        return f"Error: {e}"


# ── DATABASE ──────────────────────────────────────────────────────────────────

@mcp.tool()
def run_query(sql: str) -> str:
    """
    Run a read-only SQL SELECT or WITH query on KLDA-HFT_Database.
    Only SELECT / WITH statements allowed — no mutations.
    Example: SELECT COUNT(*), symbol FROM ticks GROUP BY symbol ORDER BY 1 DESC LIMIT 5
    """
    sql_stripped = sql.strip().upper()
    if not (sql_stripped.startswith("SELECT") or sql_stripped.startswith("WITH")):
        return "Error: only SELECT or WITH queries allowed"
    try:
        conn = get_conn()
        cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(sql)
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return _json(rows)
    except Exception as e:
        return f"Query error: {e}"


@mcp.tool()
def table_overview() -> str:
    """
    Row counts and latest timestamps for all key trading tables.
    """
    tables = [
        ('ticks',            'time'),
        ('cagg_bars_m5',     'time'),
        ('current',          'last_updated'),
        ('signals',          'time'),
        ('paper_positions',  'opened_at'),
        ('paper_orders',     'time'),
        ('account_snapshots','time'),
        ('system_flags',     None),
    ]
    result = {}
    try:
        conn = get_conn()
        cur  = conn.cursor()
        for table, time_col in tables:
            try:
                if time_col:
                    cur.execute(f"SELECT COUNT(*), MIN({time_col}), MAX({time_col}) FROM {table}")
                    cnt, mn, mx = cur.fetchone()
                    result[table] = {'rows': cnt, 'oldest': str(mn), 'newest': str(mx)}
                else:
                    cur.execute(f"SELECT COUNT(*) FROM {table}")
                    result[table] = {'rows': cur.fetchone()[0]}
            except Exception as e:
                result[table] = {'error': str(e)}
        conn.close()
        return _json(result)
    except Exception as e:
        return f"Error: {e}"


if __name__ == '__main__':
    mcp.run()
