import psycopg2

conn = psycopg2.connect(
    host='localhost', port=5432,
    database='KLDA-HFT_Database',
    user='postgres',
    password='MyKldaTechnologies2025!'
)
cur = conn.cursor()

# ── 1. CREATE positions table ─────────────────────────────────────────────────
cur.execute("""
CREATE TABLE IF NOT EXISTS positions (
    id              SERIAL PRIMARY KEY,
    symbol          VARCHAR(20)        NOT NULL,
    direction       VARCHAR(5)         NOT NULL,
    entry_time      TIMESTAMPTZ        NOT NULL,
    entry_price     DOUBLE PRECISION   NOT NULL,
    shares          DOUBLE PRECISION   NOT NULL,
    position_size   DOUBLE PRECISION   NOT NULL,
    stop_loss       DOUBLE PRECISION   NOT NULL,
    take_profit     DOUBLE PRECISION   NOT NULL,
    status          VARCHAR(10)        NOT NULL DEFAULT 'OPEN',
    exit_time       TIMESTAMPTZ,
    exit_price      DOUBLE PRECISION,
    pnl             DOUBLE PRECISION,
    exit_reason     VARCHAR(20),
    signal_id       INTEGER,
    kelly_fraction  DOUBLE PRECISION,
    created_at      TIMESTAMPTZ        NOT NULL DEFAULT NOW()
);
""")
print("positions table: OK")

# ── 2. ALTER signals — add pattern_name + pattern_data (nullable, safe) ───────
for stmt, label in [
    ("ALTER TABLE signals ADD COLUMN IF NOT EXISTS pattern_name VARCHAR(40);",
     "signals.pattern_name: OK"),
    ("ALTER TABLE signals ADD COLUMN IF NOT EXISTS pattern_data JSONB;",
     "signals.pattern_data: OK"),
]:
    try:
        cur.execute(stmt)
        print(label)
    except Exception as e:
        conn.rollback()
        print("WARN: " + label + " — " + str(e))

conn.commit()

# ── 3. Verify ─────────────────────────────────────────────────────────────────
print()
print("=== VERIFICATION ===")

cur.execute("""
    SELECT column_name, data_type, is_nullable
    FROM information_schema.columns
    WHERE table_name = 'positions'
    ORDER BY ordinal_position
""")
print("positions columns:")
for r in cur.fetchall():
    print("  " + r[0].ljust(18) + r[1].ljust(30) + r[2])

print()
cur.execute("""
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_name = 'signals'
    ORDER BY ordinal_position
""")
print("signals columns:")
for r in cur.fetchall():
    print("  " + r[0].ljust(18) + r[1])

conn.close()
print("\nDone.")
