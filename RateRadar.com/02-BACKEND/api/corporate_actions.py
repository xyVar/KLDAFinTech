import requests
import psycopg2
from datetime import datetime, timedelta
import time

# DB credentials
conn = psycopg2.connect(
    dbname="market_data",
    user="postgres",
    password="MyStrongDBpass2025!",
    host="localhost",
    port="5432"
)
cursor = conn.cursor()

# Polygon API key
API_KEY = "VjJeu2vP2eDMrGnQi4OkuWWsjrwBnElh"

# Dates
end_date = datetime.today().strftime("%Y-%m-%d")
start_date = (datetime.today() - timedelta(days=730)).strftime("%Y-%m-%d")

# Load tickers from the tickers table
cursor.execute("SELECT ticker FROM tickers")
tickers = [row[0] for row in cursor.fetchall()]

# Fetch and insert price data for each ticker
for ticker in tickers:
    print(f"Fetching data for: {ticker}")
    url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/{start_date}/{end_date}?adjusted=true&sort=asc&limit=50000&apiKey={API_KEY}"
    try:
        res = requests.get(url)
        if res.status_code == 200:
            results = res.json().get("results", [])
            for row in results:
                price_date = datetime.utcfromtimestamp(row["t"] / 1000).date()
                cursor.execute("""
                    INSERT INTO stock_prices (ticker, date, open, high, low, close, volume, vw, trades)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (ticker, date) DO UPDATE SET
                        open = EXCLUDED.open,
                        high = EXCLUDED.high,
                        low = EXCLUDED.low,
                        close = EXCLUDED.close,
                        volume = EXCLUDED.volume,
                        vw = EXCLUDED.vw,
                        trades = EXCLUDED.trades;
                """, (
                    ticker,
                    price_date,
                    row.get("o"), row.get("h"), row.get("l"), row.get("c"),
                    row.get("v"), row.get("vw"), row.get("n")
                ))
            conn.commit()
            print(f"✅ Inserted {len(results)} rows for {ticker}")
        else:
            print(f"❌ Error for {ticker}: {res.status_code} – {res.text}")
    except Exception as e:
        print(f"⚠️ Exception for {ticker}: {str(e)}")

    time.sleep(12)  # Respect API rate limit

cursor.close()
conn.close()

print("✅ All done!")
