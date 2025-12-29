# MARTINGALE EA - COMPLETE STEP-BY-STEP ANALYSIS

## INPUT PARAMETERS

```
StepPercent = 4.0%  (configurable input)
Initial Lot Size = 1.0 lot (hardcoded)
Max Steps = 9 (hardcoded, means max 10 total positions)
```

---

## EXAMPLE SIMULATION: NVDA Starting at $200

### TABLE 1: POSITION ENTRIES (Price Dropping)

| Step | Trigger Price Drop | Entry Condition | Entry Price | Lots Added | Total Lots | Total Invested | Avg Entry Price | Unrealized P&L @ Entry |
|------|-------------------|-----------------|-------------|------------|------------|----------------|-----------------|------------------------|
| 0 | Initial Entry | No position exists | $200.00 | 1.0 | 1.0 | $200 | $200.00 | $0 |
| 1 | -4% from initial | Price ≤ $192.00 | $192.00 | 1.0 | 2.0 | $392 | $196.00 | -$8 |
| 2 | -8% from initial | Price ≤ $184.00 | $184.00 | 1.0 | 3.0 | $576 | $192.00 | -$24 |
| 3 | -12% from initial | Price ≤ $176.00 | $176.00 | 1.0 | 4.0 | $752 | $188.00 | -$48 |
| 4 | -16% from initial | Price ≤ $168.00 | $168.00 | 1.0 | 5.0 | $920 | $184.00 | -$80 |
| 5 | -20% from initial | Price ≤ $160.00 | $160.00 | 1.0 | 6.0 | $1,080 | $180.00 | -$120 |
| 6 | -24% from initial | Price ≤ $152.00 | $152.00 | 1.0 | 7.0 | $1,232 | $176.00 | -$168 |
| 7 | -28% from initial | Price ≤ $144.00 | $144.00 | 1.0 | 8.0 | $1,376 | $172.00 | -$224 |
| 8 | -32% from initial | Price ≤ $136.00 | $136.00 | 1.0 | 9.0 | $1,512 | $168.00 | -$288 |
| 9 | -36% from initial | Price ≤ $128.00 | $128.00 | 1.0 | 10.0 | $1,640 | $164.00 | -$360 |

**STOP HERE** - Max 10 positions reached (step 9 is the last)

---

### TABLE 2: UNREALIZED P&L AT DIFFERENT PRICE LEVELS (After All 10 Positions Open)

| Current Price | Drop from Initial | Drop from Avg | Total Position Value | Total Invested | Unrealized P&L | P&L % |
|--------------|-------------------|---------------|---------------------|----------------|----------------|-------|
| $200 | 0% | +22% | $2,000 | $1,640 | +$360 | +22.0% ✅ |
| $190 | -5% | +16% | $1,900 | $1,640 | +$260 | +15.9% ✅ |
| $180 | -10% | +10% | $1,800 | $1,640 | +$160 | +9.8% ✅ |
| $170 | -15% | +4% | $1,700 | $1,640 | +$60 | +3.7% ✅ |
| $164 | -18% | 0% | $1,640 | $1,640 | $0 | 0% (BREAKEVEN) |
| $160 | -20% | -2% | $1,600 | $1,640 | -$40 | -2.4% ⚠️ |
| $150 | -25% | -9% | $1,500 | $1,640 | -$140 | -8.5% ⚠️ |
| $140 | -30% | -15% | $1,400 | $1,640 | -$240 | -14.6% ❌ |
| $130 | -35% | -21% | $1,300 | $1,640 | -$340 | -20.7% ❌ |
| $120 | -40% | -27% | $1,200 | $1,640 | -$440 | -26.8% 🔴 |
| $100 | -50% | -39% | $1,000 | $1,640 | -$640 | -39.0% 🔴 |

---

### TABLE 3: RECOVERY SCENARIOS (From Different Bottoms)

**Scenario A: Bottomed at $140 (Step 7, -30% drop)**

| Recovery Price | Total Lots | Avg Entry | Position Value | Unrealized P&L | P&L % | Status |
|---------------|------------|-----------|----------------|----------------|-------|--------|
| $140 | 8.0 | $172 | $1,120 | -$256 | -18.6% | Bottom ❌ |
| $150 | 8.0 | $172 | $1,200 | -$176 | -12.8% | Recovering |
| $160 | 8.0 | $172 | $1,280 | -$96 | -7.0% | Recovering |
| $172 | 8.0 | $172 | $1,376 | $0 | 0% | BREAKEVEN ✅ |
| $180 | 8.0 | $172 | $1,440 | +$64 | +4.7% | Profit ✅ |
| $190 | 8.0 | $172 | $1,520 | +$144 | +10.5% | Good Profit ✅ |
| $200 | 8.0 | $172 | $1,600 | +$224 | +16.3% | Strong Profit 🔥 |
| $220 | 8.0 | $172 | $1,760 | +$384 | +27.9% | Excellent 🔥 |

**Scenario B: Bottomed at $128 (Step 9, -36% drop)**

| Recovery Price | Total Lots | Avg Entry | Position Value | Unrealized P&L | P&L % | Status |
|---------------|------------|-----------|----------------|----------------|-------|--------|
| $128 | 10.0 | $164 | $1,280 | -$360 | -22.0% | Bottom ❌ |
| $140 | 10.0 | $164 | $1,400 | -$240 | -14.6% | Recovering |
| $150 | 10.0 | $164 | $1,500 | -$140 | -8.5% | Recovering |
| $164 | 10.0 | $164 | $1,640 | $0 | 0% | BREAKEVEN ✅ |
| $180 | 10.0 | $164 | $1,800 | +$160 | +9.8% | Profit ✅ |
| $200 | 10.0 | $164 | $2,000 | +$360 | +22.0% | Strong Profit 🔥 |
| $220 | 10.0 | $164 | $2,200 | +$560 | +34.1% | Excellent 🔥 |
| $250 | 10.0 | $164 | $2,500 | +$860 | +52.4% | Outstanding 🚀 |

---

### TABLE 4: STEP PERCENTAGE COMPARISON (Different StepPercent Values)

**For 9 stocks, if ALL drop to max steps:**

| StepPercent | Trigger Points | Max Positions per Stock | Total Positions (9 stocks) | Price Drop to Max | Avg Entry vs Initial |
|------------|----------------|------------------------|---------------------------|------------------|---------------------|
| 2% | Every -2% | 10 | 90 | -18% | -9% |
| 3% | Every -3% | 10 | 90 | -27% | -13.5% |
| 4% | Every -4% | 10 | 90 | -36% | -18% |
| 5% | Every -5% | 10 | 90 | -45% | -22.5% |
| 6% | Every -6% | 10 | 90 | -54% | -27% |
| 8% | Every -8% | 10 | 90 | -72% | -36% |
| 10% | Every -10% | 10 | 90 | -90% | -45% |

**Analysis:**
- **StepPercent = 2%**: Adds positions quickly, fills up fast, limited averaging benefit
- **StepPercent = 4%**: Good balance, allows recovery room
- **StepPercent = 6-8%**: More conservative, fewer positions, larger drops tolerated
- **StepPercent = 10%**: Very conservative, but if stock crashes -90%, you're in deep trouble

---

### TABLE 5: MARGIN REQUIREMENT CALCULATION

**Assumptions:**
- Leverage: 1:5
- Margin per lot: 0.20 EUR (from your broker specs)
- Average stock price: $200

| Total Lots | Total Exposure ($) | Margin Required (EUR) | Account Balance Needed (Safety) |
|-----------|-------------------|----------------------|--------------------------------|
| 1.0 | $200 | €0.20 | €1,000 (min) |
| 2.0 | $400 | €0.40 | €2,000 |
| 5.0 | $1,000 | €1.00 | €5,000 |
| 10.0 | $2,000 | €2.00 | €10,000 |
| 90.0 (all 9 stocks max) | $18,000 | €18.00 | €90,000 ⚠️ |

**On €100,000 account:**
- Margin used if all stocks at max: €18 (0.018% of account) ✅
- BUT unrealized losses can be massive! Need buffer.

**CRITICAL:**
- Margin is LOW, but **unrealized losses** can wipe account
- With 90 positions and -20% market crash: -€3,600 loss (-3.6% of account)
- With -50% market crash: -€9,000 loss (-9% of account) 🔴

---

### TABLE 6: LOGIC FLOW DIAGRAM

```
┌─────────────────────────────────────────────────────────┐
│ MARTINGALE EA - TICK-BY-TICK LOGIC                      │
└─────────────────────────────────────────────────────────┘

For each TICK:
    For each of 9 STOCKS:

        ┌─────────────────────────────────────┐
        │ Check: Do we have position?         │
        └─────────────────────────────────────┘
                    │
                    ├─── NO ──────────────────────────┐
                    │                                 │
                    │                                 ▼
                    │                    ┌────────────────────────┐
                    │                    │ BUY 1.0 lot            │
                    │                    │ Record initial_price   │
                    │                    │ Set step = 0           │
                    │                    └────────────────────────┘
                    │
                    └─── YES ─────────────────────────┐
                                                      │
                                                      ▼
                            ┌─────────────────────────────────────┐
                            │ Calculate price_drop %:             │
                            │ (initial_price - current) / initial │
                            └─────────────────────────────────────┘
                                                      │
                                                      ▼
                            ┌─────────────────────────────────────┐
                            │ Check: price_drop >= StepPercent    │
                            │        × (current_step + 1) ?       │
                            └─────────────────────────────────────┘
                                                      │
                                    ├─── NO ──────────┴─── Do nothing, wait
                                    │
                                    └─── YES ─────────┐
                                                      │
                                                      ▼
                            ┌─────────────────────────────────────┐
                            │ Check: step < 9 (max)?              │
                            └─────────────────────────────────────┘
                                                      │
                                    ├─── NO ──────────┴─── Max positions, stop
                                    │
                                    └─── YES ─────────┐
                                                      │
                                                      ▼
                            ┌─────────────────────────────────────┐
                            │ BUY 1.0 lot                         │
                            │ Increment step counter              │
                            └─────────────────────────────────────┘
```

---

### TABLE 7: EXAMPLE TRADE SEQUENCE (ORCL Real Data)

**Using actual ORCL 2025 prices from our analysis:**

| Date | Event | Price | Step | Lots Added | Total Lots | Avg Entry | Unrealized P&L | Comments |
|------|-------|-------|------|------------|------------|-----------|----------------|----------|
| Jan 2 | Initial Entry | $167 | 0 | 1.0 | 1.0 | $167 | $0 | Market opens |
| Jan 15 | Price drops -4% | $160 | 1 | 1.0 | 2.0 | $163.50 | -$7 | First add |
| Feb 5 | Price drops -8% | $154 | 2 | 1.0 | 3.0 | $160.33 | -$19 | Second add |
| Mar 1 | Price drops -12% | $147 | 3 | 1.0 | 4.0 | $157.00 | -$40 | Third add |
| Mar 20 | Price drops -16% | $140 | 4 | 1.0 | 5.0 | $153.60 | -$68 | Fourth add |
| Apr 7 | **BOTTOM** | $118 | 7 | 1.0 | 8.0 | $149.00 | **-$248** | **Max drawdown** |
| May 15 | Recovery starts | $150 | - | 0 | 8.0 | $149.00 | +$8 | Above breakeven! ✅ |
| Jun 30 | Strong recovery | $228 | - | 0 | 8.0 | $149.00 | **+$632** | **+53% profit** 🔥 |
| Sep 10 | Peak | $346 | - | 0 | 8.0 | $149.00 | **+$1,576** | **+132% profit** 🚀 |
| Dec 26 | Current | $197 | - | 0 | 8.0 | $149.00 | **+$384** | **+32% profit** ✅ |

**Key Insights:**
- Max drawdown: -$248 (-20.8% of invested capital)
- Recovery time: 2 months (Apr → Jun)
- Peak profit: +$1,576 (+132%)
- **Problem:** EA has NO exit logic, so never books profit! ❌

---

### TABLE 8: MODIFICATION OPTIONS

| Feature to Add | Description | Impact | Complexity |
|---------------|-------------|--------|-----------|
| **Take Profit** | Close all positions at +X% profit | Books profit, prevents giveback | Easy ⭐ |
| **Stop Loss** | Close all at -X% loss | Limits max loss | Easy ⭐ |
| **Trailing Stop** | Lock in profits as price rises | Protects gains | Medium ⭐⭐ |
| **Position Sizing** | Reduce lot size with each step | Lower risk | Easy ⭐ |
| **Max Steps Limit** | Stop adding after N steps | Control max exposure | Easy ⭐ |
| **SELL Hedge** | Open SHORT when +30% profit | Profit from pullbacks | Hard ⭐⭐⭐ |
| **Time-based Exit** | Close positions after X days | Force decision | Easy ⭐ |
| **Partial Exits** | Close 50% at +50%, rest trails | Lock some profit | Medium ⭐⭐ |

---

### TABLE 9: CURRENT EA vs WHAT WE NEED

| Feature | Current MartinG | What We Need | Priority |
|---------|----------------|--------------|----------|
| Entry Logic | ✅ BUY every -4% | ✅ Keep same | - |
| Exit Logic | ❌ None | ✅ Add TP/SL | **HIGH** |
| Max Positions | ✅ 10 per stock | ⚠️ Maybe reduce to 8? | Medium |
| Position Sizing | ❌ Fixed 1.0 lot | ⚠️ Optional: decrease per step | Low |
| Hedge Logic | ❌ None | ✅ Add SELL at +30% | **HIGH** |
| Profit Protection | ❌ None | ✅ Trailing stop | **HIGH** |
| Loss Protection | ❌ None | ✅ Emergency stop -15% | **HIGH** |
| Multi-stock | ✅ 9 stocks | ✅ Keep same | - |
| Logging | ⚠️ Basic | ✅ Add detailed tracking | Medium |

---

## SUMMARY

**MartinG Current Logic:**
```
1. Start: BUY 1.0 lot when no position
2. Price drops -4%: BUY 1.0 lot (step 1)
3. Price drops -8%: BUY 1.0 lot (step 2)
...continue every -4%...
10. Price drops -36%: BUY 1.0 lot (step 9)
11. STOP adding (max 10 positions)
12. HOLD forever (no exit) ❌
```

**What Happens:**
- ✅ Good: Averages down entry price
- ✅ Good: Recovers when price bounces
- ❌ Bad: Can lose -22% if price drops -50%
- ❌ Bad: Never takes profit
- ❌ Bad: Ties up capital forever
- ❌ Bad: 9 stocks × 10 positions = 90 positions max 🔴

**Needs:**
1. **Take Profit** at +30% to +50%
2. **SELL Hedge** when in profit
3. **Emergency Stop** at -15% account loss
4. **Partial Exits** to lock gains
