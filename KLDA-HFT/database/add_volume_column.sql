-- ============================================
-- ADD VOLUME COLUMN TO ALL TABLES
-- ============================================

-- Add volume to CURRENT table
ALTER TABLE current ADD COLUMN IF NOT EXISTS volume BIGINT DEFAULT 0;

-- Add volume to all 17 HISTORY tables
ALTER TABLE tsla_history ADD COLUMN IF NOT EXISTS volume BIGINT DEFAULT 0;
ALTER TABLE nvda_history ADD COLUMN IF NOT EXISTS volume BIGINT DEFAULT 0;
ALTER TABLE pltr_history ADD COLUMN IF NOT EXISTS volume BIGINT DEFAULT 0;
ALTER TABLE amd_history ADD COLUMN IF NOT EXISTS volume BIGINT DEFAULT 0;
ALTER TABLE avgo_history ADD COLUMN IF NOT EXISTS volume BIGINT DEFAULT 0;
ALTER TABLE meta_history ADD COLUMN IF NOT EXISTS volume BIGINT DEFAULT 0;
ALTER TABLE aapl_history ADD COLUMN IF NOT EXISTS volume BIGINT DEFAULT 0;
ALTER TABLE msft_history ADD COLUMN IF NOT EXISTS volume BIGINT DEFAULT 0;
ALTER TABLE orcl_history ADD COLUMN IF NOT EXISTS volume BIGINT DEFAULT 0;
ALTER TABLE amzn_history ADD COLUMN IF NOT EXISTS volume BIGINT DEFAULT 0;
ALTER TABLE csco_history ADD COLUMN IF NOT EXISTS volume BIGINT DEFAULT 0;
ALTER TABLE goog_history ADD COLUMN IF NOT EXISTS volume BIGINT DEFAULT 0;
ALTER TABLE intc_history ADD COLUMN IF NOT EXISTS volume BIGINT DEFAULT 0;
ALTER TABLE vix_history ADD COLUMN IF NOT EXISTS volume BIGINT DEFAULT 0;
ALTER TABLE nas100_history ADD COLUMN IF NOT EXISTS volume BIGINT DEFAULT 0;
ALTER TABLE natgas_history ADD COLUMN IF NOT EXISTS volume BIGINT DEFAULT 0;
ALTER TABLE spotcrude_history ADD COLUMN IF NOT EXISTS volume BIGINT DEFAULT 0;

-- Verification
SELECT 'Volume column added successfully!' as status;

-- Show CURRENT table structure
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'current'
ORDER BY ordinal_position;
