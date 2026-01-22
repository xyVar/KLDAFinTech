# KLDA-HFT Asset Surveillance Dashboard

## Overview

The Asset Surveillance Dashboard is a Bloomberg-style scientific research environment for real-time market analysis. It displays all 17 assets under surveillance with Renaissance Medallion metrics and provides detailed time-series analysis.

---

## Quick Start

### 1. Ensure Services Are Running

**C++ Backend (Docker):**
```bash
cd C:\Users\PC\Desktop\KLDAFinTech\KLDA-HFT
docker-compose up -d
```

**Flask API Server:**
```bash
cd C:\Users\PC\Desktop\KLDAFinTech\KLDA-HFT\api
python tick_receiver.py
```

**Python Tick Capture (Optional - if you want live broker data):**
```bash
cd C:\Users\PC\Desktop\KLDAFinTech\KLDA-HFT\python-bridge
python mt5_tick_capture_ALL_TICKS.py
```

### 2. Access Dashboard

Open in browser:
- **Asset Surveillance:** `file:///C:/Users/PC/Desktop/KLDAFinTech/KLDA-HFT/cpp-backend/klda_asset_surveillance.html`
- **Original Dashboard:** `http://localhost:8082/renaissance_trading_dashboard.html`

---

## Dashboard Features

### Main View - Asset Grid

Displays all 17 assets as clickable cards:
- **Symbol** - Asset name (TSLA, NatGas, SpotCrude, etc.)
- **Bid/Ask** - Current market prices
- **Renaissance Metrics:**
  - Mean Reversion % (distance from MA50)
  - HMM Regime (market state)
  - Transaction Cost (spread + swap)
- **Update Status** - Time since last tick (green = live < 10 min, gray = stale)
- **Entry Signal** - ENTER_LONG or WAIT

### Modal View - Detailed Analysis

Click any asset card to open detailed modal with:

**1. Time Series Chart**
- Interactive Chart.js visualization
- Displays Close, High, Low prices
- Real OHLCV data from PostgreSQL database

**2. Timeframe Selector**
- M1 (1 minute bars)
- M5 (5 minute bars)
- M15 (15 minute bars)
- H1 (1 hour bars)
- H4 (4 hour bars)
- D1 (1 day bars)

**3. Statistics Panel**
- Current Price
- 24-Hour Change (absolute and percentage)
- Total Ticks Recorded
- Average Spread
- Renaissance Signal
- Last Update Time

**4. Tick History Table**
- Last 50 ticks
- Time, Bid, Ask, Spread, Volume
- Scrollable view

---

## API Endpoints

Flask API runs on `http://localhost:5000` with the following endpoints:

### Market Data
- `GET /api/current` - Get current tick for all symbols
- `GET /api/bars/<symbol>/<timeframe>?limit=100` - Get OHLCV bars
  - Example: `/api/bars/TSLA/M5?limit=50`
- `GET /api/ticks/<symbol>?limit=50` - Get recent tick history
  - Example: `/api/ticks/NatGas?limit=100`
- `GET /api/stats/<symbol>` - Get 24h statistics
  - Example: `/api/stats/SpotCrude`

### Trading Data
- `GET /api/positions?status=OPEN&symbol=TSLA` - Get positions
- `GET /api/account` - Get account state

### System
- `GET /health` - Health check
- `GET /stats` - API statistics

---

## Supported Symbols

### Stocks (13)
- TSLA, NVDA, PLTR, AMD, AVGO, META, AAPL, MSFT, ORCL, AMZN, CSCO, GOOG, INTC

### Commodities (2)
- NatGas (Natural Gas)
- SpotCrude (Crude Oil)

### Indices (1)
- NAS100 (NASDAQ 100)

### Volatility (1)
- VIX (CBOE Volatility Index)

---

## Data Flow

```
MT5 Broker (Pepperstone)
  ↓
Python Bridge (mt5_tick_capture_ALL_TICKS.py)
  ↓
Flask API (tick_receiver.py) - Port 5000
  ↓
PostgreSQL Database (KLDA-HFT_Database)
  ├─ current table (latest tick per symbol)
  ├─ *_history tables (all historical ticks)
  └─ positions table (trading positions)
  ↓
C++ Backend (Docker) - Reads database every second
  ├─ Calculates Renaissance metrics
  ├─ Generates trading signals
  └─ Outputs live_ticks.json
  ↓
Frontend Dashboard
  ├─ Reads live_ticks.json for real-time data
  └─ Calls Flask API for historical charts
```

---

## Technical Details

### Database Schema

**Current Table:**
- Stores latest tick per symbol (17 rows total)
- Updated in real-time by Flask API

**History Tables:**
- `tsla_history`, `natgas_history`, etc.
- TimescaleDB hypertables for efficient time-series storage
- Stores every tick received from broker

**Positions Table:**
- Tracks open and closed trading positions
- Includes entry/exit price, P&L, TP/SL levels

**Account State Table:**
- Tracks account balance over time
- Realized and unrealized P&L

### Renaissance Medallion Metrics

The C++ backend calculates 5 metrics inspired by Renaissance Technologies:

1. **Mean Reversion (Simons)** - 50-tick MA deviation
2. **Spread Volatility (Patterson)** - Spread vs 100-tick average
3. **HMM Regime (Brown)** - Market state detection (200-tick window)
4. **Transaction Cost (Mercer)** - "The Devil" - spread + swap cost
5. **Kelly Position Size** - Optimal bet sizing (50.75% win rate)

### Performance

- **Tick Capture Rate:** 3-5 ticks/second/asset (~40-60 ticks per batch)
- **C++ Backend:** 86,000+ updates so far (1 update/second)
- **Database Size:** ~614,000+ ticks stored
- **API Latency:** < 200ms end-to-end
- **Chart Refresh:** 1 second interval

---

## Usage Tips

### For Live Market Analysis
1. Focus on commodities during market hours (NatGas, SpotCrude)
2. VIX and NAS100 update continuously
3. Stocks only update during NYSE hours

### For Historical Analysis
1. Use M1/M5 timeframes for recent activity
2. Use H1/H4 for trend analysis
3. Use D1 for long-term patterns

### For Signal Generation
- Green "ENTER_LONG" signal = All 5 Renaissance metrics align
- Gray "WAIT" signal = Conditions not met
- Check Transaction Cost - if > $50, spread too wide

---

## Troubleshooting

### Dashboard shows old data (hours/days ago)
- **Cause:** Broker is closed (stocks) or Python bridge not running
- **Fix:** Start `mt5_tick_capture_ALL_TICKS.py` or wait for market open

### Charts show "No Data"
- **Cause:** No ticks in last 7 days for that symbol
- **Fix:** Check database has recent data for symbol

### API returns error
- **Cause:** Flask API not running or database connection issue
- **Fix:** Restart Flask API, check PostgreSQL is running

### C++ backend not updating
- **Cause:** Docker container stopped
- **Fix:** `docker-compose restart` in KLDA-HFT directory

---

## Architecture Files

### Frontend
- `klda_asset_surveillance.html` - New surveillance dashboard (this one)
- `renaissance_trading_dashboard.html` - Original dashboard

### Backend
- `cpp-backend/src/main_live.cpp` - C++ analysis engine
- `api/tick_receiver.py` - Flask API server
- `python-bridge/mt5_tick_capture_ALL_TICKS.py` - Tick capture

### Database
- `database/create_positions_table.sql` - Position tracking schema
- `database/create_continuous_aggregates.sql` - Time series compression
- `database/setup_database.py` - Initial setup

---

## Scientific Research Environment

This system is designed for **research and analysis purposes only**. It is NOT a commercial product.

**Key Points:**
- Server restricted to authorized access only
- Connected to bank/broker account for trade execution
- Used for data analysis and strategy development
- Not for sale or public distribution

**Data Privacy:**
- EA source code (.mq5 files) excluded from repository
- Personal trading data not shared
- Broker credentials stored securely

---

## Next Steps

### Phase 1: Position Management (In Progress)
- C++ backend tracks positions from database
- Automatic TP/SL monitoring
- P&L calculation in real-time

### Phase 2: Trading Execution
- C++ opens positions based on signals
- Position tracking in database
- Dashboard displays real positions

### Phase 3: Time Series Optimization
- Create continuous aggregates for all symbols
- Pre-computed OHLCV bars
- Faster chart rendering

### Phase 4: Interactive Trading
- Click to open/close positions from dashboard
- Manual override controls
- Risk management interface

---

**KLDA-HFT Asset Surveillance System**
Version 1.0.0 | 2026-01-20
Database: PostgreSQL 16 + TimescaleDB 2.24.0
Backend: C++ 17 | API: Python Flask
Dashboard: HTML5 + Chart.js
