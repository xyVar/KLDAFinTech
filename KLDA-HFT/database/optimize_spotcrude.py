#!/usr/bin/env python3
"""
SpotCrude - Complete Parameter Optimization
"""

import psycopg2

conn = psycopg2.connect(
    host='localhost',
    port=5432,
    database='KLDA-HFT_Database',
    user='postgres',
    password='MyKldaTechnologies2025!'
)

print("=" * 80)
print("SPOTCRUDE - PARAMETER OPTIMIZATION")
print("=" * 80)

cursor = conn.cursor()

# Check data
cursor.execute("SELECT COUNT(*), MIN(time), MAX(time) FROM spotcrude_history;")
row = cursor.fetchone()
print(f"\nData: {row[0]:,} ticks from {row[1]} to {row[2]}")

if row[0] < 1000:
    print("[ERROR] Need 1000+ ticks")
    exit(1)

# Mean Reversion
print("\n" + "=" * 80)
print("MEAN REVERSION - Window Optimization")
print("=" * 80)

for window in [10, 20, 50, 100]:
    cursor.execute(f"""
        WITH signals AS (
            SELECT bid, AVG(bid) OVER (ORDER BY time ROWS BETWEEN {window} PRECEDING AND CURRENT ROW) as ma,
                   LEAD(bid, 50) OVER (ORDER BY time) as price_after
            FROM spotcrude_history ORDER BY time LIMIT 50000
        ),
        trades AS (
            SELECT ((bid - ma) / ma) * 100 as dev, ((price_after - bid) / bid) * 100 as ret,
                   CASE WHEN price_after > bid * 1.005 THEN 1 ELSE 0 END as win
            FROM signals WHERE ma IS NOT NULL AND price_after IS NOT NULL AND ((bid - ma) / ma) * 100 < -1.0
        )
        SELECT COUNT(*), SUM(win), ROUND(AVG(ret), 2) FROM trades;
    """)
    r = cursor.fetchone()
    print(f"  {window:3}-tick: {r[0]:3} signals, {r[1] or 0:3} wins, {r[2] or 0:+.2f}% avg return")

# Order Flow
print("\n" + "=" * 80)
print("ORDER FLOW - Window Optimization")
print("=" * 80)

for window in [50, 100, 200]:
    cursor.execute(f"""
        WITH signals AS (
            SELECT bid,
                   SUM(buy_volume) OVER (ORDER BY time ROWS BETWEEN {window} PRECEDING AND CURRENT ROW) -
                   SUM(sell_volume) OVER (ORDER BY time ROWS BETWEEN {window} PRECEDING AND CURRENT ROW) as flow,
                   LEAD(bid, 50) OVER (ORDER BY time) as price_after
            FROM spotcrude_history ORDER BY time LIMIT 50000
        ),
        trades AS (
            SELECT flow, ((price_after - bid) / bid) * 100 as ret,
                   CASE WHEN price_after > bid * 1.005 THEN 1 ELSE 0 END as win
            FROM signals WHERE flow > 500 AND price_after IS NOT NULL
        )
        SELECT COUNT(*), SUM(win), ROUND(AVG(ret), 2) FROM trades;
    """)
    r = cursor.fetchone()
    print(f"  {window:3}-tick: {r[0]:3} signals, {r[1] or 0:3} wins, {r[2] or 0:+.2f}% avg return")

# HMM Regime
print("\n" + "=" * 80)
print("HMM REGIME - Window Optimization")
print("=" * 80)

for window in [20, 50, 100, 200]:
    half = window // 2
    cursor.execute(f"""
        WITH signals AS (
            SELECT bid,
                   AVG(bid) OVER (ORDER BY time ROWS BETWEEN {half} PRECEDING AND CURRENT ROW) as recent,
                   AVG(bid) OVER (ORDER BY time ROWS BETWEEN {window} PRECEDING AND {half + 1} PRECEDING) as older,
                   LEAD(bid, 50) OVER (ORDER BY time) as price_after
            FROM spotcrude_history ORDER BY time LIMIT 50000
        ),
        trades AS (
            SELECT ((recent - older) / older) * 100 as trend, ((price_after - bid) / bid) * 100 as ret,
                   CASE WHEN price_after > bid * 1.005 THEN 1 ELSE 0 END as win
            FROM signals WHERE recent IS NOT NULL AND older IS NOT NULL
                          AND ((recent - older) / older) * 100 > 0.3 AND price_after IS NOT NULL
        )
        SELECT COUNT(*), SUM(win), ROUND(AVG(ret), 2) FROM trades;
    """)
    r = cursor.fetchone()
    print(f"  {window:3}-tick: {r[0]:3} signals, {r[1] or 0:3} wins, {r[2] or 0:+.2f}% avg return")

print("\n" + "=" * 80)
cursor.close()
conn.close()
