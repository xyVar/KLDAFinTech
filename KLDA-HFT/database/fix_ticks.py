import psycopg2
conn = psycopg2.connect(host='localhost', port=5432, database='KLDA-HFT_Database', user='postgres', password='MyKldaTechnologies2025!')
conn.autocommit = True
cur = conn.cursor()

# Check ticks by symbol (fast via index)
print("Checking ticks table size...")
cur.execute("SELECT pg_size_pretty(pg_total_relation_size('ticks'))")
print(f"  ticks table size: {cur.fetchone()[0]}")

# Check indexes on ticks
cur.execute("""
    SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'ticks'
""")
print("\nIndexes on ticks:")
for r in cur.fetchall():
    print(f"  {r[0]}: {r[1][:80]}")

# Drop all chunks (faster than TRUNCATE for TimescaleDB)
print("\nDropping all ticks chunks...")
cur.execute("""
    SELECT drop_chunks('ticks', older_than => NOW() + INTERVAL '100 years')
""")
result = cur.fetchall()
print(f"  Chunks dropped: {len(result)}")

cur.execute("SELECT COUNT(*) FROM ticks")
print(f"  Ticks remaining: {cur.fetchone()[0]}")

conn.close()
print("Done.")
