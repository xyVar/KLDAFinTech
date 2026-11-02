# Research Lane — Conditional Pattern Sweep

Read-only research harness for the 5 doctrine patterns. **This lane never
writes to the database** (sessions open with `default_transaction_read_only=on`)
and touches none of the execution path (router / reconciler / bridge).

## Run order (on the DB host)

```bash
# 1. What data do we actually have? (writes reports/data_inventory_<date>.md)
python KLDA-HFT/research/data_inventory.py

# 2. The sweep itself (writes reports/pattern_sweep_<date>.md/.json and,
#    only if something PASSES, KLDA-HFT/config/validated_patterns.json)
python KLDA-HFT/research/conditional_pattern_sweep.py
```

Needs: `numpy`, `pandas`, `psycopg2-binary`. Do not run two sweeps in
parallel (machine OOMs — known constraint).

## What it tests

5 patterns on M1 bars (from `cagg_bars_m1`, tick-bucket fallback):
mean_reversion, gap_fill, pairs_divergence (pairs chosen on IS data only,
|rho|>=0.7), event_drift, momentum_exhaustion — each conditioned on
**stretch** (moderate/extreme) x **regime** (TREND_UP/TREND_DOWN/RANGE) x
**time-of-day** (asia/london/ny/late, broker UTC+3).

Realism: per-symbol per-hour median dollar spread measured from ticks
(`ask-bid`, no point-size assumptions) + 25% slippage per side; entries
skipped when round-trip cost > 25% of barrier (July 2026 spread-drag rule);
signal on close -> entry next bar open; symmetric 2-sigma barriers; max hold
2h; forced flat before session end; TP+SL in the same bar counts as a LOSS.

## The gate (fixed — no tuning until something passes)

Chronological 70/30 IS/OOS. IS selection: n>=100, wr>=51%, p<0.05,
BH-FDR q<=0.10 across all cells. Survivors measured once on OOS; final gate:

```
OOS n >= 100  AND  OOS win rate >= 51%  AND  OOS p < 0.05  AND  OOS net expectancy > 0
```

## Reading the verdicts

- **PASS** — goes to `config/validated_patterns.json`; candidate for paper trading.
- **FAIL_IS / FAIL_OOS** — tested and missed the gate. Said plainly. Dead.
- **INSUFFICIENT_N_(IS|OOS)** — not enough occurrences to test. NOT a failure;
  an untested hypothesis. The cure is more feed days, not parameter changes.

Honest expectation: gap_fill fires at most ~1/symbol/day, so reaching 100 OOS
occurrences per cell needs roughly a year of data — expect INSUFFICIENT_N
there until the archive is much deeper. Most cells SHOULD die; the machine
rejecting them is the process working.
