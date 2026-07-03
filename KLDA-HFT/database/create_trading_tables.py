#!/usr/bin/env python3
"""
KLDA-HFT Trading Tables
Creates all tables needed for the full trading platform
"""
import psycopg2

conn = psycopg2.connect(
    host='localhost', port=5432, database='KLDA-HFT_Database',
    user='postgres', password='MyKldaTechnologies2025!'
)
cur = conn.cursor()

# Account snapshots (every 5 seconds)
cur.execute("""
CREATE TABLE IF NOT EXISTS account_snapshots (
    time         TIMESTAMPTZ DEFAULT NOW(),
    login        BIGINT,
    server       VARCHAR(50),
    balance      DECIMAL(18,2),
    equity       DECIMAL(18,2),
    margin       DECIMAL(18,2),
    free_margin  DECIMAL(18,2),
    margin_level DECIMAL(10,2),
    profit       DECIMAL(18,2),
    PRIMARY KEY (time)
)
""")

# All trades (open and closed)
cur.execute("""
CREATE TABLE IF NOT EXISTS trades (
    id           SERIAL PRIMARY KEY,
    ticket       BIGINT UNIQUE,
    symbol       VARCHAR(30),
    type         VARCHAR(10),
    volume       DECIMAL(10,2),
    open_price   DECIMAL(18,8),
    close_price  DECIMAL(18,8),
    sl           DECIMAL(18,8) DEFAULT 0,
    tp           DECIMAL(18,8) DEFAULT 0,
    open_time    TIMESTAMPTZ,
    close_time   TIMESTAMPTZ,
    profit       DECIMAL(18,2) DEFAULT 0,
    commission   DECIMAL(18,2) DEFAULT 0,
    swap         DECIMAL(18,2) DEFAULT 0,
    net_profit   DECIMAL(18,2) DEFAULT 0,
    signal_id    INTEGER,
    magic        BIGINT DEFAULT 234000,
    comment      VARCHAR(100),
    status       VARCHAR(20) DEFAULT 'OPEN'
)
""")

# Deposit / withdrawal / balance operations
cur.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    id            SERIAL PRIMARY KEY,
    time          TIMESTAMPTZ DEFAULT NOW(),
    type          VARCHAR(20),
    amount        DECIMAL(18,2),
    balance_after DECIMAL(18,2),
    note          VARCHAR(200)
)
""")

# Execution log (every signal fired and what happened)
cur.execute("""
CREATE TABLE IF NOT EXISTS execution_log (
    id          SERIAL PRIMARY KEY,
    time        TIMESTAMPTZ DEFAULT NOW(),
    signal_id   INTEGER,
    symbol      VARCHAR(30),
    action      VARCHAR(20),
    volume      DECIMAL(10,4),
    price       DECIMAL(18,8),
    ticket      BIGINT,
    status      VARCHAR(20),
    error       VARCHAR(200)
)
""")

# Daily P&L summary
cur.execute("""
CREATE TABLE IF NOT EXISTS daily_pnl (
    date         DATE PRIMARY KEY,
    trades_count INTEGER DEFAULT 0,
    gross_profit DECIMAL(18,2) DEFAULT 0,
    gross_loss   DECIMAL(18,2) DEFAULT 0,
    net_profit   DECIMAL(18,2) DEFAULT 0,
    win_rate     DECIMAL(6,4)  DEFAULT 0,
    balance_eod  DECIMAL(18,2) DEFAULT 0
)
""")

conn.commit()
conn.close()
print("[OK] Trading tables created:")
print("  - account_snapshots")
print("  - trades")
print("  - transactions")
print("  - execution_log")
print("  - daily_pnl")
