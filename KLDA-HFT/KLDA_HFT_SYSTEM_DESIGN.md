# KLDA-HFT TRADING ENGINE - SYSTEM DESIGN

## ARCHITECTURE OVERVIEW

```
┌───────────────────────────────────────────────────────────────┐
│                    PostgreSQL Database                         │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ TICK DATA                                                │ │
│  │  - current (latest tick per symbol)                      │ │
│  │  - *_history (all historical ticks)                      │ │
│  └──────────────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ POSITION DATA (NEW)                                      │ │
│  │  - positions table (open & closed trades)                │ │
│  │  - account_state table (balance, P&L tracking)           │ │
│  └──────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────┘
                              ↓ ↑
┌───────────────────────────────────────────────────────────────┐
│          C++ TRADING ENGINE (Docker/Ubuntu)                    │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ COMPONENTS:                                              │ │
│  │                                                          │ │
│  │ 1. Tick Processor                                       │ │
│  │    - Reads latest ticks from database                   │ │
│  │    - Updates internal tick buffer                       │ │
│  │                                                          │ │
│  │ 2. Renaissance Metrics Calculator                       │ │
│  │    - Mean Reversion (50-tick MA)                        │ │
│  │    - Spread Volatility (100-tick avg)                   │ │
│  │    - HMM Regime (200-tick trend)                        │ │
│  │    - Transaction Cost                                   │ │
│  │    - Kelly Position Size                                │ │
│  │                                                          │ │
│  │ 3. Signal Generator                                     │ │
│  │    - Combines all 5 metrics                             │ │
│  │    - Generates ENTER_LONG when ALL conditions met       │ │
│  │                                                          │ │
│  │ 4. Position Manager                                     │ │
│  │    - Tracks open positions in memory                    │ │
│  │    - Creates new positions on signals                   │ │
│  │    - Monitors stop loss / take profit                   │ │
│  │    - Closes positions automatically                     │ │
│  │    - Writes all to database                             │ │
│  │                                                          │ │
│  │ 5. JSON Exporter                                        │ │
│  │    - Outputs trading_state.json every second            │ │
│  │    - Includes: ticks, positions, metrics, P&L           │ │
│  └──────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────┘
                              ↓
┌───────────────────────────────────────────────────────────────┐
│           KLDA-HFT TRADING TERMINAL (Dashboard)                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ Reads: trading_state.json (from C++ engine)             │ │
│  │                                                          │ │
│  │ DISPLAYS:                                               │ │
│  │  - Account Balance                                      │ │
│  │  - Open Positions (live P&L)                            │ │
│  │  - Live Market Data + Signals                           │ │
│  │  - Closed Trades History                                │ │
│  │  - Performance Statistics                               │ │
│  └──────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────┘
```

---

## DATABASE SCHEMA

### Positions Table
```sql
CREATE TABLE positions (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    entry_time TIMESTAMP NOT NULL,
    entry_price DOUBLE PRECISION NOT NULL,
    shares DOUBLE PRECISION NOT NULL,
    position_size DOUBLE PRECISION NOT NULL,  -- USD value
    stop_loss DOUBLE PRECISION NOT NULL,
    take_profit DOUBLE PRECISION NOT NULL,
    status VARCHAR(10) DEFAULT 'OPEN',  -- 'OPEN' or 'CLOSED'
    exit_time TIMESTAMP,
    exit_price DOUBLE PRECISION,
    pnl DOUBLE PRECISION,
    exit_reason VARCHAR(20)  -- 'TP', 'SL', 'MANUAL'
);
```

### Account State Table
```sql
CREATE TABLE account_state (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT NOW(),
    balance DOUBLE PRECISION NOT NULL,
    realized_pnl DOUBLE PRECISION NOT NULL,
    unrealized_pnl DOUBLE PRECISION NOT NULL,
    open_positions INT NOT NULL,
    total_trades INT NOT NULL
);
```

---

## C++ TRADING ENGINE LOGIC

### Main Loop (Every 1 second)

```cpp
while (true) {
    // 1. Read latest ticks from database
    auto ticks = fetch_latest_ticks();

    // 2. For each symbol
    for (const auto& tick : ticks) {
        string symbol = tick.symbol;
        double bid = tick.bid;
        double ask = tick.ask;

        // 3. Calculate Renaissance metrics
        auto metrics = calculate_metrics(symbol, bid, tick.spread);

        // 4. Check if we have open position
        if (has_open_position(symbol)) {
            // Monitor exit conditions
            check_exit(symbol, bid);
        }
        else {
            // Check entry signal
            if (metrics.signal && can_open_position()) {
                open_position(symbol, ask, metrics);
            }
        }
    }

    // 5. Export state to JSON
    export_trading_state();

    // 6. Sleep 1 second
    sleep(1);
}
```

### Position Opening Logic

```cpp
bool open_position(string symbol, double ask, Metrics metrics) {
    // Calculate position size (Kelly criterion)
    double risk_pct = 0.02;  // 2% risk
    double position_size = account_balance * risk_pct;
    double shares = position_size / ask;

    // Calculate stops
    double stop_loss = ask * 0.99;   // -1%
    double take_profit = ask * 1.005; // +0.5%

    // Create position
    Position pos(symbol, ask, shares, position_size, stop_loss, take_profit);

    // Save to database
    save_position_to_db(pos);

    // Track in memory
    open_positions[symbol] = pos;

    return true;
}
```

### Position Monitoring Logic

```cpp
void check_exit(string symbol, double current_price) {
    Position& pos = open_positions[symbol];

    string exit_reason = "";

    // Check take profit
    if (current_price >= pos.take_profit) {
        exit_reason = "TP";
    }
    // Check stop loss
    else if (current_price <= pos.stop_loss) {
        exit_reason = "SL";
    }

    if (!exit_reason.empty()) {
        close_position(symbol, current_price, exit_reason);
    }
}
```

### Position Closing Logic

```cpp
void close_position(string symbol, double exit_price, string reason) {
    Position& pos = open_positions[symbol];

    // Calculate P&L
    double pnl = (exit_price - pos.entry_price) * pos.shares;

    // Update account
    account_balance += pnl;

    // Update position
    pos.exit_price = exit_price;
    pos.pnl = pnl;
    pos.status = "CLOSED";
    pos.exit_reason = reason;

    // Update database
    update_position_in_db(pos);

    // Move to closed
    closed_positions.push_back(pos);
    open_positions.erase(symbol);
}
```

---

## JSON OUTPUT FORMAT

The C++ engine exports `trading_state.json` every second:

```json
{
    "timestamp": 1737376814,
    "account": {
        "balance": 10245.50,
        "initial_balance": 10000.00,
        "realized_pnl": 245.50,
        "unrealized_pnl": 12.30,
        "total_pnl": 257.80,
        "total_trades": 15,
        "wins": 8,
        "losses": 7,
        "win_rate": 53.3
    },
    "open_positions": [
        {
            "symbol": "NAS100",
            "entry_time": "2026-01-20 13:45:22",
            "entry_price": 25168.50,
            "current_price": 25172.80,
            "shares": 0.01,
            "position_size": 200.00,
            "stop_loss": 24916.82,
            "take_profit": 25294.27,
            "pnl": 4.30,
            "pnl_pct": 0.17
        }
    ],
    "market_data": [
        {
            "symbol": "NAS100",
            "bid": 25172.70,
            "ask": 25174.00,
            "spread": 13.00,
            "renaissance": {
                "mean_reversion": {
                    "value": -0.15,
                    "signal": true
                },
                "spread_volatility": {
                    "value": 12.5,
                    "signal": true
                },
                "hmm_regime": {
                    "value": "BULLISH",
                    "signal": true
                },
                "transaction_cost": {
                    "value": 6.60,
                    "signal": true
                },
                "kelly_size": {
                    "value": 1.98,
                    "signal": true
                },
                "overall_signal": "WAIT"
            }
        }
    ],
    "closed_trades": [...]
}
```

---

## TRADING TERMINAL DASHBOARD

### Features

1. **Account Overview**
   - Real-time balance
   - P&L (realized + unrealized)
   - Win rate
   - Total trades

2. **Open Positions Table**
   - Symbol
   - Entry time & price
   - Current price (live)
   - Position size
   - Stop loss / take profit levels
   - Current P&L ($ and %)
   - Status (winning/losing)

3. **Market Data & Signals**
   - Live bid/ask for all symbols
   - Renaissance 5 metrics per symbol
   - Entry signals (flashing when ENTER_LONG)

4. **Closed Trades History**
   - Last 20 trades
   - Entry/exit times & prices
   - P&L per trade
   - Win/loss result

---

## EXECUTION MODES

### Mode 1: SIMULATED (Default)
- C++ engine manages positions INTERNALLY
- NO connection to MT5
- Simulated fills at bid/ask
- Perfect for backtesting and development

### Mode 2: LIVE (MT5 Integration)
- C++ engine generates signals
- Sends orders to MT5 via Python bridge
- MT5 executes on real broker
- C++ tracks positions from MT5 confirmations

---

## HOW IT WORKS

1. **Ticks flow into database** (from MT5 Python bridge)
2. **C++ engine reads database** every second
3. **Calculates Renaissance metrics** from tick history
4. **Generates signals** when all 5 conditions met
5. **Opens position** (simulated or real via MT5)
6. **Stores position in database**
7. **Monitors position** every second
8. **Closes when TP/SL hit**
9. **Updates database and account balance**
10. **Exports JSON** for dashboard
11. **Dashboard displays** live positions and stats

---

## FILES TO CREATE/MODIFY

### C++ Backend

```
cpp-backend/
├── src/
│   ├── models/
│   │   └── position.h (CREATED)
│   ├── trading/
│   │   ├── engine.h (CREATE)
│   │   └── engine.cpp (CREATE)
│   └── main_trading.cpp (CREATE - new main with trading engine)
```

### Database

```sql
-- Run these SQL scripts
database/create_positions_table.sql (CREATE)
database/create_account_state_table.sql (CREATE)
```

### Dashboard

```
cpp-backend/
└── klda_trading_terminal.html (CREATE - professional terminal)
```

---

## DEPLOYMENT

### Step 1: Create Database Tables
```bash
psql -U postgres -d KLDA-HFT_Database < database/create_positions_table.sql
```

### Step 2: Rebuild C++ Backend
```bash
cd cpp-backend
docker-compose build
docker-compose up
```

### Step 3: Open Terminal
```
http://localhost:8082/klda_trading_terminal.html
```

---

## ADVANTAGES OF THIS ARCHITECTURE

✓ **Independent** - Not reliant on MT5 EA or platform
✓ **Portable** - C++ runs on Ubuntu in Docker, works anywhere
✓ **Fast** - C++ processes ticks at microsecond speed
✓ **Scalable** - Can handle thousands of ticks per second
✓ **Professional** - Hedge fund grade architecture
✓ **Traceable** - All positions stored in database
✓ **Testable** - Simulated mode for strategy development

---

## NEXT STEPS

1. Create `engine.cpp` implementation
2. Create `main_trading.cpp` entry point
3. Create database migration scripts
4. Build Docker image
5. Create professional trading terminal dashboard
6. Test in simulated mode
7. Deploy live with MT5 integration

This is the PROPER Renaissance Medallion-style architecture.
