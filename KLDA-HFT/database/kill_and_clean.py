import psycopg2
conn = psycopg2.connect(host='localhost', port=5432, database='KLDA-HFT_Database', user='postgres', password='MyKldaTechnologies2025!')
conn.autocommit = True
cur = conn.cursor()

# Show all active connections
cur.execute("""
    SELECT pid, usename, application_name, state, wait_event_type, wait_event, left(query,60)
    FROM pg_stat_activity
    WHERE pid != pg_backend_pid()
    ORDER BY pid
""")
print("Active connections:")
for r in cur.fetchall():
    print(f"  PID {r[0]} | {r[2][:15]} | {r[3]} | {r[4]}.{r[5]} | {r[6]}")

# Kill any idle-in-transaction or long-running connections (not our own)
cur.execute("""
    SELECT pg_terminate_backend(pid)
    FROM pg_stat_activity
    WHERE pid != pg_backend_pid()
    AND (state = 'idle in transaction' OR state = 'idle in transaction (aborted)')
""")
killed = cur.fetchall()
print(f"\nKilled idle-in-transaction connections: {len(killed)}")

# Now check ticks
cur.execute("SELECT COUNT(*) FROM ticks")
print(f"ticks count: {cur.fetchone()[0]}")
cur.execute("SELECT pg_size_pretty(pg_total_relation_size('ticks'))")
print(f"ticks size: {cur.fetchone()[0]}")

conn.close()
