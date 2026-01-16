# KLDA FinTech - Algorithmic Trading Project

> **MT5 trading strategies - 7 EAs tested, 2 strategies work, lessons learned**

[![Platform](https://img.shields.io/badge/Platform-MetaTrader%205-blue)](https://www.metatrader5.com/)
[![Language](https://img.shields.io/badge/Language-MQL5-orange)](https://www.mql5.com/)
[![Status](https://img.shields.io/badge/Status-Active-green)](https://github.com)

---

## 📊 Project Overview

Systematic development and testing of trading strategies for 8 US stocks (NVDA, PLTR, META, TSLA, ORCL, AMD, BA, AVGO).

**Journey:**
- Tested 7 different Expert Advisors
- Found 2 working strategies
- Discovered why complexity fails
- Built event-driven TSMC system

**Key Discovery:** Manual trading beats automated EAs (€637 in 3 months vs €1,170 in 2 years)

---

## 📁 Repository Structure

```
KLDAFinTech/
│
├── README.md                              ⭐ You are here
├── PROJECT_THEORY.md                      ⭐ 50+ pages complete analysis
├── YOUR_MANUAL_STRATEGY_DOCUMENTED.md     ⭐ Proven €637 manual strategy
├── BROKER_COSTS_AND_STRATEGY_RULES.md     Trading costs & execution rules
├── .gitignore
│
├── tsmc_system/                           🎯 TSMC Event-Driven Trading
│   ├── TSMC_WATCHDOG_SYSTEM.md            (Main system - 4 strategies)
│   ├── TSMC_EVENT_ANALYSIS_12_QUARTERS.md (100% earnings beat rate)
│   ├── TSMC_SETUP_GUIDE.md                (Quick start guide)
│   ├── tsmc_watchdog.py                   (Automated monitoring)
│   ├── run_tsmc_watchdog.bat              (One-click launcher)
│   └── TSMC_Daily_Tracker_Template.txt    (Excel template)
│
├── active_strategies/                     ✅ Working Strategies Only
│   ├── manual_martingale/                 (€637 in 3 months - YOUR strategy)
│   │   ├── README.md
│   │   ├── GRID_MARTINGALE_STRATEGY.md
│   │   └── [Strategy files]
│   │
│   └── trend_following_ea/                (€2,028 in 2 years - Automated)
│       ├── README.md
│       ├── TrendFollowing_MA50_EA_v2.mq5
│       └── [Backtest reports]
│
├── trackers/                              📊 Excel Trackers (To be created)
│   ├── TSMC_Daily_Tracker.xlsx            (Template in tsmc_system/)
│   └── Portfolio_Tracker.xlsx             (To be created)
│
├── config/                                ⚙️ Configuration
│   └── demo_account.env                   (Pepperstone credentials)
│
├── archive/                               📦 Old/Failed Work (Preserved)
│   ├── failed_eas/                        (5 failed EA strategies)
│   ├── old_strategy_docs/                 (Historical documentation)
│   ├── analysis_tools/                    (VIX analyzers, etc.)
│   └── [Other archived material]
│
└── .git/                                  📋 Version Control
```

---

## 🎯 Quick Start

### Option 1: Use Working Manual Strategy (Recommended)

**Your Proven Strategy (€637 in 3 months):**
```
1. Read: YOUR_MANUAL_STRATEGY_DOCUMENTED.md
2. Apply to ORCL or similar range-bound stocks
3. Method: Buy -4% dips, SELL hedge at +30%, close SELL at €160 profit
4. Expected: +55% per 3-month cycle
```

### Option 2: Use TSMC Event-Driven System

**Automated Monitoring + Event Trading:**
```bash
# Navigate to tsmc_system folder
cd tsmc_system

# Run daily monitor (double-click)
run_tsmc_watchdog.bat

# Read setup guide
TSMC_SETUP_GUIDE.md
```

**Expected:** +192% annual on TSMC trades

### Option 3: Use TrendFollowing EA (Automated)

**Simple MA50 Crossover:**
```
1. Go to: active_strategies/trend_following_ea/
2. Copy TrendFollowing_MA50_EA_v2.mq5 to MT5
3. Backtest: €10k → €12k in 2 years (+20%)
4. Expected: 10%/year steady returns
```

---

## 📈 Strategies Summary

### ✅ Working Strategies

| Strategy | Type | Return | Time | Status |
|----------|------|--------|------|--------|
| **Manual Martingale** | Manual | +€637 (+55%) | 3 months | ⭐ **BEST** |
| **TrendFollowing EA** | Automated | +€2,028 (+20%) | 2 years | ✅ Works |
| **TSMC System** | Event-driven | +192% (expected) | Annual | 🆕 New |

### ❌ Failed Strategies (Archived)

| Strategy | Result | Issue |
|----------|--------|-------|
| HedgedGrid EA | Abandoned | Too complex (930 lines) |
| Optimized EA | Never tested | Overfitting |
| Simple Daily40 EA | €1,170 (+11.7%) | Hedging trap |
| BuyOnly Grid EA | €337 (+3.4%) | Poor performance |
| DynamicScalping EA | €316 (+3.2%) | Failed |

**All failed EAs preserved in `archive/failed_eas/` for reference**

---

## 🔬 Key Discoveries

### 1. The Hedging Trap 🚨

**Mathematical proof:** Equal-size hedging locks P&L regardless of price

```
BUY @ $127.00 (20 lots)
SELL @ $126.80 (20 lots)

Net P&L = ($P - $127) × 2000 + ($126.80 - $P) × 2000
        = -€400 (CONSTANT - price cancels out!)
```

📖 Full proof: [PROJECT_THEORY.md](PROJECT_THEORY.md)

### 2. Manual > Automated

| Approach | Return | Reason |
|----------|--------|--------|
| Your Manual Strategy | +55% (3 months) | Adapts to market changes |
| Best Automated EA | +20% (2 years) | Rigid rules, can't adapt |

**Insight:** Use automation for monitoring, manual for execution

### 3. Complexity Kills Performance

| Lines of Code | Result |
|---------------|--------|
| 930 | Never worked |
| 650 | Never tested |
| 180 | Failed (€1,170) |
| 50 | Success (€2,028) |

**Simple beats complex every time**

---

## 🎓 What Works

### For Range-Bound Stocks (ORCL, AMD, BA):
✅ **Manual Martingale Strategy**
- Buy every -4% dip (max 8 positions)
- SELL hedge when equity +30%
- Close SELL at €160 profit
- Keep LONG running
- Expected: +55% per cycle

### For Trending Stocks (NVDA, PLTR, TSLA):
✅ **TrendFollowing EA**
- Buy when price > MA50
- Sell when price < MA50
- Daily timeframe
- Expected: +20% annual

### For Event-Driven (TSMC):
✅ **TSMC Watchdog System**
- Trade earnings (4x/year)
- Trade tech symposiums (1x/year)
- Buy major dips ($280, $250)
- SELL hedge at peaks + VIX spikes
- Expected: +192% annual

---

## 🚀 Getting Started

### Step 1: Choose Your Approach

**If you like manual trading:**
→ Read `YOUR_MANUAL_STRATEGY_DOCUMENTED.md`
→ Apply to 1-2 stocks
→ Track in Excel

**If you want automation:**
→ Use `active_strategies/trend_following_ea/`
→ Deploy on trending stocks
→ Monitor weekly

**If you want event-driven:**
→ Go to `tsmc_system/`
→ Run `run_tsmc_watchdog.bat` daily
→ Trade on signals

### Step 2: Test First

**Demo account testing:**
1. Pepperstone demo (already configured in `config/`)
2. Test for 1-3 months
3. Verify results match expectations

### Step 3: Scale Up

**Once working:**
1. Start with €1,000-2,500 per stock
2. Add more stocks (up to 8)
3. Track everything in Excel
4. Target: €50,000 annual profit

---

## 📚 Documentation

### Must Read (Priority Order)

1. **[YOUR_MANUAL_STRATEGY_DOCUMENTED.md](YOUR_MANUAL_STRATEGY_DOCUMENTED.md)** ⭐
   - Your proven €637 strategy
   - Real trade log
   - Scaling plan to €50k

2. **[PROJECT_THEORY.md](PROJECT_THEORY.md)** ⭐
   - Complete 50-page analysis
   - Why each EA failed
   - Mathematical proofs

3. **[tsmc_system/TSMC_SETUP_GUIDE.md](tsmc_system/TSMC_SETUP_GUIDE.md)** 🆕
   - New event-driven system
   - 15-minute setup
   - Automated monitoring

4. **[BROKER_COSTS_AND_STRATEGY_RULES.md](BROKER_COSTS_AND_STRATEGY_RULES.md)**
   - Pepperstone commission structure
   - BUY/SELL rules for 100% margin deployment
   - Position sizing calculations

### Archive (Reference Only)

Old strategies and failed attempts preserved in `archive/` folder:
- Failed EA documentation
- Analysis tools
- Historical strategy docs

**Don't start here** - read working strategies first!

---

## 🎯 2026 Goals

**Realistic Target:** €50,000 annual profit

**Portfolio Allocation:**
```
Manual Martingale (3 stocks): €7,500 capital → €25,000 profit (333%)
TrendFollowing EA (3 stocks): €7,500 capital → €2,250 profit (30%)
TSMC System (1 stock):        €2,500 capital → €4,800 profit (192%)
VIX Hedges (opportunistic):   -               → €5,000 profit

Total Capital: €17,500
Total Expected: €37,050 profit (212% return)
```

**Conservative (50% success):** €18,500 profit (106% return) ✅ Achievable

---

## 📊 Project Stats

| Metric | Value |
|--------|-------|
| Strategies Tested | 7 EAs |
| Working Strategies | 2 |
| Documentation Pages | 150+ |
| Test Period | 2 years (backtest) |
| Best Manual Result | €637 (+55% in 3 months) |
| Best Automated Result | €2,028 (+20% in 2 years) |
| **Key Lesson** | **Manual > Automated** |

---

## ⚠️ Disclaimer

**Educational purposes only. Not financial advice.**

- All tests on demo accounts
- Past performance ≠ future results
- Trading involves risk of loss
- Only trade money you can afford to lose

---

## 🤝 Contributing

Personal learning project. Feedback welcome!

**Share:**
- Test results on different stocks
- Improvements to working strategies
- Bug reports

**Please don't suggest:**
- More complex EAs
- Additional hedging strategies
- Overcomplicated optimizations

**Keep it simple!**

---

## 📧 Contact

**Project:** KLDA FinTech
**Platform:** MetaTrader 5
**Broker:** Pepperstone Demo
**Repository:** https://github.com/xyVar/KLDAFinTech

---

## 🏆 Quick Win Checklist

- [ ] Read YOUR_MANUAL_STRATEGY_DOCUMENTED.md
- [ ] Pick 1-2 stocks to trade manually
- [ ] Test on demo account (1 month)
- [ ] Try TSMC watchdog system (run_tsmc_watchdog.bat)
- [ ] Deploy TrendFollowing EA on trending stocks
- [ ] Track all trades in Excel
- [ ] Scale up when profitable

---

**⭐ Star this repo if our failures taught you something!**

*"Success is stumbling from failure to failure with no loss of enthusiasm."*

---

*Last Updated: January 9, 2026 | Version: 2.0 | Status: Clean & Organized*
