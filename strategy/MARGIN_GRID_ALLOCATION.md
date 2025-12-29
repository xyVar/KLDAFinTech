# MARGIN-BASED GRID ALLOCATION STRATEGY

## CORE PRINCIPLE: EQUAL DISTRIBUTION WITH MARGIN SAFETY

```
Account: €10,000
Leverage: 5:1 (€50,000 buying power)
Safety Rule: Equity ≥ 50% of Margin Invested
Grid Step: 5% per level
Max Grid Levels: 6 per direction (30% range coverage)
```

---

## TABLE 1: CAPITAL ALLOCATION PER STOCK

### Equal Distribution Across 8 Stocks

| Stock | Allocated Capital | % of Account | Max Unbalanced Exposure | Max Balanced Exposure |
|-------|------------------|--------------|------------------------|----------------------|
| NVDA | €1,250 | 12.5% | €1,250 | €2,500 (with hedging) |
| META | €1,250 | 12.5% | €1,250 | €2,500 |
| TSLA | €1,250 | 12.5% | €1,250 | €2,500 |
| AVGO | €1,250 | 12.5% | €1,250 | €2,500 |
| MSFT | €1,250 | 12.5% | €1,250 | €2,500 |
| BA | €1,250 | 12.5% | €1,250 | €2,500 |
| PLTR | €1,250 | 12.5% | €1,250 | €2,500 |
| ORCL | €1,250 | 12.5% | €1,250 | €2,500 |
| **TOTAL** | **€10,000** | **100%** | **€10,000** | **€20,000** |

**Key:**
- **Unbalanced exposure:** All BUYs OR all SELLs (full margin requirement)
- **Balanced exposure:** Equal BUYs + SELLs (reduced margin, can double position size)

---

## TABLE 2: MARGIN CALCULATION PER STOCK

### From Pepperstone Specifications

| Stock | Current Price | Margin per 1.0 Lot | Lots per €200 | Max Lots (€1,250) |
|-------|--------------|-------------------|---------------|-------------------|
| NVDA | $500 | €100.00 | 2.0 | 12.5 |
| META | $600 | €120.00 | 1.67 | 10.4 |
| TSLA | $400 | €80.00 | 2.5 | 15.6 |
| AVGO | $180 | €36.00 | 5.56 | 34.7 |
| MSFT | $410 | €82.69 | 2.42 | 15.1 |
| BA | $180 | €36.00 | 5.56 | 34.7 |
| PLTR | $80 | €16.00 | 12.5 | 78.1 |
| ORCL | $200 | €40.00 | 5.0 | 31.25 |

**Note:** These are UNBALANCED margin requirements (5:1 leverage)

---

## TABLE 3: GRID POSITION SIZING - ORCL EXAMPLE

### Given Parameters

```
Stock: ORCL
Price Range: $150 - $350 (range = $200)
Current Price: $200
Allocated Capital: €1,250
Margin per 1.0 lot: €40
Grid Step: 5%
Max Grid Levels: 6
```

### Calculation

**Option A: Fixed €200 per Grid Level (User's Example)**

| Grid Level | Trigger Price | Direction | Lots per Level | Margin per Level | Cumulative Margin |
|------------|--------------|-----------|----------------|------------------|-------------------|
| 0 (Initial) | $200 | BUY | 5.0 | €200 | €200 |
| 1 | $210 (+5%) | SELL | 5.0 | €200 | €400 (balanced) |
| 2 | $220 (+10%) | SELL | 5.0 | €200 | €600 |
| 3 | $230 (+15%) | SELL | 5.0 | €200 | €800 |
| 4 | $240 (+20%) | SELL | 5.0 | €200 | €1,000 |
| 5 | $250 (+25%) | SELL | 5.0 | €200 | €1,200 |
| 6 | $260 (+30%) | SELL | 5.0 | €200 | €1,400 ⚠️ |

**Problem:** Exceeds allocated €1,250 at level 6

**Solution:** Reduce to 5 grid levels OR reduce lot size to 4.2 lots per level

---

**Option B: Dynamic Lot Sizing (Optimized)**

| Grid Level | Trigger Price | Direction | Lots per Level | Margin per Level | Cumulative Margin |
|------------|--------------|-----------|----------------|------------------|-------------------|
| 0 | $200 | BUY | 5.0 | €200 | €200 |
| 1 | $210 (+5%) | SELL | 5.0 | €200 | €200 (balanced!) |
| 2 | $220 (+10%) | SELL | 5.0 | €200 | €400 (net -5.0) |
| 3 | $230 (+15%) | SELL | 5.0 | €200 | €600 (net -10.0) |
| 4 | $240 (+20%) | SELL | 5.0 | €200 | €800 (net -15.0) |
| 5 | $250 (+25%) | SELL | 5.0 | €200 | €1,000 (net -20.0) |
| 6 | $260 (+30%) | SELL | 5.0 | €200 | €1,200 (net -25.0) ✅ |

**Margin Calculation:**
```
Level 0-1: 5.0 BUY + 5.0 SELL = Balanced, margin = €200
Level 2: Net -5.0 SELL (more sells), margin = €200 + €200 = €400
Level 3: Net -10.0 SELL, margin = €600
...
Level 6: Net -25.0 SELL (25 lots short), margin = 25 × €40 = €1,000 + €200 base = €1,200 ✅
```

**Key Insight:** When BALANCED (equal BUYs + SELLs), margin requirement drops significantly!

---

## TABLE 4: MARGIN REDUCTION THROUGH HEDGING

### Example: ORCL Grid Progression

| Positions | BUY Lots | SELL Lots | Net Exposure | Margin Required | Effective Leverage |
|-----------|----------|-----------|--------------|-----------------|-------------------|
| 1 BUY | 5.0 | 0 | +5.0 | €200 | 5:1 |
| 1 BUY + 1 SELL | 5.0 | 5.0 | 0 (balanced) | €200 | 10:1 effective! |
| 1 BUY + 2 SELL | 5.0 | 10.0 | -5.0 | €400 | 6.25:1 |
| 1 BUY + 3 SELL | 5.0 | 15.0 | -10.0 | €600 | 5.83:1 |
| 1 BUY + 6 SELL | 5.0 | 30.0 | -25.0 | €1,200 | 5.21:1 |

**Calculation:**
```
Net exposure = |BUY lots - SELL lots| × price
If BUY = SELL: Net = 0, margin minimal (only base margin)
If unbalanced: Margin = net lots × (price / leverage)
```

---

## TABLE 5: SAFETY RULE - 50% EQUITY PROTECTION

### Rule: Equity Must Stay Above 50% of Margin Invested

**Example Scenario:**

```
Margin Invested: €1,200 (ORCL grid at 6 levels)
Minimum Equity: €600 (50% of €1,200)
Maximum Allowed Loss: €9,400 (from €10k account)
Stop-Out Level: €600 below starting equity
```

**Calculation:**

| Scenario | Positions | Margin Used | Unrealized P&L | Equity | Safe? |
|----------|-----------|-------------|----------------|--------|-------|
| Start | 0 | €0 | €0 | €10,000 | ✅ |
| Level 1 | 5.0 BUY | €200 | €0 | €10,000 | ✅ Min: €100 |
| Level 3 | 5 BUY + 10 SELL | €600 | -€300 | €9,700 | ✅ Min: €300 |
| Level 6 | 5 BUY + 30 SELL | €1,200 | -€600 | €9,400 | ✅ Min: €600 |
| Crisis | 5 BUY + 30 SELL | €1,200 | -€1,000 | €9,000 | ❌ Below €600! |

**When Unrealized Loss = -€1,000:**
```
Equity = €10,000 - €1,000 = €9,000
Margin Invested = €1,200
50% of Margin = €600
Current Equity €9,000 > €600 ✅ SAFE (still far from stop-out)
```

**Actually, the rule means:**
```
Equity ≥ 50% of Margin Invested
€9,000 ≥ 50% × €1,200
€9,000 ≥ €600 ✅
```

**Actual Risk:**
```
If loss reaches -€9,400, equity drops to €600
This is the absolute minimum (50% of €1,200)
At this point, STOP adding positions
```

---

## TABLE 6: POSITION SIZING FORMULA

### Dynamic Lot Calculation

```cpp
// Per stock calculation
double allocated_capital = 10000.0 / 8;  // €1,250 per stock
double margin_per_lot = GetMarginPerLot(symbol);  // From broker specs
int max_grid_levels = 6;
double grid_step_percent = 5.0;

// Calculate lot size per grid level
double margin_per_level = allocated_capital / max_grid_levels;  // €208.33
double lots_per_level = margin_per_level / margin_per_lot;

// For ORCL: margin_per_lot = €40
// lots_per_level = €208.33 / €40 = 5.2 lots

// Round down for safety
lots_per_level = MathFloor(lots_per_level * 10) / 10;  // 5.2 lots
```

### Safety Check Before Opening Position

```cpp
bool CanOpenPosition(string symbol, double lots, ENUM_ORDER_TYPE type)
{
    double account_equity = AccountInfoDouble(ACCOUNT_EQUITY);
    double margin_invested = CalculateTotalMarginUsed();
    double new_margin = CalculatePositionMargin(symbol, lots, type);

    double future_margin = margin_invested + new_margin;
    double min_equity_required = future_margin * 0.5;  // 50% rule

    if(account_equity >= min_equity_required)
        return true;
    else
        return false;  // Too risky, skip this position
}
```

---

## TABLE 7: COMPLETE EXAMPLE - ORCL 2-YEAR SIMULATION

### Initial Setup

```
Starting Capital: €10,000
ORCL Allocation: €1,250 (12.5%)
ORCL Price: $200
ORCL Range: $150 - $350
Margin per lot: €40
Grid Levels: 6
Lot per level: 5.0
```

### Scenario: Price Rises to $260 (+30%)

| Step | Event | Price | Action | BUY | SELL | Margin | Equity | Safe? |
|------|-------|-------|--------|-----|------|--------|--------|-------|
| 1 | Initial | $200 | BUY 5.0 | 5.0 | 0 | €200 | €10,000 | ✅ Min: €100 |
| 2 | +5% rise | $210 | SELL 5.0 | 5.0 | 5.0 | €200 | €10,050 | ✅ Min: €100 |
| 3 | +10% rise | $220 | SELL 5.0 | 5.0 | 10.0 | €400 | €10,050 | ✅ Min: €200 |
| 4 | +15% rise | $230 | SELL 5.0 | 5.0 | 15.0 | €600 | €10,000 | ✅ Min: €300 |
| 5 | +20% rise | $240 | SELL 5.0 | 5.0 | 20.0 | €800 | €9,950 | ✅ Min: €400 |
| 6 | +25% rise | $250 | SELL 5.0 | 5.0 | 25.0 | €1,000 | €9,850 | ✅ Min: €500 |
| 7 | +30% rise | $260 | SELL 5.0 | 5.0 | 30.0 | €1,200 | €9,700 | ✅ Min: €600 |

**P&L Calculation at $260:**
```
BUY P&L: ($260 - $200) × 5.0 = +$300 = +€300
SELL P&L: (avg $230 - $260) × 30.0 = -$900 = -€900
Net P&L: +€300 - €900 = -€600
Equity: €10,000 - €600 = €9,400
Margin: €1,200
Safe: €9,400 > €600 (50% of €1,200) ✅
```

### Scenario: Price Drops Back to $200 (Full Cycle)

| Step | Event | Price | Action | BUY | SELL | P&L | Equity |
|------|-------|-------|--------|-----|------|-----|--------|
| 8 | Drop to $250 | $250 | - | 5.0 | 30.0 | -€350 | €9,650 |
| 9 | Drop to $240 | $240 | - | 5.0 | 30.0 | -€100 | €9,900 |
| 10 | Drop to $230 | $230 | - | 5.0 | 30.0 | +€150 | €10,150 |
| 11 | Drop to $220 | $220 | - | 5.0 | 30.0 | +€400 | €10,400 |
| 12 | Drop to $210 | $210 | - | 5.0 | 30.0 | +€650 | €10,650 |
| 13 | Drop to $200 | $200 | - | 5.0 | 30.0 | +€900 | €10,900 |

**P&L at $200 (Back to Start):**
```
BUY P&L: ($200 - $200) × 5.0 = $0
SELL P&L: (avg $230 - $200) × 30.0 = +$900 = +€900
Net Profit: +€900 (+9% on account) ✅
```

**Key Insight:** Full cycle (up 30%, back down 30%) = +9% profit with NO positions closed!

---

## TABLE 8: MULTI-STOCK COORDINATION

### All 8 Stocks Active Simultaneously

| Stock | Allocated | Current Positions | Margin Used | Unrealized P&L | Status |
|-------|-----------|------------------|-------------|----------------|--------|
| NVDA | €1,250 | 3 BUY + 5 SELL | €400 | +€150 | Active |
| META | €1,250 | 2 BUY + 8 SELL | €600 | -€200 | Active |
| TSLA | €1,250 | 6 BUY + 2 SELL | €500 | +€300 | Active |
| AVGO | €1,250 | 1 BUY | €200 | -€50 | Waiting |
| MSFT | €1,250 | 4 BUY + 4 SELL | €350 | +€100 | Balanced |
| BA | €1,250 | 5 BUY + 10 SELL | €700 | -€400 | Active |
| PLTR | €1,250 | 8 BUY + 3 SELL | €550 | +€200 | Active |
| ORCL | €1,250 | 5 BUY + 30 SELL | €1,200 | +€900 | MAX GRID |
| **TOTAL** | **€10,000** | **203 positions** | **€4,500** | **+€1,000** | **✅** |

**Safety Check:**
```
Total Margin Used: €4,500
50% Rule: Equity ≥ €2,250
Current Equity: €11,000
Safe: €11,000 > €2,250 ✅
```

---

## TABLE 9: DOUBLING DOWN EFFECT

### When Price Crosses Range Multiple Times

**Example: ORCL oscillates $200 ↔ $250 twice**

#### First Cycle ($200 → $250)

| Level | Price | Action | BUY | SELL |
|-------|-------|--------|-----|------|
| 1 | $200 | BUY 5.0 | 5.0 | 0 |
| 2 | $210 | SELL 5.0 | 5.0 | 5.0 |
| 3 | $220 | SELL 5.0 | 5.0 | 10.0 |
| 4 | $230 | SELL 5.0 | 5.0 | 15.0 |
| 5 | $240 | SELL 5.0 | 5.0 | 20.0 |
| 6 | $250 | SELL 5.0 | 5.0 | 25.0 |

#### Price Drops Back ($250 → $200)

| Event | Price | SELL Profit? | Action | BUY | SELL |
|-------|-------|-------------|--------|-----|------|
| Drop to $240 | $240 | SELL @$250 +4% | BUY 5.0 | 10.0 | 25.0 |
| Drop to $230 | $230 | SELL @$240 +4.2% | BUY 5.0 | 15.0 | 25.0 |
| Drop to $220 | $220 | SELL @$230 +4.3% | BUY 5.0 | 20.0 | 25.0 |
| Drop to $210 | $210 | SELL @$220 +4.5% | BUY 5.0 | 25.0 | 25.0 |
| Drop to $200 | $200 | SELL @$210 +4.8% | BUY 5.0 | 30.0 | 25.0 |

**Now positions are:** 30 BUY + 25 SELL (net +5 BUY)

#### Second Cycle ($200 → $250 again)

| Level | Price | BUY Profit? | Action | BUY | SELL |
|-------|-------|------------|--------|-----|------|
| Rise to $210 | $210 | BUY @$200 +5% | SELL 5.0 | 30.0 | 30.0 |
| Rise to $220 | $220 | BUY @$210 +4.8% | SELL 5.0 | 30.0 | 35.0 |
| Rise to $230 | $230 | BUY @$220 +4.5% | SELL 5.0 | 30.0 | 40.0 |
| Rise to $240 | $240 | BUY @$230 +4.3% | SELL 5.0 | 30.0 | 45.0 |
| Rise to $250 | $250 | BUY @$240 +4.2% | SELL 5.0 | 30.0 | 50.0 |

**After 2 full cycles:** 30 BUY + 50 SELL (total 80 positions!)

**This is "doubling down the grid"** - accumulating positions in both directions as price oscillates.

---

## TABLE 10: IMPLEMENTATION REQUIREMENTS

### EA Must Calculate Dynamic

| Component | Calculation | Purpose |
|-----------|-------------|---------|
| **Margin per lot** | From broker specs per symbol | Position sizing |
| **Free margin** | `AccountInfoDouble(ACCOUNT_MARGIN_FREE)` | Can we open? |
| **Allocated capital** | Account balance / 8 stocks | Per stock limit |
| **Lots per level** | Allocated capital / (6 levels × margin) | Fixed lot size |
| **Grid trigger** | Current price vs last level ± 5% | Entry signal |
| **Net exposure** | Sum(BUY lots) - Sum(SELL lots) | Margin calculation |
| **Safety check** | Equity ≥ 50% × Margin Used | Risk control |

### Code Structure

```cpp
struct StockGrid
{
    string symbol;
    double allocated_capital;  // €1,250
    double margin_per_lot;     // From GetMarginRequired()
    double lots_per_level;     // Calculated
    double initial_price;      // First entry price
    int buy_count;             // Total BUY positions
    int sell_count;            // Total SELL positions
    double last_buy_trigger;   // Last BUY level price
    double last_sell_trigger;  // Last SELL level price
};

StockGrid grids[8];  // One per stock

void OnTick()
{
    for(int i = 0; i < 8; i++)
    {
        UpdateGrid(grids[i]);
    }
}

void UpdateGrid(StockGrid &grid)
{
    double current_price = SymbolInfoDouble(grid.symbol, SYMBOL_BID);

    // Check SELL trigger (price up 5% from last level)
    if(current_price >= grid.last_sell_trigger * 1.05)
    {
        if(CanOpenPosition(grid.symbol, grid.lots_per_level, ORDER_TYPE_SELL))
        {
            OpenSell(grid.symbol, grid.lots_per_level);
            grid.sell_count++;
            grid.last_sell_trigger = current_price;
        }
    }

    // Check BUY trigger (any SELL in +5% profit)
    CheckSellProfitsForBuyTrigger(grid);
}
```

---

## SUMMARY

**Strategy:**
1. Split €10k equally across 8 stocks (€1,250 each)
2. Calculate lot size per grid level: allocated capital / (6 levels × margin per lot)
3. Open initial BUY position
4. Every +5% rise: ADD SELL (keep all positions)
5. Every SELL that reaches +5% profit: ADD BUY (keep all positions)
6. Maximum 6 grid levels per direction (30% range)
7. NEVER close positions
8. Safety: Equity must stay above 50% of margin invested

**Risk Control:**
- Position limits: 6 levels × 5% = 30% range coverage per direction
- Margin safety: Equity ≥ 50% × Margin Used
- Hedging reduces margin (balanced positions = lower margin)
- Doubling effect: Multiple cycles accumulate more positions

**Ready to implement this EA?**
