import psycopg2
conn = psycopg2.connect(host='localhost', port=5432, database='KLDA-HFT_Database', user='postgres', password='MyKldaTechnologies2025!')
cur = conn.cursor()

# Check active/long-running queries
cur.execute("""
    SELECT pid, now() - query_start AS duration, state, left(query,100) as query
    FROM pg_stat_activity
    WHERE state != 'idle' AND query_start IS NOT NULL
    ORDER BY duration DESC
""")
rows = cur.fetchall()
print(f'Active queries: {len(rows)}')
for r in rows:
    print(f'  PID {r[0]} | {str(r[1]).split(".")[0]} | {r[2]} | {r[3]}')

# Check blocked queries
cur.execute("""
    SELECT pid, wait_event_type, wait_event, left(query,80)
    FROM pg_stat_activity
    WHERE wait_event_type = 'Lock'
""")
blocked = cur.fetchall()
print(f'\nBlocked by locks: {len(blocked)}')
for r in blocked:
    print(f'  PID {r[0]} | {r[1]}.{r[2]} | {r[3]}')

conn.close()
