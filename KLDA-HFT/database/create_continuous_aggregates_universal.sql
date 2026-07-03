-- ============================================================
-- KLDA-HFT: Universal Continuous Aggregates
-- Source: ticks hypertable (symbol column, all 66 symbols)
-- Creates: 6 materialized views (M1, M5, M15, H1, H4, D1)
-- Generated: 2026-04-20
-- ============================================================
-- Run once. Views auto-refresh on schedule after creation.
-- DO NOT run the old create_continuous_aggregates.sql (TSLA only).
-- ============================================================

-- M1 bars
CREATE MATERIALIZED VIEW IF NOT EXISTS cagg_bars_m1
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 minute', time)   AS time,
    symbol,
    FIRST(bid, time)                AS open,
    MAX(bid)                        AS high,
    MIN(bid)                        AS low,
    LAST(bid, time)                 AS close,
    SUM(volume)                     AS volume,
    AVG(spread)::integer            AS spread
FROM ticks
GROUP BY time_bucket('1 minute', time), symbol
WITH NO DATA;

-- M5 bars
CREATE MATERIALIZED VIEW IF NOT EXISTS cagg_bars_m5
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('5 minutes', time)  AS time,
    symbol,
    FIRST(bid, time)                AS open,
    MAX(bid)                        AS high,
    MIN(bid)                        AS low,
    LAST(bid, time)                 AS close,
    SUM(volume)                     AS volume,
    AVG(spread)::integer            AS spread
FROM ticks
GROUP BY time_bucket('5 minutes', time), symbol
WITH NO DATA;

-- M15 bars
CREATE MATERIALIZED VIEW IF NOT EXISTS cagg_bars_m15
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('15 minutes', time) AS time,
    symbol,
    FIRST(bid, time)                AS open,
    MAX(bid)                        AS high,
    MIN(bid)                        AS low,
    LAST(bid, time)                 AS close,
    SUM(volume)                     AS volume,
    AVG(spread)::integer            AS spread
FROM ticks
GROUP BY time_bucket('15 minutes', time), symbol
WITH NO DATA;

-- H1 bars
CREATE MATERIALIZED VIEW IF NOT EXISTS cagg_bars_h1
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', time)     AS time,
    symbol,
    FIRST(bid, time)                AS open,
    MAX(bid)                        AS high,
    MIN(bid)                        AS low,
    LAST(bid, time)                 AS close,
    SUM(volume)                     AS volume,
    AVG(spread)::integer            AS spread
FROM ticks
GROUP BY time_bucket('1 hour', time), symbol
WITH NO DATA;

-- H4 bars
CREATE MATERIALIZED VIEW IF NOT EXISTS cagg_bars_h4
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('4 hours', time)    AS time,
    symbol,
    FIRST(bid, time)                AS open,
    MAX(bid)                        AS high,
    MIN(bid)                        AS low,
    LAST(bid, time)                 AS close,
    SUM(volume)                     AS volume,
    AVG(spread)::integer            AS spread
FROM ticks
GROUP BY time_bucket('4 hours', time), symbol
WITH NO DATA;

-- D1 bars
CREATE MATERIALIZED VIEW IF NOT EXISTS cagg_bars_d1
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', time)      AS time,
    symbol,
    FIRST(bid, time)                AS open,
    MAX(bid)                        AS high,
    MIN(bid)                        AS low,
    LAST(bid, time)                 AS close,
    SUM(volume)                     AS volume,
    AVG(spread)::integer            AS spread
FROM ticks
GROUP BY time_bucket('1 day', time), symbol
WITH NO DATA;

-- ============================================================
-- Refresh policies (auto-materialize on schedule)
-- ============================================================

SELECT add_continuous_aggregate_policy('cagg_bars_m1',
    start_offset  => INTERVAL '1 hour',
    end_offset    => INTERVAL '1 minute',
    schedule_interval => INTERVAL '1 minute');

SELECT add_continuous_aggregate_policy('cagg_bars_m5',
    start_offset  => INTERVAL '3 hours',
    end_offset    => INTERVAL '5 minutes',
    schedule_interval => INTERVAL '5 minutes');

SELECT add_continuous_aggregate_policy('cagg_bars_m15',
    start_offset  => INTERVAL '6 hours',
    end_offset    => INTERVAL '15 minutes',
    schedule_interval => INTERVAL '15 minutes');

SELECT add_continuous_aggregate_policy('cagg_bars_h1',
    start_offset  => INTERVAL '2 days',
    end_offset    => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour');

SELECT add_continuous_aggregate_policy('cagg_bars_h4',
    start_offset  => INTERVAL '7 days',
    end_offset    => INTERVAL '4 hours',
    schedule_interval => INTERVAL '4 hours');

SELECT add_continuous_aggregate_policy('cagg_bars_d1',
    start_offset  => INTERVAL '30 days',
    end_offset    => INTERVAL '1 day',
    schedule_interval => INTERVAL '1 day');

-- ============================================================
-- Backfill from first available tick to now
-- Run AFTER creating the views above.
-- This may take several minutes on 100M+ tick dataset.
-- ============================================================

CALL refresh_continuous_aggregate('cagg_bars_m1',  '2026-03-09', NOW());
CALL refresh_continuous_aggregate('cagg_bars_m5',  '2026-03-09', NOW());
CALL refresh_continuous_aggregate('cagg_bars_m15', '2026-03-09', NOW());
CALL refresh_continuous_aggregate('cagg_bars_h1',  '2026-03-09', NOW());
CALL refresh_continuous_aggregate('cagg_bars_h4',  '2026-03-09', NOW());
CALL refresh_continuous_aggregate('cagg_bars_d1',  '2026-03-09', NOW());

-- ============================================================
-- Verify
-- ============================================================

SELECT view_name, materialization_hypertable_name, compression_enabled
FROM timescaledb_information.continuous_aggregates;

SELECT 'cagg_bars_m1'  AS view, COUNT(*), MAX(time) FROM cagg_bars_m1  UNION ALL
SELECT 'cagg_bars_m5',          COUNT(*), MAX(time) FROM cagg_bars_m5  UNION ALL
SELECT 'cagg_bars_m15',         COUNT(*), MAX(time) FROM cagg_bars_m15 UNION ALL
SELECT 'cagg_bars_h1',          COUNT(*), MAX(time) FROM cagg_bars_h1  UNION ALL
SELECT 'cagg_bars_h4',          COUNT(*), MAX(time) FROM cagg_bars_h4  UNION ALL
SELECT 'cagg_bars_d1',          COUNT(*), MAX(time) FROM cagg_bars_d1;
