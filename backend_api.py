from flask import Flask, jsonify
from flask_cors import CORS
import psycopg2
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

@app.route('/api/assets', methods=['GET'])
def get_assets():
    conn = psycopg2.connect(
        host="localhost",
        database="market_data",
        user="postgres",
        password="MyStrongDBpass2025!"
    )
    cursor = conn.cursor()

    query = """
        SELECT DISTINCT ticker, open, high, low, close, volume, trades
        FROM stock_prices
        WHERE date = (SELECT MAX(date) FROM stock_prices)
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()

    assets = []
    for row in rows:
        assets.append({
            "ticker": row[0],
            "open": float(row[1]),
            "high": float(row[2]),
            "low": float(row[3]),
            "close": float(row[4]),
            "volume": int(row[5]) if row[5] is not None else 0,
            "trades": int(row[6]) if row[6] is not None else 0,
            "watch": False  # default watchlist flag
        })

    return jsonify(assets)

@app.route('/api/price-history/<string:ticker>', methods=['GET'])
def get_price_history(ticker):
    conn = psycopg2.connect(
        host="localhost",
        database="market_data",
        user="postgres",
        password="MyStrongDBpass2025!"
    )
    cursor = conn.cursor()

    two_years_ago = (datetime.now() - timedelta(days=730)).strftime('%Y-%m-%d')

    query = """
        SELECT date, open, high, low, close, volume
        FROM stock_prices
        WHERE ticker = %s AND date >= %s
        ORDER BY date ASC
    """
    cursor.execute(query, (ticker, two_years_ago))
    rows = cursor.fetchall()
    conn.close()

    data = []
    for row in rows:
        data.append({
            "date": row[0].strftime("%Y-%m-%d"),
            "open": float(row[1]),
            "high": float(row[2]),
            "low": float(row[3]),
            "close": float(row[4]),
            "volume": int(row[5]) if row[5] is not None else 0
        })

    return jsonify(data)

if __name__ == "__main__":
    app.run(port=5000, debug=True)
