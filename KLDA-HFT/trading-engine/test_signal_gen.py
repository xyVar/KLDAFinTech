#!/usr/bin/env python3
"""
Quick diagnostic — one scan, prints all metrics, does NOT write to DB.
Run: python test_signal_gen.py
"""
import psycopg2, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from signal_generator import SYMBOLS, DB_CONFIG, calculate_metrics, MIN_CONFIDENCE

conn = psycopg2.connect(**DB_CONFIG)
cur  = conn.cursor()

header = f"{'Symbol':<12} {'Bid':>10}  {'MeanRev':>9}  {'MA50':>10}  {'Regime':>8}  {'SpdOK':>5}  {'TxCost':>7}  {'Kelly':>5}  {'Cond':>4}  {'Conf':>5}  SIGNAL"
print(header)
print("-" * len(header))

for signal_sym, tick_sym, bars_table in SYMBOLS:
    m = calculate_metrics(cur, tick_sym, bars_table)
    if m is None:
        print(f"{signal_sym:<12} NO DATA (not enough M5 bars or no current tick)")
        continue
    sig = "*** BUY ***" if m['signal'] else "-"
    print(
        f"{signal_sym:<12} {m['current_bid']:>10.4f}  "
        f"{m['mean_rev']:>+9.4f}%  "
        f"{m['ma50']:>10.4f}  "
        f"{m['regime']:>8}  "
        f"{'Y' if m['spread_vol_ok'] else 'N':>5}  "
        f"{m['tx_cost_pct']:>6.4f}%  "
        f"{m['kelly_pct']:>5.2f}%  "
        f"{m['conditions_met']:>4}/5  "
        f"{m['confidence']:>5.1f}%  "
        f"{sig}"
    )

conn.close()
print()
print(f"Signal threshold: confidence >= {MIN_CONFIDENCE}% AND all 5 conditions met")
