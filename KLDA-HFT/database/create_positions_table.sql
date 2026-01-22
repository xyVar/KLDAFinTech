-- KLDA-HFT Positions Table
-- Stores all open and closed trading positions

CREATE TABLE IF NOT EXISTS positions (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    entry_time TIMESTAMP NOT NULL DEFAULT NOW(),
    entry_price DOUBLE PRECISION NOT NULL,
    shares DOUBLE PRECISION NOT NULL,
    position_size DOUBLE PRECISION NOT NULL,
    stop_loss DOUBLE PRECISION NOT NULL,
    take_profit DOUBLE PRECISION NOT NULL,
    status VARCHAR(10) DEFAULT 'OPEN',
    exit_time TIMESTAMP,
    exit_price DOUBLE PRECISION,
    pnl DOUBLE PRECISION,
    exit_reason VARCHAR(20)
);

CREATE INDEX IF NOT EXISTS idx_positions_symbol ON positions(symbol);
CREATE INDEX IF NOT EXISTS idx_positions_status ON positions(status);
CREATE INDEX IF NOT EXISTS idx_positions_entry_time ON positions(entry_time);

-- Account state tracking
CREATE TABLE IF NOT EXISTS account_state (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT NOW(),
    balance DOUBLE PRECISION NOT NULL,
    realized_pnl DOUBLE PRECISION NOT NULL,
    unrealized_pnl DOUBLE PRECISION NOT NULL,
    open_positions INT NOT NULL,
    total_trades INT NOT NULL
);

-- Initialize account
INSERT INTO account_state (balance, realized_pnl, unrealized_pnl, open_positions, total_trades)
VALUES (10000.00, 0.00, 0.00, 0, 0);

COMMENT ON TABLE positions IS 'Tracks all trading positions (open and closed)';
COMMENT ON TABLE account_state IS 'Tracks account balance and performance over time';
