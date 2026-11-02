#!/usr/bin/env python3
"""
RESEARCH LANE — Conditional pattern sweep across all instruments (read-only DB).

Tests the 5 doctrine patterns on 1-minute bars built from real ticks:
  1. mean_reversion      — fade a vol-normalized stretch from the 30-bar mean
  2. gap_fill            — trade toward the fill of an abnormal session-open gap
  3. pairs_divergence    — fade abnormal divergence of a correlated pair's spread
  4. event_drift         — follow continuation after an abnormal 5-bar shock
  5. momentum_exhaustion — fade a long one-directional run that is also stretched

Each pattern's trades are CONDITIONED on three dimensions and evaluated per cell:
  stretch bucket (moderate / extreme) x regime (TREND_UP / TREND_DOWN / RANGE)
  x time-of-day bucket (asia 03-09, london 10-15, ny 16-20, late 21-23; broker UTC+3)

Realistic costs: per-symbol, per-hour median dollar spread measured from the
ticks themselves (ask-bid; no point-size assumptions), plus slippage modeled
as 25% of spread per side. Entries are skipped when round-trip cost exceeds
25% of the barrier distance (the July 2026 spread-drag lesson, docs/PROTOCOL.md).

Execution realism: signal on bar close -> entry at NEXT bar open (no lookahead).
Exits are intraday only: symmetric sigma-scaled TP/SL, max-hold timeout, and
forced close before session end. If TP and SL are both touched within one bar,
the trade is counted as a LOSS (pessimistic).

Validation: chronological in-sample/out-of-sample split (default 70/30).
IS selection requires n>=100, win rate>=51%, one-sided binomial p<0.05,
Benjamini-Hochberg FDR q<=0.10 across all cells tested. Survivors are then
measured once on OOS; the FINAL GATE is applied there:
  n>=100  AND  win_rate>=51%  AND  p<0.05  AND  net expectancy > 0.

Verdicts are three-valued and reported plainly:
  PASS / FAIL (tested and missed the gate) / INSUFFICIENT_N (not enough
  occurrences to test — NOT a failure, an untested hypothesis).

Outputs:
  reports/pattern_sweep_<date>.md and .json          (full results, all cells)
  KLDA-HFT/config/validated_patterns.json            (PASS cells only)

This script never writes to the database: the session is opened with
default_transaction_read_only=on, so any write would raise an error.

Run on the DB host:
    python KLDA-HFT/research/conditional_pattern_sweep.py
    python KLDA-HFT/research/conditional_pattern_sweep.py --symbols SpotCrude NAS100
"""

import argparse
import json
import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import psycopg2

REPO_ROOT = Path(__file__).resolve().parents[2]
REPORTS_DIR = REPO_ROOT / "reports"
CONFIG_PATH = REPO_ROOT / "KLDA-HFT" / "config" / "validated_patterns.json"

DB_CONFIG = {
    "host": "127.0.0.1",  # never 'localhost' — see docs/PROTOCOL.md
    "port": 5432,
    "database": "KLDA-HFT_Database",
    "user": "postgres",
    "password": os.environ.get("KLDA_DB_PASSWORD", "MyKldaTechnologies2025!"),
    "connect_timeout": 10,
}

# ----------------------------- parameters (fixed; no tuning until a pass) ---
IS_FRACTION = 0.70            # chronological split
BARRIER_SIGMA = 2.0           # TP = SL = 2 sigma of 30-min move
SIGMA_WINDOW = 60             # bars used to estimate per-bar return sigma
HORIZON_BARS = 30             # sigma scaling horizon (sqrt-time)
MAX_HOLD_BARS = 120           # timeout exit (2 hours)
STRETCH_WINDOW = 30
STRETCH_MODERATE = 2.0
STRETCH_EXTREME = 3.0
REGIME_WINDOW = 30            # trend measured as MA shift over this many bars
REGIME_THRESHOLD = 0.10       # percent; |trend| above => trending
GAP_Z = 1.5
PAIR_WINDOW = 240
PAIR_Z = 2.5
EVENT_SHOCK_SIGMA = 3.0
RUN_LENGTH = 6
COST_GUARD = 0.25             # skip if round-trip cost > 25% of barrier
SLIPPAGE_FRAC_OF_SPREAD = 0.25
GATE_N = 100
GATE_WR = 0.51
GATE_P = 0.05
FDR_Q = 0.10
SESSION_LAST_HOUR = 23        # force flat before 23:50 broker time
TOD_BUCKETS = [("asia", 3, 9), ("london", 10, 15), ("ny", 16, 20), ("late", 21, 23)]


def connect_readonly():
    conn = psycopg2.connect(
        options="-c default_transaction_read_only=on -c statement_timeout=1800000",
        **DB_CONFIG,
    )
    conn.autocommit = True
    return conn


# ------------------------------------------------------------- data loading
def list_symbols(conn):
    cur = conn.cursor()
    cur.execute("SELECT symbol, COUNT(DISTINCT time::date) FROM ticks GROUP BY symbol")
    return {s: int(d) for s, d in cur.fetchall()}


def load_m1(conn, symbol):
    """M1 bars from the continuous aggregate, falling back to raw bucketing."""
    q_cagg = """
        SELECT time, open, high, low, close
        FROM cagg_bars_m1 WHERE symbol = %s ORDER BY time
    """
    df = pd.read_sql_query(q_cagg, conn, params=(symbol,))
    if len(df) < 1000:
        q_raw = """
            SELECT time_bucket('1 minute', time) AS time,
                   FIRST(bid, time) AS open, MAX(bid) AS high,
                   MIN(bid) AS low,  LAST(bid, time) AS close
            FROM ticks WHERE symbol = %s
            GROUP BY 1 ORDER BY 1
        """
        df = pd.read_sql_query(q_raw, conn, params=(symbol,))
    df = df.dropna().reset_index(drop=True)
    for c in ("open", "high", "low", "close"):
        df[c] = df[c].astype(float)
    df["time"] = pd.to_datetime(df["time"])
    return df


def load_hourly_spread(conn, symbol):
    """Median dollar spread (ask-bid) per hour-of-day, measured from real ticks."""
    q = """
        SELECT EXTRACT(HOUR FROM time)::int AS hr,
               percentile_cont(0.5) WITHIN GROUP (ORDER BY (ask - bid)) AS med
        FROM ticks WHERE symbol = %s GROUP BY 1
    """
    cur = conn.cursor()
    cur.execute(q, (symbol,))
    d = {int(h): float(m) for h, m in cur.fetchall() if m is not None}
    overall = np.median(list(d.values())) if d else np.nan
    return d, overall


# ------------------------------------------------------------- features
def add_features(df):
    df = df.copy()
    df["ret1"] = df["close"].pct_change()
    df["sigma"] = df["ret1"].rolling(SIGMA_WINDOW).std()
    ma = df["close"].rolling(STRETCH_WINDOW).mean()
    sd = df["close"].rolling(STRETCH_WINDOW).std()
    df["stretch_z"] = (df["close"] - ma) / sd
    trend = (ma - ma.shift(REGIME_WINDOW)) / ma.shift(REGIME_WINDOW) * 100.0
    df["regime"] = np.where(trend > REGIME_THRESHOLD, "TREND_UP",
                    np.where(trend < -REGIME_THRESHOLD, "TREND_DOWN", "RANGE"))
    df["hour"] = df["time"].dt.hour
    df["date"] = df["time"].dt.date
    tod = pd.Series("off", index=df.index)
    for name, h0, h1 in TOD_BUCKETS:
        tod[(df["hour"] >= h0) & (df["hour"] <= h1)] = name
    df["tod"] = tod
    df["run"] = compute_run_length(df["ret1"].values)
    return df


def compute_run_length(ret):
    """Signed length of the current consecutive same-direction run."""
    run = np.zeros(len(ret))
    cur = 0
    prev_sign = 0
    for i in range(len(ret)):
        s = 0 if (not np.isfinite(ret[i]) or ret[i] == 0) else (1 if ret[i] > 0 else -1)
        cur = cur + 1 if (s != 0 and s == prev_sign) else (1 if s != 0 else 0)
        prev_sign = s if s != 0 else prev_sign
        run[i] = cur * (prev_sign if s != 0 else 0)
    return run


def stretch_bucket(z):
    a = abs(z)
    if a >= STRETCH_EXTREME:
        return "extreme"
    if a >= STRETCH_MODERATE:
        return "moderate"
    return "mild"


# ------------------------------------------------------------- signals
def sig_mean_reversion(df):
    out = []
    z = df["stretch_z"].values
    for i in range(len(df)):
        if np.isfinite(z[i]) and abs(z[i]) >= STRETCH_MODERATE:
            out.append((i, -1 if z[i] > 0 else 1))
    return out


def sig_gap_fill(df):
    out = []
    dates = df["date"].values
    opens, closes = df["open"].values, df["close"].values
    sig = df["sigma"].values
    day_first = np.r_[True, dates[1:] != dates[:-1]]
    idx_first = np.where(day_first)[0]
    for k in range(1, len(idx_first)):
        i = idx_first[k]
        prev_close = closes[idx_first[k] - 1]
        s = sig[i - 1]
        if not (np.isfinite(prev_close) and np.isfinite(s)) or s <= 0:
            continue
        gap = (opens[i] - prev_close) / prev_close
        overnight_scale = s * math.sqrt(HORIZON_BARS)
        if abs(gap) >= GAP_Z * overnight_scale:
            out.append((i, -1 if gap > 0 else 1))  # toward the fill
    return out


def sig_event_drift(df):
    out = []
    close = df["close"].values
    sig = df["sigma"].values
    for i in range(5, len(df)):
        s = sig[i]
        if not np.isfinite(s) or s <= 0:
            continue
        move = (close[i] - close[i - 5]) / close[i - 5]
        if abs(move) >= EVENT_SHOCK_SIGMA * s * math.sqrt(5):
            out.append((i, 1 if move > 0 else -1))  # continuation
    return out


def sig_momentum_exhaustion(df):
    out = []
    run = df["run"].values
    z = df["stretch_z"].values
    for i in range(len(df)):
        if abs(run[i]) >= RUN_LENGTH and np.isfinite(z[i]) and abs(z[i]) >= STRETCH_MODERATE:
            if np.sign(run[i]) == np.sign(z[i]):
                out.append((i, -1 if run[i] > 0 else 1))  # fade the run
    return out


def build_pairs(frames, is_end_time):
    """Correlated pairs chosen ONLY from in-sample closes (|rho| >= 0.7)."""
    closes = {}
    for sym, df in frames.items():
        s = df[df["time"] < is_end_time].set_index("time")["close"].resample("5min").last()
        if s.notna().sum() > 500:
            closes[sym] = s
    if len(closes) < 2:
        return []
    aligned = pd.DataFrame(closes).dropna(how="any")
    if len(aligned) < 500:
        return []
    rho = aligned.pct_change().corr()
    pairs = []
    syms = list(aligned.columns)
    for i in range(len(syms)):
        for j in range(i + 1, len(syms)):
            r = rho.iloc[i, j]
            if np.isfinite(r) and abs(r) >= 0.7:
                pairs.append((syms[i], syms[j], float(r)))
    return pairs


def sig_pairs_divergence(dfA, dfB):
    """Signals on symbol A: fade abnormal divergence vs correlated B."""
    a = dfA.set_index("time")["close"]
    b = dfB.set_index("time")["close"].reindex(a.index, method="ffill")
    la, lb = np.log(a), np.log(b)
    beta = la.rolling(PAIR_WINDOW).cov(lb) / lb.rolling(PAIR_WINDOW).var()
    spread = la - beta * lb
    mu = spread.rolling(PAIR_WINDOW).mean()
    sd = spread.rolling(PAIR_WINDOW).std()
    z = ((spread - mu) / sd).values
    out = []
    for i in range(len(z)):
        if np.isfinite(z[i]) and abs(z[i]) >= PAIR_Z:
            out.append((i, -1 if z[i] > 0 else 1))
    return out


# ------------------------------------------------------------- simulation
def simulate(df, signals, hourly_spread, overall_spread):
    """Next-bar-open entry, symmetric sigma barriers, intraday-only exits."""
    n = len(df)
    o, h, l, c = (df[x].values for x in ("open", "high", "low", "close"))
    sig = df["sigma"].values
    hours = df["hour"].values
    dates = df["date"].values
    stretch = df["stretch_z"].values
    regime = df["regime"].values
    tod = df["tod"].values
    trades = []
    last_exit = -1
    for i, direction in signals:
        if i + 1 >= n or i <= SIGMA_WINDOW or i < last_exit:
            continue
        s = sig[i]
        if not np.isfinite(s) or s <= 0 or tod[i] == "off":
            continue
        entry = o[i + 1]
        barrier = BARRIER_SIGMA * s * math.sqrt(HORIZON_BARS) * entry
        spr = hourly_spread.get(int(hours[i]), overall_spread)
        if not np.isfinite(spr):
            continue
        rt_cost = spr * (1.0 + 2 * SLIPPAGE_FRAC_OF_SPREAD)  # spread + slip both sides
        if rt_cost > COST_GUARD * barrier:
            continue  # spread-drag guard: cost would dominate the prize
        tp = entry + direction * barrier
        sl = entry - direction * barrier
        exit_px, hit = None, None
        for j in range(i + 1, min(i + 1 + MAX_HOLD_BARS, n)):
            if dates[j] != dates[i + 1] or hours[j] >= SESSION_LAST_HOUR:
                exit_px, hit = c[j], "eod"
                break
            hi_tp = h[j] >= tp if direction > 0 else l[j] <= tp
            hi_sl = l[j] <= sl if direction > 0 else h[j] >= sl
            if hi_tp and hi_sl:
                exit_px, hit = sl, "both->loss"   # pessimistic
                break
            if hi_sl:
                exit_px, hit = sl, "sl"
                break
            if hi_tp:
                exit_px, hit = tp, "tp"
                break
        else:
            j = min(i + MAX_HOLD_BARS, n - 1)
            exit_px, hit = c[j], "timeout"
        last_exit = j
        gross = direction * (exit_px - entry) / entry
        net = gross - rt_cost / entry
        trades.append({
            "i": int(i), "dir": int(direction), "net": float(net),
            "win": bool(net > 0), "hit": hit,
            "stretch": stretch_bucket(stretch[i]),
            "regime": str(regime[i]), "tod": str(tod[i]),
        })
    return trades


# ------------------------------------------------------------- statistics
def binom_p_onesided(wins, n):
    """P(X >= wins | p=0.5), normal approximation with continuity correction."""
    if n == 0:
        return 1.0
    z = (wins - 0.5 - n / 2.0) / math.sqrt(n / 4.0)
    return 0.5 * math.erfc(z / math.sqrt(2.0))


def bh_fdr(cells, q=FDR_Q):
    """Benjamini-Hochberg: returns the set of cell keys that survive."""
    ps = sorted((c["p"], k) for k, c in cells.items())
    m = len(ps)
    keep, thresh = set(), 0.0
    for rank, (p, k) in enumerate(ps, 1):
        if p <= q * rank / m:
            thresh = p
    for p, k in ps:
        if p <= thresh and thresh > 0:
            keep.add(k)
    return keep


def cell_stats(trades):
    out = {}
    for t in trades:
        key = (t["stretch"], t["regime"], t["tod"])
        out.setdefault(key, []).append(t)
    stats = {}
    for key, ts in out.items():
        n = len(ts)
        wins = sum(t["win"] for t in ts)
        stats[key] = {
            "n": n, "wins": wins, "wr": wins / n if n else 0.0,
            "p": binom_p_onesided(wins, n),
            "exp_net": float(np.mean([t["net"] for t in ts])) if n else 0.0,
        }
    return stats


# ------------------------------------------------------------- main sweep
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", nargs="*", default=None)
    ap.add_argument("--is-fraction", type=float, default=IS_FRACTION)
    args = ap.parse_args()

    conn = connect_readonly()
    sym_days = list_symbols(conn)
    symbols = args.symbols or sorted(sym_days, key=lambda s: -sym_days[s])
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    frames, spreads, skipped = {}, {}, []
    for sym in symbols:
        df = load_m1(conn, sym)
        if len(df) < 5000:
            skipped.append((sym, f"only {len(df)} M1 bars"))
            continue
        frames[sym] = add_features(df)
        spreads[sym] = load_hourly_spread(conn, sym)
        print(f"loaded {sym}: {len(df):,} M1 bars, {sym_days.get(sym,'?')} days")
    conn.close()

    results, passes = [], []
    # pairs are selected on IS data only (no lookahead into OOS)
    any_frame = next(iter(frames.values()), None)
    pairs = []
    if any_frame is not None:
        global_is_end = any_frame["time"].quantile(args.is_fraction)
        pairs = build_pairs(frames, global_is_end)

    PATTERNS = {
        "mean_reversion": sig_mean_reversion,
        "gap_fill": sig_gap_fill,
        "event_drift": sig_event_drift,
        "momentum_exhaustion": sig_momentum_exhaustion,
    }

    def run_pattern(sym, pattern_name, df, signals):
        split = int(len(df) * args.is_fraction)
        is_sigs = [(i, d) for i, d in signals if i < split - MAX_HOLD_BARS]
        oos_sigs = [(i, d) for i, d in signals if i >= split]
        hs, ov = spreads[sym]
        is_trades = simulate(df, is_sigs, hs, ov)
        is_cells = cell_stats(is_trades)
        selected = {
            k: v for k, v in is_cells.items()
            if v["n"] >= GATE_N and v["wr"] >= GATE_WR and v["p"] < GATE_P
        }
        fdr_keep = bh_fdr(is_cells) if is_cells else set()
        selected = {k: v for k, v in selected.items() if k in fdr_keep}
        oos_trades = simulate(df, oos_sigs, hs, ov)
        oos_cells = cell_stats(oos_trades)
        for key, is_v in sorted(is_cells.items()):
            rec = {
                "symbol": sym, "pattern": pattern_name,
                "cell": {"stretch": key[0], "regime": key[1], "tod": key[2]},
                "is": is_v, "oos": oos_cells.get(key),
                "is_selected": key in selected,
            }
            o = oos_cells.get(key)
            if key not in selected:
                rec["verdict"] = ("FAIL_IS" if is_v["n"] >= GATE_N
                                  else "INSUFFICIENT_N_IS")
            elif o is None or o["n"] < GATE_N:
                rec["verdict"] = "INSUFFICIENT_N_OOS"
            elif o["wr"] >= GATE_WR and o["p"] < GATE_P and o["exp_net"] > 0:
                rec["verdict"] = "PASS"
                passes.append(rec)
            else:
                rec["verdict"] = "FAIL_OOS"
            results.append(rec)

    for sym, df in frames.items():
        for pname, fn in PATTERNS.items():
            run_pattern(sym, pname, df, fn(df))
    for a, b, rho in pairs:
        if a in frames and b in frames:
            run_pattern(a, f"pairs_divergence[{a}~{b}]", frames[a],
                        sig_pairs_divergence(frames[a], frames[b]))
            run_pattern(b, f"pairs_divergence[{b}~{a}]", frames[b],
                        sig_pairs_divergence(frames[b], frames[a]))

    # ----------------------------------------------------------- reporting
    REPORTS_DIR.mkdir(exist_ok=True)
    n_cells = len(results)
    n_pass = len(passes)
    n_fail = sum(1 for r in results if r["verdict"].startswith("FAIL"))
    n_insuf = sum(1 for r in results if r["verdict"].startswith("INSUFFICIENT"))

    md = [
        f"# Conditional Pattern Sweep — {today}",
        "",
        f"Universe: {len(frames)} symbols with usable M1 history "
        f"({', '.join(frames)}). Skipped: "
        f"{', '.join(f'{s} ({r})' for s, r in skipped) if skipped else 'none'}.",
        f"Split: {int(args.is_fraction*100)}% IS / {100-int(args.is_fraction*100)}% OOS, chronological.",
        f"Gate (OOS): n>={GATE_N}, win rate>={GATE_WR:.0%}, p<{GATE_P}, net expectancy>0.",
        f"Costs: per-symbol per-hour median (ask-bid) + {SLIPPAGE_FRAC_OF_SPREAD:.0%} slippage/side;",
        f"entries skipped when round-trip cost > {COST_GUARD:.0%} of barrier. Both-touch bars = loss.",
        "",
        f"## Headline: {n_pass} PASS, {n_fail} FAIL, {n_insuf} INSUFFICIENT_N "
        f"(of {n_cells} cells tested)",
        "",
        "| Symbol | Pattern | Stretch | Regime | ToD | IS n | IS wr | OOS n | OOS wr | OOS p | OOS exp | Verdict |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in sorted(results, key=lambda r: (r["verdict"] != "PASS", r["symbol"])):
        o = r["oos"] or {}
        md.append(
            f"| {r['symbol']} | {r['pattern']} | {r['cell']['stretch']} "
            f"| {r['cell']['regime']} | {r['cell']['tod']} "
            f"| {r['is']['n']} | {r['is']['wr']:.1%} "
            f"| {o.get('n','-')} | {(('%.1f%%' % (o['wr']*100)) if o else '-')} "
            f"| {(('%.4f' % o['p']) if o else '-')} "
            f"| {(('%.4f%%' % (o['exp_net']*100)) if o else '-')} | **{r['verdict']}** |"
        )
    if n_pass == 0:
        md += ["", "## Plain verdict: NO pattern passed the gate.",
               "No tuning follows from this. Either collect more data "
               "(INSUFFICIENT_N cells) or the tested rules have no edge (FAIL cells)."]

    md_path = REPORTS_DIR / f"pattern_sweep_{today}.md"
    json_path = REPORTS_DIR / f"pattern_sweep_{today}.json"
    md_path.write_text("\n".join(md), encoding="utf-8")
    json_path.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")

    if passes:
        validated = {
            "generated": today,
            "gate": {"n": GATE_N, "win_rate": GATE_WR, "p": GATE_P,
                     "oos_fraction": 1 - args.is_fraction},
            "patterns": [
                {
                    "symbol": r["symbol"], "pattern": r["pattern"],
                    "params": {
                        **r["cell"],
                        "barrier_sigma": BARRIER_SIGMA, "horizon_bars": HORIZON_BARS,
                        "max_hold_bars": MAX_HOLD_BARS, "cost_guard": COST_GUARD,
                    },
                    "n": r["oos"]["n"], "win_rate": round(r["oos"]["wr"], 4),
                    "p_value": round(r["oos"]["p"], 6),
                    "net_expectancy": round(r["oos"]["exp_net"], 6),
                    "date": today,
                }
                for r in passes
            ],
        }
        CONFIG_PATH.write_text(json.dumps(validated, indent=2), encoding="utf-8")
        print(f"\nPASS -> {CONFIG_PATH}")
    else:
        print("\nNO PASSES — validated_patterns.json NOT written (nothing to bless).")
    print(f"Report: {md_path}")


if __name__ == "__main__":
    main()
