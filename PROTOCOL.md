# PROTOCOL — Canonical Project Memory

> This file is the persistent memory of the project's goal and decisions.
> Sessions forget everything else. If it is not written here (or in code), it does not survive.

**Last updated:** 2025-06-28

---

## GOAL

Build a **rule-based daily trading system** that scans a broad market universe, ranks
opportunities by a signal with *proven* edge, sizes positions by fixed risk, and exits
same-day at a defined target or stop. The aim is **positive expectancy over many trades** —
not certainty on any single one.

### Context (read this every session)
- The user is recovering a previously lost sum deposited with the broker (Pepperstone).
- **Recovery-trading discipline is mandatory:** position size is driven by the *rules*, never
  by how far up or down the account is. The system must size identically in drawdown and in
  profit. Urgency is the enemy; expectancy is the recovery mechanism.

---

## DECISIONS (locked 2025-06-28)

| # | Decision | Choice |
|---|----------|--------|
| 1 | **Universe** | **Everything, ranked** — scan the full liquid Pepperstone universe; the ranking score decides what to trade. No hand-picked basket. |
| 2 | **Path** | **Validate edge first** — prove a signal predicts moves on historical data *before* risking money. |
| 3 | **Risk** | **1% per trade**, fixed fractional. Hard-coded, P&L-independent. |

---

## EXECUTION REALITY (what runs where)

- **Execution** → MT5 / Pepperstone on the user's Windows machine, via an Expert Advisor (EA).
  This sandbox cannot reach it; the EA is written here and loaded there by the user.
- **Research / validation** → KLDAFinTech platform (Polygon → PostgreSQL `market_data`).
  This is where edge is proven. Runs on the user's machine where the DB lives.

### Data reality (honest constraints)
- Current DB holds **daily** OHLCV for **US stocks** only (Polygon).
- FX / crypto / indices / gold and **intraday** data are **not yet ingested**.
- The intraday VIX-checkpoint idea (3am/6am/10am) **cannot be validated on daily data** —
  it needs intraday candles first.
- The validation harness is **universe-agnostic**: any symbol with (date, close) gets ranked,
  so the universe expands automatically as more data is added to the same table.

---

## THE CANONICAL DECISION LOOP (how we "pick what, based on what")

```
1. UNIVERSE   → all liquid symbols with sufficient history
2. SIGNAL     → score each symbol (momentum / mean-reversion / volatility regime)
3. RANK       → sort by score; strongest opportunities to the top
4. FILTER     → drop wide spreads / dead sessions / news blackouts
5. SIZE       → risk 1% per trade (fixed fractional, P&L-independent)
6. EXECUTE    → top N signals, market order
7. EXIT       → ATR target & stop, or same-day time-out
```

Picking "what" = the **rank** in step 3. The computer does not *know* — it sorts by a number
we defined and *proved* has predictive value. That proof is Quest 1.

---

## QUESTS

- **QUEST 1 (active):** Measure whether ranking signals actually predict forward returns on the
  existing daily stock data. Deliverable: `edge_validation.py`. Verdict gate: a signal needs
  positive mean spread with t-stat > ~2 to be considered a real edge.
- **QUEST 2 (pending Quest 1):** If an edge is found → build the MT5 EA implementing the loop.
- **QUEST 3 (pending):** Expand universe (FX/crypto/indices) + intraday data for the VIX idea.

---

## OPEN THREADS
- The user reported the local CLI created folders inside the MT5 app directory and disrupted
  it. No MT5 install or `.mq5`/`.mqh` files are reachable from this sandbox — those live on
  the user's Windows machine. If existing EAs need review, the user must paste/upload them.
