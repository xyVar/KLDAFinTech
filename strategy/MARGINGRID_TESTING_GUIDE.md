# MarginGrid EA - Testing Guide

## EA Location
```
C:\Users\PC\Desktop\KLDAFinTech\strategy\MarginGrid_EA.mq5
```

---

## QUICK START

### 1. Compile the EA
```
1. Open MetaEditor
2. Open: MarginGrid_EA.mq5
3. Press F7 or click Compile
4. Check for errors (should be 0 errors, 0 warnings)
```

### 2. Backtest Configuration

**Strategy Tester Settings:**
```
Expert Advisor: MarginGrid_EA
Symbol: ORCL.US-24 (or any from the 8 stocks)
Period: H1 (1 Hour)
Date Range: 2023.01.01 to 2024.12.31
Deposit: 10000 EUR
Leverage: 1:5
Execution: Hedging Account
Optimization: Disabled (first test)
```

**Input Parameters:**
```
AccountCapital = 10000.0        // Total capital
NumberOfStocks = 8              // Trading 8 stocks
GridStepPercent = 5.0           // 5% grid steps
MaxGridLevels = 6               // Max 6 levels (30% range)
EquityProtectionPercent = 50.0  // Safety: Equity ≥ 50% margin
```

### 3. Expected Behavior

**Logs to Watch:**
```
=== MarginGrid EA Starting ===
Account Capital: €10000
Stocks: 8
Grid Step: 5%
Max Levels: 6

[ORCL.US-24] Allocated: €1250 | Margin/lot: €40 | Lots/level: 5.2
[NVDA.US-24] Allocated: €1250 | Margin/lot: €100 | Lots/level: 2.1
...

[ORCL.US-24] INITIAL BUY: 5.2 lots @ $200
[ORCL.US-24] ADD SELL #1: 5.2 lots @ $210 (+5.0% from initial)
[ORCL.US-24] ADD SELL #2: 5.2 lots @ $220 (+10.0% from initial)
...
```

---

## WHAT THE EA DOES

### Initial Entry
```
1. Calculates margin per lot for each stock
2. Divides €10k equally: €1,250 per stock
3. Calculates lots per level: €1,250 / (6 levels × margin)
4. Opens initial BUY position when EA starts
```

### SELL Triggers (Price Rising)
```
IF current_price >= initial_buy_price × (1 + 5%)
THEN ADD SELL position

Example (ORCL @ $200):
├─ $210 (+5%)  → SELL level 1
├─ $220 (+10%) → SELL level 2
├─ $230 (+15%) → SELL level 3
├─ $240 (+20%) → SELL level 4
├─ $250 (+25%) → SELL level 5
└─ $260 (+30%) → SELL level 6 (MAX)
```

### BUY Triggers (SELL Profits)
```
FOR each SELL position:
    IF SELL profit >= +5%
    THEN ADD BUY position

Example:
├─ SELL opened @ $210
├─ Price drops to $200
├─ SELL profit = ($210 - $200) / $210 = +4.8% (almost there)
└─ Price drops to $199.50
    └─ SELL profit = +5.0% → TRIGGER BUY
```

### Safety Checks
```
BEFORE opening any position:
1. Calculate required margin
2. Check free margin available
3. Calculate future total margin
4. Check: Equity ≥ 50% × Future Margin
5. If FAIL → Skip this position, log warning
```

---

## MONITORING DURING TEST

### Key Metrics to Watch

**Equity Curve:**
- Should oscillate with unrealized P&L
- Should NOT drop below 50% of margin used
- Drawdown controlled by hedging

**Position Count:**
- Each stock can have max 6 SELL + unlimited BUY positions
- If range-bound: ~6 BUY + 6 SELL per stock (balanced)
- If trending up: 1 BUY + 6+ SELL (unbalanced SHORT)
- If trending down: 6+ BUY + 1 SELL (unbalanced LONG)

**Margin Usage:**
- Should increase gradually as positions accumulate
- Balanced positions = lower margin
- Unbalanced positions = higher margin
- Safety stop triggers if equity drops below 50% of margin

**Logs:**
```
Look for:
✅ "INITIAL BUY" - confirms first entry
✅ "ADD SELL #1...#6" - confirms grid building
✅ "ADD BUY (SELL ticket...)" - confirms BUY triggers
⚠️ "SAFETY: Cannot open..." - margin limit reached
🔴 "SAFETY STOP" - equity protection triggered
```

---

## COMMON SCENARIOS

### Scenario 1: Price Rises 30% Then Drops
```
Step 1-7: Price $200 → $260
├─ Opens 1 BUY @ $200
└─ Opens 6 SELL @ $210, $220, $230, $240, $250, $260

Step 8-13: Price $260 → $200
├─ 6 SELL positions go into profit
└─ Opens 6 BUY positions as each SELL hits +5% profit

Result:
├─ Total: 7 BUY + 6 SELL
├─ Net exposure: +1 BUY (nearly balanced)
└─ Unrealized P&L: Positive (SELLs averaged $240, now at $200 = profit)
```

### Scenario 2: Strong Uptrend (Risk Case)
```
Price $200 → $400 (+100%)

Positions:
├─ 1 BUY @ $200 (+100% = +€1,040)
├─ 6 SELL avg @ $230 (-74% = -€4,420)
└─ Net P&L: -€3,380 (-33.8% of account) 🔴

Safety stop should trigger before this!
```

### Scenario 3: Range-Bound Market (Best Case)
```
Price oscillates $200 ↔ $250 (10 cycles)

After 10 cycles:
├─ 30 BUY positions (avg $225)
├─ 30 SELL positions (avg $235)
├─ Net exposure: Nearly balanced
├─ Each full cycle generates unrealized profit
└─ Total unrealized: +€3,000 to €5,000 ✅
```

---

## TROUBLESHOOTING

### Issue: "Symbol not available"
```
Fix: Symbol not in Market Watch
1. Open Market Watch (Ctrl+M)
2. Right-click → Symbols
3. Search for stock (e.g., ORCL.US-24)
4. Show symbol
5. Restart backtest
```

### Issue: "OrderCalcMargin failed"
```
Fix: Symbol specifications not loaded
1. Ensure symbol is visible in Market Watch
2. Check Pepperstone demo account is active
3. Verify leverage is 1:5
4. Check account mode is HEDGING
```

### Issue: No positions opening
```
Check logs for:
1. "SAFETY: Cannot open..." - margin issue
2. "ERROR: ... failed" - trade execution issue
3. Verify lots_per_level > 0.1 (minimum lot size)
```

### Issue: Too many positions, margin call
```
This means:
1. All 8 stocks hit max grid levels
2. Unbalanced exposure (all trending same direction)
3. Safety stop should have triggered

Adjust:
├─ Reduce MaxGridLevels from 6 to 4
├─ Increase GridStepPercent from 5% to 7%
└─ Increase EquityProtectionPercent from 50% to 60%
```

---

## OPTIMIZATION IDEAS (AFTER FIRST TEST)

### If Too Conservative (Low Profit)
```
1. Reduce GridStepPercent: 5% → 4% (more triggers)
2. Increase MaxGridLevels: 6 → 8 (wider range)
3. Reduce EquityProtectionPercent: 50% → 40% (more risk)
```

### If Too Aggressive (Margin Issues)
```
1. Increase GridStepPercent: 5% → 6% (fewer triggers)
2. Reduce MaxGridLevels: 6 → 5 (narrower range)
3. Increase EquityProtectionPercent: 50% → 60% (safer)
```

### If Imbalanced Positions
```
Add logic to:
1. Stop adding SELL if net exposure < -20 lots
2. Stop adding BUY if net exposure > +20 lots
3. Force balancing trades at extreme imbalance
```

---

## EXPECTED RESULTS (2-Year Backtest)

### Conservative Estimate
```
Total Trades: 200-400 positions opened
Win Rate: N/A (positions never closed)
Max Positions: 80-120 (8 stocks × 10-15 avg)
Max Margin: €4,000-6,000
Max Drawdown: -10% to -20%
Final Unrealized P&L: +€500 to +€2,000 (+5% to +20%)
```

### Realistic Estimate (Range Markets)
```
Final Unrealized P&L: +€1,500 to +€3,000 (+15% to +30%)
Margin Usage: 30-50% of account
Position Count: 100-150
Drawdown: -15% max
```

### Worst Case (Strong Trend)
```
Final Unrealized P&L: -€2,000 to -€5,000 (-20% to -50%)
Margin Usage: 70-90% of account
Position Count: 200+
Drawdown: -40% to -60%
Safety stop triggered
```

---

## NEXT STEPS AFTER TESTING

1. **Review backtest report:**
   - Check equity curve
   - Count total positions per stock
   - Identify max drawdown point
   - Calculate margin efficiency

2. **Analyze position distribution:**
   - Which stocks accumulated most positions?
   - Which direction was dominant (BUY or SELL)?
   - Were positions balanced or unbalanced?

3. **Check safety stops:**
   - Did equity protection trigger?
   - Were there margin warnings?
   - Did any stock hit max grid levels?

4. **Optimize if needed:**
   - Adjust grid step size
   - Adjust max levels
   - Adjust position sizing
   - Add imbalance limits

5. **Forward test:**
   - Run on 2025 data (out-of-sample)
   - Compare results to backtest
   - Validate strategy robustness

---

## READY TO TEST

**Command:**
```
1. Compile MarginGrid_EA.mq5
2. Open Strategy Tester
3. Configure as shown above
4. Click START
5. Monitor logs and equity curve
6. Review results when complete
```

**Good luck with testing!**
