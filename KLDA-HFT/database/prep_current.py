import psycopg2
conn = psycopg2.connect(host='localhost', port=5432, database='KLDA-HFT_Database', user='postgres', password='MyKldaTechnologies2025!')
conn.autocommit = True
cur = conn.cursor()

# Show what's live
cur.execute("SELECT symbol, bid, ask FROM current WHERE bid > 0 ORDER BY symbol")
live = cur.fetchall()
print(f"Symbols with live prices ({len(live)}):")
for r in live:
    print(f"  {r[0]:20s} bid={r[1]}")

# Remove zero-price rows — engine will add them back when MT5 bridge runs
cur.execute("DELETE FROM current WHERE bid = 0")
print(f"\nRemoved {cur.rowcount} zero-price rows from current")

cur.execute("SELECT COUNT(*) FROM current")
print(f"current rows remaining: {cur.fetchone()[0]}")

conn.close()
