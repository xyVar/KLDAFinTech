-- ============================================================
-- KLDA-HFT Compliance Infrastructure
-- SEC/FCA-grade audit trail, RBAC, investor ledger, NAV history
-- Run once against KLDA-HFT_Database
-- ============================================================

-- ── 1. USERS ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id            SERIAL PRIMARY KEY,
    username      VARCHAR(50)  NOT NULL UNIQUE,
    email         VARCHAR(120) NOT NULL UNIQUE,
    password_hash TEXT         NOT NULL,           -- bcrypt cost 12
    role          VARCHAR(20)  NOT NULL
                  CHECK (role IN ('admin','trader','viewer','risk_manager')),
    is_active     BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    last_login    TIMESTAMPTZ,
    created_by    INTEGER REFERENCES users(id)     -- audit: who created this user
);

-- ── 2. AUDIT LOG (IMMUTABLE — never UPDATE or DELETE rows) ──
-- Every system action is appended here. Regulators review this.
CREATE TABLE IF NOT EXISTS audit_log (
    id          BIGSERIAL PRIMARY KEY,
    ts          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    user_id     INTEGER REFERENCES users(id),
    username    VARCHAR(50),    -- denormalized (user may be deactivated)
    role        VARCHAR(20),
    action      VARCHAR(100) NOT NULL,  -- LOGIN, LOGOUT, VIEW_ACCOUNT, VIEW_SIGNALS,
                                        -- TRADE_EXECUTE, USER_CREATE, EXPORT_REPORT, ...
    resource    VARCHAR(200),           -- e.g. '/api/signals', 'TSLA', 'user:3'
    detail      JSONB,                  -- extra context (trade id, symbol, amount, etc.)
    ip_address  VARCHAR(45),            -- IPv4 or IPv6
    success     BOOLEAN NOT NULL DEFAULT TRUE,
    error_msg   TEXT                    -- populated when success=FALSE
);

CREATE INDEX IF NOT EXISTS audit_log_ts_idx        ON audit_log(ts DESC);
CREATE INDEX IF NOT EXISTS audit_log_user_ts_idx   ON audit_log(user_id, ts DESC);
CREATE INDEX IF NOT EXISTS audit_log_action_ts_idx ON audit_log(action, ts DESC);

-- Prevent accidental deletes/updates on audit_log (defence in depth)
-- Run as superuser to enforce immutability at DB level:
-- CREATE RULE no_update_audit AS ON UPDATE TO audit_log DO INSTEAD NOTHING;
-- CREATE RULE no_delete_audit AS ON DELETE TO audit_log DO INSTEAD NOTHING;

-- ── 3. INVESTOR LEDGER ───────────────────────────────────────
-- Tracks capital subscriptions / redemptions per investor
CREATE TABLE IF NOT EXISTS investor_ledger (
    id              SERIAL PRIMARY KEY,
    ts              TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    investor_name   VARCHAR(100) NOT NULL,
    investor_email  VARCHAR(120),
    entry_type      VARCHAR(20)  NOT NULL
                    CHECK (entry_type IN ('SUBSCRIPTION','REDEMPTION','FEE','ADJUSTMENT')),
    amount_usd      NUMERIC(18,2) NOT NULL,   -- positive = funds in, negative = funds out
    nav_at_entry    NUMERIC(18,4),            -- fund NAV per share at time of entry
    shares_delta    NUMERIC(18,6),            -- units allocated (+) or redeemed (-)
    reference_doc   VARCHAR(200),             -- wire reference, subscription agreement ID
    approved_by     INTEGER REFERENCES users(id),
    notes           TEXT,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS investor_ledger_name_ts_idx ON investor_ledger(investor_name, ts DESC);
CREATE INDEX IF NOT EXISTS investor_ledger_type_ts_idx ON investor_ledger(entry_type, ts DESC);

-- ── 4. NAV HISTORY ───────────────────────────────────────────
-- Daily fund NAV — required for annual audit sign-off
CREATE TABLE IF NOT EXISTS nav_history (
    id              SERIAL PRIMARY KEY,
    nav_date        DATE         NOT NULL UNIQUE,
    total_aum       NUMERIC(18,2),            -- total assets under management (USD)
    total_shares    NUMERIC(18,6),            -- total shares / units outstanding
    nav_per_share   NUMERIC(18,6),            -- AUM / shares (the official unit price)
    gross_pnl       NUMERIC(18,2),            -- day's trading gross P&L
    net_pnl         NUMERIC(18,2),            -- after fees
    mgmt_fee        NUMERIC(18,2),            -- management fee accrual (e.g. 2% p.a.)
    perf_fee        NUMERIC(18,2),            -- performance fee accrual (e.g. 20%)
    calculated_by   INTEGER REFERENCES users(id),
    locked          BOOLEAN      DEFAULT FALSE, -- TRUE = auditor-sealed, no changes allowed
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- ============================================================
-- HOW TO CREATE THE FIRST ADMIN USER (run in Python):
--
--   import bcrypt, psycopg2
--   pw = bcrypt.hashpw(b'your-password', bcrypt.gensalt(rounds=12)).decode()
--   conn = psycopg2.connect(host='localhost', database='KLDA-HFT_Database',
--                           user='postgres', password='MyKldaTechnologies2025!')
--   cur = conn.cursor()
--   cur.execute("""
--       INSERT INTO users (username, email, password_hash, role)
--       VALUES ('admin', 'admin@klda.fund', %s, 'admin')
--   """, (pw,))
--   conn.commit(); conn.close()
--   print("Admin user created")
-- ============================================================
