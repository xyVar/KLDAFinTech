# Available Data Fields from MT5 Server

**Last Updated:** 2025-12-23
**Data Source:** Pepperstone MT5 Real-Time Server

This document lists ALL data fields available from the MT5 broker server that can be accessed and extracted.

---

## Price Data Fields

### Basic Price Information
```
BID                 - Current bid price (sell price)
ASK                 - Current ask price (buy price)
LAST                - Last executed deal price
SPREAD              - Difference between Ask and Bid (in points)
```

**MQL5 Access:**
```mql5
double bid = SymbolInfoDouble(symbol, SYMBOL_BID);
double ask = SymbolInfoDouble(symbol, SYMBOL_ASK);
double last = SymbolInfoDouble(symbol, SYMBOL_LAST);
int spread = (int)SymbolInfoInteger(symbol, SYMBOL_SPREAD);
```

---

### Daily Price Range
```
HIGH                - Highest price of current day
LOW                 - Lowest price of current day
DAILY CHANGE        - Price change from day open (in %)
```

**MQL5 Access:**
```mql5
double daily_high = iHigh(symbol, PERIOD_D1, 0);
double daily_low = iLow(symbol, PERIOD_D1, 0);
double daily_open = iOpen(symbol, PERIOD_D1, 0);
double daily_change_pct = ((bid - daily_open) / daily_open) * 100;
```

---

### Bid Price Range
```
BID HIGH            - Maximum bid price for the day
BID LOW             - Minimum bid price for the day
```

**MQL5 Access:**
```mql5
double bid_high = SymbolInfoDouble(symbol, SYMBOL_BIDHIGH);
double bid_low = SymbolInfoDouble(symbol, SYMBOL_BIDLOW);
```

---

### Ask Price Range
```
ASK HIGH            - Maximum ask price for the day
ASK LOW             - Minimum ask price for the day
```

**MQL5 Access:**
```mql5
double ask_high = SymbolInfoDouble(symbol, SYMBOL_ASKHIGH);
double ask_low = SymbolInfoDouble(symbol, SYMBOL_ASKLOW);
```

---

### Last Deal Price Range
```
LAST HIGH           - Highest deal price for the day
LAST LOW            - Lowest deal price for the day
```

**MQL5 Access:**
```mql5
double last_high = SymbolInfoDouble(symbol, SYMBOL_LASTHIGH);
double last_low = SymbolInfoDouble(symbol, SYMBOL_LASTLOW);
```

---

## Volume Data Fields

### Current Volume
```
VOLUME              - Volume of the last deal
VOLUME HIGH         - Maximum volume for a single deal today
VOLUME LOW          - Minimum volume for a single deal today
```

**MQL5 Access:**
```mql5
long volume = SymbolInfoInteger(symbol, SYMBOL_VOLUME);
long volume_high = SymbolInfoInteger(symbol, SYMBOL_VOLUMEHIGH);
long volume_low = SymbolInfoInteger(symbol, SYMBOL_VOLUMELOW);
long volume_real = SymbolInfoDouble(symbol, SYMBOL_VOLUME_REAL);
```

---

## Market Depth / Order Book

### Deals Information
```
DEALS               - Number of deals in current session
DEALS VOLUME        - Total volume of all deals
```

**MQL5 Access:**
```mql5
long deals = SymbolInfoInteger(symbol, SYMBOL_SESSION_DEALS);
double deals_volume = SymbolInfoDouble(symbol, SYMBOL_SESSION_VOLUME);
```

---

### Order Flow
```
BUY ORDERS          - Number of current buy orders
BUY VOLUME          - Total volume of buy orders
SELL ORDERS         - Number of current sell orders
SELL VOLUME         - Total volume of sell orders
```

**MQL5 Access:**
```mql5
long buy_orders = SymbolInfoInteger(symbol, SYMBOL_SESSION_BUY_ORDERS);
double buy_volume = SymbolInfoDouble(symbol, SYMBOL_SESSION_BUY_ORDERS_VOLUME);
long sell_orders = SymbolInfoInteger(symbol, SYMBOL_SESSION_SELL_ORDERS);
double sell_volume = SymbolInfoDouble(symbol, SYMBOL_SESSION_SELL_ORDERS_VOLUME);
```

---

### Turnover
```
TURNOVER            - Total monetary turnover for the session
```

**MQL5 Access:**
```mql5
double turnover = SymbolInfoDouble(symbol, SYMBOL_SESSION_TURNOVER);
```

---

## Options & Greeks (if available)

### Options Data
```
OPEN INTEREST       - Number of open positions/contracts
SETTLEMENT PRICE    - Settlement price for futures/options
THEORETICAL PRICE   - Theoretical fair value price
```

**MQL5 Access:**
```mql5
double open_interest = SymbolInfoDouble(symbol, SYMBOL_SESSION_INTEREST);
double settlement = SymbolInfoDouble(symbol, SYMBOL_SETTLEMENT_PRICE);
double theoretical = SymbolInfoDouble(symbol, SYMBOL_THEORETICAL_PRICE);
```

---

### Greeks (Options Trading)
```
DELTA               - Rate of change of option price vs underlying
GAMMA               - Rate of change of delta
THETA               - Time decay of option value
VEGA                - Sensitivity to volatility changes
RHO                 - Sensitivity to interest rate changes
OMEGA               - Leverage effect
```

**MQL5 Access:**
```mql5
double delta = SymbolInfoDouble(symbol, SYMBOL_OPTION_DELTA);
double gamma = SymbolInfoDouble(symbol, SYMBOL_OPTION_GAMMA);
double theta = SymbolInfoDouble(symbol, SYMBOL_OPTION_THETA);
double vega = SymbolInfoDouble(symbol, SYMBOL_OPTION_VEGA);
double rho = SymbolInfoDouble(symbol, SYMBOL_OPTION_RHO);
double omega = SymbolInfoDouble(symbol, SYMBOL_OPTION_OMEGA);
```

---

### Volatility
```
VOLATILITY          - Current implied volatility
```

**MQL5 Access:**
```mql5
double volatility = SymbolInfoDouble(symbol, SYMBOL_VOLATILITY);
```

---

## Margin & Risk Data

### Margin Requirements
```
INITIAL MARGIN      - Initial margin required to open position
MAINTENANCE MARGIN  - Maintenance margin to keep position open
INITIAL BUY MARGIN  - Initial margin for buy positions
INITIAL SELL MARGIN - Initial margin for sell positions
```

**MQL5 Access:**
```mql5
double initial_margin = SymbolInfoDouble(symbol, SYMBOL_MARGIN_INITIAL);
double maintenance_margin = SymbolInfoDouble(symbol, SYMBOL_MARGIN_MAINTENANCE);
double margin_buy = SymbolInfoDouble(symbol, SYMBOL_MARGIN_BUY);
double margin_sell = SymbolInfoDouble(symbol, SYMBOL_MARGIN_SELL);
```

---

### Limit Information
```
LOWER LIMIT         - Minimum allowed price
UPPER LIMIT         - Maximum allowed price
```

**MQL5 Access:**
```mql5
double price_limit_min = SymbolInfoDouble(symbol, SYMBOL_SESSION_PRICE_LIMIT_MIN);
double price_limit_max = SymbolInfoDouble(symbol, SYMBOL_SESSION_PRICE_LIMIT_MAX);
```

---

## Interest & Financing

### Accrued Interest
```
ACCRUED INTEREST    - Interest accumulated on position
```

**MQL5 Access:**
```mql5
double accrued_interest = SymbolInfoDouble(symbol, SYMBOL_ACCRUED_INTEREST);
```

---

## Time Information

### Timestamps
```
TIME                - Time of last quote
SOURCE              - Data source identifier
```

**MQL5 Access:**
```mql5
datetime last_time = (datetime)SymbolInfoInteger(symbol, SYMBOL_TIME);
long time_msc = SymbolInfoInteger(symbol, SYMBOL_TIME_MSC);
```

---

## Session Information

### Session Limits
```
SESSION OPEN        - Session opening price
SESSION CLOSE       - Session closing price
SESSION HIGH        - Session highest price
SESSION LOW         - Session lowest price
```

**MQL5 Access:**
```mql5
double session_open = SymbolInfoDouble(symbol, SYMBOL_SESSION_OPEN);
double session_close = SymbolInfoDouble(symbol, SYMBOL_SESSION_CLOSE);
double session_high = SymbolInfoDouble(symbol, SYMBOL_SESSION_PRICE_LIMIT_MAX);
double session_low = SymbolInfoDouble(symbol, SYMBOL_SESSION_PRICE_LIMIT_MIN);
```

---

## Trading Status Information

### Trading Permissions
```
TRADE MODE          - Full trading / Close only / Disabled
EXECUTION MODE      - Market / Exchange / Request
TRADE STOPS LEVEL   - Minimum distance for stops
TRADE FREEZE LEVEL  - Freeze distance before expiration
```

**MQL5 Access:**
```mql5
ENUM_SYMBOL_TRADE_MODE trade_mode = (ENUM_SYMBOL_TRADE_MODE)SymbolInfoInteger(symbol, SYMBOL_TRADE_MODE);
ENUM_SYMBOL_TRADE_EXECUTION exec_mode = (ENUM_SYMBOL_TRADE_EXECUTION)SymbolInfoInteger(symbol, SYMBOL_TRADE_EXEMODE);
int stops_level = (int)SymbolInfoInteger(symbol, SYMBOL_TRADE_STOPS_LEVEL);
int freeze_level = (int)SymbolInfoInteger(symbol, SYMBOL_TRADE_FREEZE_LEVEL);
```

---

## Complete MQL5 Function to Extract ALL Data

```mql5
//+------------------------------------------------------------------+
//| Structure to hold all available market data                     |
//+------------------------------------------------------------------+
struct MarketDataSnapshot
{
    // Timestamp
    datetime timestamp;
    string symbol;

    // Price data
    double bid;
    double ask;
    double last;
    int spread;

    // Daily range
    double high;
    double low;
    double daily_change_pct;

    // Bid/Ask ranges
    double bid_high;
    double bid_low;
    double ask_high;
    double ask_low;
    double last_high;
    double last_low;

    // Volume data
    long volume;
    long volume_high;
    long volume_low;
    double volume_real;

    // Market depth
    long deals;
    double deals_volume;
    long buy_orders;
    double buy_volume;
    long sell_orders;
    double sell_volume;
    double turnover;

    // Options data (if available)
    double open_interest;
    double settlement_price;
    double theoretical_price;

    // Greeks (if available)
    double delta;
    double gamma;
    double theta;
    double vega;
    double rho;
    double omega;
    double volatility;

    // Margin data
    double initial_margin;
    double maintenance_margin;
    double margin_buy;
    double margin_sell;

    // Session limits
    double price_limit_min;
    double price_limit_max;

    // Trading status
    bool is_trading;
};

//+------------------------------------------------------------------+
//| Extract complete market data snapshot for a symbol              |
//+------------------------------------------------------------------+
MarketDataSnapshot GetCompleteMarketData(string symbol)
{
    MarketDataSnapshot data;

    data.timestamp = TimeCurrent();
    data.symbol = symbol;

    // Price data
    data.bid = SymbolInfoDouble(symbol, SYMBOL_BID);
    data.ask = SymbolInfoDouble(symbol, SYMBOL_ASK);
    data.last = SymbolInfoDouble(symbol, SYMBOL_LAST);
    data.spread = (int)SymbolInfoInteger(symbol, SYMBOL_SPREAD);

    // Daily range
    data.high = iHigh(symbol, PERIOD_D1, 0);
    data.low = iLow(symbol, PERIOD_D1, 0);
    double daily_open = iOpen(symbol, PERIOD_D1, 0);
    data.daily_change_pct = ((data.bid - daily_open) / daily_open) * 100;

    // Bid/Ask ranges
    data.bid_high = SymbolInfoDouble(symbol, SYMBOL_BIDHIGH);
    data.bid_low = SymbolInfoDouble(symbol, SYMBOL_BIDLOW);
    data.ask_high = SymbolInfoDouble(symbol, SYMBOL_ASKHIGH);
    data.ask_low = SymbolInfoDouble(symbol, SYMBOL_ASKLOW);
    data.last_high = SymbolInfoDouble(symbol, SYMBOL_LASTHIGH);
    data.last_low = SymbolInfoDouble(symbol, SYMBOL_LASTLOW);

    // Volume data
    data.volume = SymbolInfoInteger(symbol, SYMBOL_VOLUME);
    data.volume_high = SymbolInfoInteger(symbol, SYMBOL_VOLUMEHIGH);
    data.volume_low = SymbolInfoInteger(symbol, SYMBOL_VOLUMELOW);
    data.volume_real = SymbolInfoDouble(symbol, SYMBOL_VOLUME_REAL);

    // Market depth
    data.deals = SymbolInfoInteger(symbol, SYMBOL_SESSION_DEALS);
    data.deals_volume = SymbolInfoDouble(symbol, SYMBOL_SESSION_VOLUME);
    data.buy_orders = SymbolInfoInteger(symbol, SYMBOL_SESSION_BUY_ORDERS);
    data.buy_volume = SymbolInfoDouble(symbol, SYMBOL_SESSION_BUY_ORDERS_VOLUME);
    data.sell_orders = SymbolInfoInteger(symbol, SYMBOL_SESSION_SELL_ORDERS);
    data.sell_volume = SymbolInfoDouble(symbol, SYMBOL_SESSION_SELL_ORDERS_VOLUME);
    data.turnover = SymbolInfoDouble(symbol, SYMBOL_SESSION_TURNOVER);

    // Options data
    data.open_interest = SymbolInfoDouble(symbol, SYMBOL_SESSION_INTEREST);
    data.settlement_price = SymbolInfoDouble(symbol, SYMBOL_SETTLEMENT_PRICE);
    data.theoretical_price = SymbolInfoDouble(symbol, SYMBOL_THEORETICAL_PRICE);

    // Greeks
    data.delta = SymbolInfoDouble(symbol, SYMBOL_OPTION_DELTA);
    data.gamma = SymbolInfoDouble(symbol, SYMBOL_OPTION_GAMMA);
    data.theta = SymbolInfoDouble(symbol, SYMBOL_OPTION_THETA);
    data.vega = SymbolInfoDouble(symbol, SYMBOL_OPTION_VEGA);
    data.rho = SymbolInfoDouble(symbol, SYMBOL_OPTION_RHO);
    data.omega = SymbolInfoDouble(symbol, SYMBOL_OPTION_OMEGA);
    data.volatility = SymbolInfoDouble(symbol, SYMBOL_VOLATILITY);

    // Margin data
    data.initial_margin = SymbolInfoDouble(symbol, SYMBOL_MARGIN_INITIAL);
    data.maintenance_margin = SymbolInfoDouble(symbol, SYMBOL_MARGIN_MAINTENANCE);
    data.margin_buy = SymbolInfoDouble(symbol, SYMBOL_MARGIN_BUY);
    data.margin_sell = SymbolInfoDouble(symbol, SYMBOL_MARGIN_SELL);

    // Session limits
    data.price_limit_min = SymbolInfoDouble(symbol, SYMBOL_SESSION_PRICE_LIMIT_MIN);
    data.price_limit_max = SymbolInfoDouble(symbol, SYMBOL_SESSION_PRICE_LIMIT_MAX);

    // Trading status
    ENUM_SYMBOL_TRADE_MODE trade_mode = (ENUM_SYMBOL_TRADE_MODE)SymbolInfoInteger(symbol, SYMBOL_TRADE_MODE);
    data.is_trading = (trade_mode == SYMBOL_TRADE_MODE_FULL);

    return data;
}

//+------------------------------------------------------------------+
//| Write data snapshot to CSV file                                 |
//+------------------------------------------------------------------+
void WriteMarketDataToCSV(MarketDataSnapshot &data, string filename)
{
    int file_handle = FileOpen(filename, FILE_WRITE|FILE_CSV|FILE_COMMON);

    if(file_handle != INVALID_HANDLE)
    {
        // Write header (only on first write)
        if(FileSize(file_handle) == 0)
        {
            FileWrite(file_handle,
                "Timestamp", "Symbol",
                "Bid", "Ask", "Last", "Spread",
                "High", "Low", "DailyChange%",
                "BidHigh", "BidLow", "AskHigh", "AskLow", "LastHigh", "LastLow",
                "Volume", "VolumeHigh", "VolumeLow", "VolumeReal",
                "Deals", "DealsVolume",
                "BuyOrders", "BuyVolume", "SellOrders", "SellVolume", "Turnover",
                "OpenInterest", "SettlementPrice", "TheoreticalPrice",
                "Delta", "Gamma", "Theta", "Vega", "Rho", "Omega", "Volatility",
                "InitialMargin", "MaintenanceMargin", "MarginBuy", "MarginSell",
                "PriceLimitMin", "PriceLimitMax",
                "IsTrading"
            );
        }

        // Write data
        FileWrite(file_handle,
            TimeToString(data.timestamp), data.symbol,
            data.bid, data.ask, data.last, data.spread,
            data.high, data.low, data.daily_change_pct,
            data.bid_high, data.bid_low, data.ask_high, data.ask_low, data.last_high, data.last_low,
            data.volume, data.volume_high, data.volume_low, data.volume_real,
            data.deals, data.deals_volume,
            data.buy_orders, data.buy_volume, data.sell_orders, data.sell_volume, data.turnover,
            data.open_interest, data.settlement_price, data.theoretical_price,
            data.delta, data.gamma, data.theta, data.vega, data.rho, data.omega, data.volatility,
            data.initial_margin, data.maintenance_margin, data.margin_buy, data.margin_sell,
            data.price_limit_min, data.price_limit_max,
            data.is_trading ? "TRUE" : "FALSE"
        );

        FileClose(file_handle);
    }
}
```

---

## Daily Extract Example

**To extract all data daily for all instruments:**

```mql5
void OnTimer()
{
    // Run once per day at specific time
    datetime now = TimeCurrent();
    if(TimeHour(now) == 23 && TimeMinute(now) == 55)  // 23:55 daily
    {
        string symbols[] = {
            "VIX",
            "ORCL.US-24",
            "AMD.US-24",
            "TSM.US",
            "NVDA.US-24",
            "MSFT.US-24",
            // ... add all symbols
        };

        string date_str = TimeToString(now, TIME_DATE);
        string filename = "MarketData_" + date_str + ".csv";

        for(int i = 0; i < ArraySize(symbols); i++)
        {
            MarketDataSnapshot data = GetCompleteMarketData(symbols[i]);
            WriteMarketDataToCSV(data, filename);
        }

        Print("Daily market data extracted to: ", filename);
    }
}
```

---

## CSV File Storage Location

**Files saved by EA go to:**
```
C:\Users\PC\AppData\Roaming\MetaQuotes\Terminal\73B7A2420D6397DFF9014A20F1201F97\MQL5\Files\
```

**With FILE_COMMON flag:**
```
C:\Users\PC\AppData\Roaming\MetaQuotes\Terminal\Common\Files\
```

---

## Summary

**You have access to these data categories:**

1. ✅ **Price Data** (Bid, Ask, Last, Spread, High, Low)
2. ✅ **Volume Data** (Volume, Volume High/Low, Real Volume)
3. ✅ **Market Depth** (Deals, Buy/Sell Orders, Turnover)
4. ✅ **Options & Greeks** (Delta, Gamma, Theta, Vega, Volatility)
5. ✅ **Margin Requirements** (Initial, Maintenance, Buy/Sell)
6. ✅ **Session Data** (Open, Close, Limits, Interest)
7. ✅ **Time & Status** (Timestamps, Trading Status)

**All data can be:**
- Extracted in real-time
- Written to CSV files
- Exported daily/hourly/per-tick
- Linked to external systems

---

**This is the complete range of data available from MT5 server that you can access and extract.**
