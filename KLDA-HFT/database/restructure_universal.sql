-- ============================================================
-- KLDA-HFT Database Restructure: Universal Tick Architecture
-- Drops all old per-symbol tables, creates one universal ticks table
-- ============================================================

-- STEP 1: Drop all old per-symbol history tables
DROP TABLE IF EXISTS aapl_history CASCADE;
DROP TABLE IF EXISTS amd_history CASCADE;
DROP TABLE IF EXISTS amzn_history CASCADE;
DROP TABLE IF EXISTS avgo_history CASCADE;
DROP TABLE IF EXISTS csco_history CASCADE;
DROP TABLE IF EXISTS goog_history CASCADE;
DROP TABLE IF EXISTS intc_history CASCADE;
DROP TABLE IF EXISTS meta_history CASCADE;
DROP TABLE IF EXISTS msft_history CASCADE;
DROP TABLE IF EXISTS nas100_history CASCADE;
DROP TABLE IF EXISTS natgas_history CASCADE;
DROP TABLE IF EXISTS nvda_history CASCADE;
DROP TABLE IF EXISTS orcl_history CASCADE;
DROP TABLE IF EXISTS pltr_history CASCADE;
DROP TABLE IF EXISTS spotcrude_history CASCADE;
DROP TABLE IF EXISTS tsla_history CASCADE;
DROP TABLE IF EXISTS vix_history CASCADE;

-- STEP 2: Drop all old per-symbol bars tables
DROP TABLE IF EXISTS aapl_bars CASCADE;
DROP TABLE IF EXISTS amd_bars CASCADE;
DROP TABLE IF EXISTS amzn_bars CASCADE;
DROP TABLE IF EXISTS avgo_bars CASCADE;
DROP TABLE IF EXISTS csco_bars CASCADE;
DROP TABLE IF EXISTS goog_bars CASCADE;
DROP TABLE IF EXISTS intc_bars CASCADE;
DROP TABLE IF EXISTS meta_bars CASCADE;
DROP TABLE IF EXISTS msft_bars CASCADE;
DROP TABLE IF EXISTS nas100_bars CASCADE;
DROP TABLE IF EXISTS natgas_bars CASCADE;
DROP TABLE IF EXISTS nvda_bars CASCADE;
DROP TABLE IF EXISTS orcl_bars CASCADE;
DROP TABLE IF EXISTS pltr_bars CASCADE;
DROP TABLE IF EXISTS spotcrude_bars CASCADE;
DROP TABLE IF EXISTS tsla_bars CASCADE;
DROP TABLE IF EXISTS vix_bars CASCADE;

-- STEP 3: Drop old current table
DROP TABLE IF EXISTS current CASCADE;

-- STEP 4: Drop any signal/pattern/position tables
DROP TABLE IF EXISTS patterns CASCADE;
DROP TABLE IF EXISTS signals CASCADE;
DROP TABLE IF EXISTS tick_events CASCADE;
DROP TABLE IF EXISTS positions CASCADE;
DROP TABLE IF EXISTS account_state CASCADE;

-- ============================================================
-- STEP 5: Create universal TICKS hypertable
-- One table for ALL symbols - fully dynamic
-- ============================================================
CREATE TABLE ticks (
    time         TIMESTAMPTZ(6)  NOT NULL,
    symbol       VARCHAR(30)     NOT NULL,
    bid          DECIMAL(18,8)   NOT NULL,
    ask          DECIMAL(18,8)   NOT NULL,
    spread       DECIMAL(10,5),
    volume       BIGINT          DEFAULT 0,
    buy_volume   BIGINT          DEFAULT 0,
    sell_volume  BIGINT          DEFAULT 0,
    flags        INTEGER         DEFAULT 0
);

-- Convert to TimescaleDB hypertable (partitioned by time)
SELECT create_hypertable('ticks', 'time', chunk_time_interval => INTERVAL '1 day');

-- Index for fast symbol queries
CREATE INDEX idx_ticks_symbol_time ON ticks (symbol, time DESC);

-- Enable compression (7 days old data gets compressed 10x)
ALTER TABLE ticks SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'symbol',
    timescaledb.compress_orderby = 'time DESC'
);
SELECT add_compression_policy('ticks', INTERVAL '7 days');

-- ============================================================
-- STEP 6: Create universal CURRENT table
-- Live snapshot - one row per symbol, auto-created on first tick
-- ============================================================
CREATE TABLE current (
    symbol       VARCHAR(30)     PRIMARY KEY,
    bid          DECIMAL(18,8),
    ask          DECIMAL(18,8),
    spread       DECIMAL(10,5),
    volume       BIGINT          DEFAULT 0,
    flags        INTEGER         DEFAULT 0,
    last_updated TIMESTAMPTZ(6)
);

-- ============================================================
-- DONE
-- ============================================================
