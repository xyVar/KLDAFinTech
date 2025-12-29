# Real Symbol Specifications - From MT5 Screenshots

**Account:** 62101051 (PepperstoneUK-Demo)
**Last Updated:** 2025-12-23
**Data Source:** MT5 Specification Screenshots

---

## IMPORTANT CLARIFICATION: "24-Hour" Trading

**The "-24" suffix does NOT mean true 24/7 trading.**

**Actual Trading Hours:**
```
Monday:    03:00 - 23:59  (20h 59m)
Tuesday:   00:01 - 23:59  (23h 58m)
Wednesday: 00:01 - 23:59  (23h 58m)
Thursday:  00:01 - 23:59  (23h 58m)
Friday:    00:01 - 23:55  (23h 54m)
Saturday:  CLOSED
Sunday:    CLOSED
```

**Trading Gaps:**
- Monday 23:59 → Tuesday 00:01 (2 minutes)
- Tuesday 23:59 → Wednesday 00:01 (2 minutes)
- Wednesday 23:59 → Thursday 00:01 (2 minutes)
- Thursday 23:59 → Friday 00:01 (2 minutes)
- **Friday 23:55 → Monday 03:00 (~51 hours WEEKEND GAP)**

**This means:**
- ✅ Almost 24-hour trading on weekdays
- ❌ NOT continuous - small gaps between days
- ❌ Weekend completely closed (51+ hour gap)
- ⚠️ Risk of weekend gap moves

---

## Standard US Stock CFD Specifications

**Based on screenshot analysis, all US stocks with "-24" suffix share these specs:**

### Contract Details
```
ISIN: Varies by stock
Sector: Technology (for most AI/chip stocks)
Industry: Software/Infrastructure/Semiconductors
Country: United States
Digits: 2
Contract Size: 1
Spread: Floating
Stops Level: 0
```

### Currencies
```
Margin Currency: USD
Profit Currency: USD
Calculation: CFD
```

### Position Sizing
```
Minimal Volume: 0.1 lots
Maximal Volume: 1848 lots (varies by symbol)
Volume Step: 0.1 lots
Volume Limit: 21839 (total exposure limit)
```

### Execution
```
Trade Mode: Full access
Execution: Market
GTC Mode: Good till cancelled
Filling: Fill or Kill / All
Expiration: All
Orders: All
```

### Margin Requirements
```
Initial Margin: 0.2000000 EUR per lot
Maintenance Margin: 0.2000000 EUR per lot
Hedged Margin: 0 (no margin for hedged positions!)

Chart Mode: By bid price
Hedged Margin: 0
```

**This is HUGE:** Hedged margin = 0 means if you open both LONG and SHORT on same symbol, the hedged portion requires ZERO additional margin!

### Swap (Overnight Fees)
```
Swap Type: In percentage terms, using current price
Swap Long: -6.23% annually
Swap Short: +1.03% annually

Daily Calculation:
  Long position: Pay ~0.017% per day
  Short position: Earn ~0.003% per day

Swap Schedule:
  Monday: 1x swap
  Tuesday: 1x swap
  Wednesday: 1x swap
  Thursday: 1x swap
  Friday: 3x swap (charges for Sat-Sun-Mon)
```

### Commission
```
Commission: 0.02 USD per lot (minimum 0.02 USD)
Round-trip: 0.04 USD per lot
```

### Trading Sessions

**Quotes (Price Feed):**
```
Monday:    03:00 - 23:59
Tuesday:   00:01 - 23:59
Wednesday: 00:01 - 23:59
Thursday:  00:01 - 23:59
Friday:    00:01 - 23:55
```

**Trade (Order Execution):**
```
Monday:    03:00 - 23:59
Tuesday:   00:01 - 23:59
Wednesday: 00:01 - 23:59
Thursday:  00:01 - 23:59
Friday:    00:01 - 23:55
```

---

## All Available Symbols (Confirmed with -24 Suffix)

Based on file system + screenshots, these symbols share the same specifications:

### Confirmed Available:
```
1. NVDA.US-24   (Nvidia)
2. PLTR.US-24   (Palantir)
3. TSLA.US-24   (Tesla)
4. AMD.US-24    (Advanced Micro Devices)
5. AVGO.US-24   (Broadcom)
6. META.US-24   (Meta/Facebook)
7. AAPL.US-24   (Apple)
8. MSFT.US-24   (Microsoft)
9. ORCL.US-24   (Oracle)
10. BA.US-24    (Boeing)
11. AMZN.US-24  (Amazon)
```

### Without -24 Suffix (May have different hours):
```
TSM.US  (Taiwan Semiconductor)
```

### NOT FOUND (Need to verify if available):
```
SMCI (Super Micro Computer)
MU (Micron)
GOOGL/GOOG (Google/Alphabet)
ADBE (Adobe)
```

---

## Margin Calculation Example

**Example: Trade 1.0 lot of NVDA.US-24**

```
NVDA price: $187.00

Position Value: 1.0 lot × $187.00 = $187.00
Margin Required: 0.2 EUR per lot = 0.20 EUR

If EUR/USD = 1.05:
  Margin in USD: 0.20 EUR × 1.05 = ~$0.21

This is TINY margin requirement!
```

**Example: Trade 10 lots across 10 stocks**

```
10 stocks × 1.0 lot each = 10 lots total
Margin: 10 lots × 0.20 EUR = 2.00 EUR (~$2.10 USD)

If account has €10,000:
  Margin usage: 2 EUR / 10,000 EUR = 0.02% (!)
```

**This means you can open MASSIVE positions with little margin.**

⚠️ **WARNING:** Low margin = easy to over-leverage!

---

## Swap Cost Example

**Example: Hold 1.0 lot NVDA.US-24 LONG overnight**

```
NVDA price: $187.00
Position value: $187.00
Swap long: -6.23% annually

Daily swap: -6.23% / 365 = -0.0171% per day
Daily cost: $187.00 × -0.0171% = -$0.032 per day

Hold 30 days: -$0.032 × 30 = -$0.96
Hold 1 year: $187.00 × -6.23% = -$11.65
```

**Example: Hold 1.0 lot NVDA.US-24 SHORT overnight**

```
NVDA price: $187.00
Swap short: +1.03% annually

Daily swap: +1.03% / 365 = +0.0028% per day
Daily earn: $187.00 × +0.0028% = +$0.005 per day

Hold 30 days: +$0.005 × 30 = +$0.15
Hold 1 year: $187.00 × +1.03% = +$1.93
```

**Conclusion:** Short positions earn small swap, long positions pay larger swap. Strategy should be intraday or short-biased if holding overnight.

---

## Commission Cost Example

**Example: Open and close 1.0 lot trade**

```
Open: 0.02 USD
Close: 0.02 USD
Total: 0.04 USD per round-trip

10 trades: 0.04 × 10 = 0.40 USD
100 trades: 0.04 × 100 = 4.00 USD
```

**Negligible commission costs.**

---

## Weekend Gap Risk

**Friday 23:55 closes → Monday 03:00 opens = 51+ hours**

**What can happen:**
- Major news over weekend
- Earnings announcements
- Geopolitical events
- Market crashes/rallies

**Example:**
```
Friday close: NVDA @ $187.00
Weekend news: Major AI breakthrough announced
Monday open: NVDA gaps to $195.00 (+4.3%)

If you were SHORT 10 lots:
  Loss: 10 lots × ($195 - $187) = -$80 instant loss on gap
```

**Protection:**
- Close all positions before Friday 23:55
- Or use wide stops if holding over weekend
- Or accept gap risk as part of strategy

---

## Strategy Implications

### For Intraday Trading:
```
✅ Low margin allows large positions
✅ Almost 24h = can trade any time during week
✅ Low commission = can trade frequently
✅ No swap if closed same day
⚠️ Must close before Friday 23:55 to avoid weekend gap
⚠️ Small gaps between days can cause slippage
```

### For Swing Trading (Multi-day):
```
✅ Can hold positions overnight
✅ Short positions earn small swap
❌ Long positions pay significant swap
❌ Weekend gaps = big risk
❌ Must plan around Friday close
```

### For High-Frequency:
```
✅ Minimal commission (0.02 USD)
✅ Market execution
✅ Good till cancelled orders
✅ Can trade almost 24 hours
⚠️ Spread costs matter more than commission
```

---

## Risk Management Considerations

### 1. Over-Leverage Risk
```
Margin so low (0.20 EUR/lot) that it's EASY to open too many positions.

Safe approach:
  - Use no more than 2-5% margin
  - Calculate position size based on STOP LOSS, not margin
  - Don't rely on low margin to justify large positions
```

### 2. Gap Risk
```
2-minute gaps between days = minor
51-hour weekend gap = MAJOR

Strategy:
  - Close all Friday before 23:55
  - OR accept weekend gap as calculated risk
  - OR use guaranteed stops (if broker offers)
```

### 3. Correlation Risk
```
All these stocks are tech/AI:
  - When tech sells off, ALL drop together
  - Diversification illusion
  - 10 stocks × 10 lots = 100x same risk, not diversification

Solution:
  - Reduce position sizes
  - Add stops
  - Don't max out margin even though you can
```

---

## Summary Table

| Feature | Value | Notes |
|---------|-------|-------|
| **Trading Hours** | ~23h/day weekdays | NOT true 24/7 |
| **Weekend** | CLOSED | 51+ hour gap |
| **Min Lot** | 0.1 | Can trade small |
| **Max Lot** | 1848 | Per symbol |
| **Margin** | 0.20 EUR/lot | VERY LOW |
| **Hedged Margin** | 0 EUR | Free hedging! |
| **Commission** | 0.02 USD/lot | Minimal |
| **Swap Long** | -6.23%/year | Pay to hold |
| **Swap Short** | +1.03%/year | Earn to hold |
| **Execution** | Market | Immediate |
| **Spread** | Floating | Varies by time |

---

**This is the REAL specification data - not assumptions.**

**Key Takeaway:** The "-24" means "weekday extended hours" not "24/7 continuous trading". There ARE gaps, especially on weekends.
