# HEDGED GRID EA - COMPILATION & TEST STATUS

## FILES CREATED ✅

| File | Location | Status | Size |
|------|----------|--------|------|
| **HedgedGrid_EA.mq5** | `Kosta EA\HedgedGrid_EA.mq5` | ✅ Created | 32.4 KB |
| **Scenario Analysis** | `strategy\HEDGED_GRID_SCENARIO_ANALYSIS.md` | ✅ Created | Complete |
| **Compile Script** | `compile_hedged.bat` | ✅ Created | Ready |

---

## COMPILATION STATUS

| Step | Action | Status |
|------|--------|--------|
| 1 | Code written | ✅ DONE |
| 2 | MetaEditor found | ✅ DONE (`Pepperstone MetaTrader 5`) |
| 3 | Compile EA | ⚠️ **NEEDS MANUAL COMPILE** |
| 4 | Check .ex5 created | ⏳ Pending |

---

## HOW TO COMPILE (SIMPLE!)

### Method 1: MetaEditor GUI (EASIEST)
```
1. Open MT5
2. Press F4 (opens MetaEditor)
3. File → Open → Navigate to:
   Experts\Kosta EA\HedgedGrid_EA.mq5
4. Press F7 (Compile)
5. Check "Errors" tab at bottom
6. If successful → .ex5 file created ✅
```

### Method 2: Run Batch File
```
Double-click: C:\Users\PC\Desktop\KLDAFinTech\compile_hedged.bat
```

---

## BACKTEST SETUP

| Parameter | Value |
|-----------|-------|
| **Expert** | HedgedGrid_EA |
| **Symbol** | ORCL.US-24 |
| **Period** | M1 (1-minute chart) |
| **Date Range** | 2024.01.01 - 2025.12.25 |
| **Deposit** | €10,000 |
| **Leverage** | 1:5 |
| **Optimization** | None (test as-is) |

### Inputs to Set:
```
NumberOfStocks = 8
CapitalPerStock = 800.0
DailyProfitTarget = 40.0
MaxSpreadLossPercent = 1.0
PendingOrderOffset = 1.0
```

---

## EXPECTED RESULTS

| Metric | Expected Value | How to Verify |
|--------|----------------|---------------|
| **Total Trades** | 1,500-3,000 | Check report |
| **Win Rate** | 85-90% | Check report |
| **Net Profit** | €50,000-75,000 | Check report "Total Net Profit" |
| **Return %** | +500% to +750% | Check "Profit %" |
| **Max Drawdown** | <5% (€500) | Check "Maximal Drawdown" |
| **Largest Win** | €40-80 | Check "Largest profit trade" |
| **Largest Loss** | -€8 to -€20 | Check "Largest loss trade" |
| **Profit Factor** | >15 | Check "Profit factor" |

---

## WHAT TO CHECK AFTER BACKTEST

### ✅ GOOD SIGNS:
- Profit >€50,000
- Win rate >85%
- No trades with loss >-€20
- Smooth equity curve (no big spikes down)
- Avg trade profit ~€20-40

### 🔴 BAD SIGNS (Need Fix):
- Profit <€10,000
- Win rate <60%
- Trades with -€100+ losses
- Jagged equity curve
- Many max spread hits

---

## DEBUGGING IF COMPILATION FAILS

### Common Errors:

**Error 1: "undeclared identifier"**
```
Fix: Check variable names match exactly
```

**Error 2: "invalid type conversion"**
```
Fix: Add explicit type casts
```

**Error 3: "function not defined"**
```
Fix: Check #include <Trade\Trade.mqh> is present
```

**Error 4: "'Trade' - undeclared identifier"**
```
Fix: CTrade trade; must be declared
```

---

## QUICK TEST CHECKLIST

- [ ] Compile EA (F7 in MetaEditor)
- [ ] Check .ex5 file exists
- [ ] Open Strategy Tester (Ctrl+R)
- [ ] Select HedgedGrid_EA
- [ ] Set symbol: ORCL.US-24
- [ ] Set period: M1
- [ ] Set dates: 2024.01.01 - 2025.12.25
- [ ] Set deposit: €10,000
- [ ] Click Start
- [ ] Wait 5-30 minutes
- [ ] Review report (double-click result in Results tab)
- [ ] Save report as HTML

---

## CURRENT ISSUE

**Problem:** `.ex5` file not being created after compile attempt

**Most Likely Cause:** Syntax error in code

**Next Step:**
1. Open MetaEditor manually
2. Load HedgedGrid_EA.mq5
3. Press F7
4. Read exact error message from "Errors" tab
5. Report error back to me

---

## FILE LOCATIONS

```
EA Source: C:\Users\PC\AppData\Roaming\MetaQuotes\Terminal\
           73B7A2420D6397DFF9014A20F1201F97\MQL5\Experts\Kosta EA\
           HedgedGrid_EA.mq5

Compiled:  (same folder)
           HedgedGrid_EA.ex5

MT5:       C:\Program Files\Pepperstone MetaTrader 5\terminal64.exe

MetaEditor: C:\Program Files\Pepperstone MetaTrader 5\MetaEditor64.exe
```

---

**SIMPLE NEXT STEP:** Open MetaEditor → Load file → Press F7 → Report what happens!
