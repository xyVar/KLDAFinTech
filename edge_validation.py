"""
edge_validation.py — QUEST 1: Does our ranking signal actually predict moves?

Canonical question (see PROTOCOL.md): before risking money, prove that ranking the
universe by a signal picks winners/losers better than random.

Method (cross-sectional factor backtest, no look-ahead bias):
  - Each day, score every symbol by a signal (momentum / reversal / etc.).
  - Go LONG the top fraction, SHORT the bottom fraction.
  - Measure the NEXT day's realised return of that long-short spread.
  - Aggregate: mean spread, win rate, t-stat. A real edge needs mean > 0 and t-stat > ~2.

Data source: PostgreSQL `market_data.stock_prices` (the existing KLDAFinTech DB).
Fallback:    a CSV with columns [ticker, date, close] via --csv.

This harness is UNIVERSE-AGNOSTIC: any symbol with (date, close) is ranked. As FX /
crypto / index candles are added to the same table, the universe expands automatically.

Run:
    python edge_validation.py
    python edge_validation.py --csv prices.csv --top-frac 0.2 --min-names 20
"""

import argparse
import sys

try:
    import numpy as np
    import pandas as pd
except ImportError:
    sys.exit("Requires pandas and numpy:  pip install pandas numpy")

# Same DB the rest of the platform uses (runs on the user's machine where the DB lives).
DB_CONFIG = {
    "host": "localhost",
    "database": "market_data",
    "user": "postgres",
    "password": "MyStrongDBpass2025!",
}


# ----------------------------------------------------------------------------- data
def load_from_db():
    try:
        import psycopg2  # noqa: F401
    except ImportError:
        sys.exit("psycopg2 not installed. Use --csv, or:  pip install psycopg2-binary")
    import psycopg2
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        df = pd.read_sql(
            "SELECT ticker, date, close FROM stock_prices WHERE close IS NOT NULL", conn
        )
    finally:
        conn.close()
    return df


def load_from_csv(path):
    df = pd.read_csv(path)
    missing = {"ticker", "date", "close"} - set(df.columns)
    if missing:
        sys.exit(f"CSV missing columns: {missing}")
    return df[["ticker", "date", "close"]]


def to_panels(df, min_history=60):
    """Return (wide_close, daily_returns, forward_returns) as date x ticker frames."""
    df = df.dropna(subset=["close"]).copy()
    df["date"] = pd.to_datetime(df["date"])
    wide = df.pivot_table(index="date", columns="ticker", values="close").sort_index()
    # keep symbols with enough history to compute signals + survive sparsity
    wide = wide.loc[:, wide.notna().sum() >= min_history]
    daily = wide.pct_change()
    # forward return: signal known at close of day t -> trade, realise over t -> t+1
    forward = daily.shift(-1)
    return wide, daily, forward


# -------------------------------------------------------------------------- signals
def momentum(wide, lookback):
    """Trend-following: recent winners keep winning. Score = trailing return."""
    return wide.pct_change(lookback)


def reversal(wide, lookback):
    """Mean-reversion: recent losers bounce. Score = negative of trailing return."""
    return -wide.pct_change(lookback)


SIGNALS = {
    "momentum_20d": lambda w: momentum(w, 20),
    "momentum_60d": lambda w: momentum(w, 60),
    "reversal_3d": lambda w: reversal(w, 3),
    "reversal_5d": lambda w: reversal(w, 5),
}


# ------------------------------------------------------------------------- backtest
def backtest(score, forward, top_frac, min_names):
    """Long top_frac / short bottom_frac each day; return the daily spread series."""
    rows = []
    for date, s in score.iterrows():
        if date not in forward.index:
            continue
        s = s.dropna()
        f = forward.loc[date].dropna()
        common = s.index.intersection(f.index)
        if len(common) < min_names:
            continue
        s, f = s[common], f[common]
        n = max(1, int(len(s) * top_frac))
        ranked = s.sort_values(ascending=False).index
        longs, shorts = ranked[:n], ranked[-n:]
        rows.append((date, f[longs].mean(), f[shorts].mean()))
    if not rows:
        return pd.DataFrame(columns=["long", "short", "spread"])
    out = pd.DataFrame(rows, columns=["date", "long", "short"]).set_index("date")
    out["spread"] = out["long"] - out["short"]
    return out


def stats(spread):
    """Edge metrics for a daily long-short return series."""
    x = spread.dropna()
    n = len(x)
    if n < 2:
        return None
    mean, sd = x.mean(), x.std(ddof=1)
    t = mean / (sd / np.sqrt(n)) if sd > 0 else 0.0
    return {
        "days": n,
        "mean_bp": mean * 1e4,                       # avg daily spread, basis points
        "win_rate": (x > 0).mean() * 100,
        "t_stat": t,
        "sharpe": (mean / sd * np.sqrt(252)) if sd > 0 else 0.0,
        "total_pct": (np.prod(1 + x) - 1) * 100,     # compounded, unlevered
    }


# ------------------------------------------------------------------------------ run
def main():
    ap = argparse.ArgumentParser(description="Validate ranking-signal edge.")
    ap.add_argument("--csv", help="CSV with ticker,date,close (else use Postgres)")
    ap.add_argument("--top-frac", type=float, default=0.2, help="long/short fraction")
    ap.add_argument("--min-names", type=int, default=10, help="min symbols/day to trade")
    ap.add_argument("--min-history", type=int, default=60, help="min days per symbol")
    args = ap.parse_args()

    print("Loading prices ...")
    raw = load_from_csv(args.csv) if args.csv else load_from_db()
    wide, _, forward = to_panels(raw, min_history=args.min_history)
    print(f"Universe: {wide.shape[1]} symbols x {wide.shape[0]} days "
          f"({wide.index.min().date()} -> {wide.index.max().date()})\n")

    if wide.shape[1] < args.min_names:
        sys.exit(f"Only {wide.shape[1]} symbols with history; need >= {args.min_names}.")

    header = f"{'signal':<14}{'days':>6}{'mean(bp)':>10}{'win%':>8}{'t-stat':>8}{'Sharpe':>8}{'total%':>9}  verdict"
    print(header)
    print("-" * len(header))

    best = None
    for name, fn in SIGNALS.items():
        bt = backtest(fn(wide), forward, args.top_frac, args.min_names)
        st = stats(bt["spread"]) if not bt.empty else None
        if st is None:
            print(f"{name:<14}{'  (insufficient data)':>0}")
            continue
        edge = st["mean_bp"] > 0 and st["t_stat"] > 2
        verdict = "EDGE" if edge else ("weak+" if st["mean_bp"] > 0 else "none")
        print(f"{name:<14}{st['days']:>6}{st['mean_bp']:>10.1f}{st['win_rate']:>8.1f}"
              f"{st['t_stat']:>8.2f}{st['sharpe']:>8.2f}{st['total_pct']:>9.1f}  {verdict}")
        if best is None or st["t_stat"] > best[1]["t_stat"]:
            best = (name, st)

    print("\nVerdict gate: a signal needs mean(bp) > 0 AND t-stat > ~2 to be a real edge.")
    if best and best[1]["t_stat"] > 2 and best[1]["mean_bp"] > 0:
        print(f"=> Strongest edge: '{best[0]}' (t={best[1]['t_stat']:.2f}). "
              f"Proceed to QUEST 2 (build EA).")
    else:
        print("=> No signal cleared the gate on this data. Do NOT trade these as-is; "
              "try other signals/lookbacks or richer data before risking money.")


if __name__ == "__main__":
    main()
