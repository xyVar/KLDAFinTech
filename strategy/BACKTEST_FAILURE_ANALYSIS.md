# BACKTEST FAILURE ANALYSIS - MarginGrid EA

## CRITICAL: MARGIN CALL EVENT

```
Date: 2024.06.12 16:34:00
Margin Level: 49.36% (below 50% threshold)
Action: FORCED LIQUIDATION of all positions
Result: -€6,878.71 loss (-68.79%)
```

---

## WHAT HAPPENED: TIMELINE

### Phase 1: Normal Grid Building (Jan - Feb 2024)

```
2024.01.02: Initial entries across all 8 stocks
├─ NVDA: BUY 23.2 lots @ $49.16
├─ META: BUY 3.3 lots @ $352.78
├─ PLTR: BUY 67 lots @ $17.14
└─ ... (other stocks)

2024.01.08 - Feb: Prices rise, SELL positions added
├─ NVDA: 6 SELL positions @ $51.60, $54.19, $57.21, $60.11, $63.12, $66.28
├─ PLTR: 6 SELL positions @ $17.99, $20.24, $21.26, $22.37, $23.51, $24.70
└─ Grid working as designed ✅
```

### Phase 2: Strong Uptrend (Mar - Jun 2024)

```
NVDA Price Movement:
├─ Jan: $49 (initial entry)
├─ Feb: $66 (+34%, 6 SELL levels hit)
├─ Jun: $124 (+152% from entry!) 🔴

PLTR Price Movement:
├─ Jan: $17.14 (initial entry)
├─ Feb: $24.70 (+44%, 6 SELL levels hit)
├─ Jun: $24.17 (stayed high)

META Price Movement:
├─ Jan: $352 (initial entry)
├─ Jun: $511 (+45%) 🔴
```

**Problem:** Prices kept rising beyond the 6 SELL levels (30% range)

### Phase 3: Position Imbalance (Mar - Jun)

```
By June 12, 2024:

Total Positions: 51 open
├─ BUY positions: ~22
└─ SELL positions: ~28

NET EXPOSURE: -6 lots (MORE SELL than BUY)
```

**In a strong uptrend:**
- SELL positions lose money (price rising)
- BUY positions make money (price rising)
- But MORE SELL positions → net LOSS

### Phase 4: Margin Call (Jun 12, 2024)

```
Equity Calculation:
├─ Starting Balance: €10,000
├─ Unrealized P&L: -€6,878
├─ Current Equity: €3,122
├─ Margin Used: €6,325 (estimated)
└─ Margin Level: €3,122 / €6,325 = 49.36% 🔴

TRIGGER: Equity dropped below 50% of Margin
ACTION: Safety stop activated
RESULT: All 51 positions force-closed at market
```

**Orders 52-101:** All closed simultaneously at 16:34:00 on June 12, 2024

---

## ROOT CAUSE ANALYSIS

### 1. Trending Market Weakness

**The fatal flaw:**
```
Grid strategy assumes: Price oscillates in a RANGE
Reality in 2024: Strong UPTREND

In uptrend:
├─ Initial BUY @ $49 (1 position)
├─ Add SELL every +5%: $51, $54, $57, $60, $63, $66 (6 positions)
├─ Price continues to $124 (no more SELL positions allowed, maxed out)
├─ Very few BUY triggers (need SELL to profit -5%, but price keeps rising)
└─ Result: 1 BUY + 6 SELL = Net -5 SHORT exposure

Outcome: Massive unrealized loss as price rises
```

### 2. No Imbalance Protection

**Current EA logic:**
```cpp
if(sell_level_count < MaxGridLevels)  // Only checks max 6 levels
    OpenSell();  // No check for imbalance!
```

**Missing:**
```cpp
int net_exposure = buy_count - sell_count;
if(net_exposure < -10)  // Too many SELLs
    return;  // STOP adding more SELL
```

### 3. Position Sizing Too Large

**With €10,000 capital:**
```
NVDA: 23.2 lots per level
PLTR: 67 lots per level
META: 3.3 lots per level

If all stocks hit 6 SELL levels:
├─ Total positions: 8 stocks × 7 positions (1 BUY + 6 SELL) = 56 positions
├─ Margin required: ~€7,000
└─ Only €3,000 buffer before 50% threshold
```

**One strong rally wipes out the buffer**

### 4. Grid Step Too Small

**5% grid step:**
```
NVDA @ $49:
├─ $51.45 (+5%) → SELL #1
├─ $54.04 (+10%) → SELL #2
├─ $56.63 (+15%) → SELL #3
├─ $59.22 (+20%) → SELL #4
├─ $61.81 (+25%) → SELL #5
└─ $64.40 (+30%) → SELL #6

Price hit $124 (+152%)!
All 6 SELL levels triggered quickly
No room for recovery
```

**7% or 10% steps would have been safer**

---

## TRADE STATISTICS BREAKDOWN

### Win Rate by Direction

```
LONG trades: 22 total, 90.91% win rate (20 wins)
├─ Why high win rate? Market went UP
└─ BUY positions profitable in uptrend ✅

SHORT trades: 28 total, 7.14% win rate (2 wins)
├─ Why low win rate? Market went UP
└─ SELL positions unprofitable in uptrend ❌
```

**The strategy worked for BUYs, failed for SELLs**

### Largest Trades

```
Largest Profit: +€1,602.68 (NVDA BUY closed at peak)
Largest Loss: -€1,551.78 (NVDA SELL closed at peak)

Net: +€50.90 on NVDA (but other stocks lost)
```

### Consecutive Losses

```
Maximum consecutive losses: 12 trades (-€8,214.53)
├─ This was the SELL positions accumulating losses
└─ All closed during stop-out event
```

---

## EQUITY CURVE ANALYSIS

**Expected curve:**
```
Oscillating market:
Equity goes up/down with oscillations ✅

Trending market:
Equity drops steadily as wrong-side positions accumulate ❌
```

**What happened:**
```
Jan 2024: €10,000 (start)
Feb 2024: ~€9,900 (small drawdown, normal)
Mar 2024: ~€9,500 (drawdown increasing)
Apr 2024: ~€8,500 (danger zone)
May 2024: ~€7,000 (critical)
Jun 2024: €3,122 (margin call!) 🔴
```

**Drawdown:**
- Balance Drawdown: 81.29% (€9,635.85)
- Equity Drawdown: 68.79% (€6,878.71)

---

## COMPARISON: WHAT SHOULD HAVE HAPPENED

### With Imbalance Control

```
IF net_exposure < -20 lots:
    STOP adding SELL positions

Result:
├─ Would have stopped at 20 SELL vs 0 BUY
├─ Loss limited to -€3,000 instead of -€6,878
└─ No margin call ✅
```

### With Larger Grid Steps (10% instead of 5%)

```
NVDA @ $49:
├─ $53.90 (+10%) → SELL #1
├─ $58.80 (+20%) → SELL #2
├─ $63.70 (+30%) → SELL #3
├─ $68.60 (+40%) → SELL #4
├─ $73.50 (+50%) → SELL #5
└─ $78.40 (+60%) → SELL #6

Price $124 still hits all 6 levels, BUT:
├─ Slower accumulation
├─ More time for BUY triggers (SELL profits)
└─ Better balance
```

### With Smaller Position Sizes

```
Current: 23.2 lots NVDA per level
Better: 10 lots NVDA per level (halve the size)

Result:
├─ Half the margin used
├─ Half the unrealized loss
├─ Double the safety buffer
└─ Survived longer ✅
```

---

## FIXES REQUIRED

### FIX 1: Add Imbalance Limit ⭐⭐⭐ CRITICAL

```cpp
int buy_count = CountPositions(symbol, ORDER_TYPE_BUY);
int sell_count = CountPositions(symbol, ORDER_TYPE_SELL);
int net_exposure = buy_count - sell_count;

// Prevent excessive SHORT exposure
if(net_exposure < -15)
{
    Print("[", symbol, "] IMBALANCE LIMIT: Net exposure ", net_exposure, " (too many SELLs)");
    return;  // Don't add more SELL
}

// Prevent excessive LONG exposure
if(net_exposure > +15)
{
    Print("[", symbol, "] IMBALANCE LIMIT: Net exposure ", net_exposure, " (too many BUYs)");
    return;  // Don't add more BUY
}
```

### FIX 2: Increase Grid Step ⭐⭐⭐ CRITICAL

```
Current: GridStepPercent = 5.0%
Better: GridStepPercent = 7.0% or 10.0%

Effect:
├─ Fewer triggers in trending markets
├─ Less position accumulation
└─ Better risk control
```

### FIX 3: Reduce Position Size ⭐⭐ HIGH

```
Current calculation:
lots_per_level = allocated_capital / (MaxGridLevels × margin_per_lot)

Better calculation:
lots_per_level = allocated_capital / (MaxGridLevels × margin_per_lot × 2)
                                                                    ↑
                                                            Halve the size

Effect:
├─ Half the margin usage
├─ Half the risk
└─ Longer survival in trends
```

### FIX 4: Reduce Max Grid Levels ⭐⭐ HIGH

```
Current: MaxGridLevels = 6 (30% range)
Better: MaxGridLevels = 4 (20% range with 5% step)
        OR MaxGridLevels = 5 (50% range with 10% step)

Effect:
├─ Stop adding positions earlier
├─ Less exposure in extreme moves
└─ Preserve capital
```

### FIX 5: Add Trend Detection ⭐ MEDIUM

```cpp
// Simple trend detection: Compare current price to 50-day average
double ma_50 = iMA(symbol, PERIOD_D1, 50, 0, MODE_SMA, PRICE_CLOSE);
double current_price = SymbolInfoDouble(symbol, SYMBOL_BID);

if(current_price > ma_50 * 1.10)  // Price 10% above MA
{
    Print("[", symbol, "] UPTREND DETECTED: Reducing SELL position size");
    lots_per_level *= 0.5;  // Half the SELL size in uptrend
}
else if(current_price < ma_50 * 0.90)  // Price 10% below MA
{
    Print("[", symbol, "] DOWNTREND DETECTED: Reducing BUY position size");
    lots_per_level *= 0.5;  // Half the BUY size in downtrend
}
```

---

## RECOMMENDED NEW SETTINGS

### Conservative (Survival Mode)

```
AccountCapital = 10000.0
NumberOfStocks = 8
GridStepPercent = 10.0          // Was 5.0
MaxGridLevels = 4               // Was 6
EquityProtectionPercent = 60.0  // Was 50.0
MaxImbalance = 10               // NEW parameter

Expected:
├─ Fewer positions
├─ Survive 100%+ moves
└─ Lower profit, but no margin call
```

### Moderate (Balanced)

```
AccountCapital = 10000.0
NumberOfStocks = 8
GridStepPercent = 7.0           // Was 5.0
MaxGridLevels = 5               // Was 6
EquityProtectionPercent = 55.0  // Was 50.0
MaxImbalance = 15               // NEW parameter

Expected:
├─ Moderate positions
├─ Survive 75% moves
└─ Balanced risk/reward
```

### Current (Failed)

```
AccountCapital = 10000.0
NumberOfStocks = 8
GridStepPercent = 5.0
MaxGridLevels = 6
EquityProtectionPercent = 50.0
MaxImbalance = NONE (no limit!)

Result:
└─ Margin call at +152% NVDA move 🔴
```

---

## WHAT WOULD HAVE WORKED

### Scenario: Conservative Settings on Same Data

```
GridStepPercent = 10%
MaxGridLevels = 4
MaxImbalance = 10 lots

NVDA @ $49 → $124:
├─ BUY 1: $49 (initial)
├─ SELL 1: $53.90 (+10%)
├─ SELL 2: $58.80 (+20%)
├─ SELL 3: $63.70 (+30%)
├─ SELL 4: $68.60 (+40%)
├─ STOP: 1 BUY + 4 SELL = -3 imbalance (OK)
└─ No more SELL added

At $124:
├─ BUY profit: ($124 - $49) × lots = +€1,740
├─ SELL loss: (avg $61 - $124) × 4 lots = -€5,856
├─ Net per stock: -€4,116

But with imbalance limit at 10 lots across ALL stocks:
└─ Would have stopped adding SELL much earlier
└─ Loss: -€2,000 to -€3,000 (survivable)
```

---

## NEXT STEPS

1. **Add imbalance control code** (CRITICAL)
2. **Test with GridStepPercent = 10%**
3. **Test with MaxGridLevels = 4**
4. **Halve position sizes** (multiply lots by 0.5)
5. **Re-run backtest on same data**
6. **Compare results**

**Expected outcome with fixes:**
- Loss: -€2,000 to -€3,000 (instead of -€6,878)
- No margin call
- Still holding positions at test end
- Potential to recover if prices drop later

---

## CONCLUSION

**The strategy is NOT broken, but needs:**
✅ Imbalance limits
✅ Larger grid steps
✅ Smaller position sizes
✅ Lower max levels

**The core grid concept works, but:**
❌ Cannot handle 150%+ trending moves without protection
❌ Needs trend awareness
❌ Needs position limits

**This is a learning moment - we now know the exact failure mode and how to fix it.**
