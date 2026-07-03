import psycopg2
conn = psycopg2.connect(host='localhost', port=5432, database='KLDA-HFT_Database', user='postgres', password='MyKldaTechnologies2025!')
cur = conn.cursor()

# Check current table
cur.execute("SELECT COUNT(*) FROM current")
print(f"current rows: {cur.fetchone()[0]}")

cur.execute("SELECT COUNT(*) FROM current WHERE bid > 0")
print(f"current with live price: {cur.fetchone()[0]}")

# Check ticks table
cur.execute("SELECT COUNT(*) FROM ticks")
print(f"ticks rows: {cur.fetchone()[0]}")

# Check signals
cur.execute("SELECT COUNT(*) FROM signals")
print(f"signals rows: {cur.fetchone()[0]}")

# Sample current rows
cur.execute("SELECT symbol, bid, ask, spread FROM current ORDER BY symbol LIMIT 10")
print("\nSample current rows:")
for r in cur.fetchall():
    print(f"  {r[0]:15s} bid={r[1]} ask={r[2]} spread={r[3]}")

conn.close()
