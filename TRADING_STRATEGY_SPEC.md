# VIX Momentum Basket Trading Strategy
## Specification for MT5 EA Implementation

**Version:** 1.0
**Created:** 2024-12-23
**Strategy Type:** Intraday VIX-momentum driven equity short positions

---

## 1. STRATEGY OVERVIEW

This strategy trades a basket of US technology stocks SHORT when VIX momentum indicates rising volatility throughout the trading day. The strategy uses progressive VIX checkpoints to confirm a fear-driven selloff is underway, then captures the inverse movement in equities.

### Core Concept:
- **VIX rising** → Market fear increasing → Stocks falling
- **Entry signal:** VIX progressive momentum (3 checkpoints)
- **Execution:** Short basket of tech stocks with high negative VIX correlation
- **Exit:** Profit targets, time-based, or VIX reversal

---

## 2. TRADING INSTRUMENTS

### Primary Signal: VIX
- **Symbol:** `VIX` (Volatility Index CFD)
- **Role:** Signal generator (not necessarily traded)
- **Contract size:** 1
- **Trading hours:** 01:00-23:59 (Mon-Thu), 01:00-23:55 (Fri)

### Basket Instruments (Tech Stocks):
```
1.  NVDA.US-24  (Nvidia)
2.  MSFT.US-24  (Microsoft)
3.  AVGO.US-24  (Broadcom)
4.  ORCL.US-24  (Oracle)
5.  PLTR.US-24  (Palantir)
6.  ADBE.US-24  (Adobe)
7.  MU.US      (Micron)
8.  SMCI.US    (Super Micro Computer)
```

**Trading hours:** 00:01-23:59 (mostly 24h, except Monday 03:00 start)

---

## 3. ENTRY CONDITIONS

### VIX Checkpoint System

**Baseline Reference:** VIX price at **01:00** (when VIX trading starts)

**Progressive Checkpoints:**

| Checkpoint | Time  | VIX % Change Required | Signal Status |
|------------|-------|----------------------|---------------|
| Stage 1    | 03:00 | +1.0% vs baseline    | Alert         |
| Stage 2    | 06:00 | +2.0% vs baseline    | Warning       |
| Stage 3    | 10:00 | +3.0% vs baseline    | **ENTRY**     |

### Entry Rules:
1. **All 3 stages must trigger sequentially** (3am → 6am → 10am)
2. If Stage 1 fails at 3am, **no trade that day**
3. If Stage 2 fails at 6am, **no trade that day**
4. **Entry executes immediately** when Stage 3 confirmed at 10am

### Entry Validation:
- ✅ At least **12 hours remaining** until day close (23:59)
- ✅ VIX baseline established at 01:00
- ✅ No existing positions from previous day
- ✅ Account has sufficient margin for full basket

### Position Sizing:
**Approach:** Equal-weight across all basket stocks

**Example (€10,000 account, 1:100 leverage):**
- Total capital allocation: **10% of account** = €1,000
- Number of stocks: **8**
- Capital per stock: €1,000 / 8 = **€125 per stock**
- Lot size calculation:
  ```
  Lot size = (Capital per stock) / (Stock price × Contract size × Leverage requirement)

  Example for NVDA @ 180.96:
  Lot size = €125 / (180.96 × 1) = 0.69 lots → Round to 0.7 lots
  ```

**Risk Limit:** Max **2% account risk** per trade (across all basket positions combined)

---

## 4. EXIT CONDITIONS

### Profit Targets (Individual Stock):
**Option 1:** Fixed percentage
- Close position when stock moves **-2.0%** (short = profit when price drops)
- Example: NVDA entry @ 180.96 → Exit @ 177.34

**Option 2:** Combined basket target
- Close **all positions** when total basket P&L reaches **+€300** (3% account)

### Stop Loss (Safety Net):
**Individual stock stop:**
- Close position if stock moves **+1.5%** against us (price rises)
- Example: NVDA entry @ 180.96 → Stop @ 183.67

**Total basket stop:**
- Close **all positions** if total basket P&L hits **-€200** (-2% account)

### Time-Based Exits:
1. **Not profitable by 20:00** → Close all at market
2. **Force close at 23:30** → End-of-day safety (avoid overnight gaps/swaps)

### VIX Reversal Exit:
- If VIX drops **-1.0%** from intraday peak → Close all positions
- Example: VIX peaks at 16.50, then drops to 16.34 → Exit signal

### Trailing Stop (Optional):
- Once basket profit reaches **+€150**, activate trailing stop at **+€100**

---

## 5. RISK MANAGEMENT

### Position Limits:
- **Max lot size per stock:** 1.0 lot
- **Max number of stocks:** 8 positions simultaneously
- **Max margin usage:** 30% of available margin

### Daily Limits:
- **Max daily loss:** -€500 or -5% account (whichever hits first)
- **Max trades per day:** 1 signal only (no re-entries same day)

### Account Protection:
- If account equity drops **-10% from peak**, **stop EA completely**

---

## 6. EXECUTION SPECS

### Order Type:
- **Market orders** (immediate execution)
- **Slippage tolerance:** 3 points max

### Magic Number:
- **123456** (unique ID for this EA's trades)

### Logging:
- Log all VIX checkpoints, signals, entries, exits to MT5 Experts log
- Format: `[YYYY-MM-DD HH:MM:SS] EVENT: Details`

---

## 7. CORRELATION TRACKING (Advanced - Phase 2)

For dynamic basket selection (future enhancement):

**Calculation:**
- Rolling 30-minute correlation between VIX and each stock
- Update every 5 minutes

**Filter:**
- Only trade stocks with correlation < **-0.6** (strong inverse relationship)
- Require minimum **3 stocks** pass filter, else skip trade

**Implementation:** Build correlation buffer in MQL5, calculate Pearson coefficient

---

## 8. BACKTESTING & VALIDATION

### Backtest Period:
- **From:** 2024-01-01
- **To:** 2024-12-20
- **Data:** 1-minute bars on VIX and basket stocks

### Success Criteria:
- **Win rate:** > 55%
- **Profit factor:** > 1.5
- **Max drawdown:** < 15%
- **Sharpe ratio:** > 1.0

### Forward Testing:
- Demo account for **14 days** before live
- Position size: **25% of planned live size**

---

## 9. SPECIAL CONDITIONS

### Market Regime Filters:
- **Don't trade if VIX > 35** at 01:00 baseline (already too elevated)
- **Don't trade if VIX < 12** at 01:00 (no volatility = weak signals)

### Weekend Handling:
- **Force close all positions Friday 23:30**
- Never hold over weekend (gap risk)

### Broker-Specific:
- **Swap awareness:**
  - Long positions cost **-6.23%** annually
  - Short positions earn **+1.03%** annually
  - Triple swap on Friday
- **Spread monitoring:** Log if spread > 5 points (liquidity issue)

---

## 10. IMPLEMENTATION CHECKLIST

### Phase 1: Core EA (Priority)
- [ ] VIX baseline tracker (01:00 reference)
- [ ] Checkpoint monitor (3am, 6am, 10am)
- [ ] Entry signal validator
- [ ] Basket position opener (8 stocks, market orders)
- [ ] Profit target monitor (individual + combined)
- [ ] Stop loss monitor (individual + combined)
- [ ] Time-based exit (20:00, 23:30)
- [ ] VIX reversal monitor
- [ ] Risk management (margin, daily loss limits)

### Phase 2: Enhancements (Future)
- [ ] Real-time correlation calculator
- [ ] Dynamic basket selection
- [ ] Trailing stop logic
- [ ] Trade performance logger to database
- [ ] Email/push notification alerts

### Phase 3: Integration with KLDAFinTech Platform (Optional)
- [ ] Send trade signals to PostgreSQL database
- [ ] Fetch VIX data from backend API (instead of broker)
- [ ] Dashboard for real-time monitoring

---

## 11. EXAMPLE TRADE SCENARIO

**Date:** 2024-12-23
**VIX Baseline (01:00):** 15.25

**Progression:**
- **03:00** → VIX: 15.41 (+1.05%) ✅ Stage 1 triggered
- **06:00** → VIX: 15.56 (+2.03%) ✅ Stage 2 triggered
- **10:00** → VIX: 15.72 (+3.08%) ✅ **ENTRY SIGNAL**

**Execution (10:01):**
```
SHORT 0.5 lots NVDA.US-24 @ 180.96
SHORT 0.3 lots MSFT.US-24 @ 485.02
SHORT 0.5 lots AVGO.US-24 @ 340.43
SHORT 0.5 lots ORCL.US-24 @ 193.67
SHORT 0.6 lots PLTR.US-24 @ 193.67
SHORT 0.3 lots ADBE.US-24 @ 354.03
SHORT 0.4 lots MU.US @ 265.69
SHORT 0.5 lots SMCI.US @ 31.20
```

**Monitoring:**
- Target: Each stock -2% OR total basket +€300
- Stop: Each stock +1.5% OR total basket -€200
- VIX reversal: Exit if VIX drops -1% from peak
- Time: Exit if not profitable by 20:00, force close 23:30

**Outcome Example:**
- **14:30** → NVDA hits -2% target (177.34) → Close NVDA position (+€100)
- **15:45** → Combined basket P&L reaches +€305 → **Close all remaining positions**
- **Final P&L:** +€305 (3.05% account)

**VIX Movement:**
- Peak: 16.20 @ 12:00
- Close: 15.90 @ 15:45 (never hit -1% reversal threshold)

---

## 12. KNOWN RISKS & MITIGATIONS

### Risk 1: VIX Reversal (False Breakout)
- **Scenario:** VIX spikes +3% then immediately reverses
- **Mitigation:** VIX reversal exit (-1% from peak)

### Risk 2: Stocks Don't Follow VIX
- **Scenario:** VIX rises but stocks don't fall (correlation breakdown)
- **Mitigation:** Individual stop losses, time-based exit

### Risk 3: Slippage on Market Orders
- **Scenario:** Fast market, wide spreads
- **Mitigation:** Slippage tolerance (3 points), monitor spread in logs

### Risk 4: Overnight Gap (If Friday Close Fails)
- **Scenario:** Position held over weekend, gap up Monday
- **Mitigation:** Force close Friday 23:30

### Risk 5: Broker Feed Delay
- **Scenario:** VIX data lags, wrong checkpoint readings
- **Mitigation:** Log all timestamps, verify against external VIX source

---

## STRATEGY STATUS: READY FOR IMPLEMENTATION

This specification is complete and viable for MQL5 EA development. All parameters are defined, testable, and aligned with broker specifications.

**Next Step:** Build MQL5 Expert Advisor files based on this spec.
