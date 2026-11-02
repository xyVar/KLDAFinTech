import os
import psycopg2
import requests
import datetime
import time

# === CONFIGURATION ===
API_KEY = "VjJeu2vP2eDMrGnQi4OkuWWsjrwBnElh"
DB_CONFIG = {
    "host": "localhost",
    "database": "market_data",
    "user": "postgres",
    "password": "MyStrongDBpass2025!"
}
DATE_FROM = "2023-03-21"
DATE_TO = "2025-03-20"

def get_tickers():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("SELECT ticker FROM stocks_available ORDER BY ticker ASC")
    tickers = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return tickers

def get_last_fetched_ticker():
    try:
        with open("last_ticker.txt", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return None

def save_last_fetched_ticker(ticker):
    with open("last_ticker.txt", "w") as f:
        f.write(ticker)

def fetch_data(ticker):
    url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/{DATE_FROM}/{DATE_TO}?adjusted=true&sort=asc&limit=50000&apiKey={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get("results", [])
    else:
        print(f"❌ Failed to fetch {ticker}: {response.status_code}")
        return []

def insert_data(ticker, data):
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    inserted = 0
    try:
        for row in data:
            cursor.execute("""
                INSERT INTO stock_prices (
                    ticker, date, open, high, low, close, volume, trades, vwap
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                ticker,
                datetime.datetime.fromtimestamp(row["t"] / 1000, datetime.UTC).date(),
                row["o"],
                row["h"],
                row["l"],
                row["c"],
                row["v"],
                row.get("n"),
                row.get("vw")
            ))
            inserted += 1
        conn.commit()
    except Exception as e:
        print(f"⚠️ Insert error for {ticker}: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
    return inserted

def main():
    tickers = get_tickers()

    # HARD RESUME from index 813 (VFC)
    start_index = 3420
    print(f"🚀 Hard resume from ticker: {tickers[start_index]}")
    print(f"📊 Total tickers to process: {len(tickers) - start_index}")

    for i, ticker in enumerate(tickers[start_index:], start=start_index + 1):
        print(f"📡 Fetching data for {ticker} ({i}/{len(tickers)})...")
        data = fetch_data(ticker)
        inserted = insert_data(ticker, data)
        print(f"✅ Inserted {inserted} records for {ticker}.")
        save_last_fetched_ticker(ticker)
        time.sleep(12)


if __name__ == "__main__":
    main()
