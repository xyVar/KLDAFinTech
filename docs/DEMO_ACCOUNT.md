# Demo Account - Testing Environment

**Account:** 62101051
**Broker:** PepperstoneUK-Demo
**Server:** LD2
**Mode:** Hedging (can hold long + short simultaneously)
**Status:** Trading Enabled ✅
**Last Login:** 2025-12-23 18:01:00
**Previous Session:** 2025-12-23 19:00:46 from 109.236.43.7
**Connection:** Authorized (ping: 41.15 ms)
**Build:** 5370

---

## Purpose

This demo account is used for testing new trading strategies before deploying them to live account.

**Testing Protocol:**
1. Test strategy on demo for minimum 2 weeks
2. Monitor performance daily
3. Verify all entry/exit logic works correctly
4. Check risk management functions
5. Only deploy to live after consistent demo results

---

## Account Specifications

```
Account Type: Hedging
Leverage: [To be verified in MT5]
Base Currency: [To be verified]
Initial Balance: [To be verified]
```

**Hedging Mode Benefits:**
- Can open LONG and SHORT on same symbol
- Can hedge positions
- More flexibility for complex strategies
- Better for testing multiple approaches

---

## Connection Details

**Server:** PepperstoneUK-Demo (LD2 datacenter)
**Ping:** 41.15 ms (good latency)
**Build:** 5370 (current MT5 version)

**Network Log:**
```
2025.12.23 18:00:58 - Connection lost
2025.12.23 18:00:59 - Reconnected and authorized
2025.12.23 18:01:00 - Trading enabled (hedging mode)
```

---

## Testing Schedule

**Phase 1: Initial Testing (Week 1-2)**
- Test strategy logic
- Verify entry signals
- Confirm exit execution
- Check risk limits

**Phase 2: Extended Testing (Week 3-4)**
- Run in various market conditions
- Test edge cases
- Monitor for bugs
- Track performance metrics

**Phase 3: Pre-Live Validation (Week 5-6)**
- Final strategy parameters
- Stress test with live market volatility
- Document all trades
- Calculate expected live performance

---

## Safety Notes

- ✅ Demo account = no real money risk
- ✅ Perfect for testing aggressive strategies
- ✅ Test position sizing before live
- ✅ Verify all functions work correctly
- ⚠️ Demo spreads may differ from live
- ⚠️ Demo fills may be more favorable than live
- ⚠️ Slippage may be less on demo

---

**This is a SAFE environment for testing the new strategy before risking real capital.**
