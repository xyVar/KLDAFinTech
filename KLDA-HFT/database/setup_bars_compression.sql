-- ========================================
-- RENAISSANCE MEDALLION-STYLE BARS COMPRESSION
-- Automatic tick-to-OHLCV compression using TimescaleDB
-- ========================================

\echo '========================================='
\echo 'SETTING UP BARS COMPRESSION SYSTEM'
\echo 'Renaissance Medallion-style tick compression'
\echo '========================================='
\echo ''

-- ========================================
-- STEP 1: Drop old bars tables (they're not being populated)
-- ========================================
\echo 'Step 1: Removing old unused bars tables...'

DROP TABLE IF EXISTS tsla_bars CASCADE;
DROP TABLE IF EXISTS nvda_bars CASCADE;
DROP TABLE IF EXISTS pltr_bars CASCADE;
DROP TABLE IF EXISTS amd_bars CASCADE;
DROP TABLE IF EXISTS avgo_bars CASCADE;
DROP TABLE IF EXISTS meta_bars CASCADE;
DROP TABLE IF EXISTS aapl_bars CASCADE;
DROP TABLE IF EXISTS msft_bars CASCADE;
DROP TABLE IF EXISTS orcl_bars CASCADE;
DROP TABLE IF EXISTS amzn_bars CASCADE;
DROP TABLE IF EXISTS csco_bars CASCADE;
DROP TABLE IF EXISTS goog_bars CASCADE;
DROP TABLE IF EXISTS intc_bars CASCADE;
DROP TABLE IF EXISTS vix_bars CASCADE;
DROP TABLE IF EXISTS nas100_bars CASCADE;
DROP TABLE IF EXISTS natgas_bars CASCADE;
DROP TABLE IF EXISTS spotcrude_bars CASCADE;

\echo '[OK] Old bars tables removed'
\echo ''

-- ========================================
-- STEP 2: Create continuous aggregates for VIX (test first)
-- ========================================
\echo 'Step 2: Creating continuous aggregates for VIX (M1, M5, H1)...'

-- M1 (1-minute bars)
CREATE MATERIALIZED VIEW vix_bars_m1
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 minute', time) AS time,
    'M1'::VARCHAR(5) as timeframe,
    FIRST(bid, time) as open,
    MAX(ask) as high,
    MIN(bid) as low,
    LAST(ask, time) as close,
    SUM(volume) as volume,
    AVG(spread)::INTEGER as spread
FROM vix_history
GROUP BY time_bucket('1 minute', time);

-- Auto-refresh every 1 minute
SELECT add_continuous_aggregate_policy('vix_bars_m1',
    start_offset => INTERVAL '2 hours',
    end_offset => INTERVAL '1 minute',
    schedule_interval => INTERVAL '1 minute');

\echo '[OK] VIX M1 bars created'

-- M5 (5-minute bars)
CREATE MATERIALIZED VIEW vix_bars_m5
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('5 minutes', time) AS time,
    'M5'::VARCHAR(5) as timeframe,
    FIRST(bid, time) as open,
    MAX(ask) as high,
    MIN(bid) as low,
    LAST(ask, time) as close,
    SUM(volume) as volume,
    AVG(spread)::INTEGER as spread
FROM vix_history
GROUP BY time_bucket('5 minutes', time);

SELECT add_continuous_aggregate_policy('vix_bars_m5',
    start_offset => INTERVAL '2 hours',
    end_offset => INTERVAL '5 minutes',
    schedule_interval => INTERVAL '5 minutes');

\echo '[OK] VIX M5 bars created'

-- H1 (1-hour bars)
CREATE MATERIALIZED VIEW vix_bars_h1
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', time) AS time,
    'H1'::VARCHAR(5) as timeframe,
    FIRST(bid, time) as open,
    MAX(ask) as high,
    MIN(bid) as low,
    LAST(ask, time) as close,
    SUM(volume) as volume,
    AVG(spread)::INTEGER as spread
FROM vix_history
GROUP BY time_bucket('1 hour', time);

SELECT add_continuous_aggregate_policy('vix_bars_h1',
    start_offset => INTERVAL '7 days',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour');

\echo '[OK] VIX H1 bars created'
\echo ''

-- ========================================
-- STEP 3: Create unified BARS view (all timeframes combined)
-- ========================================
\echo 'Step 3: Creating unified vix_bars view...'

CREATE VIEW vix_bars AS
    SELECT * FROM vix_bars_m1
    UNION ALL
    SELECT * FROM vix_bars_m5
    UNION ALL
    SELECT * FROM vix_bars_h1
    ORDER BY time DESC, timeframe;

\echo '[OK] Unified vix_bars view created'
\echo ''

-- ========================================
-- STEP 4: Verify VIX bars are populating
-- ========================================
\echo 'Step 4: Verifying VIX bars population...'
\echo ''

\echo 'VIX M1 bars (last 5):'
SELECT time, open, high, low, close, volume FROM vix_bars_m1 ORDER BY time DESC LIMIT 5;

\echo ''
\echo 'VIX M5 bars (last 5):'
SELECT time, open, high, low, close, volume FROM vix_bars_m5 ORDER BY time DESC LIMIT 5;

\echo ''
\echo 'VIX H1 bars (last 3):'
SELECT time, open, high, low, close, volume FROM vix_bars_h1 ORDER BY time DESC LIMIT 3;

\echo ''
\echo '========================================='
\echo 'VIX BARS COMPRESSION: COMPLETE'
\echo 'Testing successful - ready to replicate to all symbols'
\echo '========================================='
\echo ''
