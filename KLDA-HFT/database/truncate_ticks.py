import psycopg2
conn = psycopg2.connect(host='localhost', port=5432, database='KLDA-HFT_Database', user='postgres', password='MyKldaTechnologies2025!')
conn.autocommit = True
cur = conn.cursor()

print("Getting actual ticks size (all chunks)...")
cur.execute("""
    SELECT pg_size_pretty(hypertable_size('ticks'))
""")
print(f"  Total ticks size: {cur.fetchone()[0]}")

print("Truncating ticks table (all chunks)...")
cur.execute("TRUNCATE ticks")
print("Done.")

cur.execute("SELECT COUNT(*) FROM ticks")
print(f"ticks count after: {cur.fetchone()[0]}")

conn.close()
