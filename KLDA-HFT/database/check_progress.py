import psycopg2
conn = psycopg2.connect(host='localhost', port=5432, database='KLDA-HFT_Database', user='postgres', password='MyKldaTechnologies2025!')
cur = conn.cursor()

cur.execute('SELECT symbol, timeframe, COUNT(*) as cnt, MIN(time) as first FROM bars GROUP BY symbol, timeframe ORDER BY symbol, timeframe')
rows = cur.fetchall()
print(f'BARS TABLE: {len(rows)} symbol/timeframe combos')
by_sym = {}
for r in rows:
    if r[0] not in by_sym: by_sym[r[0]] = {}
    by_sym[r[0]][r[1]] = (r[2], str(r[3])[:10])
for sym, tfs in sorted(by_sym.items()):
    first_date = min(v[1] for v in tfs.values())
    total = sum(v[0] for v in tfs.values())
    print(f'  {sym:15s} {total:8,} bars | from {first_date}')

cur.execute('SELECT COUNT(*) FROM ticks')
print(f'\nTICKS: {cur.fetchone()[0]:,} total')
conn.close()
