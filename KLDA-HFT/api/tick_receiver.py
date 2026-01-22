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

# Enable CORS manually
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    return response

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

@app.route('/api/bars/<symbol>/<timeframe>', methods=['GET'])
def get_bars(symbol, timeframe):
    """
    Get OHLCV bar data for a symbol at a specific timeframe

    Parameters:
    - symbol: Asset symbol (e.g., TSLA, NatGas, SpotCrude)
    - timeframe: M1, M5, M15, M30, H1, H4, D1, W1, MN1

    Optional query params:
    - limit: Number of bars to return (default: 100)

    Returns:
    [
        {"time": "2026-01-20T10:00:00", "open": 100.5, "high": 101.2, "low": 100.3, "close": 101.0, "volume": 1234, "spread": 3},
        ...
    ]
    """
    try:
        limit = request.args.get('limit', 100, type=int)

        # Validate timeframe
        timeframe_intervals = {
            'M1': '1 minute',
            'M5': '5 minutes',
            'M15': '15 minutes',
            'M30': '30 minutes',
            'H1': '1 hour',
            'H4': '4 hours',
            'D1': '1 day',
            'W1': '1 week',
            'MN1': '1 month'
        }

        if timeframe.upper() not in timeframe_intervals:
            return jsonify({'error': f'Invalid timeframe. Must be one of: {list(timeframe_intervals.keys())}'}), 400

        interval = timeframe_intervals[timeframe.upper()]
        symbol_lower = symbol.lower()
        history_table = f"{symbol_lower}_history"

        conn = get_db_connection()
        cursor = conn.cursor()

        # Query history table and aggregate on-the-fly
        query = f"""
            WITH bucketed_data AS (
                SELECT
                    time_bucket('{interval}', time) AS time_bucket,
                    FIRST(bid, time) as open,
                    MAX(ask) as high,
                    MIN(bid) as low,
                    LAST(ask, time) as close,
                    SUM(volume) as volume,
                    AVG(spread)::INTEGER as spread
                FROM {history_table}
                WHERE time >= NOW() - INTERVAL '7 days'
                GROUP BY time_bucket
                ORDER BY time_bucket DESC
                LIMIT %s
            )
            SELECT * FROM bucketed_data ORDER BY time_bucket ASC;
        """

        cursor.execute(query, (limit,))
        rows = cursor.fetchall()

        # Format response
        bars = []
        for row in rows:
            bars.append({
                'time': row[0].isoformat(),
                'open': float(row[1]) if row[1] else 0,
                'high': float(row[2]) if row[2] else 0,
                'low': float(row[3]) if row[3] else 0,
                'close': float(row[4]) if row[4] else 0,
                'volume': int(row[5]) if row[5] else 0,
                'spread': int(row[6]) if row[6] else 0
            })

        cursor.close()
        conn.close()

        return jsonify(bars), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ticks/<symbol>', methods=['GET'])
def get_tick_history(symbol):
    """
    Get recent tick history for a symbol

    Parameters:
    - symbol: Asset symbol (e.g., TSLA, NatGas, SpotCrude)

    Optional query params:
    - limit: Number of ticks to return (default: 50)

    Returns:
    [
        {"time": "2026-01-20T10:00:00.123", "bid": 100.5, "ask": 100.53, "spread": 3, "volume": 100},
        ...
    ]
    """
    try:
        limit = request.args.get('limit', 50, type=int)

        # Build history table name (e.g., tsla_history)
        symbol_lower = symbol.lower()
        history_table = f"{symbol_lower}_history"

        conn = get_db_connection()
        cursor = conn.cursor()

        # Query history table
        query = f"""
            SELECT
                time,
                bid,
                ask,
                spread,
                volume
            FROM {history_table}
            ORDER BY time DESC
            LIMIT %s;
        """

        cursor.execute(query, (limit,))
        rows = cursor.fetchall()

        # Format response
        ticks = []
        for row in rows:
            ticks.append({
                'time': row[0].isoformat(),
                'bid': float(row[1]),
                'ask': float(row[2]),
                'spread': int(row[3]) if row[3] else 0,
                'volume': int(row[4]) if row[4] else 0
            })

        # Reverse to get chronological order
        ticks.reverse()

        cursor.close()
        conn.close()

        return jsonify(ticks), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/current', methods=['GET'])
def get_current_ticks():
    """
    Get current tick data for all symbols

    Returns:
    [
        {"symbol": "TSLA", "bid": 100.5, "ask": 100.53, "spread": 3, "volume": 100, "last_updated": "2026-01-20T10:00:00"},
        ...
    ]
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
            SELECT
                symbol,
                bid,
                ask,
                spread,
                volume,
                last_updated,
                EXTRACT(EPOCH FROM (NOW() - last_updated)) as seconds_ago
            FROM current
            ORDER BY symbol;
        """

        cursor.execute(query)
        rows = cursor.fetchall()

        # Format response
        ticks = []
        for row in rows:
            ticks.append({
                'symbol': row[0],
                'bid': float(row[1]),
                'ask': float(row[2]),
                'spread': int(row[3]) if row[3] else 0,
                'volume': int(row[4]) if row[4] else 0,
                'last_updated': row[5].isoformat() if row[5] else None,
                'seconds_ago': int(row[6]) if row[6] else 0
            })

        cursor.close()
        conn.close()

        return jsonify(ticks), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/positions', methods=['GET'])
def get_positions():
    """
    Get all positions (open and closed)

    Optional query params:
    - status: Filter by status ('OPEN' or 'CLOSED')
    - symbol: Filter by symbol
    - limit: Number of positions to return (default: 100)

    Returns:
    [
        {
            "id": 1,
            "symbol": "TSLA",
            "entry_time": "2026-01-20T10:00:00",
            "entry_price": 100.5,
            "shares": 10.0,
            "position_size": 1005.0,
            "stop_loss": 99.0,
            "take_profit": 102.0,
            "status": "OPEN",
            "exit_time": null,
            "exit_price": null,
            "pnl": null,
            "exit_reason": null
        },
        ...
    ]
    """
    try:
        status = request.args.get('status', None)
        symbol = request.args.get('symbol', None)
        limit = request.args.get('limit', 100, type=int)

        conn = get_db_connection()
        cursor = conn.cursor()

        # Build query
        query = "SELECT id, symbol, entry_time, entry_price, shares, position_size, stop_loss, take_profit, status, exit_time, exit_price, pnl, exit_reason FROM positions WHERE 1=1"
        params = []

        if status:
            query += " AND status = %s"
            params.append(status.upper())

        if symbol:
            query += " AND symbol = %s"
            params.append(symbol.upper())

        query += " ORDER BY entry_time DESC LIMIT %s;"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()

        # Format response
        positions = []
        for row in rows:
            positions.append({
                'id': row[0],
                'symbol': row[1],
                'entry_time': row[2].isoformat() if row[2] else None,
                'entry_price': float(row[3]) if row[3] else 0,
                'shares': float(row[4]) if row[4] else 0,
                'position_size': float(row[5]) if row[5] else 0,
                'stop_loss': float(row[6]) if row[6] else 0,
                'take_profit': float(row[7]) if row[7] else 0,
                'status': row[8],
                'exit_time': row[9].isoformat() if row[9] else None,
                'exit_price': float(row[10]) if row[10] else None,
                'pnl': float(row[11]) if row[11] else None,
                'exit_reason': row[12]
            })

        cursor.close()
        conn.close()

        return jsonify(positions), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/account', methods=['GET'])
def get_account_state():
    """
    Get current account state

    Returns:
    {
        "balance": 10000.00,
        "realized_pnl": 0.00,
        "unrealized_pnl": 0.00,
        "open_positions": 0,
        "total_trades": 0,
        "timestamp": "2026-01-20T10:00:00"
    }
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get latest account state
        query = """
            SELECT balance, realized_pnl, unrealized_pnl, open_positions, total_trades, timestamp
            FROM account_state
            ORDER BY timestamp DESC
            LIMIT 1;
        """

        cursor.execute(query)
        row = cursor.fetchone()

        if not row:
            return jsonify({'error': 'No account data found'}), 404

        account = {
            'balance': float(row[0]),
            'realized_pnl': float(row[1]),
            'unrealized_pnl': float(row[2]),
            'open_positions': int(row[3]),
            'total_trades': int(row[4]),
            'timestamp': row[5].isoformat() if row[5] else None
        }

        cursor.close()
        conn.close()

        return jsonify(account), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats/<symbol>', methods=['GET'])
def get_symbol_stats(symbol):
    """
    Get 24-hour statistics for a symbol

    Returns:
    {
        "symbol": "TSLA",
        "current_price": 100.5,
        "24h_open": 99.0,
        "24h_high": 102.0,
        "24h_low": 98.5,
        "24h_close": 100.5,
        "24h_change": 1.52,
        "24h_change_pct": 1.52,
        "total_ticks": 12345,
        "avg_spread": 3.2
    }
    """
    try:
        symbol_lower = symbol.lower()
        history_table = f"{symbol_lower}_history"

        conn = get_db_connection()
        cursor = conn.cursor()

        # Get current price
        cursor.execute("SELECT bid, ask FROM current WHERE symbol = %s;", (symbol.upper(),))
        current = cursor.fetchone()

        if not current:
            return jsonify({'error': f'Symbol {symbol} not found'}), 404

        current_bid = float(current[0])
        current_ask = float(current[1])
        current_price = (current_bid + current_ask) / 2

        # Get 24h statistics
        query = f"""
            WITH last_24h AS (
                SELECT bid, ask, spread, time
                FROM {history_table}
                WHERE time >= NOW() - INTERVAL '24 hours'
                ORDER BY time
            ),
            first_tick AS (
                SELECT (bid + ask) / 2 as price
                FROM {history_table}
                WHERE time >= NOW() - INTERVAL '24 hours'
                ORDER BY time ASC
                LIMIT 1
            )
            SELECT
                (SELECT price FROM first_tick) as h24_open,
                MAX((bid + ask) / 2) as h24_high,
                MIN((bid + ask) / 2) as h24_low,
                AVG(spread) as avg_spread,
                COUNT(*) as total_ticks
            FROM last_24h;
        """

        cursor.execute(query)
        stats_row = cursor.fetchone()

        if not stats_row or not stats_row[0]:
            # No data in last 24 hours, use all-time data
            query_all = f"""
                SELECT
                    MIN((bid + ask) / 2) as all_time_low,
                    MAX((bid + ask) / 2) as all_time_high,
                    AVG(spread) as avg_spread,
                    COUNT(*) as total_ticks
                FROM {history_table};
            """
            cursor.execute(query_all)
            all_time = cursor.fetchone()

            stats = {
                'symbol': symbol.upper(),
                'current_price': round(current_price, 2),
                '24h_open': None,
                '24h_high': round(float(all_time[1]), 2) if all_time[1] else None,
                '24h_low': round(float(all_time[0]), 2) if all_time[0] else None,
                '24h_close': round(current_price, 2),
                '24h_change': None,
                '24h_change_pct': None,
                'total_ticks': int(all_time[3]) if all_time[3] else 0,
                'avg_spread': round(float(all_time[2]), 2) if all_time[2] else 0
            }
        else:
            h24_open = float(stats_row[0])
            h24_high = float(stats_row[1])
            h24_low = float(stats_row[2])
            avg_spread = float(stats_row[3]) if stats_row[3] else 0
            total_ticks = int(stats_row[4])

            change = current_price - h24_open
            change_pct = (change / h24_open) * 100 if h24_open > 0 else 0

            stats = {
                'symbol': symbol.upper(),
                'current_price': round(current_price, 2),
                '24h_open': round(h24_open, 2),
                '24h_high': round(h24_high, 2),
                '24h_low': round(h24_low, 2),
                '24h_close': round(current_price, 2),
                '24h_change': round(change, 2),
                '24h_change_pct': round(change_pct, 2),
                'total_ticks': total_ticks,
                'avg_spread': round(avg_spread, 2)
            }

        cursor.close()
        conn.close()

        return jsonify(stats), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
    print("  POST /tick                      - Receive single tick")
    print("  POST /tick/batch                - Receive batch of ticks")
    print("  GET  /stats                     - View API statistics")
    print("  GET  /health                    - Health check")
    print("  GET  /api/current               - Get all current ticks")
    print("  GET  /api/bars/<symbol>/<tf>    - Get OHLCV bars (M1/M5/M15/H1/H4/D1)")
    print("  GET  /api/ticks/<symbol>        - Get recent tick history")
    print("  GET  /api/stats/<symbol>        - Get 24h symbol statistics")
    print("  GET  /api/positions             - Get trading positions")
    print("  GET  /api/account               - Get account state")
    print("=" * 60)

    # Run Flask app
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
