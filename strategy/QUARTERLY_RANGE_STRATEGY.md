# QUARTERLY RANGE TRADING STRATEGY

## CONCEPT

Trade stocks based on their position within the current quarter's historical range.

---

## STRATEGY RULES

### **ENTRY LOGIC**

**BUY Signal (LONG):**
```
IF current_price <= (quarterly_min + range * 0.30)
   → Price in LOWER 30% of quarterly range
   → Enter LONG position
```

**SELL Signal (SHORT):**
```
IF current_price >= (quarterly_min + range * 0.70)
   → Price in UPPER 30% of quarterly range
   → Enter SHORT position
```

**WAIT/HOLD:**
```
IF price between 30%-70% of range
   → MIDDLE zone
   → No new positions
```

---

## EXIT LOGIC

**Take Profit:**
- LONG positions: Exit at 50% of quarterly range (middle)
- SHORT positions: Exit at 50% of quarterly range (middle)

**Stop Loss:**
- LONG positions: -15% from entry
- SHORT positions: +15% from entry

**End of Quarter:**
- Close ALL positions on last day of quarter
- Recalculate ranges for new quarter

---

## POSITION SIZING

Based on quarterly volatility:

```
HIGH VOLATILITY quarters (>80% range):
  → Position size: 50% of normal
  → Higher risk, smaller position

MEDIUM VOLATILITY quarters (40-80% range):
  → Position size: 100% of normal
  → Standard position

LOW VOLATILITY quarters (<40% range):
  → Position size: 150% of normal
  → Lower risk, larger position
```

---

## CURRENT QUARTER RANGES (Q4 2025)

### **ORCL.US-24**
```
Q4 2025 Range: $177.06 → $322.09 (81.91% range) [HIGH VOL]
Current Price: $197.00

BUY ZONE (lower 30%):  $177.06 → $220.57
WAIT ZONE (middle 40%): $220.57 → $278.58
SELL ZONE (upper 30%):  $278.58 → $322.09

STATUS: In BUY ZONE ✅
ACTION: ENTER LONG
Entry: $197.00
Target: $249.58 (50% of range)
Stop: $167.45 (-15%)
Potential: +26.7%
```

### **AVGO.US-24**
```
Q4 2025 Range: $321.42 → $423.93 (31.89% range) [LOW VOL]
Current Price: $351.35

BUY ZONE (lower 30%):  $321.42 → $352.17
WAIT ZONE (middle 40%): $352.17 → $393.18
SELL ZONE (upper 30%):  $393.18 → $423.93

STATUS: In BUY ZONE ✅ (barely)
ACTION: ENTER LONG (or WAIT)
Entry: $351.35
Target: $372.68 (50% of range)
Stop: $298.65 (-15%)
Potential: +6.1%
```

### **TSLA.US-24**
```
Q4 2025 Range: $380.96 → $498.79 (30.93% range) [LOW VOL]
Current Price: $485.98

BUY ZONE (lower 30%):  $380.96 → $416.31
WAIT ZONE (middle 40%): $416.31 → $463.66
SELL ZONE (upper 30%):  $463.66 → $498.79

STATUS: In SELL ZONE ✅
ACTION: ENTER SHORT
Entry: $485.98
Target: $439.88 (50% of range)
Stop: $558.88 (+15%)
Potential: +9.5%
```

---

## PREDICTED Q1 2026 RANGES

Based on historical patterns (Q1 2024 vs Q1 2025):

### **ORCL**
```
Q1 2024: 30.42% range
Q1 2025: 41.36% range (+36% increase)

Predicted Q1 2026:
  Starting from Q4 2025 close (~$197)
  Expected range: 45-55% (increasing volatility trend)
  Predicted MIN: $175
  Predicted MAX: $285
```

### **AVGO**
```
Q1 2024: 38.16% range
Q1 2025: 55.31% range (+45% increase)

Predicted Q1 2026:
  Starting from Q4 2025 close (~$351)
  Expected range: 65-80% (increasing volatility trend)
  Predicted MIN: $310
  Predicted MAX: $530
```

### **TSLA**
```
Q1 2024: 56.48% range
Q1 2025: 108.87% range (+93% increase)

Predicted Q1 2026:
  Starting from Q4 2025 close (~$486)
  Expected range: 100-120% (maintaining high volatility)
  Predicted MIN: $400
  Predicted MAX: $900
```

---

## RISK MANAGEMENT

**Account Allocation:**
- ORCL: 40% (high volatility, high opportunity)
- AVGO: 30% (low volatility, stable)
- TSLA: 30% (high volatility, risky)

**Maximum Positions:**
- Only 1 position per stock at a time
- Maximum 3 positions total (all 3 stocks)

**Daily Limits:**
- Max daily loss: -3% of account
- Max drawdown: -10% of account

**Quarter End:**
- Close all positions on last day of quarter
- Recalculate ranges before new quarter
- Review and adjust strategy

---

## TESTING PARAMETERS

**Backtest Period:**
- Test on Q3 2025 + Q4 2025 data
- Validate rules work as expected

**Forward Test:**
- Run on demo account for Q1 2026
- Monitor performance vs predictions

**Success Metrics:**
- Win rate > 60%
- Profit factor > 1.5
- Average trade > +5%
