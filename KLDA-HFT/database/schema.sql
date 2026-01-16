-- ============================================
-- KLDA-HFT DATABASE SCHEMA
-- Renaissance Philosophy: 50.75% win rate through 300,000 trades/day
-- ============================================

-- Create database (run this separately first)
-- CREATE DATABASE klda_hft;
-- \c klda_hft

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- ============================================
-- TABLE 1: TICKS (Raw tick data from MT5)
-- ============================================
-- Renaissance: "Tick data collection when providers only offered open/close"
-- Stores EVERY price change from broker

CREATE TABLE IF NOT EXISTS ticks (
    time TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    bid DECIMAL(10,5) NOT NULL,
    ask DECIMAL(10,5) NOT NULL,
    volume BIGINT NOT NULL,
    spread DECIMAL(10,5) NOT NULL
);

-- Convert to hypertable for time-series optimization
SELECT create_hypertable('ticks', 'time', if_not_exists => TRUE);

-- Index for fast symbol queries
CREATE INDEX IF NOT EXISTS idx_ticks_symbol_time ON ticks (symbol, time DESC);

-- Compression policy (compress data older than 7 days to save space)
ALTER TABLE ticks SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'symbol'
);

SELECT add_compression_policy('ticks', INTERVAL '7 days', if_not_exists => TRUE);

-- Retention policy (delete ticks older than 1 year to save space)
SELECT add_retention_policy('ticks', INTERVAL '1 year', if_not_exists => TRUE);

-- Expected volume: ~10M ticks/day, ~200GB/year compressed

-- ============================================
-- TABLE 2: BARS (OHLCV bar data - M1, M5, H1, D1, etc.)
-- ============================================
-- Your 575,816 existing bars + new bars from EA

CREATE TABLE IF NOT EXISTS bars (
    time TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(5) NOT NULL,  -- M1, M5, M15, M30, H1, H4, D1, W1, MN
    open DECIMAL(10,5) NOT NULL,
    high DECIMAL(10,5) NOT NULL,
    low DECIMAL(10,5) NOT NULL,
    close DECIMAL(10,5) NOT NULL,
    volume BIGINT NOT NULL,
    spread DECIMAL(10,5) NOT NULL
);

SELECT create_hypertable('bars', 'time', if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS idx_bars_symbol_tf_time ON bars (symbol, timeframe, time DESC);

-- Compression for bars older than 30 days
ALTER TABLE bars SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'symbol, timeframe'
);

SELECT add_compression_policy('bars', INTERVAL '30 days', if_not_exists => TRUE);

-- Expected volume: ~220k bars/day, ~18GB/year

-- ============================================
-- TABLE 3: INDICATORS (Technical indicators: MA, RSI, ATR, HMM states)
-- ============================================
-- Renaissance: "Dynamic and adaptive, adjusting real-time"

CREATE TABLE IF NOT EXISTS indicators (
    time TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(5) NOT NULL,
    -- Moving averages
    ma20 DECIMAL(10,5),
    ma50 DECIMAL(10,5),
    ma200 DECIMAL(10,5),
    -- Volatility
    atr14 DECIMAL(10,5),
    bb_upper DECIMAL(10,5),  -- Bollinger Bands
    bb_lower DECIMAL(10,5),
    -- Momentum
    rsi14 DECIMAL(5,2),
    -- Volume
    volume_ma20 BIGINT,
    -- HMM (Hidden Markov Model) state
    hmm_state INT,            -- 0=bearish, 1=neutral, 2=bullish
    hmm_confidence DECIMAL(5,4),
    -- Custom indicators stored as JSON
    metadata JSONB
);

SELECT create_hypertable('indicators', 'time', if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS idx_indicators_symbol_tf_time ON indicators (symbol, timeframe, time DESC);

-- Compression
ALTER TABLE indicators SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'symbol, timeframe'
);

SELECT add_compression_policy('indicators', INTERVAL '30 days', if_not_exists => TRUE);

-- Expected volume: ~220k rows/day, ~30GB/year

-- ============================================
-- TABLE 4: SIGNALS (Pattern detection results)
-- ============================================
-- Renaissance: "Over half the signals discovered were ones they couldn't explain"

CREATE TABLE IF NOT EXISTS signals (
    signal_id BIGSERIAL PRIMARY KEY,
    time TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(5) NOT NULL,
    signal_type VARCHAR(50) NOT NULL,  -- mean_reversion, hmm_regime, gap_fill, momentum, etc.
    direction VARCHAR(5) NOT NULL,     -- BUY or SELL
    confidence DECIMAL(5,4) NOT NULL,  -- 0.5075 = 50.75% win rate
    entry_price DECIMAL(10,5) NOT NULL,
    stop_loss DECIMAL(10,5) NOT NULL,
    take_profit DECIMAL(10,5) NOT NULL,
    position_size DECIMAL(10,5) NOT NULL,  -- Kelly Criterion calculated
    expected_value DECIMAL(10,5),          -- Expected profit
    metadata JSONB                         -- Store pattern-specific data
);

SELECT create_hypertable('signals', 'time', if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS idx_signals_symbol_time ON signals (symbol, time DESC);
CREATE INDEX IF NOT EXISTS idx_signals_type ON signals (signal_type);
CREATE INDEX IF NOT EXISTS idx_signals_confidence ON signals (confidence DESC);

-- Expected volume: 300k signals/day, ~36GB/year

-- ============================================
-- TABLE 5: TRADES (Executed orders)
-- ============================================
-- Renaissance: "150,000-300,000 daily trades"

CREATE TABLE IF NOT EXISTS trades (
    trade_id BIGSERIAL PRIMARY KEY,
    signal_id BIGINT,                      -- Link to signals table
    time TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    direction VARCHAR(5) NOT NULL,         -- BUY or SELL
    entry_price DECIMAL(10,5) NOT NULL,
    entry_time TIMESTAMPTZ NOT NULL,
    exit_price DECIMAL(10,5),
    exit_time TIMESTAMPTZ,
    stop_loss DECIMAL(10,5) NOT NULL,
    take_profit DECIMAL(10,5) NOT NULL,
    position_size DECIMAL(10,5) NOT NULL,
    commission DECIMAL(10,5) NOT NULL,      -- "The Devil" - transaction costs
    slippage DECIMAL(10,5) NOT NULL,        -- Actual vs theoretical execution
    pnl DECIMAL(10,5),                      -- Profit/loss in $
    pnl_pct DECIMAL(10,5),                  -- Profit/loss in %
    holding_period_seconds INT,             -- Renaissance: "1-2 days average"
    status VARCHAR(20) NOT NULL             -- OPEN, CLOSED, STOPPED_OUT, TAKE_PROFIT
);

SELECT create_hypertable('trades', 'time', if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS idx_trades_symbol_time ON trades (symbol, time DESC);
CREATE INDEX IF NOT EXISTS idx_trades_status ON trades (status);
CREATE INDEX IF NOT EXISTS idx_trades_signal_id ON trades (signal_id);
CREATE INDEX IF NOT EXISTS idx_trades_entry_time ON trades (entry_time DESC);

-- Expected volume: 300k trades/day, ~55GB/year

-- ============================================
-- TABLE 6: PORTFOLIO (Real-time position state)
-- ============================================
-- Renaissance: "4,000 long and 4,000 short positions simultaneously"

CREATE TABLE IF NOT EXISTS portfolio (
    symbol VARCHAR(20) PRIMARY KEY,
    position DECIMAL(10,5) NOT NULL,       -- Positive = long, negative = short
    avg_entry_price DECIMAL(10,5) NOT NULL,
    current_price DECIMAL(10,5) NOT NULL,
    unrealized_pnl DECIMAL(10,5) NOT NULL,
    realized_pnl_today DECIMAL(10,5) NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_portfolio_updated ON portfolio (updated_at DESC);

-- Expected volume: ~8,000 rows max (4k long + 4k short)

-- ============================================
-- TABLE 7: PERFORMANCE (Daily/hourly metrics)
-- ============================================
-- Renaissance: "66% average annual gross returns"

CREATE TABLE IF NOT EXISTS performance (
    time TIMESTAMPTZ NOT NULL,
    period VARCHAR(10) NOT NULL,          -- HOURLY, DAILY, WEEKLY, MONTHLY
    total_trades INT NOT NULL,
    winning_trades INT NOT NULL,
    losing_trades INT NOT NULL,
    win_rate DECIMAL(5,4) NOT NULL,       -- Target: 0.5075 (50.75%)
    gross_pnl DECIMAL(15,5) NOT NULL,
    net_pnl DECIMAL(15,5) NOT NULL,
    total_commission DECIMAL(15,5) NOT NULL,
    total_slippage DECIMAL(15,5) NOT NULL,
    sharpe_ratio DECIMAL(10,5),           -- Target: >7.0 like Renaissance
    max_drawdown DECIMAL(10,5),
    avg_holding_period_seconds INT,
    total_volume DECIMAL(15,5),
    metadata JSONB
);

SELECT create_hypertable('performance', 'time', if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS idx_performance_period_time ON performance (period, time DESC);

-- Expected volume: ~25 rows/day (24 hourly + 1 daily)

-- ============================================
-- CONTINUOUS AGGREGATES (Auto-calculated views)
-- ============================================

-- Auto-aggregate 5-minute bars from ticks
CREATE MATERIALIZED VIEW IF NOT EXISTS bars_m5
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('5 minutes', time) AS time,
    symbol,
    'M5' as timeframe,
    FIRST(bid, time) as open,
    MAX(bid) as high,
    MIN(bid) as low,
    LAST(bid, time) as close,
    SUM(volume) as volume,
    AVG(spread) as spread
FROM ticks
GROUP BY time_bucket('5 minutes', time), symbol;

-- Refresh M5 bars every minute
SELECT add_continuous_aggregate_policy('bars_m5',
    start_offset => INTERVAL '1 hour',
    end_offset => INTERVAL '1 minute',
    schedule_interval => INTERVAL '1 minute',
    if_not_exists => TRUE);

-- Auto-calculate hourly performance
CREATE MATERIALIZED VIEW IF NOT EXISTS performance_hourly
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', exit_time) AS time,
    'HOURLY' as period,
    COUNT(*)::INT as total_trades,
    SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END)::INT as winning_trades,
    SUM(CASE WHEN pnl <= 0 THEN 1 ELSE 0 END)::INT as losing_trades,
    AVG(CASE WHEN pnl > 0 THEN 1.0 ELSE 0.0 END)::DECIMAL(5,4) as win_rate,
    SUM(pnl + commission + slippage)::DECIMAL(15,5) as gross_pnl,
    SUM(pnl)::DECIMAL(15,5) as net_pnl,
    SUM(commission)::DECIMAL(15,5) as total_commission,
    SUM(slippage)::DECIMAL(15,5) as total_slippage,
    0::DECIMAL(10,5) as sharpe_ratio,
    0::DECIMAL(10,5) as max_drawdown,
    AVG(holding_period_seconds)::INT as avg_holding_period_seconds,
    SUM(position_size * entry_price)::DECIMAL(15,5) as total_volume,
    NULL::JSONB as metadata
FROM trades
WHERE status = 'CLOSED' AND exit_time IS NOT NULL
GROUP BY time_bucket('1 hour', exit_time);

-- Refresh hourly performance every hour
SELECT add_continuous_aggregate_policy('performance_hourly',
    start_offset => INTERVAL '1 day',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists => TRUE);

-- ============================================
-- HELPER FUNCTIONS
-- ============================================

-- Function to calculate current win rate
CREATE OR REPLACE FUNCTION get_win_rate(start_date TIMESTAMPTZ DEFAULT CURRENT_DATE)
RETURNS TABLE (
    total_trades BIGINT,
    wins BIGINT,
    losses BIGINT,
    win_rate DECIMAL,
    status TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*) as total_trades,
        SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins,
        SUM(CASE WHEN pnl <= 0 THEN 1 ELSE 0 END) as losses,
        ROUND(AVG(CASE WHEN pnl > 0 THEN 1.0 ELSE 0.0 END), 4) as win_rate,
        CASE
            WHEN AVG(CASE WHEN pnl > 0 THEN 1.0 ELSE 0.0 END) >= 0.5075 THEN '✓ ABOVE TARGET'
            ELSE '✗ BELOW TARGET'
        END as status
    FROM trades
    WHERE status = 'CLOSED'
      AND exit_time >= start_date;
END;
$$ LANGUAGE plpgsql;

-- Function to get portfolio summary
CREATE OR REPLACE FUNCTION get_portfolio_summary()
RETURNS TABLE (
    total_positions BIGINT,
    long_positions BIGINT,
    short_positions BIGINT,
    total_unrealized_pnl DECIMAL,
    total_realized_pnl_today DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*) as total_positions,
        SUM(CASE WHEN position > 0 THEN 1 ELSE 0 END) as long_positions,
        SUM(CASE WHEN position < 0 THEN 1 ELSE 0 END) as short_positions,
        SUM(unrealized_pnl) as total_unrealized_pnl,
        SUM(realized_pnl_today) as total_realized_pnl_today
    FROM portfolio
    WHERE position != 0;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- GRANT PERMISSIONS (adjust username as needed)
-- ============================================

-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_username;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO your_username;

-- ============================================
-- SCHEMA CREATION COMPLETE
-- ============================================

-- Next steps:
-- 1. Run this file: psql -U postgres -d klda_hft -f schema.sql
-- 2. Import historical data: seed_historical_data.sql
-- 3. Test queries: test_queries.sql
