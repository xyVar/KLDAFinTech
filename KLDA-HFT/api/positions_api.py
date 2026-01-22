#!/usr/bin/env python3
"""
Positions API - Serves trading data to dashboard
"""

from flask import Flask, jsonify
import psycopg2

app = Flask(__name__)

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'KLDA-HFT_Database',
    'user': 'postgres',
    'password': 'MyKldaTechnologies2025!'
}

def get_db():
    return psycopg2.connect(**DB_CONFIG)

@app.route('/api/positions', methods=['GET'])
def get_positions():
    """Get open positions"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            symbol,
            entry_time,
            entry_price,
            shares,
            position_size,
            stop_loss,
            take_profit,
            mt5_ticket
        FROM positions
        WHERE status = 'OPEN'
        ORDER BY entry_time DESC;
    """)

    positions = []
    for row in cursor.fetchall():
        positions.append({
            'symbol': row[0],
            'entry_time': str(row[1]),
            'entry_price': float(row[2]),
            'shares': float(row[3]),
            'position_size': float(row[4]),
            'stop_loss': float(row[5]),
            'take_profit': float(row[6]),
            'mt5_ticket': int(row[7])
        })

    cursor.close()
    conn.close()

    return jsonify({'positions': positions})

@app.route('/api/closed_trades', methods=['GET'])
def get_closed_trades():
    """Get closed trades"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            symbol,
            entry_time,
            exit_time,
            entry_price,
            exit_price,
            position_size,
            pnl
        FROM positions
        WHERE status = 'CLOSED'
        ORDER BY exit_time DESC
        LIMIT 20;
    """)

    trades = []
    for row in cursor.fetchall():
        trades.append({
            'symbol': row[0],
            'entry_time': str(row[1]),
            'exit_time': str(row[2]),
            'entry_price': float(row[3]),
            'exit_price': float(row[4]),
            'position_size': float(row[5]),
            'pnl': float(row[6])
        })

    cursor.close()
    conn.close()

    return jsonify({'trades': trades})

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get trading statistics"""
    conn = get_db()
    cursor = conn.cursor()

    # Open positions count
    cursor.execute("SELECT COUNT(*) FROM positions WHERE status = 'OPEN';")
    open_count = cursor.fetchone()[0]

    # Total closed trades
    cursor.execute("SELECT COUNT(*) FROM positions WHERE status = 'CLOSED';")
    total_trades = cursor.fetchone()[0]

    # Win rate
    cursor.execute("SELECT COUNT(*) FROM positions WHERE status = 'CLOSED' AND pnl > 0;")
    wins = cursor.fetchone()[0]
    win_rate = (wins / total_trades * 100) if total_trades > 0 else 0

    # Realized P&L
    cursor.execute("SELECT COALESCE(SUM(pnl), 0) FROM positions WHERE status = 'CLOSED';")
    realized_pnl = cursor.fetchone()[0]

    # Unrealized P&L (would need current prices - placeholder)
    unrealized_pnl = 0

    # Account balance
    initial_balance = 10000.0
    balance = initial_balance + realized_pnl

    cursor.close()
    conn.close()

    return jsonify({
        'balance': balance,
        'open_positions': open_count,
        'unrealized_pnl': unrealized_pnl,
        'realized_pnl': realized_pnl,
        'win_rate': win_rate,
        'total_trades': total_trades
    })

if __name__ == '__main__':
    print("=" * 60)
    print("POSITIONS API SERVER")
    print("=" * 60)
    print("Starting on http://localhost:5001")
    print("Endpoints:")
    print("  GET /api/positions      - Open positions")
    print("  GET /api/closed_trades  - Closed trades")
    print("  GET /api/stats          - Trading statistics")
    print("=" * 60)

    app.run(host='0.0.0.0', port=5001, debug=False, threaded=True)
