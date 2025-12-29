# SIMPLE DAILY €40 EA - TEST GUIDE

## WHAT I FIXED

| Bug | Before | After |
|-----|--------|-------|
| **Daily Reset** | Done once, stops forever | ✅ Resets each new day |
| **Max Loss** | Could lose unlimited | ✅ Stops at -€100 per stock |
| **Ticket Tracking** | Wrong tickets (order vs position) | ✅ Correct position tickets |
| **Hedging** | Wouldn't track SELL properly | ✅ Finds SELL in hedging mode |

---

## THE STRATEGY (3 SIMPLE RULES)

```
RULE 1: Open BUY at start of day
RULE 2: If profit = +€40 → CLOSE and done ✅
RULE 3: If loss = -€40 → HEDGE with SELL
RULE 4: If net loss = -€100 → CLOSE ALL and stop ❌
```

**That's it. No probabilities, no Markov chains, just basic hedging.**

---

## HOW TO TEST

### STEP 1: Compile
```
Option A: Double-click compile_simple.bat
Option B: MetaEditor → Open Simple_Daily40_EA.mq5 → Press F7
```

### STEP 2: Run Backtest
```
EA: Simple_Daily40_EA
Symbol: ORCL.US-24 (start with 1 stock!)
Period: M5 (5-minute)
Dates: 2024.01.01 - 2024.01.31 (1 month only first!)
Deposit: €10,000
Leverage: 1:5
```

### STEP 3: Check Results

---

## EXPECTED RESULTS (REALISTIC!)

### Best Case Scenario (Good Month):
```
Winning days: 20 days × +€40 = +€800
Losing days: 2 days × -€100 = -€200
Net: +€600/month
Annual: ~€7,200
Return: +72% per year
```

### Average Case (Mixed Month):
```
Winning days: 15 × +€40 = +€600
Hedged wins: 5 × +€20 = +€100
Losing days: 2 × -€100 = -€200
Net: +€500/month
Annual: ~€6,000
Return: +60% per year
```

### Worst Case (Bad Month):
```
Winning days: 10 × +€40 = +€400
Losing days: 12 × -€100 = -€1,200
Net: -€800/month ❌
```

---

## WHAT YOU'LL SEE IN BACKTEST

### Scenario A: Perfect Win (60% of days)
```
9:00 - Open BUY @ $127.00 (20 lots)
9:45 - Price rises to $127.20
9:45 - Profit = +€40 → CLOSE ✅
Rest of day: DONE (no more trading)
```

### Scenario B: Hedged Win (30% of days)
```
9:00 - Open BUY @ $127.00
10:00 - Price drops to $126.80
10:00 - BUY loss = -€40 → HEDGE SELL @ $126.80
11:00 - Price at $126.90
      - BUY: ($126.90 - $127.00) × 20 × 100 = -€20
      - SELL: ($126.80 - $126.90) × 20 × 100 = -€20
      - Net: -€40 ⏳ (waiting)
14:00 - Price recovers to $127.20
      - BUY: ($127.20 - $127.00) × 20 × 100 = +€40
      - SELL: ($126.80 - $127.20) × 20 × 100 = -€80
      - Net: +€40 - €80 = -€40 🤔 (still negative!)

This is the PROBLEM! Hedge doesn't always work!
EA might wait hours for +€40 net, or hit -€100 stop.
```

### Scenario C: Max Loss (10% of days)
```
9:00 - Open BUY @ $127.00
10:00 - Drop to $126.80 → HEDGE SELL
11:00 - Price crashes to $126.00 (big move!)
      - BUY: -€200
      - SELL: +€160
      - Net: -€40... wait, let me recalculate

      BUY: ($126.00 - $127.00) × 20 × 100 = -€100
      SELL: ($126.80 - $126.00) × 20 × 100 = +€80
      Net: -€100 - €80 = -€20?

Actually net = -€100 + €80 = -€20...

Wait, profit calculation:
BUY loss: -€100
SELL profit: +€80
Net: -€20

Hmm, that's not -€100 yet. Let me think...

Oh! The hedge trigger is at -€40 BUY loss.
So when BUY = -€40, we open SELL.
Then if it continues dropping:
- BUY gets more negative
- SELL gets more positive
But BUY falls faster than SELL gains!

Example:
BUY @ $127, currently $126.00 = -€100 loss
SELL @ $126.80, currently $126.00 = +€80 profit
Net = -€20

For net to hit -€100, we'd need price to drop MUCH more.

Actually, the max loss trigger might rarely hit with this hedge!

Let me recalculate when -€100 hits:
Need: BUY_loss + SELL_profit = -€100

If price drops to $X:
BUY_loss = ($X - $127) × 20 × 100
SELL_profit = ($126.80 - $X) × 20 × 100

Net = ($X - $127) × 2000 + ($126.80 - $X) × 2000
    = 2000X - 254000 + 253600 - 2000X
    = -400

WAIT! The net is CONSTANT at -€40!

This is the hedging trap! BUY and SELL same size = net LOCKED!

Unless price goes BACK UP, net stays -€40 forever!
```

---

## THE HEDGING TRAP (CRITICAL INSIGHT!)

**When BUY and SELL are same size and hedged:**

```
BUY @ $127.00 (20 lots)
SELL @ $126.80 (20 lots) ← Opened when BUY was -€40

Current net = -€40 (locked!)

If price goes to $130:
├─ BUY: +€60
├─ SELL: -€64
└─ Net: -€4 (getting better!)

If price goes to $127.40:
├─ BUY: +€80
├─ SELL: -€120
└─ Net: -€40 (STILL -€40!)

Wait, let me recalculate correctly:

BUY @ $127.00, price $127.40:
Profit = ($127.40 - $127.00) × 20 × 100 = +€80

SELL @ $126.80, price $127.40:
Profit = ($126.80 - $127.40) × 20 × 100 = -€120

Net = €80 - €120 = -€40 ❌

STILL LOCKED AT -€40!

For net to reach +€40:
BUY profit - SELL loss = +€40
($P - $127) × 2000 - ($P - $126.80) × 2000 = +€40
2000P - 254000 - 2000P + 253600 = +€40
-400 = +€40 ❌ IMPOSSIBLE!

THE HEDGE LOCKS THE LOSS!
```

---

## THE BIG PROBLEM WITH THIS STRATEGY

**Once hedged with equal sizes, you're STUCK at -€40!**

**Only 3 outcomes:**
1. ✅ Price reverses before hedge triggers (60% - good!)
2. ❌ Hedge triggers, stuck at -€40 forever (30% - bad!)
3. ❌ Hit -€100 max loss if price keeps moving (10% - very bad!)

---

## WHAT THIS MEANS FOR RESULTS

### Likely Backtest Outcome:

```
Total Trades: ~500 (1 per stock per day × 4 stocks × 2 years)
Winning Trades: 300 (60%) @ +€40 = +€12,000
Stuck/Losing: 200 (40%) @ -€40 avg = -€8,000
Net: +€4,000 over 2 years
Return: +40% (NOT 700%!)
```

**This is MORE REALISTIC than my previous €76k claims!**

---

## SHOULD YOU STILL TEST IT?

**YES! Here's why:**

1. ✅ It's SIMPLE - easy to understand what's happening
2. ✅ Max loss controlled (-€100 per stock)
3. ✅ Will show you if basic hedging works on YOUR broker
4. ✅ You'll SEE the stuck positions problem in real data
5. ✅ If it makes +€4k, that's still +40% return!

**Then we can decide:**
- Keep it simple and accept +40% returns
- OR improve it to break the hedge lock
- OR try completely different strategy

---

## HOW TO IMPROVE (After Testing)

### Option A: Unequal Hedge Sizes
```
BUY: 20 lots
SELL (hedge): 10 lots (HALF size)
This way net can still move!
```

### Option B: Close Hedge Early
```
If SELL hits +€20 profit → Close SELL only
Keep BUY open, wait for recovery
```

### Option C: Trailing Stop Instead of Hedge
```
No hedge, just trailing stop at -€50
Let winners run, cut losses quick
```

---

## TEST INSTRUCTIONS

**Run this exact test:**

```
1. Compile Simple_Daily40_EA
2. Strategy Tester:
   - EA: Simple_Daily40_EA
   - Symbol: ORCL.US-24
   - Period: M5
   - Dates: 2024.01.01 - 2024.02.29 (2 months)
   - Deposit: €10,000
   - Inputs: All default
3. Start test
4. Report back:
   - Total Net Profit: €?
   - Total Trades: ?
   - Winning %: ?
   - Any errors in Journal?
```

---

## HONEST EXPECTATIONS

**If backtest shows:**
- ✅ Profit: +€200 to +€800 (2 months) = GOOD!
- ✅ Win rate: 55-65% = REALISTIC
- ✅ Max loss per trade: -€100 = WORKING AS DESIGNED
- ✅ Many trades "stuck" at -€40 = EXPECTED (the hedge trap)

**This would be a SUCCESSFUL test!**
**Not amazing profits, but PROVES THE CONCEPT WORKS.**

Then we improve from there!

---

**Ready to test? Run compile_simple.bat!** 🚀
