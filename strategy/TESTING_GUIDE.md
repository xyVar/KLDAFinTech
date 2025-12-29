# TESTING GUIDE - Quarterly Range EA

## FILES CREATED

1. **QUARTERLY_RANGE_STRATEGY.md** - Complete strategy documentation
2. **QuarterlyRange_EA.mq5** - Expert Advisor implementation
3. **3stock_quarterly_ranges.csv** - Historical data export

---

## CURRENT MARKET SIGNALS (Dec 26, 2025)

Based on Q4 2025 ranges:

```
╔══════════════════════════════════════════════════════════╗
║ ORCL.US-24 - Current: $197.00                           ║
╠══════════════════════════════════════════════════════════╣
║ Q4 Range: $177.06 → $322.09                             ║
║ BUY ZONE: $177.06 → $220.57                             ║
║                                                          ║
║ STATUS: In BUY ZONE ✅                                   ║
║ SIGNAL: OPEN LONG                                        ║
║ Entry: $197.00                                           ║
║ Target: $249.58 (50% of range)                          ║
║ Stop Loss: $167.45 (-15%)                               ║
║ Potential Profit: +26.7%                                ║
╚══════════════════════════════════════════════════════════╝

╔══════════════════════════════════════════════════════════╗
║ AVGO.US-24 - Current: $351.35                           ║
╠══════════════════════════════════════════════════════════╣
║ Q4 Range: $321.42 → $423.93                             ║
║ BUY ZONE: $321.42 → $352.17                             ║
║                                                          ║
║ STATUS: At edge of BUY ZONE ⚠️                          ║
║ SIGNAL: OPEN LONG (marginal)                            ║
║ Entry: $351.35                                           ║
║ Target: $372.68 (50% of range)                          ║
║ Stop Loss: $298.65 (-15%)                               ║
║ Potential Profit: +6.1%                                 ║
╚══════════════════════════════════════════════════════════╝

╔══════════════════════════════════════════════════════════╗
║ TSLA.US-24 - Current: $485.98                           ║
╠══════════════════════════════════════════════════════════╣
║ Q4 Range: $380.96 → $498.79                             ║
║ SELL ZONE: $463.66 → $498.79                            ║
║                                                          ║
║ STATUS: In SELL ZONE ✅                                  ║
║ SIGNAL: OPEN SHORT                                       ║
║ Entry: $485.98                                           ║
║ Target: $439.88 (50% of range)                          ║
║ Stop Loss: $558.88 (+15%)                               ║
║ Potential Profit: +9.5%                                 ║
╚══════════════════════════════════════════════════════════╝
```

**Expected positions when EA starts:**
- ORCL: LONG (strong signal)
- AVGO: LONG (weak signal, barely in buy zone)
- TSLA: SHORT (strong signal)

---

## HOW TO TEST

### **Option 1: Live Test on Demo Account (Recommended)**

1. **Compile EA**
   - Open MetaEditor
   - Open: `QuarterlyRange_EA.mq5`
   - Click "Compile" (F7)
   - Check for errors

2. **Attach to Chart**
   - Open MT5
   - Open any chart (ORCL.US-24 recommended)
   - Drag `QuarterlyRange_EA` from Navigator → Expert Advisors
   - Set parameters:
     - LotSize: 0.1 (or smaller for safety)
     - StopLossPercent: 15
     - TakeProfitPercent: 50
   - Click "OK"

3. **Monitor**
   - Check "Experts" tab for logs
   - EA will print current status on start
   - Will open positions if in BUY/SELL zones
   - Watch "Trade" tab for opened positions

4. **What to Expect**
   - EA should immediately open:
     - LONG ORCL at ~$197
     - LONG AVGO at ~$351 (maybe)
     - SHORT TSLA at ~$486
   - Positions will close when:
     - Target reached (50% of range)
     - Stop loss hit (-15% for LONG, +15% for SHORT)
     - You manually close them

---

### **Option 2: Strategy Tester (Backtest)**

1. **Open Strategy Tester**
   - Press Ctrl+R
   - Or View → Strategy Tester

2. **Configure**
   - Expert Advisor: QuarterlyRange_EA
   - Symbol: ORCL.US-24
   - Period: H1 (1 hour)
   - Date Range: 2025.10.01 → 2025.12.26 (Q4 2025)
   - Deposit: 10000
   - Leverage: 1:100
   - Execution: Every tick based on real ticks

3. **Set Parameters**
   - LotSize: 0.1
   - StopLossPercent: 15
   - TakeProfitPercent: 50

4. **Run**
   - Click "Start"
   - Wait for backtest to complete

5. **Analyze Results**
   - Check "Results" tab for trades
   - Check "Graph" for equity curve
   - Check "Report" for statistics

**Expected backtest results:**
- Should show 2-3 trades per stock
- Win rate: ~60-70%
- Profit factor: >1.5
- Total profit: Positive

---

## MONITORING

### **Key Metrics to Track**

```
1. Entry Accuracy
   → Did EA enter at correct zones?
   → ORCL should enter when price < $220.57
   → TSLA should SHORT when price > $463.66

2. Exit Accuracy
   → Did positions close at targets?
   → ORCL target: $249.58
   → TSLA target: $439.88

3. Stop Loss Triggers
   → Any positions stopped out?
   → ORCL stop: $167.45 (-15%)
   → TSLA stop: $558.88 (+15%)

4. Overall Performance
   → Total profit/loss
   → Win rate %
   → Average trade duration
```

---

## LOGS TO CHECK

When EA starts, you should see:

```
========================================
QUARTERLY RANGE EA - Q4 2025
========================================

Current Market Status:
========================================
ORCL.US-24:
  Price: $197.00
  Zone: BUY ZONE (lower 30%)
  Signal: LONG
  Range: $177.06 → $322.09

AVGO.US-24:
  Price: $351.35
  Zone: BUY ZONE (lower 30%)
  Signal: LONG
  Range: $321.42 → $423.93

TSLA.US-24:
  Price: $485.98
  Zone: SELL ZONE (upper 30%)
  Signal: SHORT
  Range: $380.96 → $498.79
```

Then trades opening:

```
LONG opened: ORCL.US-24 at $197.00 Target: $249.58 Stop: $167.45
LONG opened: AVGO.US-24 at $351.35 Target: $372.68 Stop: $298.65
SHORT opened: TSLA.US-24 at $485.98 Target: $439.88 Stop: $558.88
```

---

## TROUBLESHOOTING

**EA doesn't open trades:**
- Check "AutoTrading" is enabled (green button in toolbar)
- Check lot size isn't too large for account balance
- Check symbols are available in Market Watch

**Compilation errors:**
- Check MQL5 syntax
- Ensure all brackets closed
- Check log for specific error line

**Wrong entry prices:**
- EA uses BID price for checks
- Actual entry uses ASK (LONG) or BID (SHORT)
- Small spread difference is normal

---

## NEXT STEPS

After testing:

1. **If profitable** → Increase lot size gradually
2. **If losing** → Review entry zones, adjust percentages
3. **Monitor for Q4 end** → Close all positions Dec 31
4. **Prepare for Q1 2026** → Update ranges based on predictions

**Predicted Q1 2026 ranges in strategy doc** → Adjust EA code when Q1 starts
