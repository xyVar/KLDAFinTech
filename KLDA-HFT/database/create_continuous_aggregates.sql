-- ========================================
-- KLDA-HFT Continuous Aggregates Setup
-- Automatically compress ticks into OHLCV bars
-- ========================================

-- This script creates TimescaleDB continuous aggregates that:
-- 1. Read from *_history tables (live ticks)
-- 2. Compress into OHLCV bars (M1, M5, M15, M30, H1, H4, D1, W1, MN)
-- 3. Insert into *_bars tables automatically
-- 4. Refresh every X minutes based on timeframe

-- ========================================
-- TSLA (Tesla) - All Timeframes
-- ========================================

-- M1 (1 minute bars)
CREATE MATERIALIZED VIEW tsla_bars_m1_continuous
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
FROM tsla_history
GROUP BY time_bucket('1 minute', time);

-- M5 (5 minute bars)
CREATE MATERIALIZED VIEW tsla_bars_m5_continuous
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
FROM tsla_history
GROUP BY time_bucket('5 minutes', time);

-- M15 (15 minute bars)
CREATE MATERIALIZED VIEW tsla_bars_m15_continuous
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('15 minutes', time) AS time,
    'M15'::VARCHAR(5) as timeframe,
    FIRST(bid, time) as open,
    MAX(ask) as high,
    MIN(bid) as low,
    LAST(ask, time) as close,
    SUM(volume) as volume,
    AVG(spread)::INTEGER as spread
FROM tsla_history
GROUP BY time_bucket('15 minutes', time);

-- M30 (30 minute bars)
CREATE MATERIALIZED VIEW tsla_bars_m30_continuous
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('30 minutes', time) AS time,
    'M30'::VARCHAR(5) as timeframe,
    FIRST(bid, time) as open,
    MAX(ask) as high,
    MIN(bid) as low,
    LAST(ask, time) as close,
    SUM(volume) as volume,
    AVG(spread)::INTEGER as spread
FROM tsla_history
GROUP BY time_bucket('30 minutes', time);

-- H1 (1 hour bars)
CREATE MATERIALIZED VIEW tsla_bars_h1_continuous
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
FROM tsla_history
GROUP BY time_bucket('1 hour', time);

-- H4 (4 hour bars)
CREATE MATERIALIZED VIEW tsla_bars_h4_continuous
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('4 hours', time) AS time,
    'H4'::VARCHAR(5) as timeframe,
    FIRST(bid, time) as open,
    MAX(ask) as high,
    MIN(bid) as low,
    LAST(ask, time) as close,
    SUM(volume) as volume,
    AVG(spread)::INTEGER as spread
FROM tsla_history
GROUP BY time_bucket('4 hours', time);

-- D1 (1 day bars)
CREATE MATERIALIZED VIEW tsla_bars_d1_continuous
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', time) AS time,
    'D1'::VARCHAR(5) as timeframe,
    FIRST(bid, time) as open,
    MAX(ask) as high,
    MIN(bid) as low,
    LAST(ask, time) as close,
    SUM(volume) as volume,
    AVG(spread)::INTEGER as spread
FROM tsla_history
GROUP BY time_bucket('1 day', time);

-- W1 (1 week bars)
CREATE MATERIALIZED VIEW tsla_bars_w1_continuous
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 week', time) AS time,
    'W1'::VARCHAR(5) as timeframe,
    FIRST(bid, time) as open,
    MAX(ask) as high,
    MIN(bid) as low,
    LAST(ask, time) as close,
    SUM(volume) as volume,
    AVG(spread)::INTEGER as spread
FROM tsla_history
GROUP BY time_bucket('1 week', time);

-- MN1 (1 month bars)
CREATE MATERIALIZED VIEW tsla_bars_mn1_continuous
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 month', time) AS time,
    'MN1'::VARCHAR(5) as timeframe,
    FIRST(bid, time) as open,
    MAX(ask) as high,
    MIN(bid) as low,
    LAST(ask, time) as close,
    SUM(volume) as volume,
    AVG(spread)::INTEGER as spread
FROM tsla_history
GROUP BY time_bucket('1 month', time);

-- ========================================
-- REFRESH POLICIES (Automatic Updates)
-- ========================================

-- M1: Refresh every 1 minute, keep last 2 hours materialized
SELECT add_continuous_aggregate_policy('tsla_bars_m1_continuous',
    start_offset => INTERVAL '2 hours',
    end_offset => INTERVAL '1 minute',
    schedule_interval => INTERVAL '1 minute');

-- M5: Refresh every 5 minutes, keep last 12 hours materialized
SELECT add_continuous_aggregate_policy('tsla_bars_m5_continuous',
    start_offset => INTERVAL '12 hours',
    end_offset => INTERVAL '5 minutes',
    schedule_interval => INTERVAL '5 minutes');

-- M15: Refresh every 15 minutes, keep last 24 hours materialized
SELECT add_continuous_aggregate_policy('tsla_bars_m15_continuous',
    start_offset => INTERVAL '24 hours',
    end_offset => INTERVAL '15 minutes',
    schedule_interval => INTERVAL '15 minutes');

-- M30: Refresh every 30 minutes, keep last 48 hours materialized
SELECT add_continuous_aggregate_policy('tsla_bars_m30_continuous',
    start_offset => INTERVAL '48 hours',
    end_offset => INTERVAL '30 minutes',
    schedule_interval => INTERVAL '30 minutes');

-- H1: Refresh every 1 hour, keep last 7 days materialized
SELECT add_continuous_aggregate_policy('tsla_bars_h1_continuous',
    start_offset => INTERVAL '7 days',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour');

-- H4: Refresh every 4 hours, keep last 30 days materialized
SELECT add_continuous_aggregate_policy('tsla_bars_h4_continuous',
    start_offset => INTERVAL '30 days',
    end_offset => INTERVAL '4 hours',
    schedule_interval => INTERVAL '4 hours');

-- D1: Refresh every 1 day, keep last 90 days materialized
SELECT add_continuous_aggregate_policy('tsla_bars_d1_continuous',
    start_offset => INTERVAL '90 days',
    end_offset => INTERVAL '1 day',
    schedule_interval => INTERVAL '1 day');

-- W1: Refresh every 1 week, keep last 1 year materialized
SELECT add_continuous_aggregate_policy('tsla_bars_w1_continuous',
    start_offset => INTERVAL '1 year',
    end_offset => INTERVAL '1 week',
    schedule_interval => INTERVAL '1 week');

-- MN1: Refresh every 1 month, keep last 5 years materialized
SELECT add_continuous_aggregate_policy('tsla_bars_mn1_continuous',
    start_offset => INTERVAL '5 years',
    end_offset => INTERVAL '1 month',
    schedule_interval => INTERVAL '1 month');

-- ========================================
-- SUCCESS MESSAGE
-- ========================================
SELECT 'TSLA continuous aggregates created successfully!' as status;
