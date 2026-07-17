#!/usr/bin/env python3
"""
Renaissance 5-Metric Strategy - Python Backtest
Tests on YOUR real tick data from PostgreSQL
"""

import psycopg2
import pandas as pd
import math
from datetime import datetime

# Configuration
SYMBOL = 'SpotCrude'  # Test on live commodity
INITIAL_CAPITAL = 10000.0
RISK_PER_TRADE = 0.02  # 2%
TARGET_PROFIT = 0.005  # 0.5%
STOP_LOSS = 0.01       # 1%

# Per-symbol contract spec (from MT5 symbol_info)
POINT_SIZE = 0.001        # SpotCrude: point=0.001 (digits=3)
COMMISSION_PER_SHARE = 0.0  # CFD — built into spread

# Renaissance Parameters (OPTIMIZED FOR SPOTCRUDE)
MEAN_REV_WINDOW = 50
MEAN_REV_THRESHOLD = -0.2  # Commodities move less than stocks
SPREAD_VOL_WINDOW = 100
SPREAD_WIDEN_THRESHOLD = 50.0  # Commodity spreads are more volatile
HMM_WINDOW = 200
HMM_TREND_THRESHOLD = 0.1  # Lower trend threshold for commodities
MAX_KELLY_PCT = 2.0

print("=" * 80)
print("RENAISSANCE 5-METRIC BACKTEST")
print("=" * 80)
print(f"Symbol: {SYMBOL}")
print(f"Initial Capital: ${INITIAL_CAPITAL:,.2f}")
print("=" * 80)

# Connect to database
conn = psycopg2.connect(
    host='localhost',
    port=5432,
    database='KLDA-HFT_Database',
    user='postgres',
    password='MyKldaTechnologies2025!'
)

# Load tick data
print("\n[1/7] Loading tick data from PostgreSQL...")
query = """
    SELECT time, bid, ask, spread
    FROM ticks
    WHERE symbol = %s
    ORDER BY time ASC;
"""

df = pd.read_sql_query(query, conn, params=(SYMBOL,))
conn.close()

print(f"    Loaded {len(df):,} ticks")
print(f"    Period: {df['time'].min()} to {df['time'].max()}")

if len(df) < HMM_WINDOW:
    print(f"\n[ERROR] Need at least {HMM_WINDOW} ticks, only have {len(df)}")
    exit(1)

# Calculate Renaissance Metrics
print("\n[2/7] Calculating Mean Reversion (50-tick MA)...")
df['ma50'] = df['bid'].rolling(window=MEAN_REV_WINDOW).mean()
df['mean_rev'] = ((df['bid'] - df['ma50']) / df['ma50']) * 100.0

print("\n[3/7] Calculating Spread Volatility (100-tick avg)...")
df['spread_ma100'] = df['spread'].rolling(window=SPREAD_VOL_WINDOW).mean()
df['spread_vol'] = ((df['spread'] - df['spread_ma100']) / df['spread_ma100']) * 100.0

print("\n[4/7] Calculating HMM Regime (200-tick trend)...")
df['recent_avg'] = df['bid'].rolling(window=HMM_WINDOW//2).mean()
df['older_avg'] = df['bid'].shift(HMM_WINDOW//2).rolling(window=HMM_WINDOW//2).mean()
df['trend_pct'] = ((df['recent_avg'] - df['older_avg']) / df['older_avg']) * 100.0
df['regime'] = 'NEUTRAL'
df.loc[df['trend_pct'] > HMM_TREND_THRESHOLD, 'regime'] = 'BULLISH'
df.loc[df['trend_pct'] < -HMM_TREND_THRESHOLD, 'regime'] = 'BEARISH'

print("\n[5/7] Calculating Transaction Cost (per share)...")
# spread is stored in POINTS (bridge: (ask-bid)/point) — convert to dollars per share
df['tx_cost_per_share'] = (df['spread'] * POINT_SIZE) / 2.0 + COMMISSION_PER_SHARE

print("\n[6/7] Setting fixed 1% position size (A2: bypassing broken Kelly)...")
df['kelly_pct'] = 1.0

print("\n[7/7] Generating Entry Signals...")
# 4 conditions (tx_cost filter dropped — meaningless after unit fix; revisit with % filter later)
df['signal'] = (
    (df['mean_rev'] < MEAN_REV_THRESHOLD) &  # Price below MA
    (df['spread_vol'] < SPREAD_WIDEN_THRESHOLD) &  # Spread not too wide
    (df['regime'] != 'BEARISH') &  # mean reversion in non-bearish regimes
    (df['kelly_pct'] < MAX_KELLY_PCT)  # Safe position size
)

# Drop NaN rows
df = df.dropna()

# Backtest
print("\n" + "=" * 80)
print("BACKTESTING...")
print("=" * 80)

trades = []
capital = INITIAL_CAPITAL
position = None

# NOTE on costs: entry fills at ASK, exits trigger on BID against levels derived
# from the entry ask — the full bid/ask spread is therefore already paid inside
# the fill prices. Charging tx_cost_per_share on top double-counts the spread,
# so the explicit charge below is commission only (0 for CFDs).
for row in df.itertuples(index=False):
    # Check for entry signal
    if position is None and row.signal:
        # Open position
        entry_price = row.ask
        position_size = capital * (row.kelly_pct / 100.0)
        shares = position_size / entry_price
        stop_loss_price = entry_price * (1.0 - STOP_LOSS)
        take_profit_price = entry_price * (1.0 + TARGET_PROFIT)

        position = {
            'entry_time': row.time,
            'entry_price': entry_price,
            'shares': shares,
            'position_size': position_size,
            'stop_loss': stop_loss_price,
            'take_profit': take_profit_price,
        }

    # Check for exit
    elif position is not None:
        current_price = row.bid

        # Commission only — spread is already in the ask-entry/bid-exit prices
        tx_cost_total = COMMISSION_PER_SHARE * position['shares'] * 2

        # Check TP
        if current_price >= position['take_profit']:
            gross = (position['take_profit'] - position['entry_price']) * position['shares']
            profit = gross - tx_cost_total
            capital += profit

            trades.append({
                'entry_time': position['entry_time'],
                'exit_time': row.time,
                'entry_price': position['entry_price'],
                'exit_price': position['take_profit'],
                'profit': profit,
                'result': 'WIN' if profit > 0 else 'LOSS'
            })

            position = None

        # Check SL
        elif current_price <= position['stop_loss']:
            gross = (position['stop_loss'] - position['entry_price']) * position['shares']  # negative
            profit = gross - tx_cost_total
            capital += profit

            trades.append({
                'entry_time': position['entry_time'],
                'exit_time': row.time,
                'entry_price': position['entry_price'],
                'exit_price': position['stop_loss'],
                'profit': profit,
                'result': 'WIN' if profit > 0 else 'LOSS'
            })

            position = None

# Results
print("\n" + "=" * 80)
print("BACKTEST RESULTS")
print("=" * 80)

if len(trades) == 0:
    print("\n[!] NO TRADES EXECUTED")
    print("    Conditions were NEVER true simultaneously")
    print("\nDIAGNOSTICS:")
    print(f"  Ticks analyzed: {len(df):,}")
    print(f"  Mean Rev < {MEAN_REV_THRESHOLD}%: {(df['mean_rev'] < MEAN_REV_THRESHOLD).sum():,} ticks")
    print(f"  Spread Vol < {SPREAD_WIDEN_THRESHOLD}%: {(df['spread_vol'] < SPREAD_WIDEN_THRESHOLD).sum():,} ticks")
    print(f"  Regime != BEARISH: {(df['regime'] != 'BEARISH').sum():,} ticks")
    print(f"  ALL TRUE: {df['signal'].sum()} ticks")
else:
    trades_df = pd.DataFrame(trades)

    total_trades = len(trades_df)
    wins = len(trades_df[trades_df['result'] == 'WIN'])
    losses = total_trades - wins
    win_rate = (wins / total_trades) * 100.0

    total_profit = trades_df['profit'].sum()
    avg_win = trades_df[trades_df['profit'] > 0]['profit'].mean() if wins > 0 else 0
    avg_loss = abs(trades_df[trades_df['profit'] < 0]['profit'].mean()) if losses > 0 else 0

    profit_factor = (wins * avg_win) / (losses * avg_loss) if losses > 0 else float('inf')

    final_capital = capital
    net_return = ((final_capital - INITIAL_CAPITAL) / INITIAL_CAPITAL) * 100.0

    print(f"\nTotal Trades: {total_trades}")
    print(f"Wins: {wins} | Losses: {losses}")
    print(f"Win Rate: {win_rate:.1f}%")
    print(f"\nInitial Capital: ${INITIAL_CAPITAL:,.2f}")
    print(f"Final Capital: ${final_capital:,.2f}")
    print(f"Net Profit: ${total_profit:,.2f}")
    print(f"Return: {net_return:+.2f}%")
    print(f"\nAvg Win: ${avg_win:.2f}")
    print(f"Avg Loss: ${avg_loss:.2f}")
    print(f"Profit Factor: {profit_factor:.2f}")

    # ── Statistical validation ────────────────────────────────────────────
    def binom_p_one_sided(k, n, p0):
        """P(X >= k | n, p0), exact for small n, normal approx otherwise."""
        if n <= 1000:
            return sum(math.comb(n, i) * p0**i * (1 - p0)**(n - i) for i in range(k, n + 1))
        mu = n * p0
        sd = math.sqrt(n * p0 * (1 - p0))
        z = (k - 0.5 - mu) / sd  # continuity correction
        return 0.5 * math.erfc(z / math.sqrt(2))

    # With TP=+0.5% and SL=-1.0%, a driftless random walk hits TP with
    # probability SL/(TP+SL) — that geometry-implied rate is the honest null.
    p_null_geom = STOP_LOSS / (TARGET_PROFIT + STOP_LOSS)
    p_vs_50 = binom_p_one_sided(wins, total_trades, 0.50)
    p_vs_geom = binom_p_one_sided(wins, total_trades, p_null_geom)

    print("\n" + "=" * 80)
    print("VALIDATION (bar: >=100 occurrences, >=51% win rate, p < 0.05)")
    print("=" * 80)
    print(f"Occurrences: {total_trades}  ({'PASS' if total_trades >= 100 else 'FAIL'} >=100)")
    print(f"Win rate:    {win_rate:.1f}%  ({'PASS' if win_rate >= 51.0 else 'FAIL'} >=51%)")
    print(f"p-value vs 50% null:                 {p_vs_50:.2e}  ({'PASS' if p_vs_50 < 0.05 else 'FAIL'} <0.05)")
    print(f"p-value vs {p_null_geom*100:.1f}% geometry null:      {p_vs_geom:.2e}  ({'PASS' if p_vs_geom < 0.05 else 'FAIL'} <0.05)")
    print(f"NOTE: with asymmetric TP/SL ({TARGET_PROFIT*100:.1f}%/{STOP_LOSS*100:.1f}%), a no-edge random walk")
    print(f"      already wins ~{p_null_geom*100:.1f}% of trades — the geometry null is the real test.")

    print("\n" + "=" * 80)
    print("TRADE LOG (First 10 trades)")
    print("=" * 80)
    print(f"{'Entry Time':<20} {'Exit Time':<20} {'Entry $':<10} {'Exit $':<10} {'P&L':<10} {'Result'}")
    print("-" * 80)

    for i, trade in trades_df.head(10).iterrows():
        print(f"{str(trade['entry_time'])[:19]:<20} {str(trade['exit_time'])[:19]:<20} "
              f"{trade['entry_price']:<10.2f} {trade['exit_price']:<10.2f} "
              f"${trade['profit']:<9.2f} {trade['result']}")

print("\n" + "=" * 80)
