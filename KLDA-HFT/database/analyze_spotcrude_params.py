#!/usr/bin/env python3
"""
Analyze SpotCrude actual characteristics to find realistic thresholds
"""

import psycopg2
import pandas as pd

conn = psycopg2.connect(
    host='localhost',
    port=5432,
    database='KLDA-HFT_Database',
    user='postgres',
    password='MyKldaTechnologies2025!'
)

# Load SpotCrude data
df = pd.read_sql_query("""
    SELECT time, bid, ask, spread
    FROM spotcrude_history
    ORDER BY time ASC;
""", conn)
conn.close()

print("=" * 80)
print("SPOTCRUDE PARAMETER ANALYSIS")
print("=" * 80)
print(f"Total ticks: {len(df):,}")
print(f"Period: {df['time'].min()} to {df['time'].max()}")

# Calculate metrics
df['ma50'] = df['bid'].rolling(window=50).mean()
df['mean_rev'] = ((df['bid'] - df['ma50']) / df['ma50']) * 100.0

df['spread_ma100'] = df['spread'].rolling(window=100).mean()
df['spread_vol'] = ((df['spread'] - df['spread_ma100']) / df['spread_ma100']) * 100.0

df['recent_avg'] = df['bid'].rolling(window=100).mean()
df['older_avg'] = df['bid'].shift(100).rolling(window=100).mean()
df['trend_pct'] = ((df['recent_avg'] - df['older_avg']) / df['older_avg']) * 100.0

df['tx_cost'] = df['spread'] / 2.0 + 0.10

df = df.dropna()

print("\n" + "=" * 80)
print("MEAN REVERSION STATISTICS")
print("=" * 80)
print(f"Min: {df['mean_rev'].min():.2f}%")
print(f"Max: {df['mean_rev'].max():.2f}%")
print(f"Mean: {df['mean_rev'].mean():.2f}%")
print(f"Std: {df['mean_rev'].std():.2f}%")
print(f"\nTicks < -1.0%: {(df['mean_rev'] < -1.0).sum():,} ({(df['mean_rev'] < -1.0).sum() / len(df) * 100:.1f}%)")
print(f"Ticks < -0.5%: {(df['mean_rev'] < -0.5).sum():,} ({(df['mean_rev'] < -0.5).sum() / len(df) * 100:.1f}%)")
print(f"Ticks < -0.3%: {(df['mean_rev'] < -0.3).sum():,} ({(df['mean_rev'] < -0.3).sum() / len(df) * 100:.1f}%)")

print("\n" + "=" * 80)
print("SPREAD VOLATILITY STATISTICS")
print("=" * 80)
print(f"Min: {df['spread_vol'].min():.2f}%")
print(f"Max: {df['spread_vol'].max():.2f}%")
print(f"Mean: {df['spread_vol'].mean():.2f}%")
print(f"Std: {df['spread_vol'].std():.2f}%")
print(f"\nTicks < 20%: {(df['spread_vol'] < 20).sum():,} ({(df['spread_vol'] < 20).sum() / len(df) * 100:.1f}%)")
print(f"Ticks < 50%: {(df['spread_vol'] < 50).sum():,} ({(df['spread_vol'] < 50).sum() / len(df) * 100:.1f}%)")

print("\n" + "=" * 80)
print("HMM REGIME STATISTICS")
print("=" * 80)
print(f"Min trend: {df['trend_pct'].min():.2f}%")
print(f"Max trend: {df['trend_pct'].max():.2f}%")
print(f"Mean trend: {df['trend_pct'].mean():.2f}%")
print(f"Std: {df['trend_pct'].std():.2f}%")
print(f"\nBullish (> 0.5%): {(df['trend_pct'] > 0.5).sum():,} ({(df['trend_pct'] > 0.5).sum() / len(df) * 100:.1f}%)")
print(f"Bullish (> 0.3%): {(df['trend_pct'] > 0.3).sum():,} ({(df['trend_pct'] > 0.3).sum() / len(df) * 100:.1f}%)")
print(f"Bullish (> 0.1%): {(df['trend_pct'] > 0.1).sum():,} ({(df['trend_pct'] > 0.1).sum() / len(df) * 100:.1f}%)")

print("\n" + "=" * 80)
print("TRANSACTION COST STATISTICS")
print("=" * 80)
print(f"Min: ${df['tx_cost'].min():.2f}")
print(f"Max: ${df['tx_cost'].max():.2f}")
print(f"Mean: ${df['tx_cost'].mean():.2f}")
print(f"Std: ${df['tx_cost'].std():.2f}")
print(f"\nTicks < $10: {(df['tx_cost'] < 10).sum():,} ({(df['tx_cost'] < 10).sum() / len(df) * 100:.1f}%)")
print(f"Ticks < $20: {(df['tx_cost'] < 20).sum():,} ({(df['tx_cost'] < 20).sum() / len(df) * 100:.1f}%)")

print("\n" + "=" * 80)
print("RECOMMENDED THRESHOLDS FOR SPOTCRUDE")
print("=" * 80)
print(f"Mean Reversion: < -0.3% (instead of -1.0%)")
print(f"Spread Volatility: < 50% (instead of 20%)")
print(f"HMM Trend: > 0.1% (instead of 0.5%)")
print(f"TX Cost: < $20 (instead of $10)")
print("=" * 80)
