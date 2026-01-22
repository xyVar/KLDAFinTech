-- ========================================
-- KLDA-HFT TimescaleDB Compression Setup
-- Enable 10x storage reduction
-- ========================================

\echo 'Enabling compression on all history tables...'
\echo ''

-- TSLA History
ALTER TABLE tsla_history SET (
    timescaledb.compress,
    timescaledb.compress_orderby = 'time DESC'
);
SELECT add_compression_policy('tsla_history', INTERVAL '7 days');
\echo '[OK] TSLA compression enabled'

-- NVDA History
ALTER TABLE nvda_history SET (
    timescaledb.compress,
    timescaledb.compress_orderby = 'time DESC'
);
SELECT add_compression_policy('nvda_history', INTERVAL '7 days');
\echo '[OK] NVDA compression enabled'

-- PLTR History
ALTER TABLE pltr_history SET (
    timescaledb.compress,
    timescaledb.compress_orderby = 'time DESC'
);
SELECT add_compression_policy('pltr_history', INTERVAL '7 days');
\echo '[OK] PLTR compression enabled'

-- AMD History
ALTER TABLE amd_history SET (
    timescaledb.compress,
    timescaledb.compress_orderby = 'time DESC'
);
SELECT add_compression_policy('amd_history', INTERVAL '7 days');
\echo '[OK] AMD compression enabled'

-- AVGO History
ALTER TABLE avgo_history SET (
    timescaledb.compress,
    timescaledb.compress_orderby = 'time DESC'
);
SELECT add_compression_policy('avgo_history', INTERVAL '7 days');
\echo '[OK] AVGO compression enabled'

-- META History
ALTER TABLE meta_history SET (
    timescaledb.compress,
    timescaledb.compress_orderby = 'time DESC'
);
SELECT add_compression_policy('meta_history', INTERVAL '7 days');
\echo '[OK] META compression enabled'

-- AAPL History
ALTER TABLE aapl_history SET (
    timescaledb.compress,
    timescaledb.compress_orderby = 'time DESC'
);
SELECT add_compression_policy('aapl_history', INTERVAL '7 days');
\echo '[OK] AAPL compression enabled'

-- MSFT History
ALTER TABLE msft_history SET (
    timescaledb.compress,
    timescaledb.compress_orderby = 'time DESC'
);
SELECT add_compression_policy('msft_history', INTERVAL '7 days');
\echo '[OK] MSFT compression enabled'

-- ORCL History
ALTER TABLE orcl_history SET (
    timescaledb.compress,
    timescaledb.compress_orderby = 'time DESC'
);
SELECT add_compression_policy('orcl_history', INTERVAL '7 days');
\echo '[OK] ORCL compression enabled'

-- AMZN History
ALTER TABLE amzn_history SET (
    timescaledb.compress,
    timescaledb.compress_orderby = 'time DESC'
);
SELECT add_compression_policy('amzn_history', INTERVAL '7 days');
\echo '[OK] AMZN compression enabled'

-- CSCO History
ALTER TABLE csco_history SET (
    timescaledb.compress,
    timescaledb.compress_orderby = 'time DESC'
);
SELECT add_compression_policy('csco_history', INTERVAL '7 days');
\echo '[OK] CSCO compression enabled'

-- GOOG History
ALTER TABLE goog_history SET (
    timescaledb.compress,
    timescaledb.compress_orderby = 'time DESC'
);
SELECT add_compression_policy('goog_history', INTERVAL '7 days');
\echo '[OK] GOOG compression enabled'

-- INTC History
ALTER TABLE intc_history SET (
    timescaledb.compress,
    timescaledb.compress_orderby = 'time DESC'
);
SELECT add_compression_policy('intc_history', INTERVAL '7 days');
\echo '[OK] INTC compression enabled'

-- VIX History
ALTER TABLE vix_history SET (
    timescaledb.compress,
    timescaledb.compress_orderby = 'time DESC'
);
SELECT add_compression_policy('vix_history', INTERVAL '7 days');
\echo '[OK] VIX compression enabled'

-- NAS100 History
ALTER TABLE nas100_history SET (
    timescaledb.compress,
    timescaledb.compress_orderby = 'time DESC'
);
SELECT add_compression_policy('nas100_history', INTERVAL '7 days');
\echo '[OK] NAS100 compression enabled'

-- NatGas History
ALTER TABLE natgas_history SET (
    timescaledb.compress,
    timescaledb.compress_orderby = 'time DESC'
);
SELECT add_compression_policy('natgas_history', INTERVAL '7 days');
\echo '[OK] NatGas compression enabled'

-- SpotCrude History
ALTER TABLE spotcrude_history SET (
    timescaledb.compress,
    timescaledb.compress_orderby = 'time DESC'
);
SELECT add_compression_policy('spotcrude_history', INTERVAL '7 days');
\echo '[OK] SpotCrude compression enabled'

\echo ''
\echo '========================================'
\echo 'COMPRESSION ENABLED ON ALL 17 TABLES'
\echo '========================================'
\echo 'Policy: Compress data older than 7 days'
\echo 'Expected: 10x storage reduction'
\echo 'Benefit: Faster queries on old data'
\echo '========================================'
\echo ''

-- Show compression status
SELECT
    hypertable_name,
    compression_enabled,
    (SELECT COUNT(*) FROM timescaledb_information.chunks WHERE hypertable_name = h.hypertable_name) as total_chunks,
    (SELECT COUNT(*) FROM timescaledb_information.chunks WHERE hypertable_name = h.hypertable_name AND is_compressed) as compressed_chunks
FROM timescaledb_information.hypertables h
ORDER BY hypertable_name;
