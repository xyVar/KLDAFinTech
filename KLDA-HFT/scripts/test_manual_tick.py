#!/usr/bin/env python3
"""Send a manual test tick with unique timestamp to verify HISTORY table inserts"""

import requests
from datetime import datetime

# Send a test tick with current timestamp
test_tick = {
    'ticks': [{
        'symbol': 'TSLA.US',
        'bid': 449.99,
        'ask': 450.01,
        'spread': 2.0,
        'volume': 9999,
        'flags': 2,  # BUY flag
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    }]
}

print("Sending manual test tick...")
print(f"Timestamp: {test_tick['ticks'][0]['timestamp']}")

response = requests.post('http://localhost:5000/tick/batch', json=test_tick)

print(f"Response: {response.status_code}")
print(f"Body: {response.text}")

# Wait a moment and check database
import time
time.sleep(2)

import psycopg2
conn = psycopg2.connect(
    host='localhost',
    port=5432,
    database='KLDA-HFT_Database',
    user='postgres',
    password='MyKldaTechnologies2025!'
)
cursor = conn.cursor()

# Check CURRENT table
cursor.execute("SELECT bid, ask, buy_volume, last_updated FROM current WHERE symbol='TSLA';")
row = cursor.fetchone()
print(f"\n[CURRENT] TSLA: Bid={row[0]}, Ask={row[1]}, BuyVol={row[2]}, Updated={row[3]}")

# Check HISTORY table (last 3 ticks)
cursor.execute("SELECT time, bid, ask, buy_volume FROM tsla_history ORDER BY time DESC LIMIT 3;")
print(f"\n[HISTORY] TSLA last 3 ticks:")
for row in cursor.fetchall():
    print(f"  {row[0]} | Bid={row[1]} | Ask={row[2]} | BuyVol={row[3]}")

conn.close()
