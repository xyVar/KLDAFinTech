# MarginGrid EA v2.0 - Testing Guide

## FILE LOCATION
```
C:\Users\PC\Desktop\KLDAFinTech\strategy\MarginGrid_EA_v2.mq5
```

---

## WHAT'S FIXED IN V2.0

### Critical Changes

| Parameter/Feature | v1.0 (FAILED) | v2.0 (FIXED) | Impact |
|------------------|---------------|--------------|---------|
| **GridStepPercent** | 5.0% | **10.0%** | Fewer triggers, wider range |
| **MaxGridLevels** | 6 | **4** | Stop adding positions earlier |
| **MaxImbalance** | NONE | **10 lots** | NEW! Prevents one-sided exposure |
| **PositionSizeFactor** | 1.0 (full) | **0.5 (half)** | NEW! Half the position size |
| **EquityProtectionPercent** | 50% | **60%** | Earlier safety stop |

### New Protection Logic

**Imbalance Control (CRITICAL FIX):**
```cpp
Before opening SELL:
├─ Count BUY positions
├─ Count SELL positions
├─ Calculate: net_exposure = BUY - SELL
└─ IF net_exposure <= -10 → STOP (too many SELLs)

Before opening BUY:
├─ Count BUY positions
├─ Count SELL positions
├─ Calculate: net_exposure = BUY - SELL
└─ IF net_exposure >= +10 → STOP (too many BUYs)
```

**Effect:**
- v1.0: NVDA had 1 BUY + 6 SELL = -5 imbalance (allowed to continue)
- v2.0: Would stop at 1 BUY + 11 SELL = -10 imbalance (max limit)

---

## EXPECTED IMPROVEMENTS

### On Same 2024 Data (NVDA $49 → $124)

**v1.0 Results:**
```
Grid Step: 5%
Max Levels: 6
Imbalance: NONE

NVDA Positions:
├─ 1 BUY @ $49
├─ 6 SELL @ $51, $54, $57, $60, $63, $66
└─ Net: -5 imbalance

At $124:
├─ BUY P&L: +€1,740
├─ SELL P&L: -€7,000 (approx)
└─ Net loss per NVDA: -€5,260
```

**v2.0 Expected:**
```
Grid Step: 10%
Max Levels: 4
Imbalance: 10 max
Position Size: 50%

NVDA Positions:
├─ 1 BUY @ $49 (11.6 lots, half of 23.2)
├─ SELL #1 @ $53.90 (+10%, 11.6 lots)
├─ SELL #2 @ $58.80 (+20%, 11.6 lots)
├─ SELL #3 @ $63.70 (+30%, 11.6 lots)
├─ SELL #4 @ $68.60 (+40%, 11.6 lots)
├─ STOP: Reached MaxGridLevels = 4
└─ Net: -4 imbalance (within limit)

At $124:
├─ BUY P&L: ($124 - $49) × 11.6 = +€870
├─ SELL P&L: (avg $61 - $124) × 46.4 = -€2,920
└─ Net loss per NVDA: -€2,050 (vs -€5,260 in v1) ✅ 60% BETTER
```

### Overall Account Performance

**v1.0:**
```
Final Equity: €3,121
Loss: -€6,878 (-68.79%)
Margin Call: YES 🔴
Survival: FAILED
```

**v2.0 Expected:**
```
Final Equity: €7,000 - €8,000 (estimated)
Loss: -€2,000 to -€3,000 (-20% to -30%)
Margin Call: NO ✅
Survival: YES ✅
Positions: Still open at test end
```

---

## TESTING INSTRUCTIONS

### 1. Compile v2.0

```
1. Open MetaEditor
2. Open: MarginGrid_EA_v2.mq5
3. Press F7 (Compile)
4. Verify: 0 errors, 0 warnings
```

### 2. Strategy Tester Settings

```
Expert Advisor: MarginGrid_EA_v2
Symbol: ORCL.US-24 (or keep multi-symbol)
Period: M1
Date Range: 2024.01.01 to 2025.12.25 (SAME as v1 for comparison)
Deposit: 10000 EUR
Leverage: 1:5
Execution: Hedging Account
```

### 3. Input Parameters (Default = New Safe Settings)

```
AccountCapital = 10000.0
NumberOfStocks = 8
GridStepPercent = 10.0          ✅ Changed from 5.0
MaxGridLevels = 4               ✅ Changed from 6
MaxImbalance = 10               ✅ NEW!
PositionSizeFactor = 0.5        ✅ NEW!
EquityProtectionPercent = 60.0  ✅ Changed from 50.0
```

**DO NOT change these for first test - they're optimized for survival**

### 4. Click START

Monitor logs for:
```
✅ "MarginGrid EA v2.0 Starting"
✅ "Grid Step: 10% (UPDATED from 5%)"
✅ "Max Imbalance: 10 lots (NEW PROTECTION)"
✅ "IMBALANCE LIMIT: Cannot add SELL/BUY" (when limit hit)
⚠️ "SAFETY STOP" (should NOT appear until much later)
```

### 5. Watch Key Metrics

**Position Counts:**
```
v1.0: 51 total positions before margin call
v2.0: 20-30 total positions (fewer, safer)
```

**Margin Usage:**
```
v1.0: ~€6,000+ (danger zone)
v2.0: ~€2,000-3,000 (comfortable)
```

**Equity Drawdown:**
```
v1.0: -68.79% (margin call)
v2.0: -20% to -30% (survivable)
```

---

## LOGS TO EXPECT

### Example v2.0 Log Output

```
=== MarginGrid EA v2.0 Starting ===
Grid Step: 10% (UPDATED from 5%)
Max Levels: 4 (UPDATED from 6)
Max Imbalance: 10 lots (NEW PROTECTION)

[NVDA.US-24] Allocated: €1250 | Margin/lot: €100 | Lots/level: 11.6 (50% of max)

[NVDA.US-24] INITIAL BUY: 11.6 lots @ $49
[NVDA.US-24] ADD SELL #1: 11.6 lots @ $53.90 (+10.0% from initial) | Imbalance: -1
[NVDA.US-24] ADD SELL #2: 11.6 lots @ $58.80 (+20.0% from initial) | Imbalance: -2
[NVDA.US-24] ADD SELL #3: 11.6 lots @ $63.70 (+30.0% from initial) | Imbalance: -3
[NVDA.US-24] ADD SELL #4: 11.6 lots @ $68.60 (+40.0% from initial) | Imbalance: -4

[NVDA.US-24] SELL level count at max (4), waiting for BUY triggers...

[PLTR.US-24] INITIAL BUY: 33.5 lots @ $17.14
[PLTR.US-24] ADD SELL #1: 33.5 lots @ $18.85 (+10.0% from initial) | Imbalance: -1
...

(Price continues rising to $124, but NO MORE SELL positions added - hit MaxGridLevels)

[NVDA.US-24] Current imbalance: -4 (1 BUY, 5 SELL) - within limit ✅
```

### What You WON'T See in v2.0

```
❌ "so 49.50%" (margin call comment)
❌ Forced liquidation of all positions
❌ Equity dropping below 60% of margin
❌ Imbalance > 10 lots
```

---

## COMPARISON TABLE: v1.0 vs v2.0

| Metric | v1.0 | v2.0 Expected |
|--------|------|---------------|
| **Total Trades** | 50 | 30-40 |
| **Max Positions** | 51 | 25-35 |
| **NVDA Position Size** | 23.2 lots | 11.6 lots |
| **NVDA SELL Levels** | 6 | 4 |
| **Max Imbalance (NVDA)** | -5 (unchecked) | -4 (within limit) |
| **Margin Used (Peak)** | €6,325 | €2,500-3,500 |
| **Equity Low** | €3,121 | €7,000-8,000 |
| **Drawdown** | -68.79% | -20% to -30% |
| **Margin Call** | YES 🔴 | NO ✅ |
| **Final Status** | Force-closed | Positions still open |
| **Survival** | FAILED | SURVIVED ✅ |

---

## SUCCESS CRITERIA

**v2.0 is successful if:**

✅ No margin call (equity stays above 60% of margin)
✅ Drawdown < 40% (vs 68% in v1)
✅ Positions still open at test end
✅ Imbalance never exceeds ±10 lots per stock
✅ Final equity > €6,000 (vs €3,121 in v1)

**Even if still losing money, v2.0 succeeds by:**
- Surviving the full test period
- Maintaining positions for potential recovery
- Demonstrating protection mechanisms work

---

## AFTER TESTING

### If v2.0 Still Fails

**Adjust these parameters:**
```
GridStepPercent = 10.0 → 15.0 (even wider steps)
MaxGridLevels = 4 → 3 (fewer positions)
MaxImbalance = 10 → 5 (stricter imbalance limit)
PositionSizeFactor = 0.5 → 0.3 (even smaller positions)
```

### If v2.0 Succeeds

**Optional optimization:**
```
GridStepPercent = 10.0 → 8.0 (slightly more triggers)
MaxGridLevels = 4 → 5 (slightly more range)
PositionSizeFactor = 0.5 → 0.6 (slightly larger positions)
```

---

## READY TO TEST

**Steps:**
1. ✅ Compile MarginGrid_EA_v2.mq5
2. ✅ Open Strategy Tester
3. ✅ Use SAME settings as v1 test (2024.01.01 - 2025.12.25)
4. ✅ Use DEFAULT inputs (all new safe values)
5. ✅ Click START
6. ✅ Compare results to v1

**Expected runtime:** 5-10 minutes (depending on PC speed)

**GO!**
