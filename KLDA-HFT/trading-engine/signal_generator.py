#!/usr/bin/env python3
"""
KLDA Renaissance Signal Generator
Reads M5 bars + live ticks → calculates 5 metrics → writes PENDING signals

Flow:
  cagg_bars_m5 (live continuous aggregate, last 200 bars = ~17h lookback)
  + ticks (current bid/ask/spread)
  → 5 Renaissance metrics (thresholds per-symbol from config/trading_config.json)
  → signals table (status=PENDING)
  → order_router.py picks up → broker_adapter (paper or live per config)

Run continuously:  python signal_generator.py
Run once (daily):  python signal_generator.py --daily --symbol SpotCrude
                   one scan, writes signals, prints + saves an end-of-day report
"""

import psycopg2
import psycopg2.extras
import time
import json
import argparse
from datetime import datetime, date
from pathlib import Path
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config_loader import paper_mode, thresholds_for

# ── CONFIG ────────────────────────────────────────────────────────────────────
DB_CONFIG = {
    'host':     os.environ.get('DB_HOST',     '127.0.0.1'),
    'port':     int(os.environ.get('DB_PORT', '5432')),
    'database': os.environ.get('DB_NAME',     'KLDA-HFT_Database'),
    'user':     os.environ.get('DB_USER',     'postgres'),
    'password': os.environ.get('DB_PASSWORD', 'MyKldaTechnologies2025!'),
}

# Symbol map: (signal_name, tick_symbol)
# Bars come from cagg_bars_m5 (live continuous aggregate)
# Only include symbols actively streaming in cagg_bars_m5
SYMBOLS = [
    # Backtest-confirmed edge on this signal (March–April 2026)
    ('NatGas',    'NatGas'),
    ('SpotCrude', 'SpotCrude'),
    ('NAS100',    'NAS100'),
    ('GER40',     'GER40'),
    # Removed — no edge on this signal: XAUUSD, XAGUSD, Gasoline, US500, Copper, XPTUSD, AMD, US30
]

# Paper mode — single source of truth: config/trading_config.json
PAPER_MODE = paper_mode()

# ── RUN CONTROL (not per-symbol) ─────────────────────────────────────────────
LOOP_INTERVAL_SEC    = 10      # scan every 10s (continuous mode)
MIN_BARS_REQUIRED    = 60      # need at least 60 bars to compute metrics
MIN_CONFIDENCE       = 80.0    # need 4/5 or 5/5 conditions met

REPORTS_DIR = Path(__file__).resolve().parent.parent / 'reports'

# ── HELPERS ───────────────────────────────────────────────────────────────────
def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

def get_conn():
    return psycopg2.connect(**DB_CONFIG)

# ── METRICS ───────────────────────────────────────────────────────────────────
def calculate_metrics(cur, tick_sym, th):
    """
    5 Renaissance metrics using cagg_bars_m5 + current tick.
    th: per-symbol threshold dict from config (see thresholds_for()).
    Returns dict or None if not enough data.
    """

    # ── Current tick (bid/ask) ──────────────────────────────────────────
    cur.execute("""
        SELECT bid, ask FROM current WHERE symbol = %s
    """, (tick_sym,))
    row = cur.fetchone()
    if not row:
        return None
    current_bid = float(row[0])
    current_ask = float(row[1])
    if current_ask <= 0:
        return None

    # ── M5 bars from live continuous aggregate ───────────────────────────
    cur.execute("""
        SELECT close, open, high, low, spread
        FROM cagg_bars_m5
        WHERE symbol = %s
        ORDER BY time DESC
        LIMIT 200
    """, (tick_sym,))
    rows = cur.fetchall()
    if len(rows) < MIN_BARS_REQUIRED:
        return None

    closes  = [float(r[0]) for r in rows]
    spreads = [float(r[4]) for r in rows if r[4] is not None and float(r[4]) > 0]

    # ── 1. Mean Reversion ───────────────────────────────────────────────
    ma50      = sum(closes[:50]) / 50
    mean_rev  = ((current_bid - ma50) / ma50) * 100.0
    mean_rev_ok = mean_rev < th['mean_rev_threshold']   # price meaningfully below MA

    # ── 2. Spread Volatility ────────────────────────────────────────────
    # Compare current bar spread vs 100-bar average (from bars table)
    avg_bar_spread   = sum(spreads[:100]) / min(100, len(spreads)) if spreads else 0
    current_bar_spread = float(rows[0][4]) if rows[0][4] else avg_bar_spread
    spread_ratio     = (current_bar_spread / avg_bar_spread * 100.0) if avg_bar_spread > 0 else 100.0
    spread_vol_ok    = spread_ratio < th['spread_vol_max']

    # ── 3. HMM Regime ──────────────────────────────────────────────────
    recent_50 = closes[:50]
    older_50  = closes[50:100]
    recent_avg = sum(recent_50) / len(recent_50)
    older_avg  = sum(older_50)  / len(older_50) if older_50 else recent_avg
    trend_pct  = ((recent_avg - older_avg) / older_avg) * 100.0 if older_avg > 0 else 0

    if trend_pct > th['hmm_trend_threshold']:
        regime = 'BULLISH'
    elif trend_pct < -th['hmm_trend_threshold']:
        regime = 'BEARISH'
    else:
        regime = 'NEUTRAL'
    regime_ok = (regime in th['regime_allow'])

    # ── 4. Transaction Cost (real) ──────────────────────────────────────
    tx_cost_pct = (current_ask - current_bid) / current_ask * 100.0
    tx_cost_ok  = tx_cost_pct < th['max_tx_cost_pct']

    # ── 5. Kelly Criterion ──────────────────────────────────────────────
    # Use win_rate_baseline (theoretical edge) — no trade history yet
    p = th['win_rate_baseline']
    q = 1.0 - p
    b = 1.0  # 1:1 base risk/reward (conservative)
    kelly_raw = (b * p - q) / b
    kelly_pct = max(0.0, kelly_raw * th['kelly_fraction'] * 100.0)
    kelly_ok  = kelly_pct >= th['min_kelly_pct']

    # ── Summary ─────────────────────────────────────────────────────────
    conditions_met = sum([mean_rev_ok, spread_vol_ok, regime_ok, tx_cost_ok, kelly_ok])
    confidence     = (conditions_met / 5.0) * 100.0

    return {
        'current_bid':    current_bid,
        'current_ask':    current_ask,
        'ma50':           round(ma50, 6),
        'mean_rev':       round(mean_rev, 4),
        'spread_ratio':   round(spread_ratio, 2),
        'avg_bar_spread': round(avg_bar_spread, 2),
        'regime':         regime,
        'trend_pct':      round(trend_pct, 4),
        'tx_cost_pct':    round(tx_cost_pct, 6),
        'kelly_pct':      round(kelly_pct, 4),
        'mean_rev_ok':    mean_rev_ok,
        'spread_vol_ok':  spread_vol_ok,
        'regime_ok':      regime_ok,
        'tx_cost_ok':     tx_cost_ok,
        'kelly_ok':       kelly_ok,
        'conditions_met': conditions_met,
        'confidence':     round(confidence, 1),
        'signal':         (conditions_met == 5),
    }

# ── SIGNAL WRITER ─────────────────────────────────────────────────────────────
def has_pending_signal(cur, signal_sym):
    cur.execute("""
        SELECT COUNT(*) FROM signals
        WHERE symbol = %s AND status IN ('PENDING', 'EXECUTING')
    """, (signal_sym,))
    return cur.fetchone()[0] > 0

def write_signal(cur, conn, signal_sym, m):
    pattern_data = json.dumps({
        'mean_rev':      m['mean_rev'],
        'ma50':          m['ma50'],
        'spread_ratio':  m['spread_ratio'],
        'regime':        m['regime'],
        'trend_pct':     m['trend_pct'],
        'tx_cost_pct':   m['tx_cost_pct'],
        'kelly_pct':     m['kelly_pct'],
    })
    cur.execute("""
        INSERT INTO signals
            (time, symbol, action, price, confidence,
             mean_rev, regime, spread_ok, cost_ok, kelly_pct,
             status, pattern_name, pattern_data)
        VALUES
            (NOW(), %s, 'BUY', %s, %s,
             %s, %s, %s, %s, %s,
             'PENDING', 'MEAN_REVERSION', %s)
    """, (
        signal_sym, m['current_ask'], m['confidence'],
        m['mean_rev'], m['regime'],
        m['spread_vol_ok'], m['tx_cost_ok'],
        m['kelly_pct'], pattern_data,
    ))
    conn.commit()

# ── ONE SCAN ──────────────────────────────────────────────────────────────────
def scan_once(conn, cur, symbols):
    """
    Evaluate all symbols once. Writes signals for full-confidence setups.
    Returns list of dicts: {symbol, metrics, fired}.
    """
    results = []
    for signal_sym, tick_sym in symbols:
        fired = False
        m = None
        try:
            m = calculate_metrics(cur, tick_sym, thresholds_for(signal_sym))

            if m is not None and m['confidence'] >= MIN_CONFIDENCE and m['signal']:
                if not has_pending_signal(cur, signal_sym):
                    write_signal(cur, conn, signal_sym, m)
                    fired = True
                    log(
                        f"[SIGNAL] {signal_sym:<12} BUY  conf={m['confidence']}%  "
                        f"mean_rev={m['mean_rev']:+.3f}%  "
                        f"regime={m['regime']}  "
                        f"tx={m['tx_cost_pct']:.4f}%  "
                        f"kelly={m['kelly_pct']:.2f}%"
                    )
        except Exception as e:
            conn.rollback()
            log(f"[WARN] {signal_sym}: {e}")
        results.append({'symbol': signal_sym, 'metrics': m, 'fired': fired})
    return results

# ── DAILY MODE ────────────────────────────────────────────────────────────────
def daily_run(symbol_filter):
    """
    --daily mode: one scan for the selected symbol(s), write signals,
    then print + save an end-of-day report (signals today, paper P&L,
    metric values from this scan).
    """
    symbols = [(s, t) for s, t in SYMBOLS
               if symbol_filter is None or s == symbol_filter]
    if not symbols:
        log(f"[ERROR] --symbol {symbol_filter} not in SYMBOLS list "
            f"({', '.join(s for s, _ in SYMBOLS)})")
        return 1

    conn = get_conn()
    cur  = conn.cursor()
    results = scan_once(conn, cur, symbols)

    today = date.today().isoformat()
    lines = []
    w = lines.append
    w("=" * 72)
    w(f"KLDA DAILY SIGNAL REPORT — {today} "
      f"({'PAPER' if PAPER_MODE else 'LIVE'} mode)")
    w("=" * 72)

    # ── This scan's metrics ─────────────────────────────────────────────
    w("")
    w("METRICS (this scan)")
    for r in results:
        m = r['metrics']
        if m is None:
            w(f"  {r['symbol']:<12} NO DATA (not enough M5 bars or no current tick)")
            continue
        th = thresholds_for(r['symbol'])
        w(f"  {r['symbol']:<12} bid={m['current_bid']:.4f}  "
          f"mean_rev={m['mean_rev']:+.3f}% (thr {th['mean_rev_threshold']})  "
          f"regime={m['regime']} (allow {'/'.join(th['regime_allow'])})  "
          f"spread_ratio={m['spread_ratio']:.0f}%  "
          f"tx={m['tx_cost_pct']:.4f}%  "
          f"cond={m['conditions_met']}/5"
          + ("  → SIGNAL FIRED" if r['fired'] else ""))

    # ── Signals written today ───────────────────────────────────────────
    sym_names = tuple(s for s, _ in symbols)
    cur.execute("""
        SELECT status, COUNT(*) FROM signals
        WHERE time::date = %s AND symbol IN %s
        GROUP BY status ORDER BY status
    """, (today, sym_names))
    sig_rows = cur.fetchall()
    w("")
    w("SIGNALS TODAY (" + ", ".join(sym_names) + ")")
    if sig_rows:
        for status, cnt in sig_rows:
            w(f"  {status:<10} {cnt}")
    else:
        w("  none")

    # ── Paper P&L today ─────────────────────────────────────────────────
    try:
        cur.execute("""
            SELECT
                COUNT(*) FILTER (WHERE status='CLOSED')                    AS closed,
                COUNT(*) FILTER (WHERE status='OPEN')                      AS open,
                COALESCE(SUM(pnl_eur) FILTER (WHERE status='CLOSED'), 0)   AS pnl,
                COUNT(*) FILTER (WHERE status='CLOSED' AND pnl_eur > 0)    AS wins,
                COUNT(*) FILTER (WHERE status='CLOSED' AND pnl_eur < 0)    AS losses
            FROM paper_positions
            WHERE opened_at::date = %s AND symbol IN %s
        """, (today, sym_names))
        closed, open_pos, pnl, wins, losses = cur.fetchone()
        w("")
        w("PAPER P&L TODAY")
        w(f"  closed={closed}  open={open_pos}  "
          f"pnl={float(pnl):+.4f} EUR  W/L={wins}/{losses}")
    except Exception as e:
        conn.rollback()
        w("")
        w(f"PAPER P&L TODAY: unavailable ({e})")

    w("=" * 72)
    conn.close()

    report = "\n".join(lines)
    print(report, flush=True)

    REPORTS_DIR.mkdir(exist_ok=True)
    suffix = symbol_filter or 'ALL'
    out = REPORTS_DIR / f"daily_{today}_{suffix}.txt"
    out.write_text(report + "\n", encoding='utf-8')
    log(f"[REPORT] saved to {out}")
    return 0

# ── MAIN LOOP (continuous mode) ───────────────────────────────────────────────
def main_loop():
    log("=" * 70)
    log("KLDA Renaissance Signal Generator — STARTING")
    log(f"  Symbols : {len(SYMBOLS)}")
    log(f"  Bars    : cagg_bars_m5 (live continuous aggregate, last 200 = ~17h)")
    log(f"  Signal  : all 5 conditions met (confidence = 100%)")
    log(f"  Interval: every {LOOP_INTERVAL_SEC}s")
    log(f"  Mode    : {'PAPER' if PAPER_MODE else 'LIVE'} (config/trading_config.json)")
    for s, _ in SYMBOLS:
        th = thresholds_for(s)
        log(f"  {s:<12} mean_rev<{th['mean_rev_threshold']}  "
            f"regime {'/'.join(th['regime_allow'])}  "
            f"trend_thr={th['hmm_trend_threshold']}")
    log("=" * 70)

    scan_count = 0
    while True:
        scan_count += 1
        signals_fired = 0
        skipped_no_data = 0

        try:
            conn = get_conn()
            cur  = conn.cursor()
            results = scan_once(conn, cur, SYMBOLS)
            signals_fired  = sum(1 for r in results if r['fired'])
            skipped_no_data = sum(1 for r in results if r['metrics'] is None)
            conn.close()
        except Exception as e:
            log(f"[ERROR] DB error: {e}")

        if scan_count % 6 == 0:  # every ~60s
            log(f"[STATUS] scan #{scan_count}  signals_fired={signals_fired}  no_data={skipped_no_data}")

        time.sleep(LOOP_INTERVAL_SEC)


def main():
    ap = argparse.ArgumentParser(description="KLDA Renaissance signal generator")
    ap.add_argument('--daily', action='store_true',
                    help='run one scan, write signals, save end-of-day report, exit')
    ap.add_argument('--symbol', default=None,
                    help='restrict to one symbol (e.g. SpotCrude); only with --daily')
    args = ap.parse_args()

    if args.symbol and not args.daily:
        ap.error('--symbol requires --daily')

    if args.daily:
        raise SystemExit(daily_run(args.symbol))
    main_loop()


if __name__ == '__main__':
    main()
