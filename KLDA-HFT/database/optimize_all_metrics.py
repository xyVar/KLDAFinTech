#!/usr/bin/env python3
"""
TSLA - Complete Parameter Optimization
Finds optimal tick windows for ALL Renaissance metrics
"""

import psycopg2
from datetime import datetime

# Database connection
conn = psycopg2.connect(
    host='localhost',
    port=5432,
    database='KLDA-HFT_Database',
    user='postgres',
    password='MyKldaTechnologies2025!'
)

print("=" * 80)
print("TSLA - COMPLETE PARAMETER OPTIMIZATION")
print("=" * 80)

cursor = conn.cursor()

# Check data availability
cursor.execute("SELECT COUNT(*), MIN(time), MAX(time) FROM tsla_history;")
row = cursor.fetchone()
print(f"\nData Available:")
print(f"  Total Ticks: {row[0]:,}")
print(f"  Period: {row[1]} to {row[2]}")

if row[0] < 1000:
    print("\n[ERROR] Insufficient data (need 1000+ ticks)")
    exit(1)

# ============================================================================
# 1. MEAN REVERSION OPTIMIZATION (Already done - showing result)
# ============================================================================
print("\n" + "=" * 80)
print("1. MEAN REVERSION - Window Optimization")
print("=" * 80)
print("Result: 50-tick window, +0.23% avg return (COMPLETED)")

# ============================================================================
# 2. ORDER FLOW OPTIMIZATION
# ============================================================================
print("\n" + "=" * 80)
print("2. ORDER FLOW - Window Optimization")
print("=" * 80)
print("Testing different windows for buy/sell volume accumulation...")

windows_to_test = [50, 100, 200, 500]
results = []

for window in windows_to_test:
    print(f"\nTesting {window}-tick window...")

    cursor.execute(f"""
        WITH signals AS (
            SELECT
                bid,
                SUM(buy_volume) OVER (ORDER BY time ROWS BETWEEN {window} PRECEDING AND CURRENT ROW) as total_buy,
                SUM(sell_volume) OVER (ORDER BY time ROWS BETWEEN {window} PRECEDING AND CURRENT ROW) as total_sell,
                SUM(buy_volume) OVER (ORDER BY time ROWS BETWEEN {window} PRECEDING AND CURRENT ROW) -
                SUM(sell_volume) OVER (ORDER BY time ROWS BETWEEN {window} PRECEDING AND CURRENT ROW) as net_flow,
                LEAD(bid, 50) OVER (ORDER BY time) as price_after
            FROM tsla_history
            ORDER BY time
            LIMIT 50000
        ),
        trades AS (
            SELECT
                bid,
                net_flow,
                ((price_after - bid) / bid) * 100 as return_pct,
                CASE WHEN price_after > bid * 1.005 THEN 1 ELSE 0 END as is_win
            FROM signals
            WHERE price_after IS NOT NULL
              AND net_flow > 1000  -- Signal threshold: positive flow > 1000
        )
        SELECT
            COUNT(*) as total_signals,
            SUM(is_win) as wins,
            ROUND((SUM(is_win)::numeric / NULLIF(COUNT(*), 0)) * 100, 1) as win_rate,
            ROUND(AVG(return_pct), 2) as avg_return,
            ROUND(MIN(return_pct), 2) as worst_return,
            ROUND(MAX(return_pct), 2) as best_return
        FROM trades;
    """)

    row = cursor.fetchone()
    total_signals = row[0] or 0
    wins = row[1] or 0
    win_rate = row[2] or 0.0
    avg_return = row[3] or 0.0
    worst_return = row[4] or 0.0
    best_return = row[5] or 0.0

    results.append({
        'window': window,
        'signals': total_signals,
        'wins': wins,
        'win_rate': win_rate,
        'avg_return': avg_return,
        'worst': worst_return,
        'best': best_return
    })

    print(f"  Signals: {total_signals}, Wins: {wins}, Win Rate: {win_rate}%")
    print(f"  Avg Return: {avg_return}%, Range: {best_return}% / {worst_return}%")

print("\n" + "-" * 80)
print("RESULTS - Order Flow Optimization")
print("-" * 80)
print(f"{'Window':<8} {'Signals':<8} {'Wins':<8} {'Win%':<8} {'Avg Ret':<10} {'Best/Worst'}")
print("-" * 80)

best_window = None
best_metric = -999

for r in results:
    metric = r['avg_return'] if r['signals'] > 20 else -999
    marker = " <-- BEST" if metric > best_metric else ""

    print(f"{r['window']:<8} {r['signals']:<8} {r['wins']:<8} {r['win_rate']:<8} "
          f"{r['avg_return']:<10} {r['best']}% / {r['worst']}%{marker}")

    if metric > best_metric:
        best_metric = metric
        best_window = r['window']

if best_window and best_metric > 0:
    print(f"\n[OK] OPTIMAL ORDER FLOW WINDOW: {best_window} ticks")
    print(f"     Average Return: +{best_metric}%")
else:
    print(f"\n[X] Order Flow shows NO EDGE on this data")
    print(f"     Best avg return: {best_metric}%")

# ============================================================================
# 3. HMM REGIME OPTIMIZATION
# ============================================================================
print("\n" + "=" * 80)
print("3. HMM REGIME - Window Optimization")
print("=" * 80)
print("Testing different windows for trend detection...")

windows_to_test = [20, 50, 100, 200]
results = []

for window in windows_to_test:
    print(f"\nTesting {window}-tick window...")

    half_window = window // 2

    cursor.execute(f"""
        WITH signals AS (
            SELECT
                bid,
                AVG(bid) OVER (ORDER BY time ROWS BETWEEN {half_window} PRECEDING AND CURRENT ROW) as recent_avg,
                AVG(bid) OVER (ORDER BY time ROWS BETWEEN {window} PRECEDING AND {half_window + 1} PRECEDING) as older_avg,
                LEAD(bid, 50) OVER (ORDER BY time) as price_after
            FROM tsla_history
            ORDER BY time
            LIMIT 50000
        ),
        regime_signals AS (
            SELECT
                bid,
                recent_avg,
                older_avg,
                ((recent_avg - older_avg) / older_avg) * 100 as trend_pct,
                CASE
                    WHEN ((recent_avg - older_avg) / older_avg) * 100 > 0.3 THEN 'BULLISH'
                    WHEN ((recent_avg - older_avg) / older_avg) * 100 < -0.3 THEN 'BEARISH'
                    ELSE 'NEUTRAL'
                END as regime,
                price_after
            FROM signals
            WHERE recent_avg IS NOT NULL
              AND older_avg IS NOT NULL
        ),
        trades AS (
            SELECT
                bid,
                regime,
                ((price_after - bid) / bid) * 100 as return_pct,
                CASE WHEN price_after > bid * 1.005 THEN 1 ELSE 0 END as is_win
            FROM regime_signals
            WHERE regime = 'BULLISH'
              AND price_after IS NOT NULL
        )
        SELECT
            COUNT(*) as total_signals,
            SUM(is_win) as wins,
            ROUND((SUM(is_win)::numeric / NULLIF(COUNT(*), 0)) * 100, 1) as win_rate,
            ROUND(AVG(return_pct), 2) as avg_return,
            ROUND(MIN(return_pct), 2) as worst_return,
            ROUND(MAX(return_pct), 2) as best_return
        FROM trades;
    """)

    row = cursor.fetchone()
    total_signals = row[0] or 0
    wins = row[1] or 0
    win_rate = row[2] or 0.0
    avg_return = row[3] or 0.0
    worst_return = row[4] or 0.0
    best_return = row[5] or 0.0

    results.append({
        'window': window,
        'signals': total_signals,
        'wins': wins,
        'win_rate': win_rate,
        'avg_return': avg_return,
        'worst': worst_return,
        'best': best_return
    })

    print(f"  Signals: {total_signals}, Wins: {wins}, Win Rate: {win_rate}%")
    print(f"  Avg Return: {avg_return}%, Range: {best_return}% / {worst_return}%")

print("\n" + "-" * 80)
print("RESULTS - HMM Regime Optimization")
print("-" * 80)
print(f"{'Window':<8} {'Signals':<8} {'Wins':<8} {'Win%':<8} {'Avg Ret':<10} {'Best/Worst'}")
print("-" * 80)

best_window = None
best_metric = -999

for r in results:
    metric = r['avg_return'] if r['signals'] > 20 else -999
    marker = " <-- BEST" if metric > best_metric else ""

    print(f"{r['window']:<8} {r['signals']:<8} {r['wins']:<8} {r['win_rate']:<8} "
          f"{r['avg_return']:<10} {r['best']}% / {r['worst']}%{marker}")

    if metric > best_metric:
        best_metric = metric
        best_window = r['window']

if best_window and best_metric > 0:
    print(f"\n[OK] OPTIMAL HMM REGIME WINDOW: {best_window} ticks")
    print(f"     Average Return: +{best_metric}%")
else:
    print(f"\n[X] HMM Regime shows NO EDGE on this data")
    print(f"     Best avg return: {best_metric}%")

# ============================================================================
# FINAL SUMMARY
# ============================================================================
print("\n" + "=" * 80)
print("OPTIMIZATION COMPLETE - TSLA OPTIMAL PARAMETERS")
print("=" * 80)
print("\nRecommended Settings:")
print("  Mean Reversion:  50-tick window   (+0.23% avg return)")
print("  Order Flow:      [See results above]")
print("  HMM Regime:      [See results above]")
print("\nNext Steps:")
print("  1. Update C++ backend with optimal parameters")
print("  2. Start Docker container")
print("  3. Monitor renaissance_terminal.html for entry signals")
print("=" * 80)

cursor.close()
conn.close()
