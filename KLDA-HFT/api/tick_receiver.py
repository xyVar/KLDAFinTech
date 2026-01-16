#!/usr/bin/env python3
"""
KLDA-HFT Tick Receiver API
Receives real-time tick data from MT5 and stores in PostgreSQL
"""

from flask import Flask, request, jsonify
import psycopg2
from psycopg2.extras import execute_batch
from datetime import datetime
import threading
import time

app = Flask(__name__)

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'KLDA-HFT_Database',
    'user': 'postgres',
    'password': 'MyKldaTechnologies2025!'
}

# Symbol mapping (MT5 symbol -> database symbol)
# MUST match case in CURRENT table!
SYMBOL_MAP = {
    'TSLA.US': 'TSLA',
    'NVDA.US': 'NVDA',
    'PLTR.US': 'PLTR',
    'AMD.US': 'AMD',
    'AVGO.US': 'AVGO',
    'META.US': 'META',
    'AAPL.US': 'AAPL',
    'MSFT.US': 'MSFT',
    'ORCL.US': 'ORCL',
    'AMZN.US': 'AMZN',
    'CSCO.US': 'CSCO',
    'GOOG.US': 'GOOG',
    'INTC.US': 'INTC',
    'VIX': 'VIX',
    'NAS100': 'NAS100',
    'NatGas': 'NatGas',
    'SpotCrude': 'SpotCrude'
}

# Batch processing
tick_buffer = []
buffer_lock = threading.Lock()
MAX_BUFFER_SIZE = 100
FLUSH_INTERVAL = 1.0  # seconds

# Statistics
stats = {
    'ticks_received': 0,
    'ticks_processed': 0,
    'errors': 0,
    'last_flush': datetime.now()
}

def get_db_connection():
    """Create database connection"""
    return psycopg2.connect(**DB_CONFIG)

def flush_ticks_to_db():
    """Flush buffered ticks to database"""
    global tick_buffer

    with buffer_lock:
        if not tick_buffer:
            return

        ticks_to_process = tick_buffer.copy()
        tick_buffer = []

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Group ticks by symbol for batch processing
        symbol_ticks = {}
        current_updates = []

        for tick in ticks_to_process:
            symbol = tick['symbol']
            if symbol not in symbol_ticks:
                symbol_ticks[symbol] = []
            symbol_ticks[symbol].append(tick)

            # Prepare CURRENT table update (keep only latest per symbol)
            current_updates.append(tick)

        # Update CURRENT table (one row per symbol)
        for tick in current_updates:
            symbol = tick['symbol']

            # Separate buy/sell volume based on flags
            # MT5 flags: BID=2, ASK=4, LAST=8, VOLUME=16, BUY=32, SELL=64
            flags = tick.get('flags', 0)

            # Only trades have volume (flags with LAST=8)
            if flags & 8:  # This is a TRADE tick
                buy_vol = tick['volume'] if (flags & 32) else 0   # BUY flag
                sell_vol = tick['volume'] if (flags & 64) else 0  # SELL flag
            else:  # This is a QUOTE tick (bid/ask update only)
                buy_vol = 0
                sell_vol = 0

            cursor.execute(f"""
                UPDATE current
                SET bid = %s,
                    ask = %s,
                    spread = %s,
                    volume = %s,
                    buy_volume = %s,
                    sell_volume = %s,
                    flags = %s,
                    last_updated = %s
                WHERE symbol = %s;
            """, (
                tick['bid'],
                tick['ask'],
                tick['spread'],
                tick['volume'],
                buy_vol,
                sell_vol,
                flags,
                tick['timestamp'],
                symbol
            ))

        # Insert into HISTORY tables (archive every tick)
        for symbol, ticks in symbol_ticks.items():
            # History table names are lowercase (e.g., tsla_history)
            history_table = f"{symbol.lower()}_history"

            insert_sql = f"""
                INSERT INTO {history_table} (time, bid, ask, spread, volume, buy_volume, sell_volume, flags)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (time) DO NOTHING;
            """

            batch_data = []
            for tick in ticks:
                # Separate buy/sell volume based on flags
                # MT5 flags: BID=2, ASK=4, LAST=8, VOLUME=16, BUY=32, SELL=64
                flags = tick.get('flags', 0)

                # Only trades have volume (flags with LAST=8)
                if flags & 8:  # This is a TRADE tick
                    buy_vol = tick['volume'] if (flags & 32) else 0   # BUY flag
                    sell_vol = tick['volume'] if (flags & 64) else 0  # SELL flag
                else:  # This is a QUOTE tick (bid/ask update only)
                    buy_vol = 0
                    sell_vol = 0

                batch_data.append((
                    tick['timestamp'], tick['bid'], tick['ask'], tick['spread'],
                    tick['volume'], buy_vol, sell_vol, flags
                ))

            execute_batch(cursor, insert_sql, batch_data)

        conn.commit()

        stats['ticks_processed'] += len(ticks_to_process)
        stats['last_flush'] = datetime.now()

        print(f"[FLUSH] Processed {len(ticks_to_process)} ticks | Total: {stats['ticks_processed']}")

        cursor.close()
        conn.close()

    except Exception as e:
        stats['errors'] += 1
        print(f"[ERROR] Database flush failed: {e}")

def background_flusher():
    """Background thread to flush ticks periodically"""
    while True:
        time.sleep(FLUSH_INTERVAL)
        flush_ticks_to_db()

@app.route('/tick', methods=['POST'])
def receive_tick():
    """
    Receive single tick from MT5 EA
    Expected JSON:
    {
        "symbol": "TSLA.US",
        "bid": 489.17,
        "ask": 489.20,
        "spread": 3,
        "volume": 12345,
        "flags": 2,
        "timestamp": "2026-01-13 15:30:45.123456"
    }
    """
    try:
        data = request.get_json()

        # Validate required fields
        required = ['symbol', 'bid', 'ask', 'spread', 'volume', 'flags', 'timestamp']
        if not all(field in data for field in required):
            return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400

        # Map MT5 symbol to database symbol
        mt5_symbol = data['symbol']
        db_symbol = SYMBOL_MAP.get(mt5_symbol)

        if not db_symbol:
            return jsonify({'status': 'error', 'message': f'Unknown symbol: {mt5_symbol}'}), 400

        # Parse timestamp
        timestamp = datetime.strptime(data['timestamp'], '%Y-%m-%d %H:%M:%S.%f')

        # Add to buffer
        with buffer_lock:
            tick_buffer.append({
                'symbol': db_symbol,
                'bid': float(data['bid']),
                'ask': float(data['ask']),
                'spread': float(data['spread']),
                'volume': int(data['volume']),
                'flags': int(data['flags']),
                'timestamp': timestamp
            })

            stats['ticks_received'] += 1

            # Force flush if buffer is full
            if len(tick_buffer) >= MAX_BUFFER_SIZE:
                threading.Thread(target=flush_ticks_to_db).start()

        return jsonify({'status': 'success'}), 200

    except Exception as e:
        stats['errors'] += 1
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/tick/batch', methods=['POST'])
def receive_tick_batch():
    """
    Receive batch of ticks from MT5 EA
    Expected JSON:
    {
        "ticks": [
            {"symbol": "TSLA.US", "bid": 489.17, ...},
            {"symbol": "NVDA.US", "bid": 145.23, ...}
        ]
    }
    """
    try:
        data = request.get_json()
        ticks = data.get('ticks', [])

        with buffer_lock:
            for tick_data in ticks:
                mt5_symbol = tick_data['symbol']
                db_symbol = SYMBOL_MAP.get(mt5_symbol)

                if not db_symbol:
                    continue

                timestamp = datetime.strptime(tick_data['timestamp'], '%Y-%m-%d %H:%M:%S.%f')

                tick_buffer.append({
                    'symbol': db_symbol,
                    'bid': float(tick_data['bid']),
                    'ask': float(tick_data['ask']),
                    'spread': float(tick_data['spread']),
                    'volume': int(tick_data['volume']),
                    'flags': int(tick_data.get('flags', 0)),
                    'timestamp': timestamp
                })

            stats['ticks_received'] += len(ticks)

        return jsonify({'status': 'success', 'received': len(ticks)}), 200

    except Exception as e:
        stats['errors'] += 1
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/stats', methods=['GET'])
def get_stats():
    """Get API statistics"""
    return jsonify({
        'ticks_received': stats['ticks_received'],
        'ticks_processed': stats['ticks_processed'],
        'buffer_size': len(tick_buffer),
        'errors': stats['errors'],
        'last_flush': stats['last_flush'].isoformat()
    }), 200

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1;")
        cursor.close()
        conn.close()
        return jsonify({'status': 'healthy', 'database': 'connected'}), 200
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

if __name__ == '__main__':
    print("=" * 60)
    print("KLDA-HFT Tick Receiver API")
    print("=" * 60)
    print("Starting background flusher thread...")

    # Start background flusher thread
    flusher_thread = threading.Thread(target=background_flusher, daemon=True)
    flusher_thread.start()

    print("API Server starting on http://localhost:5000")
    print("Endpoints:")
    print("  POST /tick        - Receive single tick")
    print("  POST /tick/batch  - Receive batch of ticks")
    print("  GET  /stats       - View statistics")
    print("  GET  /health      - Health check")
    print("=" * 60)

    # Run Flask app
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
