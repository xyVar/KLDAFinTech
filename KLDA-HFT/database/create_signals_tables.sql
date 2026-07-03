-- ============================================
-- SIGNALS & PATTERNS TABLES
-- For Renaissance Trading Engine
-- ============================================

-- PATTERNS table (detected statistical patterns)
CREATE TABLE IF NOT EXISTS patterns (
    pattern_id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    pattern_type VARCHAR(50) NOT NULL,  -- 'mean_reversion', 'gap', 'momentum', etc.
    detected_at TIMESTAMPTZ(6) NOT NULL DEFAULT NOW(),

    -- Pattern parameters
    entry_price DECIMAL(18,8),
    trigger_price DECIMAL(18,8),
    strength DECIMAL(5,2),  -- 0-100 confidence score

    -- Statistical validation
    occurrences INTEGER,     -- How many times seen
    win_rate DECIMAL(5,2),   -- Historical win %
    p_value DECIMAL(6,4),    -- Statistical significance

    -- Pattern state
    status VARCHAR(20) DEFAULT 'ACTIVE',  -- ACTIVE, EXPIRED, TRIGGERED
    expires_at TIMESTAMPTZ(6)
);

CREATE INDEX idx_patterns_symbol ON patterns(symbol);
CREATE INDEX idx_patterns_detected ON patterns(detected_at);
CREATE INDEX idx_patterns_status ON patterns(status);


-- SIGNALS table (trading signals generated from patterns)
CREATE TABLE IF NOT EXISTS signals (
    signal_id SERIAL PRIMARY KEY,
    pattern_id INTEGER REFERENCES patterns(pattern_id),

    symbol VARCHAR(20) NOT NULL,
    signal_type VARCHAR(10) NOT NULL,  -- 'BUY', 'SELL', 'CLOSE'
    generated_at TIMESTAMPTZ(6) NOT NULL DEFAULT NOW(),

    -- Entry parameters
    entry_price DECIMAL(18,8) NOT NULL,
    stop_loss DECIMAL(18,8),
    take_profit DECIMAL(18,8),

    -- Position sizing
    position_size INTEGER,     -- Number of shares
    risk_amount DECIMAL(18,2), -- $ risk per trade
    kelly_fraction DECIMAL(5,4), -- Kelly Criterion fraction

    -- Signal state
    status VARCHAR(20) DEFAULT 'PENDING',  -- PENDING, EXECUTED, EXPIRED, CANCELLED
    executed_at TIMESTAMPTZ(6),
    execution_price DECIMAL(18,8),

    -- Outcome (filled after trade closes)
    closed_at TIMESTAMPTZ(6),
    close_price DECIMAL(18,8),
    profit_loss DECIMAL(18,2),
    win BOOLEAN
);

CREATE INDEX idx_signals_symbol ON signals(symbol);
CREATE INDEX idx_signals_generated ON signals(generated_at);
CREATE INDEX idx_signals_status ON signals(status);


-- TICK_EVENTS table (continuous backlog of tick analysis)
CREATE TABLE IF NOT EXISTS tick_events (
    event_id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    tick_time TIMESTAMPTZ(6) NOT NULL,

    -- Tick data snapshot
    bid DECIMAL(18,8),
    ask DECIMAL(18,8),
    spread DECIMAL(10,6),

    -- Renaissance metrics (calculated on this tick)
    ma50 DECIMAL(18,8),
    deviation_pct DECIMAL(8,4),
    regime VARCHAR(20),          -- BULLISH, BEARISH, NEUTRAL
    order_flow_imbalance DECIMAL(18,2),
    spread_volatility DECIMAL(8,4),
    transaction_cost DECIMAL(8,2),

    -- Overall signal
    overall_signal VARCHAR(20),  -- ENTER_LONG, WAIT, EXIT

    created_at TIMESTAMPTZ(6) NOT NULL DEFAULT NOW()
);

-- Convert to hypertable for time-series efficiency
SELECT create_hypertable('tick_events', 'tick_time', if_not_exists => TRUE);

CREATE INDEX idx_tick_events_symbol ON tick_events(symbol);
CREATE INDEX idx_tick_events_time ON tick_events(tick_time DESC);


-- VIEW: Recent signals per symbol
CREATE OR REPLACE VIEW recent_signals AS
SELECT
    symbol,
    signal_type,
    entry_price,
    position_size,
    status,
    generated_at,
    EXTRACT(EPOCH FROM (NOW() - generated_at)) as seconds_ago
FROM signals
WHERE status IN ('PENDING', 'EXECUTED')
ORDER BY generated_at DESC;


-- VIEW: Pattern performance
CREATE OR REPLACE VIEW pattern_performance AS
SELECT
    pattern_type,
    COUNT(*) as total_patterns,
    AVG(win_rate) as avg_win_rate,
    AVG(p_value) as avg_p_value,
    COUNT(CASE WHEN status = 'TRIGGERED' THEN 1 END) as triggered_count
FROM patterns
GROUP BY pattern_type
ORDER BY avg_win_rate DESC;
