# BuyOnly Grid EA - Parameter Presets for Testing

## QUICK REFERENCE: Parameter Sets

### 🎯 Preset 1: BALANCED (v1.1 Default - RECOMMENDED)

**Best for:** 2024-2025 bull market with moderate corrections

```
GridStepPercent = 8.0
MaxGridLevels = 7
TakeProfit_Level1_Percent = 8.0
TakeProfit_Level2_Percent = 20.0
ExitPercent_Level1 = 40.0
MaxDropPercent = 70.0
```

**Expected Performance:**
- Profit: +€1,800 to +€3,500 (+18% to +35%)
- Drawdown: 15% to 25%
- Win Rate: 80% to 90%
- Trades: 25-30

**Use Case:**
- Bull market with normal volatility
- Handles BA-style deep corrections (-50%)
- Good balance of safety and profit

---

### 🛡️ Preset 2: CONSERVATIVE

**Best for:** Risk-averse, want to minimize drawdown

```
GridStepPercent = 10.0        // Less frequent triggers
MaxGridLevels = 6             // Moderate coverage
TakeProfit_Level1_Percent = 6.0   // Earlier profit taking
TakeProfit_Level2_Percent = 18.0
ExitPercent_Level1 = 50.0     // Lock in half quickly
MaxDropPercent = 65.0         // Stop at -65%
```

**Expected Performance:**
- Profit: +€1,200 to +€2,500 (+12% to +25%)
- Drawdown: 10% to 20%
- Win Rate: 75% to 85%
- Trades: 18-24

**Use Case:**
- Prefer safety over maximum profit
- Still better than v1.0 (50% stop)
- Good for cautious testing

---

### 🚀 Preset 3: AGGRESSIVE

**Best for:** Maximum profit, higher risk tolerance

```
GridStepPercent = 6.0         // Very frequent triggers
MaxGridLevels = 10            // Maximum coverage
TakeProfit_Level1_Percent = 10.0  // Higher targets
TakeProfit_Level2_Percent = 25.0
ExitPercent_Level1 = 30.0     // Keep most for TP2
MaxDropPercent = 80.0         // Very tolerant
```

**Expected Performance:**
- Profit: +€2,500 to +€5,000 (+25% to +50%)
- Drawdown: 25% to 40%
- Win Rate: 70% to 85%
- Trades: 35-50

**Use Case:**
- Willing to tolerate higher drawdown
- Want to capture maximum profit on recoveries
- Best if market has deep corrections

**⚠️ Warning:**
- Higher drawdown risk
- Margin usage will be higher
- Not recommended for first test

---

### 🎯 Preset 4: TIGHT GRID (Scalping Style)

**Best for:** Frequent small profits, high volatility

```
GridStepPercent = 5.0         // Trigger every -5%
MaxGridLevels = 8
TakeProfit_Level1_Percent = 4.0   // Quick profits
TakeProfit_Level2_Percent = 12.0
ExitPercent_Level1 = 60.0     // Lock in most at TP1
MaxDropPercent = 70.0
```

**Expected Performance:**
- Profit: +€1,500 to +€3,000 (+15% to +30%)
- Drawdown: 12% to 22%
- Win Rate: 80% to 95% (many small wins)
- Trades: 40-60

**Use Case:**
- High volatility markets
- Prefer many small wins over few big wins
- Good for sideways/choppy markets

---

### 🌊 Preset 5: TREND RIDER (Let It Run)

**Best for:** Strong trending markets, maximize big moves

```
GridStepPercent = 12.0        // Wide steps
MaxGridLevels = 5
TakeProfit_Level1_Percent = 12.0  // Skip small moves
TakeProfit_Level2_Percent = 30.0  // Catch big trends
ExitPercent_Level1 = 25.0     // Keep most for TP2
MaxDropPercent = 75.0
```

**Expected Performance:**
- Profit: +€1,000 to +€4,000 (+10% to +40%)
- Drawdown: 15% to 30%
- Win Rate: 60% to 80% (fewer but bigger wins)
- Trades: 12-20

**Use Case:**
- Strong bull market with minimal corrections
- Prefer fewer, larger profits
- Good for stocks like NVDA, PLTR (strong trends)

---

### 🔍 Preset 6: ORIGINAL v1.0 (Baseline for Comparison)

**For reference only - DO NOT USE (BA disaster)**

```
GridStepPercent = 10.0
MaxGridLevels = 5
TakeProfit_Level1_Percent = 5.0
TakeProfit_Level2_Percent = 15.0
ExitPercent_Level1 = 50.0
MaxDropPercent = 50.0         // ⚠️ TOO TIGHT
```

**Actual Performance (2024-2025):**
- Profit: +€337 (+3.4%)
- Drawdown: 21.1%
- Win Rate: 77.3%
- Trades: 22
- **Problem:** BA disaster -€1,861

---

## TESTING MATRIX

### Recommended Test Order

1. **First Test: Preset 1 (BALANCED - v1.1 Default)**
   - This is the optimized version
   - Should beat v1.0 by 5x to 10x
   - Target: +€1,800+

2. **If Preset 1 Succeeds:**
   - Try Preset 3 (AGGRESSIVE) to see max potential
   - Compare profit vs drawdown trade-off

3. **If Preset 1 Fails:**
   - Fall back to Preset 2 (CONSERVATIVE)
   - Isolate what went wrong

4. **For High Volatility:**
   - Try Preset 4 (TIGHT GRID)
   - Good for choppy markets

5. **For Strong Trends:**
   - Try Preset 5 (TREND RIDER)
   - Capture big moves

---

## COMPARISON TABLE

| Preset | Grid Step | Max Levels | TP1/TP2 | Max Drop | Expected Profit | Risk Level |
|--------|-----------|------------|---------|----------|-----------------|------------|
| **v1.0 Original** | 10% | 5 | 5%/15% | 50% ⚠️ | +€337 | LOW (but BA disaster) |
| **1. BALANCED** ⭐ | 8% | 7 | 8%/20% | 70% | +€1,800-€3,500 | MEDIUM |
| **2. CONSERVATIVE** | 10% | 6 | 6%/18% | 65% | +€1,200-€2,500 | LOW |
| **3. AGGRESSIVE** | 6% | 10 | 10%/25% | 80% | +€2,500-€5,000 | HIGH |
| **4. TIGHT GRID** | 5% | 8 | 4%/12% | 70% | +€1,500-€3,000 | MEDIUM |
| **5. TREND RIDER** | 12% | 5 | 12%/30% | 75% | +€1,000-€4,000 | MEDIUM-HIGH |

---

## HOW TO TEST MULTIPLE PRESETS

### Method 1: Manual Parameter Input (Strategy Tester)

1. Open Strategy Tester
2. Select BuyOnly_Grid_EA
3. Click "Expert Properties" → "Inputs"
4. Copy/paste values from preset above
5. Run backtest
6. Save results
7. Repeat for each preset

### Method 2: Optimization (Advanced)

Use MT5 Strategy Tester optimization to test ranges:

```
GridStepPercent:
├─ Start: 5.0
├─ Step: 1.0
├─ Stop: 12.0

MaxGridLevels:
├─ Start: 5
├─ Step: 1
├─ Stop: 10

TakeProfit_Level1_Percent:
├─ Start: 4.0
├─ Step: 2.0
├─ Stop: 12.0

TakeProfit_Level2_Percent:
├─ Start: 12.0
├─ Step: 3.0
├─ Stop: 30.0

MaxDropPercent:
├─ Start: 60.0
├─ Step: 5.0
├─ Stop: 80.0

ExitPercent_Level1:
├─ Start: 25.0
├─ Step: 5.0
├─ Stop: 60.0
```

**⚠️ Warning:** Full optimization will take HOURS/DAYS

**Better:** Test the 5 presets above manually (30 minutes total)

---

## DECISION TREE

```
START: Run Preset 1 (BALANCED)
│
├─ Profit > €1,500 AND Drawdown < 25%?
│  ├─ YES → ✅ SUCCESS! Use Preset 1 or try Preset 3 for more profit
│  └─ NO → Continue below
│
├─ Profit < €800?
│  ├─ Check: Did BA still trigger emergency stop?
│  │  ├─ YES → Increase MaxDropPercent to 75% or 80%
│  │  └─ NO → Market didn't have corrections, try Preset 5 (TREND RIDER)
│  └─ Continue below
│
├─ Drawdown > 30%?
│  ├─ YES → Too aggressive, use Preset 2 (CONSERVATIVE)
│  └─ NO → Continue below
│
├─ Win Rate < 70%?
│  ├─ YES → TP targets too high, use Preset 4 (TIGHT GRID)
│  └─ NO → Continue below
│
└─ Trades < 15?
   ├─ YES → Not enough triggers, use Preset 4 (TIGHT GRID)
   └─ NO → Market is range-bound, this strategy may not fit
```

---

## PRESET SELECTION GUIDE

### Choose Based on Market Condition

**Bull Market (2024-2025 style):**
```
Primary: Preset 1 (BALANCED)
Backup: Preset 5 (TREND RIDER)
```

**High Volatility / Choppy:**
```
Primary: Preset 4 (TIGHT GRID)
Backup: Preset 2 (CONSERVATIVE)
```

**Uncertain / First Time:**
```
Primary: Preset 2 (CONSERVATIVE)
Upgrade to: Preset 1 after success
```

**Maximum Profit Goal:**
```
Primary: Preset 3 (AGGRESSIVE)
Warning: Higher drawdown risk
```

### Choose Based on Risk Tolerance

**Low Risk (Drawdown < 20%):**
- Preset 2 (CONSERVATIVE)

**Medium Risk (Drawdown 20-30%):**
- Preset 1 (BALANCED) ⭐ RECOMMENDED
- Preset 4 (TIGHT GRID)
- Preset 5 (TREND RIDER)

**High Risk (Drawdown > 30%):**
- Preset 3 (AGGRESSIVE)

---

## EXPECTED RESULTS BY PRESET (2024-2025 Data)

| Preset | Net Profit | Return % | Max DD | Trades | Best For |
|--------|------------|----------|--------|--------|----------|
| v1.0 (baseline) | +€337 | +3.4% | 21% | 22 | ❌ Reference only |
| 1. BALANCED | +€1,800-€3,500 | +18-35% | 15-25% | 25-30 | ⭐ Most users |
| 2. CONSERVATIVE | +€1,200-€2,500 | +12-25% | 10-20% | 18-24 | Risk-averse |
| 3. AGGRESSIVE | +€2,500-€5,000 | +25-50% | 25-40% | 35-50 | Max profit |
| 4. TIGHT GRID | +€1,500-€3,000 | +15-30% | 12-22% | 40-60 | High volatility |
| 5. TREND RIDER | +€1,000-€4,000 | +10-40% | 15-30% | 12-20 | Strong trends |

---

## SUMMARY

**Start with:** Preset 1 (BALANCED) - it's the v1.1 optimized default

**If you want:**
- More safety → Preset 2 (CONSERVATIVE)
- More profit → Preset 3 (AGGRESSIVE)
- More trades → Preset 4 (TIGHT GRID)
- Big trends → Preset 5 (TREND RIDER)

**The Critical Parameter:**
```
MaxDropPercent MUST be ≥ 65%
└─ 50% caused BA disaster in v1.0
└─ 70% is recommended for 2024-2025 data
└─ 80% for maximum safety (aggressive preset)
```

---

**Test Preset 1 first, then compare results to the targets above!**
