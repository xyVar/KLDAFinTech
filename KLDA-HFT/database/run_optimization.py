#!/usr/bin/env python3
"""
TSLA Parameter Optimization
Finds optimal tick windows for Renaissance metrics
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
print("TSLA PARAMETER OPTIMIZATION")
print("=" * 80)

# Check data availability
cursor = conn.cursor()
cursor.execute("""
    SELECT
        COUNT(*) as total_ticks,
        MIN(time) as earliest,
        MAX(time) as latest
    FROM tsla_history;
""")

row = cursor.fetchone()
print(f"\nData Available (ALL TIME):")
print(f"  Total Ticks: {row[0]:,}")
print(f"  Earliest: {row[1]}")
print(f"  Latest: {row[2]}")

if row[0] < 1000:
    print("\n[WARNING] Insufficient data for optimization (need 1000+ ticks)")
    print("Make sure Python bridge has been running and capturing ticks.")
    exit(1)

print("\n" + "-" * 80)
print("OPTIMIZING: Mean Reversion Window Size")
print("-" * 80)

# Test different window sizes for mean reversion
windows_to_test = [10, 20, 50, 100]
results = []

for window in windows_to_test:
    print(f"\nTesting {window}-tick window...")

    cursor.execute(f"""
        WITH signals AS (
            SELECT
                bid,
                AVG(bid) OVER (ORDER BY time ROWS BETWEEN {window} PRECEDING AND CURRENT ROW) as ma,
                LEAD(bid, 50) OVER (ORDER BY time) as price_after
            FROM tsla_history
            ORDER BY time
            LIMIT 50000
        ),
        trades AS (
            SELECT
                bid,
                ((bid - ma) / ma) * 100 as deviation_pct,
                ((price_after - bid) / bid) * 100 as return_pct,
                CASE WHEN price_after > bid * 1.005 THEN 1 ELSE 0 END as is_win
            FROM signals
            WHERE ma IS NOT NULL
              AND price_after IS NOT NULL
              AND ((bid - ma) / ma) * 100 < -1.0
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

    print(f"  Total Signals: {total_signals}")
    print(f"  Winning Trades: {wins}")
    print(f"  Win Rate: {win_rate}%")
    print(f"  Avg Return: {avg_return}%")
    print(f"  Best/Worst: {best_return}% / {worst_return}%")

# Find best window
print("\n" + "=" * 80)
print("RESULTS - Mean Reversion Optimization (Target: +0.5% in 50 ticks)")
print("=" * 80)
print(f"{'Window':<8} {'Signals':<8} {'Wins':<8} {'Win%':<8} {'Avg Ret':<10} {'Best/Worst'}")
print("-" * 80)

best_window = None
best_metric = -999

for r in results:
    # Use avg_return as primary metric if win_rate is low
    metric = r['avg_return'] if r['signals'] > 20 else -999
    marker = " <-- BEST" if metric > best_metric else ""

    print(f"{r['window']:<8} {r['signals']:<8} {r['wins']:<8} {r['win_rate']:<8} "
          f"{r['avg_return']:<10} {r['best']}% / {r['worst']}%{marker}")

    if metric > best_metric:
        best_metric = metric
        best_window = r['window']

print("=" * 80)
if best_window and best_metric > -0.5:
    print(f"\n[OK] OPTIMAL MEAN REVERSION WINDOW: {best_window} ticks")
    print(f"  Average Return per Signal: {best_metric}%")
    print(f"\n  Interpretation:")
    if best_metric > 0:
        print(f"    Mean reversion strategy shows POSITIVE edge (+{best_metric}%)")
        print(f"    Use {best_window}-tick window for entries")
    else:
        print(f"    Mean reversion strategy shows NEGATIVE edge ({best_metric}%)")
        print(f"    DO NOT USE during this market regime")
else:
    print("\n[X] MEAN REVERSION DOES NOT WORK ON THIS DATA")
    print("  Possible reasons:")
    print("    1. TSLA was trending (not mean-reverting) during Jan 12-16")
    print("    2. Insufficient signals (need more data)")
    print("    3. Market regime not suitable for mean reversion")
    print("\n  Recommendation: Test OTHER strategies (momentum/trend-following)")

cursor.close()
conn.close()

print("\nOptimization complete!")
