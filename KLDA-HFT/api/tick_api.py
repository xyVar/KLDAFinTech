#!/usr/bin/env python3
"""
KLDA-HFT Tick Monitor API
Serves live tick data and symbol list to the frontend dashboard
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2
import psycopg2.extras
from datetime import datetime, timezone
import time

app = Flask(__name__)
CORS(app)

DB_CONFIG = {
    'host': 'localhost', 'port': 5432,
    'database': 'KLDA-HFT_Database',
    'user': 'postgres', 'password': 'MyKldaTechnologies2025!'
}

SYMBOL_GROUPS = {
    'Stocks': [
        'AAPL.US-24','AMD.US-24','AMZN.US-24','AVGO.US-24','CSCO.US-24',
        'GOOG.US-24','INTC.US-24','META.US-24','MSFT.US-24','NVDA.US-24',
        'ORCL.US-24','PLTR.US-24','TSLA.US-24','NFLX.US-24','TSM.US'
    ],
    'Commodities': [
        'SpotCrude','SpotBrent','NatGas','XAUUSD','XAGUSD',
        'XPTUSD','XPDUSD','Copper','Gasoline','Corn',
        'Wheat','Soybeans','Coffee','Cotton','Sugar'
    ],
    'Indices': [
        'NAS100','US500','US30','UK100','GER40',
        'JPN225','FRA40','AUS200','HK50','CN50',
        'EUSTX50','VIX','USDX','EURX','JPYX','US2000'
    ],
    'Forex': [
        'EURUSD','GBPUSD','USDJPY','USDCAD','AUDUSD',
        'NZDUSD','USDCHF','USDCNH','EURGBP','EURJPY',
        'GBPJPY','AUDJPY','EURAUD','GBPAUD','CADJPY',
        'CHFJPY','EURCAD','GBPCAD','USDMXN','USDZAR'
    ]
}

def get_conn():
    return psycopg2.connect(**DB_CONFIG)

# ── GET /api/symbols ─────────────────────────────────────────
@app.route('/api/symbols')
def get_symbols():
    try:
        conn = get_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT symbol, bid, ask, spread,
                   EXTRACT(EPOCH FROM (NOW() - last_updated)) AS age_seconds
            FROM current
            ORDER BY symbol
        """)
        rows = {r['symbol']: r for r in cur.fetchall()}
        conn.close()

        result = {}
        for group, symbols in SYMBOL_GROUPS.items():
            result[group] = []
            for sym in symbols:
                row = rows.get(sym, {})
                result[group].append({
                    'symbol': sym,
                    'bid':    float(row.get('bid', 0) or 0),
                    'ask':    float(row.get('ask', 0) or 0),
                    'spread': float(row.get('spread', 0) or 0),
                    'age':    float(row.get('age_seconds', 9999) or 9999),
                    'live':   bool(row and float(row.get('bid', 0) or 0) > 0)
                })
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ── GET /api/ticks/<symbol>?since=<epoch_ms>&limit=100 ───────
@app.route('/api/ticks/<symbol>')
def get_ticks(symbol):
    since_ms = request.args.get('since', 0, type=float)
    limit    = request.args.get('limit', 100, type=int)

    try:
        conn = get_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        if since_ms > 0:
            since_ts = datetime.fromtimestamp(since_ms / 1000.0, tz=timezone.utc)
            cur.execute("""
                SELECT time, bid, ask, spread, volume, buy_volume, sell_volume
                FROM ticks
                WHERE symbol = %s AND time > %s
                ORDER BY time DESC
                LIMIT %s
            """, (symbol, since_ts, limit))
        else:
            cur.execute("""
                SELECT time, bid, ask, spread, volume, buy_volume, sell_volume
                FROM ticks
                WHERE symbol = %s
                ORDER BY time DESC
                LIMIT %s
            """, (symbol, limit))

        ticks = []
        for r in cur.fetchall():
            ticks.append({
                'time':       r['time'].isoformat(),
                'time_ms':    int(r['time'].timestamp() * 1000),
                'bid':        float(r['bid'] or 0),
                'ask':        float(r['ask'] or 0),
                'spread':     float(r['spread'] or 0),
                'volume':     int(r['volume'] or 0),
                'buy_vol':    int(r['buy_volume'] or 0),
                'sell_vol':   int(r['sell_volume'] or 0),
            })
        conn.close()
        return jsonify({'symbol': symbol, 'ticks': ticks, 'count': len(ticks)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ── GET /api/current ─────────────────────────────────────────
@app.route('/api/current')
def get_current():
    try:
        conn = get_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT symbol, bid, ask, spread,
                   last_updated,
                   EXTRACT(EPOCH FROM (NOW() - last_updated)) AS age_seconds
            FROM current
            WHERE bid > 0
            ORDER BY symbol
        """)
        rows = []
        for r in cur.fetchall():
            rows.append({
                'symbol':  r['symbol'],
                'bid':     float(r['bid']),
                'ask':     float(r['ask']),
                'spread':  float(r['spread']),
                'updated': r['last_updated'].isoformat(),
                'age':     float(r['age_seconds'] or 0)
            })
        conn.close()
        return jsonify(rows)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ── GET /api/stats ────────────────────────────────────────────
@app.route('/api/stats')
def get_stats():
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM ticks")
        tick_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM signals")
        signal_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM current WHERE bid > 0")
        live_count = cur.fetchone()[0]
        conn.close()
        return jsonify({
            'ticks_total':   tick_count,
            'signals_total': signal_count,
            'live_symbols':  live_count,
            'server_time':   datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("=" * 50)
    print("KLDA-HFT Tick Monitor API")
    print("http://localhost:5001")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5001, debug=False, threaded=True)
