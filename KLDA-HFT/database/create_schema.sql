-- ============================================
-- KLDA-HFT DATABASE SCHEMA
-- Architecture: Broker → Current → History
-- ============================================

-- Check TimescaleDB availability
SELECT * FROM pg_available_extensions WHERE name = 'timescaledb';

-- Enable TimescaleDB (if not already enabled)
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- ============================================
-- TABLE: CURRENT (17 assets - live broker feed)
-- ============================================
CREATE TABLE IF NOT EXISTS current (
    symbol_id INTEGER PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL UNIQUE,
    mt5_symbol VARCHAR(50),
    bid DECIMAL(18,8) NOT NULL DEFAULT 0,
    ask DECIMAL(18,8) NOT NULL DEFAULT 0,
    spread DECIMAL(10,6) DEFAULT 0,
    last_updated TIMESTAMPTZ(6) NOT NULL DEFAULT NOW()
);

-- Insert 17 assets
INSERT INTO current (symbol_id, symbol, mt5_symbol) VALUES
(1, 'TSLA', 'TSLA.US-24'),
(2, 'NVDA', 'NVDA.US-24'),
(3, 'PLTR', 'PLTR.US-24'),
(4, 'AMD', 'AMD.US-24'),
(5, 'AVGO', 'AVGO.US-24'),
(6, 'META', 'META.US-24'),
(7, 'AAPL', 'AAPL.US-24'),
(8, 'MSFT', 'MSFT.US-24'),
(9, 'ORCL', 'ORCL.US-24'),
(10, 'AMZN', 'AMZN.US-24'),
(11, 'CSCO', 'CSCO.US-24'),
(12, 'GOOG', 'GOOG.US-24'),
(13, 'INTC', 'INTC.US-24'),
(14, 'VIX', 'VIX'),
(15, 'NAS100', 'NAS100'),
(16, 'NatGas', 'NatGas'),
(17, 'SpotCrude', 'SpotCrude')
ON CONFLICT (symbol_id) DO NOTHING;

-- ============================================
-- HISTORY TABLES (17 tables - one per asset)
-- ============================================

-- TSLA history
CREATE TABLE IF NOT EXISTS tsla_history (
    time TIMESTAMPTZ(6) NOT NULL,
    bid DECIMAL(18,8) NOT NULL,
    ask DECIMAL(18,8) NOT NULL,
    spread DECIMAL(10,6),
    PRIMARY KEY (time)
);

-- NVDA history
CREATE TABLE IF NOT EXISTS nvda_history (
    time TIMESTAMPTZ(6) NOT NULL,
    bid DECIMAL(18,8) NOT NULL,
    ask DECIMAL(18,8) NOT NULL,
    spread DECIMAL(10,6),
    PRIMARY KEY (time)
);

-- PLTR history
CREATE TABLE IF NOT EXISTS pltr_history (
    time TIMESTAMPTZ(6) NOT NULL,
    bid DECIMAL(18,8) NOT NULL,
    ask DECIMAL(18,8) NOT NULL,
    spread DECIMAL(10,6),
    PRIMARY KEY (time)
);

-- AMD history
CREATE TABLE IF NOT EXISTS amd_history (
    time TIMESTAMPTZ(6) NOT NULL,
    bid DECIMAL(18,8) NOT NULL,
    ask DECIMAL(18,8) NOT NULL,
    spread DECIMAL(10,6),
    PRIMARY KEY (time)
);

-- AVGO history
CREATE TABLE IF NOT EXISTS avgo_history (
    time TIMESTAMPTZ(6) NOT NULL,
    bid DECIMAL(18,8) NOT NULL,
    ask DECIMAL(18,8) NOT NULL,
    spread DECIMAL(10,6),
    PRIMARY KEY (time)
);

-- META history
CREATE TABLE IF NOT EXISTS meta_history (
    time TIMESTAMPTZ(6) NOT NULL,
    bid DECIMAL(18,8) NOT NULL,
    ask DECIMAL(18,8) NOT NULL,
    spread DECIMAL(10,6),
    PRIMARY KEY (time)
);

-- AAPL history
CREATE TABLE IF NOT EXISTS aapl_history (
    time TIMESTAMPTZ(6) NOT NULL,
    bid DECIMAL(18,8) NOT NULL,
    ask DECIMAL(18,8) NOT NULL,
    spread DECIMAL(10,6),
    PRIMARY KEY (time)
);

-- MSFT history
CREATE TABLE IF NOT EXISTS msft_history (
    time TIMESTAMPTZ(6) NOT NULL,
    bid DECIMAL(18,8) NOT NULL,
    ask DECIMAL(18,8) NOT NULL,
    spread DECIMAL(10,6),
    PRIMARY KEY (time)
);

-- ORCL history
CREATE TABLE IF NOT EXISTS orcl_history (
    time TIMESTAMPTZ(6) NOT NULL,
    bid DECIMAL(18,8) NOT NULL,
    ask DECIMAL(18,8) NOT NULL,
    spread DECIMAL(10,6),
    PRIMARY KEY (time)
);

-- AMZN history
CREATE TABLE IF NOT EXISTS amzn_history (
    time TIMESTAMPTZ(6) NOT NULL,
    bid DECIMAL(18,8) NOT NULL,
    ask DECIMAL(18,8) NOT NULL,
    spread DECIMAL(10,6),
    PRIMARY KEY (time)
);

-- CSCO history
CREATE TABLE IF NOT EXISTS csco_history (
    time TIMESTAMPTZ(6) NOT NULL,
    bid DECIMAL(18,8) NOT NULL,
    ask DECIMAL(18,8) NOT NULL,
    spread DECIMAL(10,6),
    PRIMARY KEY (time)
);

-- GOOG history
CREATE TABLE IF NOT EXISTS goog_history (
    time TIMESTAMPTZ(6) NOT NULL,
    bid DECIMAL(18,8) NOT NULL,
    ask DECIMAL(18,8) NOT NULL,
    spread DECIMAL(10,6),
    PRIMARY KEY (time)
);

-- INTC history
CREATE TABLE IF NOT EXISTS intc_history (
    time TIMESTAMPTZ(6) NOT NULL,
    bid DECIMAL(18,8) NOT NULL,
    ask DECIMAL(18,8) NOT NULL,
    spread DECIMAL(10,6),
    PRIMARY KEY (time)
);

-- VIX history
CREATE TABLE IF NOT EXISTS vix_history (
    time TIMESTAMPTZ(6) NOT NULL,
    bid DECIMAL(18,8) NOT NULL,
    ask DECIMAL(18,8) NOT NULL,
    spread DECIMAL(10,6),
    PRIMARY KEY (time)
);

-- NAS100 history
CREATE TABLE IF NOT EXISTS nas100_history (
    time TIMESTAMPTZ(6) NOT NULL,
    bid DECIMAL(18,8) NOT NULL,
    ask DECIMAL(18,8) NOT NULL,
    spread DECIMAL(10,6),
    PRIMARY KEY (time)
);

-- NatGas history
CREATE TABLE IF NOT EXISTS natgas_history (
    time TIMESTAMPTZ(6) NOT NULL,
    bid DECIMAL(18,8) NOT NULL,
    ask DECIMAL(18,8) NOT NULL,
    spread DECIMAL(10,6),
    PRIMARY KEY (time)
);

-- SpotCrude history
CREATE TABLE IF NOT EXISTS spotcrude_history (
    time TIMESTAMPTZ(6) NOT NULL,
    bid DECIMAL(18,8) NOT NULL,
    ask DECIMAL(18,8) NOT NULL,
    spread DECIMAL(10,6),
    PRIMARY KEY (time)
);

-- ============================================
-- CONVERT HISTORY TABLES TO HYPERTABLES
-- ============================================
SELECT create_hypertable('tsla_history', 'time', if_not_exists => TRUE);
SELECT create_hypertable('nvda_history', 'time', if_not_exists => TRUE);
SELECT create_hypertable('pltr_history', 'time', if_not_exists => TRUE);
SELECT create_hypertable('amd_history', 'time', if_not_exists => TRUE);
SELECT create_hypertable('avgo_history', 'time', if_not_exists => TRUE);
SELECT create_hypertable('meta_history', 'time', if_not_exists => TRUE);
SELECT create_hypertable('aapl_history', 'time', if_not_exists => TRUE);
SELECT create_hypertable('msft_history', 'time', if_not_exists => TRUE);
SELECT create_hypertable('orcl_history', 'time', if_not_exists => TRUE);
SELECT create_hypertable('amzn_history', 'time', if_not_exists => TRUE);
SELECT create_hypertable('csco_history', 'time', if_not_exists => TRUE);
SELECT create_hypertable('goog_history', 'time', if_not_exists => TRUE);
SELECT create_hypertable('intc_history', 'time', if_not_exists => TRUE);
SELECT create_hypertable('vix_history', 'time', if_not_exists => TRUE);
SELECT create_hypertable('nas100_history', 'time', if_not_exists => TRUE);
SELECT create_hypertable('natgas_history', 'time', if_not_exists => TRUE);
SELECT create_hypertable('spotcrude_history', 'time', if_not_exists => TRUE);

-- ============================================
-- INDEXES FOR FAST QUERIES
-- ============================================
CREATE INDEX IF NOT EXISTS idx_current_symbol ON current(symbol);
CREATE INDEX IF NOT EXISTS idx_current_updated ON current(last_updated DESC);

-- ============================================
-- COMPRESSION POLICIES (save space)
-- ============================================
ALTER TABLE tsla_history SET (timescaledb.compress, timescaledb.compress_segmentby = 'time');
ALTER TABLE nvda_history SET (timescaledb.compress, timescaledb.compress_segmentby = 'time');
ALTER TABLE pltr_history SET (timescaledb.compress, timescaledb.compress_segmentby = 'time');
ALTER TABLE amd_history SET (timescaledb.compress, timescaledb.compress_segmentby = 'time');
ALTER TABLE avgo_history SET (timescaledb.compress, timescaledb.compress_segmentby = 'time');
ALTER TABLE meta_history SET (timescaledb.compress, timescaledb.compress_segmentby = 'time');
ALTER TABLE aapl_history SET (timescaledb.compress, timescaledb.compress_segmentby = 'time');
ALTER TABLE msft_history SET (timescaledb.compress, timescaledb.compress_segmentby = 'time');
ALTER TABLE orcl_history SET (timescaledb.compress, timescaledb.compress_segmentby = 'time');
ALTER TABLE amzn_history SET (timescaledb.compress, timescaledb.compress_segmentby = 'time');
ALTER TABLE csco_history SET (timescaledb.compress, timescaledb.compress_segmentby = 'time');
ALTER TABLE goog_history SET (timescaledb.compress, timescaledb.compress_segmentby = 'time');
ALTER TABLE intc_history SET (timescaledb.compress, timescaledb.compress_segmentby = 'time');
ALTER TABLE vix_history SET (timescaledb.compress, timescaledb.compress_segmentby = 'time');
ALTER TABLE nas100_history SET (timescaledb.compress, timescaledb.compress_segmentby = 'time');
ALTER TABLE natgas_history SET (timescaledb.compress, timescaledb.compress_segmentby = 'time');
ALTER TABLE spotcrude_history SET (timescaledb.compress, timescaledb.compress_segmentby = 'time');

-- Compress data older than 1 day
SELECT add_compression_policy('tsla_history', INTERVAL '1 day', if_not_exists => TRUE);
SELECT add_compression_policy('nvda_history', INTERVAL '1 day', if_not_exists => TRUE);
SELECT add_compression_policy('pltr_history', INTERVAL '1 day', if_not_exists => TRUE);
SELECT add_compression_policy('amd_history', INTERVAL '1 day', if_not_exists => TRUE);
SELECT add_compression_policy('avgo_history', INTERVAL '1 day', if_not_exists => TRUE);
SELECT add_compression_policy('meta_history', INTERVAL '1 day', if_not_exists => TRUE);
SELECT add_compression_policy('aapl_history', INTERVAL '1 day', if_not_exists => TRUE);
SELECT add_compression_policy('msft_history', INTERVAL '1 day', if_not_exists => TRUE);
SELECT add_compression_policy('orcl_history', INTERVAL '1 day', if_not_exists => TRUE);
SELECT add_compression_policy('amzn_history', INTERVAL '1 day', if_not_exists => TRUE);
SELECT add_compression_policy('csco_history', INTERVAL '1 day', if_not_exists => TRUE);
SELECT add_compression_policy('goog_history', INTERVAL '1 day', if_not_exists => TRUE);
SELECT add_compression_policy('intc_history', INTERVAL '1 day', if_not_exists => TRUE);
SELECT add_compression_policy('vix_history', INTERVAL '1 day', if_not_exists => TRUE);
SELECT add_compression_policy('nas100_history', INTERVAL '1 day', if_not_exists => TRUE);
SELECT add_compression_policy('natgas_history', INTERVAL '1 day', if_not_exists => TRUE);
SELECT add_compression_policy('spotcrude_history', INTERVAL '1 day', if_not_exists => TRUE);

-- ============================================
-- VERIFICATION
-- ============================================
SELECT 'Tables created successfully!' as status;
SELECT COUNT(*) as asset_count FROM current;
SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name LIKE '%_history' ORDER BY table_name;
