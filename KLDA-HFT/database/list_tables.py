import psycopg2
conn = psycopg2.connect(host='localhost', port=5432, database='KLDA-HFT_Database', user='postgres', password='MyKldaTechnologies2025!')
cur = conn.cursor()

cur.execute("""
    SELECT table_name,
           pg_size_pretty(pg_total_relation_size(quote_ident(table_name))) as size,
           (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name AND table_schema = 'public') as cols
    FROM information_schema.tables t
    WHERE table_schema = 'public'
    ORDER BY table_name
""")
rows = cur.fetchall()

bars   = [(r[0],r[1]) for r in rows if r[0].endswith('_bars')]
hist   = [(r[0],r[1]) for r in rows if r[0].endswith('_history')]
other  = [(r[0],r[1]) for r in rows if not r[0].endswith('_bars') and not r[0].endswith('_history')]

print(f"TOTAL TABLES: {len(rows)}")
print(f"  _bars tables:    {len(bars)}")
print(f"  _history tables: {len(hist)}")
print(f"  system tables:   {len(other)}")

print(f"\n--- SYSTEM / UNIVERSAL TABLES ({len(other)}) ---")
for name, size in other:
    print(f"  {name:20s}  {size}")

print(f"\n--- _BARS TABLES ({len(bars)}) ---")
# Group by category
stocks   = [r for r in bars if any(s in r[0] for s in ['tsla','nvda','pltr','amd','avgo','meta','aapl','msft','orcl','amzn','csco','goog','intc'])]
comm     = [r for r in bars if any(s in r[0] for s in ['spotcrude','spotbrent','natgas','xauusd','xagusd','xptusd','xpdusd','copper','gasoline','corn','wheat','soybeans','coffee','cotton','sugar'])]
indices  = [r for r in bars if any(s in r[0] for s in ['nas100','us500','us30','uk100','ger40','jpn225','fra40','aus200','hk50','cn50','eustx50','vix','usdx','eurx','jpyx','us2000'])]
forex    = [r for r in bars if r not in stocks and r not in comm and r not in indices]

print(f"\n  Stocks ({len(stocks)}):")
for name, size in sorted(stocks): print(f"    {name:25s}  {size}")
print(f"\n  Commodities ({len(comm)}):")
for name, size in sorted(comm): print(f"    {name:25s}  {size}")
print(f"\n  Indices ({len(indices)}):")
for name, size in sorted(indices): print(f"    {name:25s}  {size}")
print(f"\n  Forex ({len(forex)}):")
for name, size in sorted(forex): print(f"    {name:25s}  {size}")

conn.close()
