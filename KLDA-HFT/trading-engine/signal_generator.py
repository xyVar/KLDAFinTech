#!/usr/bin/env python3
"""
KLDA Renaissance Signal Generator
Reads M5 bars + live ticks → calculates 5 metrics → writes PENDING signals

Flow:
  cagg_bars_m5 (live continuous aggregate, last 200 bars = ~17h lookback)
  + ticks (current bid/ask/spread)
  → 5 Renaissance metrics
  → signals table (status=PENDING)
  → klda_engine.py picks up → MT5 execution (or paper log in PAPER_MODE)

Run: python signal_generator.py
"""

import psycopg2
import psycopg2.extras
import time
import json
from datetime import datetime
import os

# ── CONFIG ────────────────────────────────────────────────────────────────────
DB_CONFIG = {
    'host':     os.environ.get('DB_HOST',     'localhost'),
    'port':     int(os.environ.get('DB_PORT', '5432')),
    'database': os.environ.get('DB_NAME',     'KLDA-HFT_Database'),
    'user':     os.environ.get('DB_USER',     'postgres'),
    'password': os.environ.get('DB_PASSWORD', 'MyKldaTechnologies2025!'),
}

# Symbol map: (signal_name, tick_symbol)
# Bars now come from cagg_bars_m5 (live continuous aggregate)
# Only include symbols actively streaming in cagg_bars_m5
SYMBOLS = [
    # Backtest-confirmed edge on this signal (March–April 2026)
    ('NatGas',    'NatGas'),
    ('SpotCrude', 'SpotCrude'),
    ('NAS100',    'NAS100'),
    ('GER40',     'GER40'),
    # Removed — no edge on this signal: XAUUSD, XAGUSD, Gasoline, US500, Copper, XPTUSD, AMD, US30
]

# Paper mode — writes to signals table, order router opens paper positions
PAPER_MODE = False

# ── THRESHOLDS ────────────────────────────────────────────────────────────────
# 1. Mean Reversion — price % below 50-bar M5 MA (~4h lookback)
MEAN_REV_THRESHOLD   = -0.30   # must be ≥0.30% below MA50

# 2. Spread Volatility — current spread vs 100-bar avg spread (M5 bars)
SPREAD_VOL_MAX       = 150.0   # current spread < 150% of avg (not unusually wide)

# 3. HMM Regime — recent 50-bar avg vs older 50-bar avg (trend direction)
HMM_TREND_THRESHOLD  = 0.05    # % difference to qualify as BULLISH

# 4. Transaction Cost — (ask - bid) / ask as % — real spread ratio
MAX_TX_COST_PCT      = 0.15    # max 0.15% actual spread (NAS100 ~0.004%, stocks ~0.01-0.08%)

# 5. Kelly — baseline 51.5% theoretical win rate (Renaissance-style edge)
WIN_RATE_BASELINE    = 0.515   # use this when no trade history
KELLY_FRACTION       = 0.25    # 25% Kelly (conservative)
MIN_KELLY_PCT        = 0.3     # minimum 0.3% position size

# Run control
LOOP_INTERVAL_SEC    = 10      # scan every 10s
MIN_BARS_REQUIRED    = 60      # need at least 60 bars to compute metrics
MIN_CONFIDENCE       = 80.0    # need 4/5 or 5/5 conditions met

# ── HELPERS ───────────────────────────────────────────────────────────────────
def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

def get_conn():
    return psycopg2.connect(**DB_CONFIG)

# ── METRICS ───────────────────────────────────────────────────────────────────
def calculate_metrics(cur, tick_sym):
    """
    5 Renaissance metrics using cagg_bars_m5 + current tick.
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
    mean_rev_ok = mean_rev < MEAN_REV_THRESHOLD   # price meaningfully below MA

    # ── 2. Spread Volatility ────────────────────────────────────────────
    # Compare current bar spread vs 100-bar average (from bars table)
    avg_bar_spread   = sum(spreads[:100]) / min(100, len(spreads)) if spreads else 0
    current_bar_spread = float(rows[0][4]) if rows[0][4] else avg_bar_spread
    spread_ratio     = (current_bar_spread / avg_bar_spread * 100.0) if avg_bar_spread > 0 else 100.0
    spread_vol_ok    = spread_ratio < SPREAD_VOL_MAX

    # ── 3. HMM Regime ──────────────────────────────────────────────────
    recent_50 = closes[:50]
    older_50  = closes[50:100]
    recent_avg = sum(recent_50) / len(recent_50)
    older_avg  = sum(older_50)  / len(older_50) if older_50 else recent_avg
    trend_pct  = ((recent_avg - older_avg) / older_avg) * 100.0 if older_avg > 0 else 0

    if trend_pct > HMM_TREND_THRESHOLD:
        regime = 'BULLISH'
    elif trend_pct < -HMM_TREND_THRESHOLD:
        regime = 'BEARISH'
    else:
        regime = 'NEUTRAL'
    regime_ok = (regime == 'BULLISH')

    # ── 4. Transaction Cost (real) ──────────────────────────────────────
    tx_cost_pct = (current_ask - current_bid) / current_ask * 100.0
    tx_cost_ok  = tx_cost_pct < MAX_TX_COST_PCT

    # ── 5. Kelly Criterion ──────────────────────────────────────────────
    # Use WIN_RATE_BASELINE (theoretical edge) — no trade history yet
    p = WIN_RATE_BASELINE
    q = 1.0 - p
    b = 1.0  # 1:1 base risk/reward (conservative)
    kelly_raw = (b * p - q) / b
    kelly_pct = max(0.0, kelly_raw * KELLY_FRACTION * 100.0)
    kelly_ok  = kelly_pct >= MIN_KELLY_PCT

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

# ── MAIN LOOP ─────────────────────────────────────────────────────────────────
def main():
    log("=" * 70)
    log("KLDA Renaissance Signal Generator — STARTING")
    log(f"  Symbols : {len(SYMBOLS)}")
    log(f"  Bars    : cagg_bars_m5 (live continuous aggregate, last 200 = ~17h)")
    log(f"  Signal  : all 5 conditions met (confidence = 100%)")
    log(f"  Interval: every {LOOP_INTERVAL_SEC}s")
    log(f"  Mode    : {'PAPER (log only)' if PAPER_MODE else 'LIVE (writes to signals table)'}")
    log("=" * 70)

    scan_count = 0

    while True:
        scan_count += 1
        signals_fired = 0
        skipped_no_data = 0

        try:
            conn = get_conn()
            cur  = conn.cursor()

            for signal_sym, tick_sym in SYMBOLS:
                try:
                    m = calculate_metrics(cur, tick_sym)

                    if m is None:
                        skipped_no_data += 1
                        continue

                    if m['confidence'] < MIN_CONFIDENCE:
                        continue

                    if not m['signal']:
                        continue

                    if not PAPER_MODE and has_pending_signal(cur, signal_sym):
                        continue

                    signals_fired += 1
                    log(
                        f"[SIGNAL] {signal_sym:<12} BUY  conf={m['confidence']}%  "
                        f"mean_rev={m['mean_rev']:+.3f}%  "
                        f"regime={m['regime']}  "
                        f"tx={m['tx_cost_pct']:.4f}%  "
                        f"kelly={m['kelly_pct']:.2f}%"
                        + (" [PAPER]" if PAPER_MODE else "")
                    )

                    if not PAPER_MODE:
                        write_signal(cur, conn, signal_sym, m)

                except Exception as e:
                    conn.rollback()
                    log(f"[WARN] {signal_sym}: {e}")

            conn.close()

        except Exception as e:
            log(f"[ERROR] DB error: {e}")

        if scan_count % 6 == 0:  # every ~60s
            log(f"[STATUS] scan #{scan_count}  signals_fired={signals_fired}  no_data={skipped_no_data}")

        time.sleep(LOOP_INTERVAL_SEC)


if __name__ == '__main__':
    main()
