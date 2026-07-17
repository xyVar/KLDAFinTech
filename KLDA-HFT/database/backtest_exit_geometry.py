#!/usr/bin/env python3
"""
Exit-geometry sweep for the Renaissance 5-metric signal (SpotCrude).

The 2026-07-17 full-history run showed the ENTRY signal hits 58.4%
directionally, but the 0.5%TP/1.0%SL exit geometry loses money (breakeven
there is 66.7%). This script holds the entry signal fixed and sweeps exits:

  (a) symmetric      TP 0.50% / SL 0.50%
  (b) 2:1 reward     TP 1.00% / SL 0.50%
  (c) symmetric wide TP 0.75% / SL 0.75%
  (d) original       TP 0.50% / SL 1.00%   (reference)

Each geometry also runs with a TIME STOP variant: force exit at market
(bid) after TIME_STOP_MIN minutes if neither level hit — intraday-only
means positions can't ride anyway.

For each variant: occurrences, win rate, geometry-implied null win rate,
one-sided binomial p-value vs that null, net P&L, profit factor.

Data is loaded ONCE and signals computed ONCE (entry logic identical to
backtest_5metric.py). Run one backtest at a time on this machine (OOM).
"""

import psycopg2
import pandas as pd
import numpy as np
import math
from datetime import datetime

SYMBOL = 'SpotCrude'
INITIAL_CAPITAL = 10000.0
POSITION_PCT = 1.0          # fixed 1% sizing (same as backtest_5metric.py A2)
COMMISSION_PER_SHARE = 0.0  # CFD — spread paid via ask entry / bid exit

# Entry parameters — identical to backtest_5metric.py (do not tune here)
MEAN_REV_WINDOW = 50
MEAN_REV_THRESHOLD = -0.2
SPREAD_VOL_WINDOW = 100
SPREAD_WIDEN_THRESHOLD = 50.0
HMM_WINDOW = 200
HMM_TREND_THRESHOLD = 0.1

TIME_STOP_MIN = 60  # minutes (= 12 M5 bars)

GEOMETRIES = [
    ('a  0.50/0.50', 0.0050, 0.0050),
    ('b  1.00/0.50', 0.0100, 0.0050),
    ('c  0.75/0.75', 0.0075, 0.0075),
    ('d  0.50/1.00 (orig)', 0.0050, 0.0100),
]


def binom_p_one_sided(k, n, p0):
    """P(X >= k | n, p0), exact for small n, normal approx otherwise."""
    if n == 0:
        return float('nan')
    if n <= 1000:
        return sum(math.comb(n, i) * p0**i * (1 - p0)**(n - i) for i in range(k, n + 1))
    mu = n * p0
    sd = math.sqrt(n * p0 * (1 - p0))
    z = (k - 0.5 - mu) / sd
    return 0.5 * math.erfc(z / math.sqrt(2))


print("=" * 100)
print(f"EXIT-GEOMETRY SWEEP — {SYMBOL} — entry signal fixed, exits varied")
print("=" * 100)

print("\n[1/3] Loading ticks...")
conn = psycopg2.connect(host='127.0.0.1', port=5432, database='KLDA-HFT_Database',
                        user='postgres', password='MyKldaTechnologies2025!')
df = pd.read_sql_query(
    "SELECT time, bid, ask, spread FROM ticks WHERE symbol = %s ORDER BY time ASC",
    conn, params=(SYMBOL,))
conn.close()
print(f"    {len(df):,} ticks  {df['time'].min()} -> {df['time'].max()}")

print("\n[2/3] Computing entry signal (identical to backtest_5metric.py)...")
df['ma50'] = df['bid'].rolling(MEAN_REV_WINDOW).mean()
df['mean_rev'] = ((df['bid'] - df['ma50']) / df['ma50']) * 100.0
df['spread_ma100'] = df['spread'].rolling(SPREAD_VOL_WINDOW).mean()
df['spread_vol'] = ((df['spread'] - df['spread_ma100']) / df['spread_ma100']) * 100.0
df['recent_avg'] = df['bid'].rolling(HMM_WINDOW // 2).mean()
df['older_avg'] = df['bid'].shift(HMM_WINDOW // 2).rolling(HMM_WINDOW // 2).mean()
df['trend_pct'] = ((df['recent_avg'] - df['older_avg']) / df['older_avg']) * 100.0
bearish = df['trend_pct'] < -HMM_TREND_THRESHOLD
df['signal'] = (
    (df['mean_rev'] < MEAN_REV_THRESHOLD)
    & (df['spread_vol'] < SPREAD_WIDEN_THRESHOLD)
    & (~bearish)
)
df = df.dropna(subset=['mean_rev', 'spread_vol', 'trend_pct'])

# Plain arrays — 8 variants over 14.6M rows is too slow via itertuples
times = df['time'].values.astype('datetime64[ns]').astype(np.int64)  # ns
bids = df['bid'].to_numpy(dtype=np.float64)
asks = df['ask'].to_numpy(dtype=np.float64)
sigs = df['signal'].to_numpy(dtype=bool)
n_rows = len(bids)
TIME_STOP_NS = TIME_STOP_MIN * 60 * 1_000_000_000

print(f"    {n_rows:,} usable rows, {sigs.sum():,} signal-true ticks")

print(f"\n[3/3] Running {len(GEOMETRIES)} geometries x (no stop | {TIME_STOP_MIN}min stop)...")


def run_variant(tp_pct, sl_pct, time_stop_ns):
    capital = INITIAL_CAPITAL
    in_pos = False
    entry_price = shares = tp_level = sl_level = 0.0
    entry_ns = 0
    profits = []
    time_stop_exits = 0

    for i in range(n_rows):
        if not in_pos:
            if sigs[i]:
                entry_price = asks[i]
                shares = (capital * POSITION_PCT / 100.0) / entry_price
                tp_level = entry_price * (1.0 + tp_pct)
                sl_level = entry_price * (1.0 - sl_pct)
                entry_ns = times[i]
                in_pos = True
        else:
            bid = bids[i]
            exit_price = None
            if bid >= tp_level:
                exit_price = tp_level
            elif bid <= sl_level:
                exit_price = sl_level
            elif time_stop_ns and times[i] - entry_ns >= time_stop_ns:
                exit_price = bid
                time_stop_exits += 1
            if exit_price is not None:
                profit = (exit_price - entry_price) * shares - COMMISSION_PER_SHARE * shares * 2
                capital += profit
                profits.append(profit)
                in_pos = False

    profits = np.array(profits)
    n = len(profits)
    wins = int((profits > 0).sum())
    losses = int((profits < 0).sum())
    win_rate = wins / n * 100 if n else 0.0
    net = profits.sum() if n else 0.0
    gross_win = profits[profits > 0].sum() if wins else 0.0
    gross_loss = abs(profits[profits < 0].sum()) if losses else 0.0
    pf = gross_win / gross_loss if gross_loss > 0 else float('inf')

    # Geometry-implied null: breakeven win rate from realized avg win/loss.
    # For pure TP/SL exits this equals SL/(TP+SL); with time stops it
    # reflects the realized (mixed) payoff distribution.
    avg_win = gross_win / wins if wins else 0.0
    avg_loss = gross_loss / losses if losses else 0.0
    p_null = avg_loss / (avg_win + avg_loss) if (avg_win + avg_loss) > 0 else 0.5
    p_val = binom_p_one_sided(wins, wins + losses, p_null)

    return {
        'n': n, 'wins': wins, 'losses': losses, 'win_rate': win_rate,
        'p_null': p_null * 100, 'p_val': p_val, 'net': net, 'pf': pf,
        'time_stop_exits': time_stop_exits,
    }


results = []
for name, tp, sl in GEOMETRIES:
    theo_null = sl / (tp + sl) * 100
    for stop_label, stop_ns in (('no stop', 0), (f'{TIME_STOP_MIN}m stop', TIME_STOP_NS)):
        r = run_variant(tp, sl, stop_ns)
        r['name'] = name
        r['stop'] = stop_label
        r['theo_null'] = theo_null
        results.append(r)
        print(f"    {name:<22} {stop_label:<9} n={r['n']:<5} done")

print("\n" + "=" * 100)
print("SUMMARY — entry signal fixed (243-trade class), exits varied")
print("=" * 100)
hdr = (f"{'Geometry TP/SL':<22} {'Stop':<9} {'N':>5} {'WinRate':>8} "
       f"{'Null*':>7} {'p-value':>10} {'NetP&L':>10} {'PF':>6} {'TStops':>7}")
print(hdr)
print("-" * len(hdr))
for r in results:
    verdict = 'PASS' if (r['p_val'] < 0.05 and r['net'] > 0 and r['n'] >= 100) else '    '
    print(f"{r['name']:<22} {r['stop']:<9} {r['n']:>5} {r['win_rate']:>7.1f}% "
          f"{r['p_null']:>6.1f}% {r['p_val']:>10.2e} {r['net']:>+10.2f} "
          f"{r['pf']:>6.2f} {r['time_stop_exits']:>7} {verdict}")
print("-" * len(hdr))
print("*Null = breakeven win rate implied by realized avg win/loss (equals SL/(TP+SL)")
print(" for pure TP/SL exits). PASS requires: N>=100, p<0.05 vs null, AND net>0.")
print("=" * 100)
