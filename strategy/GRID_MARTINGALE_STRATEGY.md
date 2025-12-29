# GRID MARTINGALE STRATEGY - BUY + SELL ACCUMULATION

## CORE CONCEPT

**NEVER CLOSE POSITIONS** - Instead, add opposite positions to profit from swings

```
Traditional: BUY → Wait → SELL to exit
Grid Strategy: BUY → ADD SELL → ADD BUY → ADD SELL → ...forever
```

---

## TABLE 1: POSITION ENTRY LOGIC

### Rule Set

| Direction | Entry Trigger | Lot Size | Keep Existing? | Example |
|-----------|---------------|----------|----------------|---------|
| **BUY #1** | Initial entry OR no positions | 1.0 | N/A | $200 |
| **SELL #1** | BUY profit ≥ +5% | 1.0 | ✅ Keep all BUYs | BUY @$200, price $210 → ADD SELL |
| **SELL #2** | BUY profit ≥ +10% from initial | 1.0 | ✅ Keep all | Price $220 → ADD SELL |
| **SELL #3** | BUY profit ≥ +15% from initial | 1.0 | ✅ Keep all | Price $230 → ADD SELL |
| **BUY #2** | Any SELL profit ≥ +5% | 1.0 | ✅ Keep all SELLs | SELL @$210, price $200 → ADD BUY |
| **BUY #3** | Each additional SELL in +5% profit | 1.0 | ✅ Keep all | For each SELL profit → ADD BUY |

### Critical Rule: NEVER CLOSE

```
❌ WRONG: BUY @$200 → Price $210 → CLOSE BUY (take profit)
✅ RIGHT: BUY @$200 → Price $210 → KEEP BUY + ADD SELL @$210
```

---

## TABLE 2: EXAMPLE SEQUENCE (ORCL)

### Scenario A: Price Rises Then Falls

| Step | Event | Price | Action | BUY Positions | SELL Positions | BUY P&L | SELL P&L | Net P&L |
|------|-------|-------|--------|---------------|----------------|---------|----------|---------|
| 1 | Initial | $200 | BUY 1.0 | 1.0 @$200 | 0 | $0 | $0 | $0 |
| 2 | +5% rise | $210 | ADD SELL | 1.0 @$200 | 1.0 @$210 | +$10 | $0 | +$10 |
| 3 | +10% rise | $220 | ADD SELL | 1.0 @$200 | 2.0 (@$210, @$220) | +$20 | -$10 | +$10 |
| 4 | +15% rise | $230 | ADD SELL | 1.0 @$200 | 3.0 (@$210, @$220, @$230) | +$30 | -$30 | $0 |
| 5 | Drop to $220 | $220 | ADD BUY | 2.0 (@$200, @$220) | 3.0 | +$30 | -$20 | +$10 |
| 6 | Drop to $210 | $210 | ADD BUY | 3.0 (@$200, @$220, @$210) | 3.0 | +$20 | $0 | +$20 |
| 7 | Drop to $200 | $200 | ADD BUY | 4.0 (@$200, @$220, @$210, @$200) | 3.0 | $0 | +$30 | +$30 |
| 8 | Rise to $210 | $210 | ADD SELL | 4.0 | 4.0 | +$20 | +$20 | +$40 |
| 9 | Rise to $220 | $220 | ADD SELL | 4.0 | 5.0 | +$40 | $0 | +$40 |
| 10 | Rise to $230 | $230 | ADD SELL | 4.0 | 6.0 | +$60 | -$40 | +$20 |

**After 10 steps:**
- Total BUY: 4.0 lots (avg $207.50)
- Total SELL: 6.0 lots (avg $218.33)
- Net exposure: -2.0 lots (more SELL than BUY)
- Unrealized P&L: +$20
- **NO positions closed, NO profit realized**

---

## TABLE 3: POSITION TRACKING SYSTEM

### Data Structures Needed

```cpp
struct GridPosition
{
    string symbol;
    int ticket;
    ENUM_ORDER_TYPE type;  // ORDER_TYPE_BUY or ORDER_TYPE_SELL
    double entry_price;
    double lots;
    datetime open_time;
    bool counted_for_next_level;  // Flag to prevent duplicate triggers
};

GridPosition all_positions[];  // Array of all open positions
```

### Tracking Variables Per Stock

| Variable | Purpose | Example Value |
|----------|---------|---------------|
| `initial_buy_price` | First BUY entry price | $200.00 |
| `last_sell_level` | Last SELL level triggered | 3 (means +15%) |
| `last_buy_level` | Last BUY level from SELLs | 2 (means 2 SELLs profited) |
| `total_buy_lots` | Sum of all BUY positions | 4.0 |
| `total_sell_lots` | Sum of all SELL positions | 6.0 |
| `buy_avg_price` | Average BUY entry | $207.50 |
| `sell_avg_price` | Average SELL entry | $218.33 |

---

## TABLE 4: TRIGGER CALCULATIONS

### SELL Entry Triggers (Based on BUY Profit)

```cpp
double current_price = SymbolInfoDouble(symbol, SYMBOL_ASK);
double buy_profit_percent = (current_price - initial_buy_price) / initial_buy_price * 100.0;

// Check for SELL levels
if(buy_profit_percent >= 5.0 && last_sell_level < 1)
{
    OpenSell(1.0, symbol);
    last_sell_level = 1;
}
else if(buy_profit_percent >= 10.0 && last_sell_level < 2)
{
    OpenSell(1.0, symbol);
    last_sell_level = 2;
}
else if(buy_profit_percent >= 15.0 && last_sell_level < 3)
{
    OpenSell(1.0, symbol);
    last_sell_level = 3;
}
// Continue for +20%, +25%, +30%...
```

### BUY Entry Triggers (Based on SELL Profit)

```cpp
// Check each SELL position
for(int i = 0; i < ArraySize(all_positions); i++)
{
    if(all_positions[i].type == ORDER_TYPE_SELL && !all_positions[i].counted_for_next_level)
    {
        double sell_entry = all_positions[i].entry_price;
        double current_price = SymbolInfoDouble(symbol, SYMBOL_BID);
        double sell_profit_percent = (sell_entry - current_price) / sell_entry * 100.0;

        if(sell_profit_percent >= 5.0)
        {
            OpenBuy(1.0, symbol);
            all_positions[i].counted_for_next_level = true;  // Don't trigger again
        }
    }
}
```

---

## TABLE 5: MARGIN CALCULATION FOR €10,000 ACCOUNT

### Pepperstone Conditions

```
Leverage: 1:5
Margin per lot: 0.20 EUR (from previous analysis)
Account: €10,000
```

### Maximum Positions Calculation

**Assuming average stock price: $200 (≈€200)**

| Total Lots | Total Exposure | Margin Required | % of Account | Positions Left |
|------------|----------------|-----------------|--------------|----------------|
| 1.0 | €200 | €0.20 | 0.002% | 49,999 lots ✅ |
| 10.0 | €2,000 | €2.00 | 0.02% | Safe ✅ |
| 50.0 | €10,000 | €10.00 | 0.1% | Safe ✅ |
| 100.0 | €20,000 | €20.00 | 0.2% | Safe ✅ |
| 500.0 | €100,000 | €100.00 | 1.0% | Safe ✅ |

**CRITICAL:** Margin is LOW, but **UNREALIZED LOSSES** are the real risk!

### Risk Scenario: Strong Trend

**Example: Price rises from $200 → $300 (+50%)**

Assume we accumulated:
- 10 BUY positions (avg $200) = 10.0 lots
- 50 SELL positions (avg $250) = 50.0 lots

```
BUY P&L: ($300 - $200) × 10.0 = +$1,000
SELL P&L: ($250 - $300) × 50.0 = -$2,500
Net P&L: -$1,500 (-15% of €10k account) 🔴
```

**Problem:** More SELL positions than BUY = net SHORT exposure during uptrend

---

## TABLE 6: POSITION IMBALANCE MANAGEMENT

### Natural Grid Imbalance

As price oscillates, one side accumulates faster:

**Uptrend:**
- More SELL positions added (every +5% from BUY)
- Fewer BUY positions added (only when SELLs profit)
- Net exposure: SHORT
- Risk: Continued uptrend causes losses

**Downtrend:**
- More BUY positions added (SELL profits trigger BUYs)
- Fewer SELL positions added (BUY not in profit)
- Net exposure: LONG
- Risk: Continued downtrend causes losses

### Protection Strategy

**Option 1: Position Limit**
```
Max total positions per stock: 100 lots
Max imbalance: |BUY - SELL| ≤ 20 lots
```

**Option 2: Exposure Limit**
```
Max net exposure: ±€5,000 per stock
If exceeded, stop adding to dominant side
```

**Option 3: Emergency Hedging**
```
If net exposure > €5,000:
    └─ Add balancing positions to neutralize
```

---

## TABLE 7: COMPLETE LOGIC FLOWCHART

```
Every TICK for each STOCK:
    │
    ├─── Have ANY positions? ────────────────┐
    │                                         │
    │                                         NO
    │                                         │
    │                                         ▼
    │                         ┌────────────────────────┐
    │                         │ BUY 1.0 lot            │
    │                         │ Record initial_price   │
    │                         └────────────────────────┘
    │
    └─── YES ───────────────────────────────┐
                                            │
                                            ▼
                        ┌────────────────────────────────┐
                        │ Calculate current BUY profit   │
                        │ from initial_buy_price         │
                        └────────────────────────────────┘
                                            │
                                            ▼
                        ┌────────────────────────────────┐
                        │ Check SELL triggers:           │
                        │ +5%, +10%, +15%, +20%...       │
                        │ Add SELL if level not hit yet  │
                        └────────────────────────────────┘
                                            │
                                            ▼
                        ┌────────────────────────────────┐
                        │ Loop through all SELL positions│
                        │ Check if any SELL profit ≥ +5% │
                        │ Add BUY for each profitable SELL│
                        │ Mark SELL as "counted"         │
                        └────────────────────────────────┘
                                            │
                                            ▼
                        ┌────────────────────────────────┐
                        │ Check position limits:         │
                        │ - Max 100 total lots?          │
                        │ - Imbalance > 20 lots?         │
                        │ - Net exposure > €5,000?       │
                        │ If exceeded, SKIP new entries  │
                        └────────────────────────────────┘
```

---

## TABLE 8: 2-YEAR BACKTEST PARAMETERS

### Test Configuration

| Parameter | Value | Reason |
|-----------|-------|--------|
| **Account Size** | €10,000 | User's capital |
| **Test Period** | 2023-01-01 to 2024-12-31 | Past 2 years |
| **Stocks** | ORCL only (initial test) | Simplify first test |
| **Initial Lot** | 1.0 | Standard size |
| **Step Size** | 5% | Add SELL every +5%, BUY when SELL +5% |
| **Max Positions** | 100 total | Risk control |
| **Max Imbalance** | 20 lots | Prevent extreme exposure |
| **Leverage** | 1:5 | Pepperstone condition |

### Expected Outcomes

**Best Case (Range-Bound Market):**
```
Price oscillates $200 ↔ $250
- Accumulates 20 BUY + 20 SELL positions
- Each swing generates unrealized profit
- Final P&L: +€2,000 to +€5,000 (+20-50%) ✅
```

**Worst Case (Strong Trend):**
```
Price trends $200 → $400 (uptrend)
- 10 BUY positions @ avg $200
- 60 SELL positions @ avg $300
- Net SHORT 50 lots
- Final P&L: -€5,000 to -€10,000 (-50% to -100%) 🔴 MARGIN CALL
```

**Realistic Case (Mixed):**
```
Price oscillates with trend $200 → $300 over 2 years
- 30 BUY + 40 SELL positions
- Net SHORT 10 lots
- Final P&L: +€500 to +€1,500 (+5-15%) ⚠️
```

---

## TABLE 9: RISK WARNINGS

| Risk Factor | Severity | Impact | Mitigation |
|-------------|----------|--------|------------|
| **Strong Trend** | 🔴 HIGH | Net exposure builds, -50% loss possible | Position limits, imbalance control |
| **Low Volatility** | 🟡 MEDIUM | Few triggers, low profit | Reduce step size to 3% |
| **High Volatility** | 🟡 MEDIUM | Too many positions fast | Increase step to 7% |
| **Margin Call** | 🔴 HIGH | Account wipeout if trending market | Emergency stop at -20% |
| **Overtrading** | 🟢 LOW | Margin is cheap, fees minimal | Not a concern |
| **Gap Risk** | 🟡 MEDIUM | Overnight gap can trigger multiple levels | Accept risk, part of strategy |

---

## TABLE 10: IMPLEMENTATION CHECKLIST

### Before Coding

- [x] Understand grid logic (accumulate BUY + SELL)
- [x] Know trigger conditions (+5% steps)
- [ ] Confirm position tracking method
- [ ] Set position limits (100 total, 20 imbalance?)
- [ ] Set emergency stop (-20% account loss?)

### EA Features Required

```cpp
class GridManager
{
    // Track all positions per symbol
    GridPosition positions[];

    // Track levels
    double initial_buy_price;
    int last_sell_level;

    // Check triggers
    void CheckSellTriggers();
    void CheckBuyTriggers();

    // Position management
    void OpenBuy(double lots);
    void OpenSell(double lots);
    void CountPositions(int &buy_count, int &sell_count);

    // Risk management
    bool ExceedsPositionLimit();
    bool ExceedsImbalanceLimit();
    double CalculateNetExposure();
};
```

### Backtest Steps

1. Code EA with grid logic
2. Test on ORCL 2023-2024 (2 years)
3. Analyze equity curve for:
   - Max positions reached
   - Max drawdown
   - Position imbalance patterns
   - Final P&L
4. Optimize step size (3%, 5%, 7%)
5. Optimize position limits

---

## SUMMARY: GRID MARTINGALE RULES

```
1. START: BUY 1.0 lot (initial entry)

2. PRICE RISES:
   ├─ +5%  → ADD SELL 1.0 lot (keep BUY)
   ├─ +10% → ADD SELL 1.0 lot (keep all)
   ├─ +15% → ADD SELL 1.0 lot (keep all)
   └─ Continue every +5%

3. PRICE FALLS:
   ├─ Each SELL reaches +5% profit → ADD BUY 1.0 lot (keep SELL)
   └─ Continue for each profitable SELL

4. NEVER CLOSE:
   ├─ BUY positions stay open forever
   ├─ SELL positions stay open forever
   └─ Profit from unrealized oscillations

5. RISK CONTROL:
   ├─ Max 100 total positions per stock
   ├─ Max 20 lot imbalance (|BUY - SELL|)
   └─ Emergency stop at -20% account loss
```

**Ready to implement this grid strategy?**
