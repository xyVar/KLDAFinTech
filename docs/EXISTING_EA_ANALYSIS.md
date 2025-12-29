# Existing EA Analysis - Kosta EA Folder

**Location:** `C:\Users\PC\AppData\Roaming\MetaQuotes\Terminal\73B7A2420D6397DFF9014A20F1201F97\MQL5\Experts\Kosta EA\`

**Date Analyzed:** 2025-12-23

---

## EA #1: MartinG..mq5

### Basic Information
```
Version: 2.8
Copyright: 2025
Strategy Type: Martingale / Dollar Cost Averaging
Direction: LONG only (BUY)
Language: Italian comments
```

### Traded Instruments (9 symbols)
```
1. NVDA.US-24   (Nvidia)
2. META.US-24   (Meta/Facebook)
3. TSLA.US-24   (Tesla)
4. AVGO.US-24   (Broadcom)
5. MSFT.US-24   (Microsoft)
6. BA.US-24     (Boeing)
7. PLTR.US-24   (Palantir)
8. ORCL.US-24   (Oracle)
9. AAPL.US-24   (Apple)
```

### Input Parameters
```
StepPercent = 4.0%
  - Every time price drops 4% from initial entry, add another position
```

### Strategy Logic

**Entry Rules:**
```
1. If NO position exists on symbol:
   → BUY 1.0 lot at current ASK price
   → Record initial price

2. If position EXISTS:
   → Calculate: (Initial Price - Current ASK) / Initial Price * 100
   → If drop >= 4%, BUY 1.0 lot
   → If drop >= 8%, BUY 1.0 lot
   → If drop >= 12%, BUY 1.0 lot
   → ... up to 9 additional positions (10 total)

Maximum positions per symbol: 10 (initial + 9 additional)
```

**Exit Rules:**
```
❌ NONE
- No take profit
- No stop loss
- No time-based exit
- Positions accumulate indefinitely
```

### Code Breakdown

**Variables:**
```mql5
double initial_price[9];   // Stores first entry price for each symbol
int step[9];               // Counts how many additional positions added
```

**On Every Tick:**
```mql5
For each of 9 symbols:
  Get current ASK price

  If position exists:
    Calculate % drop from initial price
    If drop >= StepPercent * (step + 1) AND step < 9:
      BUY 1.0 lot
      Increment step counter

  Else (no position):
    BUY 1.0 lot
    Record initial price
    Reset step to 0
```

### Risk Analysis

**Strengths:**
- ✅ Simple, clear logic
- ✅ Trades multiple instruments simultaneously
- ✅ Dollar cost averaging approach

**Weaknesses:**
- ❌ NO EXIT STRATEGY - positions never close automatically
- ❌ Can accumulate 90 positions total (10 per symbol × 9 symbols)
- ❌ No stop loss - unlimited downside risk
- ❌ No profit target - requires manual closing
- ❌ No capital management - fixed 1.0 lots regardless of account size
- ❌ Requires significant margin (up to 90 lots open)
- ❌ Will average down forever if price keeps dropping

**Capital Requirements:**
```
Worst case scenario (all 9 symbols hit max positions):
- 90 total lots open
- Example: If each lot requires €500 margin
- Total margin: €45,000
- Plus buffer for drawdown
- Recommended account: €100,000+
```

**Message on Start:**
```
"Strategia BUY incrementale +1 lotto ogni -4% fino a 9 volte avviata."
Translation: "BUY incremental strategy +1 lot every -4% up to 9 times started."
```

---

## EA #2: MartinG+ifs.mq5

### Basic Information
```
Version: 1.0
Copyright: 2025
Strategy Type: Martingale with Profit/Loss Exits
Direction: LONG only (BUY)
Language: Italian comments
```

### Traded Instruments (Same 9 symbols)
```
1. NVDA.US-24
2. META.US-24
3. TSLA.US-24
4. AVGO.US-24
5. MSFT.US-24
6. BA.US-24
7. PLTR.US-24
8. ORCL.US-24
9. AAPL.US-24
```

### Input Parameters
```
StepDropPercent = 2.0%     // Add position every -2% drop
ProfitClose = 3.0%         // Close position at +3% profit
LossClose = 1.0%           // Close position at -1% loss
MaxPositions = 6           // Maximum 6 positions per symbol
```

### Strategy Logic

**Entry Rules:**
```
1. If NO BUY positions exist on symbol:
   → BUY 2.0 lots at current price

2. If 1-5 positions exist:
   → Find last (most recent) position entry price
   → Calculate: (Last Entry Price - Current BID) / Last Entry Price * 100
   → If drop >= 2.0%, BUY 2.0 lots

Maximum positions per symbol: 6
```

**Exit Rules:**
```
✅ HAS EXIT STRATEGY

For EACH open position:
  Calculate profit %: (Current BID - Entry Price) / Entry Price * 100
  Calculate loss %: (Entry Price - Current BID) / Entry Price * 100

  If profit >= +3.0%:
    → CLOSE position

  If loss >= -1.0%:
    → CLOSE position (stop loss)
```

### Code Breakdown

**Key Function:**
```mql5
GetLastOpenPrice(symbol):
  - Loops through all open positions
  - Finds most recent BUY position for symbol
  - Returns its entry price
  - Used to calculate drop % from last entry (not first)
```

**On Every Tick:**
```mql5
For each of 9 symbols:
  Count BUY positions for this symbol

  If 0 positions:
    BUY 2.0 lots

  If 1-5 positions:
    Get last entry price
    If price dropped 2% from last entry:
      BUY 2.0 lots

  For EACH open position:
    If profit >= +3% OR loss >= -1%:
      CLOSE position
```

### Risk Analysis

**Strengths:**
- ✅ Has profit target (+3%)
- ✅ Has stop loss (-1%)
- ✅ More aggressive lot size (2.0 vs 1.0)
- ✅ Lower drop threshold (2% vs 4%) = more responsive
- ✅ Limited max positions (6 vs 10)
- ✅ Exits positions automatically

**Weaknesses:**
- ⚠️ Stop loss (-1%) tighter than profit target (+3%) - needs high win rate
- ❌ Averages down from LAST entry, not first - can pyramid into losses
- ❌ No capital management - fixed 2.0 lots
- ❌ Can still accumulate 54 positions (6 × 9 symbols)
- ❌ Multiple positions may all hit -1% stop simultaneously

**Capital Requirements:**
```
Worst case scenario:
- 54 total lots open (6 per symbol × 9 symbols)
- Each position 2.0 lots
- Total exposure: 54 × 2.0 = 108 lots equivalent
- Example: If €500 margin per lot
- Total margin: €54,000
- Recommended account: €75,000+
```

**Message on Start:**
```
"=== EA PARTITO: MartinG_2lots ==="
Translation: "=== EA STARTED: MartinG_2lots ==="
```

---

## Comparison Table

| Feature | MartinG | MartinG+ifs |
|---------|---------|-------------|
| **Lot Size** | 1.0 | 2.0 |
| **Drop Threshold** | 4% | 2% |
| **Max Positions/Symbol** | 10 | 6 |
| **Total Max Positions** | 90 | 54 |
| **Profit Target** | ❌ None | ✅ +3% |
| **Stop Loss** | ❌ None | ✅ -1% |
| **Drop Reference** | Initial price | Last entry price |
| **Auto Exit** | ❌ No | ✅ Yes |
| **Risk Level** | VERY HIGH | HIGH |
| **Capital Needed** | €100k+ | €75k+ |
| **Version** | 2.8 | 1.0 |

---

## Trading Style

Both EAs use **Martingale / Averaging Down** strategy:

**Concept:**
- Buy long positions on tech stocks
- If price drops, buy MORE (dollar cost averaging)
- Hope price eventually recovers for profit

**When This Works:**
- Trending up markets
- Temporary dips that recover
- High-quality stocks (mega-cap tech)

**When This FAILS:**
- Bear markets / prolonged downtrends
- Stock-specific crashes (e.g., accounting scandal)
- Margin calls from accumulated positions
- 2022-style tech selloff (-50% on some stocks)

---

## Common Risks (Both EAs)

### 1. **Unlimited Downside**
```
Example:
- NVDA at $200, buy 2.0 lots
- Drops to $196 (-2%), buy 2.0 lots
- Drops to $192 (-4%), buy 2.0 lots
- Drops to $188 (-6%), buy 2.0 lots
- ... continues to $150 (-25%)
- Now holding 12 lots with massive unrealized loss
```

### 2. **Correlation Risk**
```
All 9 stocks are tech/growth:
- When tech sells off, ALL 9 positions drop together
- Instead of diversification, you have 9× the same risk
- March 2020, COVID crash: All tech dropped 30-40% simultaneously
- Would have triggered maximum positions on ALL symbols
```

### 3. **No Market Regime Filter**
```
Both EAs:
- Trade 24/7 regardless of market conditions
- No VIX check
- No trend filter
- Buy in bull AND bear markets
```

### 4. **Fixed Position Sizing**
```
- MartinG: Always 1.0 lot
- MartinG+ifs: Always 2.0 lots
- No adjustment for:
  - Account size
  - Current risk
  - Volatility
  - Margin usage
```

---

## Files Present

```
Kosta EA/
├── MartinG..mq5           (source code - EA #1)
├── MartinG..ex5           (compiled - EA #1)
├── MartinG+ifs.mq5        (source code - EA #2)
└── MartinG+ifs.ex5        (compiled - EA #2)
```

**Source files (.mq5):**
- Human-readable code
- Can be edited in MetaEditor
- Must be recompiled after changes

**Compiled files (.ex5):**
- Machine executable
- Attached to charts to run EA
- Generated from .mq5 files

---

## Recommendation

**For MartinG (v2.8):**
- ⚠️ DO NOT USE without adding exit logic
- Missing stop loss = account can blow up
- Need to add profit targets manually

**For MartinG+ifs (v1.0):**
- ⚠️ USE WITH CAUTION
- Test on DEMO first for at least 2 weeks
- Reduce lot sizes (0.5 instead of 2.0)
- Consider adding:
  - Maximum daily loss limit
  - VIX filter (don't trade when VIX > 25)
  - Account equity stop (close all if -10% drawdown)

**Both EAs:**
- Are AGGRESSIVE strategies
- Require LARGE capital
- Work best in BULL MARKETS
- Can DESTROY account in bear markets

---

## Next Steps

**If you want to use these:**
1. Backtest on historical data (2022 bear market period)
2. Run on demo account minimum 1 month
3. Start with 25% position sizes
4. Monitor DAILY
5. Set broker-side emergency stops

**If you want to build new strategy:**
- Learn from these (what works, what doesn't)
- Add proper risk management
- Add market regime filters
- Use dynamic position sizing
- Test extensively before live

---

**Analysis Complete:** These are high-risk martingale strategies that average down on losing positions. MartinG+ifs is safer (has exits) but both require significant capital and active monitoring.
