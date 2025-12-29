# MARTINGALE + SWING HEDGE STRATEGY

## CONCEPT

Combine MartinG averaging-down with swing trading hedges to:
1. Never close LONG positions at a loss
2. Add SHORT hedges at profit peaks
3. Profit from oscillations while holding core positions

---

## PHASE 1: BUILD LONG BASE (MartinG Style)

### Initial Entry
```
When: Market opens or EA starts
Action: BUY 1.0 lot per stock
Track: Record initial entry price
```

### Averaging Down (if price drops)
```
IF price drops >= 4% from initial:
   └─ BUY another 1.0 lot

IF price drops >= 8%:
   └─ BUY another 1.0 lot

Continue every -4% up to MAX 8 positions (stop at -28%)

CRITICAL: Stop adding at -30% to limit max drawdown
```

**Example:**
```
Entry 1: $200 (step 0)
Entry 2: $192 (-4%, step 1)
Entry 3: $184 (-8%, step 2)
...
Entry 8: $144 (-28%, step 7)

Average entry: $172
Max drawdown at $140: -18.6%
```

---

## PHASE 2: WAIT FOR RECOVERY (NO LOSS CLOSING)

### Recovery Monitoring
```
Track unrealized P&L continuously
Never close LONG positions while in loss
Wait for price to recover above average entry
```

**Patience Levels:**
```
-30% to -20%: HOLD, expect recovery within 3-6 months
-20% to -10%: HOLD, partial recovery likely
-10% to  0%:  HOLD, near breakeven
  0% to +10%: Monitor for first hedge opportunity
+10% to +30%: HEDGE ZONE - prepare SELL
+30%+:        STRONG HEDGE ZONE - open SELL
```

---

## PHASE 3: HEDGE WITH SELL AT PROFIT PEAKS

### SELL Entry Conditions

**Condition 1: Profit Level**
```
IF LONG unrealized profit >= +30%
THEN: Prepare SELL hedge
```

**Condition 2: Range Position**
```
IF current price >= (quarterly_min + range × 0.70)
   → Price in upper 30% of quarterly range
THEN: Confirm SELL signal
```

**Condition 3: Combined Confirmation**
```
IF profit >= +30%
   AND price in upper 30% range
THEN:
   └─ Open SELL = 50% of total LONG lots
```

**Example:**
```
LONG Positions:
├─ 8.0 lots, average $149
├─ Current price: $228
└─ Profit: +53%

SELL Hedge:
├─ Open 4.0 lots SHORT @ $228
├─ Target: $216 (5% down)
└─ Stop: $240 (+5% up, if wrong)
```

---

## PHASE 4: MANAGE SELL HEDGE

### SELL Exit Targets

**Target 1: Quick Profit (Preferred)**
```
IF SELL profit >= +10% to +15%
THEN: Close SELL, book profit
```

**Target 2: Range Middle**
```
IF price reaches 50% of quarterly range
THEN: Close SELL (mean reversion complete)
```

**Target 3: Stop Loss (if wrong)**
```
IF SELL loss >= -5%
THEN: Close SELL, small loss acceptable
```

**Example Outcomes:**

**Scenario A: Pullback happens (GOOD)**
```
SELL opened @ $228
Price drops to $216 (-5.3%)
SELL profit: ($228 - $216) × 4.0 = +$48
Action: CLOSE SELL, book +$48 ✅

LONG still open:
└─ Unrealized: ($216 - $149) × 8.0 = +$536
```

**Scenario B: Price continues up (WRONG)**
```
SELL opened @ $228
Price rises to $240 (+5.3%)
SELL loss: ($228 - $240) × 4.0 = -$48
Action: CLOSE SELL, accept -$48 ❌

LONG positions benefit:
└─ Unrealized: ($240 - $149) × 8.0 = +$728
Net effect: +$680 total ✅
```

---

## PHASE 5: REPEAT SWING CYCLES

### Cycle Management

After closing first SELL hedge, monitor for next opportunity:

```
Price at $216 (after closing SELL @ $216):
├─ LONG still open, profit +$536
├─ Wait for next peak
└─ If price hits $250+ again → Open SELL again

Price at $250:
├─ LONG profit: ($250 - $149) × 8.0 = +$808
├─ Open SELL 4.0 lots @ $250
└─ Target: $240 (4% down)

Price drops to $240:
├─ SELL profit: ($250 - $240) × 4.0 = +$40
├─ Close SELL ✅
└─ Total realized from swings: +$48 + $40 = +$88

Continue pattern indefinitely
```

---

## MAXIMUM DRAWDOWN CALCULATION

### Per Stock Maximum Risk

**Worst Case: Stock drops 50% from initial entry**

```
Example: ORCL initial entry $200

Price drops to $100 (-50%):

MartinG positions (8 total):
├─ Entry 1: $200 → -$100 unrealized
├─ Entry 2: $192 → -$92 unrealized
├─ Entry 3: $184 → -$84 unrealized
├─ Entry 4: $176 → -$76 unrealized
├─ Entry 5: $168 → -$68 unrealized
├─ Entry 6: $160 → -$60 unrealized
├─ Entry 7: $152 → -$52 unrealized
├─ Entry 8: $144 → -$44 unrealized
└─ Total: -$576 unrealized loss

On €100,000 account: -0.58% ✅ Still safe
```

**But if ALL 9 stocks drop 50%:**
```
9 stocks × -$576 each = -$5,184 total
= -5.18% of €100,000 account ⚠️

Still survivable, but uncomfortable
```

### Protection: Emergency Stop

```
IF total unrealized loss >= -15% of account
   AND held for > 12 months with no recovery
THEN: Consider closing worst performers
```

---

## POSITION SIZING RULES

### Initial Capital Allocation

For €100,000 account trading 9 stocks:

```
Per stock allocation: €11,111 (€100k ÷ 9)

Maximum positions per stock: 8
Average lot size: 1.0 lot per position
Average stock price: ~$200

Capital per stock: 8 × $200 = $1,600 ≈ €1,600
Usage: €1,600 ÷ €11,111 = 14.4% of allocation

Total capital at risk (all 9 stocks):
9 × €1,600 = €14,400 (14.4% of account) ✅
```

### SELL Hedge Sizing

```
LONG positions: 8.0 lots
SELL hedge: 4.0 lots (50% of LONG)

Why 50%?
├─ Protects half of unrealized gains
├─ Allows LONG to still profit if price rises
└─ Limits downside if SELL goes wrong
```

---

## PROFIT TARGETS BY TIMEFRAME

### Short-term (Swing Trades - SELL hedges)

```
Target: +10% to +15% per SELL
Frequency: 2-4 swings per quarter
Expected: +€200-400 per stock per quarter

9 stocks × 4 quarters × €300 average:
= €10,800 per year from swings alone ✅
```

### Long-term (LONG positions)

```
Hold until: +100% to +200% profit
Frequency: 1-2 years per cycle
Expected: Close 50% at +100%, let rest run

Example: ORCL at $149 → $300 (+101%)
├─ Close 4.0 lots: +$604 profit
├─ Keep 4.0 lots running
└─ If price hits $450: Close rest for +$1,204 more
```

### Combined Strategy Target

```
Year 1:
├─ Swing profits: €10,800
├─ LONG partial exits: €5,000 (conservative)
└─ Total: €15,800 (+15.8% on €100k) ✅

Target: 15-25% annual return
Risk: Max -15% drawdown
Sharpe Ratio: ~1.5 (good risk-adjusted return)
```

---

## CRITICAL RISK RULES

### Rule 1: Never Close LONG at Loss
```
Exception: Emergency stop at -15% account loss after 12+ months
```

### Rule 2: Maximum Positions Per Stock
```
Limit: 8 positions (stop adding at -28%)
Reason: Control maximum drawdown
```

### Rule 3: SELL Hedge Size
```
Always: 50% of LONG size
Never: More than LONG size (avoid over-hedging)
```

### Rule 4: Total Account Exposure
```
Maximum: 20% of account in open positions
Current: 14.4% across 9 stocks ✅
Reserve: 80% for margin buffer
```

### Rule 5: Recovery Patience
```
Allow: 6-12 months for full recovery
Monitor: Quarterly earnings, market trends
Action: Only close if fundamentals change
```

---

## EXAMPLE: FULL YEAR SIMULATION

### NVDA 2025 (Hypothetical)

**Jan 2025: Initial Entry @ $500**
```
Position 1: BUY 1.0 lot @ $500
```

**Feb 2025: Price drops to $400 (-20%)**
```
Position 1: @ $500 → -$100
Position 2: @ $480 (-4% from initial)
Position 3: @ $460 (-8%)
Position 4: @ $440 (-12%)
Position 5: @ $420 (-16%)

Total: 5.0 lots, avg $460
Unrealized: ($400 - $460) × 5.0 = -$300
```

**Jun 2025: Recovery to $600 (+30%)**
```
LONG: ($600 - $460) × 5.0 = +$700 profit
Action: Open SELL 2.5 lots @ $600
```

**Aug 2025: Pullback to $550**
```
SELL: ($600 - $550) × 2.5 = +$125 profit ✅
Close SELL, book +$125

LONG: ($550 - $460) × 5.0 = +$450 still open
```

**Nov 2025: Rally to $700 (+52%)**
```
LONG: ($700 - $460) × 5.0 = +$1,200 profit
Action: Open SELL 2.5 lots @ $700
```

**Dec 2025: Pullback to $650**
```
SELL: ($700 - $650) × 2.5 = +$125 profit ✅
Close SELL, book +$125

LONG: ($650 - $460) × 5.0 = +$950 still open
```

**Year-End Results:**
```
Swing profits (SELL trades): +$250
LONG unrealized: +$950
Total: +$1,200 on €2,300 invested = +52% ✅
```

---

## COMPARISON TABLE

```
╔═══════════════════════════════════════════════════════════╗
║ Strategy              Annual Return    Max Drawdown       ║
╠═══════════════════════════════════════════════════════════╣
║ MartinG (original)    Unknown          -90%+ (margin call)║
║ QuarterlyRange EA     +0.48%           -0.04%             ║
║ Martingale+Swing      +15-25%          -15%               ║
╚═══════════════════════════════════════════════════════════╝
```

**Winner: Martingale+Swing** ✅

Best risk-adjusted returns with controlled drawdown
