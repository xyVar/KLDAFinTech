# EXIT LOGIC CLARIFICATION - MARTINGALE + SWING STRATEGY

## CRITICAL QUESTION: WHEN DO WE CLOSE POSITIONS?

---

## SECTION 1: SELL HEDGE EXIT CONDITIONS

### Primary Exit Conditions (Check in Order)

| Priority | Condition | Action | Reason | Example |
|----------|-----------|--------|--------|---------|
| **1** | SELL profit ≥ +15% | Close SELL, book profit | Maximum swing target hit | Opened @$228 → Close @$194 (-15%) = +$34/lot |
| **2** | SELL profit ≥ +10% | Close SELL, book profit | Good swing profit achieved | Opened @$228 → Close @$205 (-10%) = +$23/lot |
| **3** | SELL loss ≥ -5% | Close SELL, accept loss | Wrong direction, cut loss | Opened @$228 → Close @$240 (+5%) = -$12/lot |
| **4** | Price ≤ 50% range | Close SELL, mean reversion | Reached middle of range | Q4 range $177-$322, close @$249 |

### Decision Tree for SELL Exits

```
SELL Position Open @ $228
    │
    ├─ Current Price $194 (-15%) ──→ PRIORITY 1: Close @ +15% profit ✅
    │
    ├─ Current Price $205 (-10%) ──→ PRIORITY 2: Close @ +10% profit ✅
    │
    ├─ Current Price $240 (+5%)  ──→ PRIORITY 3: Close @ -5% loss ❌
    │
    └─ Current Price $249 (mid)  ──→ PRIORITY 4: Close @ 50% range ✅
```

### What if Multiple Conditions Match?

**Scenario A: Price drops to $194 (-15% from entry)**
- Condition 1 (≥+15%): ✅ YES
- Condition 2 (≥+10%): ✅ YES
- Condition 4 (≤50% range): ✅ YES (if range mid is $249)

**Action:** Close at +15% (Priority 1 takes precedence)

**Scenario B: Price rises to $240 (+5.3% from entry)**
- Condition 1: ❌ NO (not +15% profit)
- Condition 2: ❌ NO (not +10% profit)
- Condition 3 (≥-5%): ✅ YES

**Action:** Close at -5% loss (Priority 3)

---

## SECTION 2: LONG POSITION EXIT CONDITIONS

### Exit Strategy (Conservative Approach)

| Condition | Action | % to Close | Keep Open | Example |
|-----------|--------|------------|-----------|---------|
| **Profit +100%** | Partial exit | 50% | 50% | 8 lots → Close 4, keep 4 |
| **Profit +200%** | Partial exit | 25% more | 25% | 4 lots → Close 1, keep 3 |
| **Profit +300%** | Full exit | 100% | 0% | 3 lots → Close all |

### Exit Strategy (Aggressive Approach - Alternative)

| Condition | Action | % to Close | Keep Open | Example |
|-----------|--------|------------|-----------|---------|
| **Profit +50%** | Partial exit | 25% | 75% | 8 lots → Close 2, keep 6 |
| **Profit +100%** | Partial exit | 50% | 50% | 8 lots → Close 4, keep 4 |
| **Profit +200%** | Full exit | 100% | 0% | 4 lots → Close all |

### LONG Exit Decision Tree

```
LONG Positions: 8.0 lots @ avg $149
Current Price: $298 (+100% profit = $1,192)
    │
    ├─ Conservative: Close 4.0 lots
    │   ├─ Realized: ($298 - $149) × 4.0 = +$596
    │   └─ Remaining: 4.0 lots still open
    │
    └─ Aggressive: Close 6.0 lots
        ├─ Realized: ($298 - $149) × 6.0 = +$894
        └─ Remaining: 2.0 lots still open
```

### NEVER CLOSE LONG AT LOSS

**Rule:** LONG positions are NEVER closed while in loss (< 0% profit)

**Exception:** Emergency stop ONLY if:
1. Total account loss ≥ -15% (unrealized)
2. Position held > 12 months with no recovery sign
3. Fundamental change (bankruptcy, delisting risk)

---

## SECTION 3: SIMULTANEOUS CONDITIONS

### What if SELL hits target WHILE LONG also at exit level?

**Example Scenario:**
```
LONG: 8.0 lots @ avg $149
SELL: 4.0 lots @ $346
Current Price: $306

SELL Status: ($346 - $306) × 4.0 = +$160 profit (+11.6%) → EXIT SIGNAL ✅
LONG Status: ($306 - $149) × 8.0 = +$1,256 profit (+105%) → EXIT SIGNAL ✅

What to do?
```

**Priority Decision:**

| Step | Action | Reason |
|------|--------|--------|
| **1** | Close SELL first | Book short-term swing profit (+$160) |
| **2** | Wait 1 tick | Ensure SELL close executed |
| **3** | Close 50% LONG (4.0 lots) | Partial exit at +105% profit |
| **4** | Keep 4.0 LONG open | Let rest run for potential +200% |

**Code Logic:**
```cpp
if(SellProfitPercent >= 10.0 && LongProfitPercent >= 100.0)
{
    // Close SELL first (higher priority)
    CloseSellPositions();
    Sleep(100);  // Wait 100ms

    // Then close 50% LONG
    CloseLongPartial(0.5);
}
```

---

## SECTION 4: POSITION TRACKING AFTER PARTIAL EXITS

### Scenario: Close 50% LONG at +100%

**Before Close:**
```
LONG Positions: 8.0 lots
├─ Step 0: 1.0 lot @ $167
├─ Step 1: 1.0 lot @ $160
├─ Step 2: 1.0 lot @ $154
├─ Step 3: 1.0 lot @ $147
├─ Step 4: 1.0 lot @ $140
├─ Step 5: 1.0 lot @ $133
├─ Step 6: 1.0 lot @ $126
└─ Step 7: 1.0 lot @ $118

Average Entry: $149
Current Step Counter: 7
```

**After Closing 50% (4.0 lots):**

**Option A: Close Newest Positions (FIFO)**
```
Closed: Steps 4-7 (1.0 lot each @ $140, $133, $126, $118)
Remaining: Steps 0-3 (1.0 lot each @ $167, $160, $154, $147)
New Average: $157
New Step Counter: 3 ✅ (Can add 4 more positions)
```

**Option B: Close Oldest Positions (LIFO)**
```
Closed: Steps 0-3 (1.0 lot each @ $167, $160, $154, $147)
Remaining: Steps 4-7 (1.0 lot each @ $140, $133, $126, $118)
New Average: $129
New Step Counter: Still 7 ⚠️ (Only 1 more position allowed)
```

**Option C: Close Proportionally (All Steps Equally)**
```
Closed: 0.5 lot from each step
Remaining: 0.5 lot × 8 steps = 4.0 lots
New Average: Still $149
New Step Counter: Still 7 ⚠️ (Tracking becomes complex)
```

### RECOMMENDED: Use Option A (FIFO - Newest First)

**Why:**
- Resets step counter to allow more averaging down
- Keeps oldest (highest cost basis) positions open
- If price drops again, can add more positions
- Simpler tracking logic

---

## SECTION 5: COOLDOWN PERIODS

### After Closing SELL Hedge

**Question:** Can we immediately open another SELL if price rises again?

**Example:**
```
Close SELL #1 @ $216 (profit booked)
Price rises to $250 next day
LONG profit now +68% → Should we open SELL #2?
```

**Option A: No Cooldown (Aggressive)**
```
Allow immediate re-entry if conditions met:
├─ LONG profit ≥ +30% ✅
├─ Price in upper 30% range ✅
└─ No previous SELL open ✅
→ Open SELL #2 @ $250
```

**Option B: 30-Day Cooldown (Conservative)**
```
After closing SELL, wait 30 days before opening new SELL
├─ Prevents over-trading
├─ Gives price time to develop trend
└─ Reduces transaction costs
```

**Option C: Profit-Based Cooldown (Balanced)**
```
After closing SELL, only open new SELL if:
├─ LONG profit increased by another +20% from last SELL entry
└─ Example: Last SELL @ +53%, next SELL only if +73%
```

### RECOMMENDATION: Use Option A (No Cooldown)

**Reason:** Swing trading requires flexibility to catch multiple peaks

---

## SECTION 6: COMPLETE EXIT LOGIC FLOWCHART

```
┌─────────────────────────────────────────┐
│ Every Tick: Check Exit Conditions      │
└─────────────────────────────────────────┘
             │
             ├─── Have SELL Position? ────┐
             │                             │
             │                             ▼
             │              ┌──────────────────────────┐
             │              │ Check SELL Exit:         │
             │              │ 1. Profit ≥ +15%? → EXIT │
             │              │ 2. Profit ≥ +10%? → EXIT │
             │              │ 3. Loss ≥ -5%?    → EXIT │
             │              │ 4. Price ≤ 50% range? → EXIT │
             │              └──────────────────────────┘
             │
             └─── Have LONG Position? ────┐
                                           │
                                           ▼
                           ┌──────────────────────────┐
                           │ Check LONG Profit:       │
                           │ +300%? → Close ALL       │
                           │ +200%? → Close 25% more  │
                           │ +100%? → Close 50%       │
                           │ < 0%?  → NEVER CLOSE     │
                           └──────────────────────────┘
```

---

## SECTION 7: IMPLEMENTATION QUESTIONS FOR YOU

**Before we code, please confirm:**

### Question 1: LONG Exit Strategy
```
A) Conservative (exit at +100%, +200%, +300%)
B) Aggressive (exit at +50%, +100%, +200%)
C) Never exit LONG (only SELL hedges for profit)
```

### Question 2: SELL Exit Priority
```
Current: +15% > +10% > -5% > 50% range
Is this correct? Or different order?
```

### Question 3: Partial Exit Method
```
A) FIFO (close newest positions first) - RECOMMENDED
B) LIFO (close oldest positions first)
C) Proportional (close % from all positions)
```

### Question 4: Cooldown After SELL Close
```
A) No cooldown (can re-enter immediately)
B) 30-day cooldown
C) Profit-based cooldown (+20% increase required)
```

### Question 5: Emergency LONG Exit
```
IF total account loss ≥ -15% AND held > 12 months:
A) Close all LONG positions (cut losses)
B) Close worst performing stocks only
C) Never close, wait for recovery
```

---

## SUMMARY: DEFAULT SETTINGS (IF YOU APPROVE)

```
SELL EXITS:
├─ Priority 1: +15% profit → CLOSE
├─ Priority 2: +10% profit → CLOSE
├─ Priority 3: -5% loss → CLOSE
└─ Priority 4: 50% range → CLOSE

LONG EXITS:
├─ +100% profit → Close 50% (FIFO method)
├─ +200% profit → Close 25% more (FIFO)
├─ +300% profit → Close ALL
└─ < 0% profit → NEVER CLOSE (except emergency)

COOLDOWN:
└─ None (can re-enter SELL immediately)

EMERGENCY:
└─ -15% account loss + 12 months → Close worst stocks
```

**Ready to implement with these rules?**
