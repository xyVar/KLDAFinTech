#!/usr/bin/env python3
"""
KLDA-HFT Trading API — Compliance-Grade Edition
JWT auth, RBAC, immutable audit log, investor ledger, NAV history.

Auth endpoints:
  POST /api/login             — username+password → JWT token
  GET  /api/me                — current user from token
  POST /api/logout            — log LOGOUT (token invalidation is client-side)
  GET  /api/users             — list users  [admin]
  POST /api/users             — create user [admin]
  PUT  /api/users/<id>        — update role/active [admin]

Compliance endpoints:
  GET  /api/audit_log         — full audit trail [admin, risk_manager]
  GET  /api/investor_ledger   — capital in/out   [admin, risk_manager]
  POST /api/investor_ledger   — record entry      [admin]
  GET  /api/nav               — NAV history       [admin, risk_manager, viewer]
  POST /api/nav               — record daily NAV  [admin]
  GET  /api/compliance_report — exportable JSON   [admin]

Data endpoints (unchanged, now auth-gated):
  /api/account  /api/positions  /api/trades     /api/daily_pnl
  /api/transactions  /api/execution_log  /api/signals  /api/equity_history
  /api/symbols  /api/ticks/<s>  /api/bars/<s>   /api/stats  /api/current
"""

from flask import Flask, jsonify, request, g, send_file
from flask_cors import CORS
import psycopg2
import psycopg2.extras
from datetime import datetime, timezone, timedelta
import time
import functools
import os
import json
import jwt
import bcrypt
from dotenv import load_dotenv

load_dotenv()

JWT_SECRET       = os.environ.get('JWT_SECRET', 'dev-secret-change-in-prod')
JWT_EXPIRY_HOURS = int(os.environ.get('JWT_EXPIRY_HOURS', 8))

ALL_ROLES = ['admin', 'trader', 'viewer', 'risk_manager']

app = Flask(__name__)
CORS(app)

DB_CONFIG = {
    'host':     os.environ.get('DB_HOST',     'localhost'),
    'port':     int(os.environ.get('DB_PORT', 5432)),
    'database': os.environ.get('DB_NAME',     'KLDA-HFT_Database'),
    'user':     os.environ.get('DB_USER',     'postgres'),
    'password': os.environ.get('DB_PASSWORD', 'MyKldaTechnologies2025!'),
}

SYMBOL_GROUPS = {
    'Stocks': [
        'AAPL.US-24','AMD.US-24','AMZN.US-24','AVGO.US-24','CSCO.US-24',
        'GOOG.US-24','INTC.US-24','META.US-24','MSFT.US-24','NVDA.US-24',
        'ORCL.US-24','PLTR.US-24','TSLA.US-24'
    ],
    'Indices': [
        'NAS100','US500','US30','UK100','GER40',
        'JPN225','FRA40','AUS200','HK50','CN50',
        'EUSTX50','VIX','USDX','EURX','JPYX','US2000'
    ],
    'Commodities': [
        'SpotCrude','SpotBrent','NatGas','XAUUSD','XAGUSD',
        'XPTUSD','XPDUSD','Copper','Gasoline','Corn',
        'Wheat','Soybeans','Coffee','Cotton','Sugar'
    ],
    'Forex': [
        'EURUSD','GBPUSD','USDJPY','USDCAD','AUDUSD',
        'NZDUSD','USDCHF','USDCNH','EURGBP','EURJPY',
        'GBPJPY','AUDJPY','EURAUD','GBPAUD','CADJPY',
        'CHFJPY','EURCAD','GBPCAD','USDMXN','USDZAR'
    ]
}

# ── DB HELPERS ────────────────────────────────────────────────
def get_conn():
    return psycopg2.connect(**DB_CONFIG)

def safe_float(v, default=0.0):
    try:
        return float(v) if v is not None else default
    except:
        return default

def safe_int(v, default=0):
    try:
        return int(v) if v is not None else default
    except:
        return default

# ── AUTH HELPERS ──────────────────────────────────────────────
def hash_password(plain):
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt(rounds=12)).decode()

def check_password(plain, hashed):
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except:
        return False

def make_token(user_row):
    payload = {
        'sub':      str(user_row['id']),   # PyJWT requires sub to be a string
        'username': user_row['username'],
        'role':     user_row['role'],
        'exp':      datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRY_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')

def decode_token(token):
    return jwt.decode(token, JWT_SECRET, algorithms=['HS256'])

# ── AUDIT LOG ─────────────────────────────────────────────────
def log_action(user_id, username, role, action, resource,
               detail, ip, success=True, error_msg=None):
    """Write one immutable row to audit_log. Never raises — compliance logging
    must not break the main request flow."""
    try:
        conn = get_conn()
        cur  = conn.cursor()
        cur.execute("""
            INSERT INTO audit_log
                (user_id, username, role, action, resource, detail,
                 ip_address, success, error_msg)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            user_id, username, role,
            str(action)[:100], str(resource)[:200] if resource else None,
            psycopg2.extras.Json(detail) if detail else None,
            ip, success, error_msg
        ))
        conn.commit()
        conn.close()
    except Exception:
        pass  # silent — never let audit logging break the API

# ── RBAC DECORATOR ───────────────────────────────────────────
def require_auth(roles=None):
    """Decorator that validates JWT, enforces role, and writes audit log."""
    def decorator(f):
        @functools.wraps(f)
        def wrapped(*args, **kwargs):
            token = None
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                token = auth_header[7:]
            if not token:
                return jsonify({'error': 'Authentication required'}), 401

            try:
                payload = decode_token(token)
            except jwt.ExpiredSignatureError:
                return jsonify({'error': 'Token expired'}), 401
            except Exception:
                return jsonify({'error': 'Invalid token'}), 401

            user_id  = payload.get('sub')
            username = payload.get('username')
            role     = payload.get('role')

            if roles and role not in roles:
                log_action(user_id, username, role, 'ACCESS_DENIED',
                           request.path, None, request.remote_addr,
                           False, 'Insufficient role')
                return jsonify({'error': 'Access denied'}), 403

            g.user = payload
            g.user['uid'] = int(payload['sub'])   # integer version for DB FK columns
            # Log every authenticated request
            log_action(user_id, username, role,
                       request.path[:100], request.path,
                       None, request.remote_addr, True, None)
            return f(*args, **kwargs)
        return wrapped
    return decorator

# ═══════════════════════════════════════════════════════════════
# AUTH ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@app.route('/api/login', methods=['POST'])
def login():
    data     = request.get_json() or {}
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''
    ip       = request.remote_addr

    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400

    try:
        conn = get_conn()
        cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT id, username, email, password_hash, role, is_active
            FROM users WHERE username = %s
        """, (username,))
        user = cur.fetchone()

        if not user or not check_password(password, user['password_hash']):
            log_action(None, username, None, 'LOGIN', '/api/login',
                       None, ip, False, 'Invalid credentials')
            conn.close()
            return jsonify({'error': 'Invalid credentials'}), 401

        if not user['is_active']:
            log_action(user['id'], username, user['role'], 'LOGIN',
                       '/api/login', None, ip, False, 'Account inactive')
            conn.close()
            return jsonify({'error': 'Account is inactive'}), 403

        cur.execute("UPDATE users SET last_login = NOW() WHERE id = %s", (user['id'],))
        conn.commit()
        conn.close()

        token = make_token(user)
        log_action(user['id'], username, user['role'], 'LOGIN',
                   '/api/login', None, ip, True, None)

        return jsonify({
            'token': token,
            'user': {
                'id':       user['id'],
                'username': user['username'],
                'email':    user['email'],
                'role':     user['role'],
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/me')
@require_auth()
def get_me():
    u = g.user
    return jsonify({
        'id':       u['uid'],
        'username': u['username'],
        'role':     u['role'],
    })


@app.route('/api/logout', methods=['POST'])
@require_auth()
def logout():
    u = g.user
    log_action(u['uid'], u['username'], u['role'], 'LOGOUT',
               '/api/logout', None, request.remote_addr, True, None)
    return jsonify({'ok': True})


@app.route('/api/users')
@require_auth(roles=['admin'])
def get_users():
    try:
        conn = get_conn()
        cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT id, username, email, role, is_active, created_at, last_login
            FROM users ORDER BY id
        """)
        users = []
        for r in cur.fetchall():
            users.append({
                'id':         r['id'],
                'username':   r['username'],
                'email':      r['email'],
                'role':       r['role'],
                'is_active':  r['is_active'],
                'created_at': r['created_at'].isoformat() if r['created_at'] else None,
                'last_login': r['last_login'].isoformat() if r['last_login'] else None,
            })
        conn.close()
        return jsonify(users)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/users', methods=['POST'])
@require_auth(roles=['admin'])
def create_user():
    data     = request.get_json() or {}
    username = (data.get('username') or '').strip()
    email    = (data.get('email') or '').strip()
    password = data.get('password') or ''
    role     = data.get('role') or 'viewer'
    admin    = g.user

    if not username or not email or not password:
        return jsonify({'error': 'username, email, password required'}), 400
    if role not in ALL_ROLES:
        return jsonify({'error': 'Invalid role'}), 400

    try:
        pw_hash = hash_password(password)
        conn = get_conn()
        cur  = conn.cursor()
        cur.execute("""
            INSERT INTO users (username, email, password_hash, role, created_by)
            VALUES (%s, %s, %s, %s, %s) RETURNING id
        """, (username, email, pw_hash, role, admin['uid']))
        new_id = cur.fetchone()[0]
        conn.commit()
        conn.close()

        log_action(admin['uid'], admin['username'], admin['role'],
                   'USER_CREATE', f'user:{new_id}',
                   {'new_username': username, 'role': role},
                   request.remote_addr, True, None)
        return jsonify({'id': new_id, 'username': username, 'role': role}), 201
    except psycopg2.errors.UniqueViolation:
        return jsonify({'error': 'Username or email already exists'}), 409
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/users/<int:user_id>', methods=['PUT'])
@require_auth(roles=['admin'])
def update_user(user_id):
    data  = request.get_json() or {}
    admin = g.user

    updates = []
    params  = []
    if 'role' in data:
        if data['role'] not in ALL_ROLES:
            return jsonify({'error': 'Invalid role'}), 400
        updates.append('role = %s')
        params.append(data['role'])
    if 'is_active' in data:
        updates.append('is_active = %s')
        params.append(bool(data['is_active']))

    if not updates:
        return jsonify({'error': 'Nothing to update'}), 400

    try:
        params.append(user_id)
        conn = get_conn()
        cur  = conn.cursor()
        cur.execute(f"UPDATE users SET {', '.join(updates)} WHERE id = %s", params)
        conn.commit()
        conn.close()

        action = 'USER_DEACTIVATE' if data.get('is_active') is False else 'USER_UPDATE'
        log_action(admin['uid'], admin['username'], admin['role'],
                   action, f'user:{user_id}', data,
                   request.remote_addr, True, None)
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ═══════════════════════════════════════════════════════════════
# COMPLIANCE ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@app.route('/api/audit_log')
@require_auth(roles=['admin', 'risk_manager'])
def get_audit_log():
    limit     = request.args.get('limit', 200, type=int)
    offset    = request.args.get('offset', 0, type=int)
    filter_uid = request.args.get('user_id', None, type=int)
    filter_act = request.args.get('action', None)
    date_from  = request.args.get('from', None)
    date_to    = request.args.get('to', None)

    wheres = []
    params = []
    if filter_uid:
        wheres.append('user_id = %s'); params.append(filter_uid)
    if filter_act:
        wheres.append('action = %s'); params.append(filter_act)
    if date_from:
        wheres.append('ts >= %s'); params.append(date_from)
    if date_to:
        wheres.append('ts <= %s'); params.append(date_to)
    where = ('WHERE ' + ' AND '.join(wheres)) if wheres else ''

    try:
        conn = get_conn()
        cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            f"SELECT * FROM audit_log {where} ORDER BY ts DESC LIMIT %s OFFSET %s",
            params + [limit, offset]
        )
        rows = []
        for r in cur.fetchall():
            rows.append({
                'id':         r['id'],
                'ts':         r['ts'].isoformat() if r['ts'] else None,
                'user_id':    r['user_id'],
                'username':   r['username'],
                'role':       r['role'],
                'action':     r['action'],
                'resource':   r['resource'],
                'detail':     r['detail'],
                'ip_address': r['ip_address'],
                'success':    r['success'],
                'error_msg':  r['error_msg'],
            })
        cur.execute(f"SELECT COUNT(*) FROM audit_log {where}", params)
        total = cur.fetchone()[0]
        conn.close()
        return jsonify({'logs': rows, 'total': total, 'limit': limit, 'offset': offset})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/investor_ledger')
@require_auth(roles=['admin', 'risk_manager'])
def get_investor_ledger():
    try:
        conn = get_conn()
        cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM investor_ledger ORDER BY ts DESC LIMIT 500")
        rows = []
        for r in cur.fetchall():
            rows.append({
                'id':             r['id'],
                'ts':             r['ts'].isoformat() if r['ts'] else None,
                'investor_name':  r['investor_name'],
                'investor_email': r['investor_email'],
                'entry_type':     r['entry_type'],
                'amount_usd':     safe_float(r['amount_usd']),
                'nav_at_entry':   safe_float(r['nav_at_entry']),
                'shares_delta':   safe_float(r['shares_delta']),
                'reference_doc':  r['reference_doc'],
                'notes':          r['notes'],
            })
        conn.close()
        return jsonify(rows)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/investor_ledger', methods=['POST'])
@require_auth(roles=['admin'])
def add_investor_ledger():
    data  = request.get_json() or {}
    admin = g.user

    for field in ['investor_name', 'entry_type', 'amount_usd']:
        if not data.get(field) and data.get(field) != 0:
            return jsonify({'error': f'{field} required'}), 400
    if data['entry_type'] not in ['SUBSCRIPTION', 'REDEMPTION', 'FEE', 'ADJUSTMENT']:
        return jsonify({'error': 'Invalid entry_type'}), 400

    try:
        conn = get_conn()
        cur  = conn.cursor()
        cur.execute("""
            INSERT INTO investor_ledger
                (investor_name, investor_email, entry_type, amount_usd,
                 nav_at_entry, shares_delta, reference_doc, approved_by, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
        """, (
            data['investor_name'], data.get('investor_email'),
            data['entry_type'], data['amount_usd'],
            data.get('nav_at_entry'), data.get('shares_delta'),
            data.get('reference_doc'), admin['uid'], data.get('notes')
        ))
        new_id = cur.fetchone()[0]
        conn.commit()
        conn.close()

        log_action(admin['uid'], admin['username'], admin['role'],
                   'INVESTOR_ENTRY', f'ledger:{new_id}', data,
                   request.remote_addr, True, None)
        return jsonify({'id': new_id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/nav')
@require_auth(roles=['admin', 'risk_manager', 'viewer'])
def get_nav():
    try:
        conn = get_conn()
        cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM nav_history ORDER BY nav_date DESC LIMIT 365")
        rows = []
        for r in cur.fetchall():
            rows.append({
                'id':            r['id'],
                'nav_date':      r['nav_date'].isoformat() if r['nav_date'] else None,
                'total_aum':     safe_float(r['total_aum']),
                'total_shares':  safe_float(r['total_shares']),
                'nav_per_share': safe_float(r['nav_per_share']),
                'gross_pnl':     safe_float(r['gross_pnl']),
                'net_pnl':       safe_float(r['net_pnl']),
                'mgmt_fee':      safe_float(r['mgmt_fee']),
                'perf_fee':      safe_float(r['perf_fee']),
                'locked':        r['locked'],
            })
        conn.close()
        return jsonify(rows)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/nav', methods=['POST'])
@require_auth(roles=['admin'])
def add_nav():
    data  = request.get_json() or {}
    admin = g.user

    if not data.get('nav_date'):
        return jsonify({'error': 'nav_date required'}), 400

    try:
        conn = get_conn()
        cur  = conn.cursor()
        cur.execute("""
            INSERT INTO nav_history
                (nav_date, total_aum, total_shares, nav_per_share,
                 gross_pnl, net_pnl, mgmt_fee, perf_fee, calculated_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
        """, (
            data['nav_date'], data.get('total_aum'), data.get('total_shares'),
            data.get('nav_per_share'), data.get('gross_pnl'), data.get('net_pnl'),
            data.get('mgmt_fee', 0), data.get('perf_fee', 0), admin['uid']
        ))
        new_id = cur.fetchone()[0]
        conn.commit()
        conn.close()
        return jsonify({'id': new_id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/compliance_report')
@require_auth(roles=['admin'])
def get_compliance_report():
    default_from = (datetime.now(timezone.utc) - timedelta(days=30)).date().isoformat()
    default_to   = datetime.now(timezone.utc).date().isoformat()
    date_from    = request.args.get('from', default_from)
    date_to      = request.args.get('to', default_to)

    def serialize_row(row):
        out = {}
        for k, v in row.items():
            if hasattr(v, 'isoformat'):
                out[k] = v.isoformat()
            elif hasattr(v, '__float__') and not isinstance(v, (int, float, bool)):
                out[k] = float(v)
            else:
                out[k] = v
        return out

    try:
        conn = get_conn()
        cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cur.execute("""
            SELECT * FROM trades
            WHERE close_time::date BETWEEN %s AND %s
            ORDER BY close_time
        """, (date_from, date_to))
        trades = [serialize_row(dict(r)) for r in cur.fetchall()]

        cur.execute("""
            SELECT * FROM audit_log
            WHERE ts::date BETWEEN %s AND %s
            ORDER BY ts
        """, (date_from, date_to))
        audit = [serialize_row(dict(r)) for r in cur.fetchall()]

        cur.execute("""
            SELECT * FROM nav_history
            WHERE nav_date BETWEEN %s AND %s
            ORDER BY nav_date
        """, (date_from, date_to))
        nav = [serialize_row(dict(r)) for r in cur.fetchall()]

        conn.close()

        admin = g.user
        log_action(admin['uid'], admin['username'], admin['role'],
                   'EXPORT_REPORT', '/api/compliance_report',
                   {'from': date_from, 'to': date_to},
                   request.remote_addr, True, None)

        return jsonify({
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'generated_by': admin['username'],
            'period':       {'from': date_from, 'to': date_to},
            'trades':       trades,
            'audit_log':    audit,
            'nav_history':  nav,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ═══════════════════════════════════════════════════════════════
# EXISTING DATA ENDPOINTS — now auth-gated
# Roles: admin=A  trader=T  viewer=V  risk_manager=R
# ═══════════════════════════════════════════════════════════════

# ── ACCOUNT ── (A T V R)
@app.route('/api/account')
@require_auth(roles=ALL_ROLES)
def get_account():
    try:
        conn = get_conn()
        cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cur.execute("""
            SELECT time, login, server, balance, equity, margin,
                   free_margin, margin_level, profit
            FROM account_snapshots ORDER BY time DESC LIMIT 1
        """)
        snap = cur.fetchone()

        cur.execute("""
            SELECT trades_count, gross_profit, gross_loss, net_profit, win_rate
            FROM daily_pnl WHERE date = CURRENT_DATE
        """)
        today = cur.fetchone()

        cur.execute("""
            SELECT
                COUNT(*) as total_trades,
                COALESCE(SUM(CASE WHEN net_profit > 0 THEN 1 ELSE 0 END)::float
                         / NULLIF(COUNT(*),0), 0) as lifetime_win_rate,
                COALESCE(SUM(net_profit), 0) as lifetime_pnl
            FROM trades WHERE status = 'CLOSED'
        """)
        lifetime = cur.fetchone()
        conn.close()

        return jsonify({
            'time':         snap['time'].isoformat() if snap else None,
            'login':        safe_int(snap['login'] if snap else 0),
            'server':       snap['server'] if snap else '',
            'balance':      safe_float(snap['balance'] if snap else 0),
            'equity':       safe_float(snap['equity'] if snap else 0),
            'margin':       safe_float(snap['margin'] if snap else 0),
            'free_margin':  safe_float(snap['free_margin'] if snap else 0),
            'margin_level': safe_float(snap['margin_level'] if snap else 0),
            'floating_pnl': safe_float(snap['profit'] if snap else 0),
            'today': {
                'trades':       safe_int(today['trades_count'] if today else 0),
                'gross_profit': safe_float(today['gross_profit'] if today else 0),
                'gross_loss':   safe_float(today['gross_loss'] if today else 0),
                'net_profit':   safe_float(today['net_profit'] if today else 0),
                'win_rate':     safe_float(today['win_rate'] if today else 0),
            },
            'lifetime': {
                'trades':   safe_int(lifetime['total_trades'] if lifetime else 0),
                'win_rate': safe_float(lifetime['lifetime_win_rate'] if lifetime else 0),
                'net_pnl':  safe_float(lifetime['lifetime_pnl'] if lifetime else 0),
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── OPEN POSITIONS ── (A T V)
# Primary source: positions table (engine-managed state, written by renaissance engine)
# Fallback:       trades WHERE status='OPEN' (MT5-confirmed tickets, legacy)
@app.route('/api/positions')
@require_auth(roles=['admin', 'trader', 'viewer'])
def get_positions():
    try:
        conn = get_conn()
        cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # Try the new positions table first
        try:
            cur.execute("""
                SELECT p.id, p.symbol, p.direction, p.entry_time, p.entry_price,
                       p.shares, p.position_size, p.stop_loss, p.take_profit,
                       p.pnl, p.exit_reason, p.signal_id, p.kelly_fraction,
                       p.status, c.bid AS current_price
                FROM positions p
                LEFT JOIN current c ON c.symbol = p.symbol
                WHERE p.status = 'OPEN'
                ORDER BY p.entry_time DESC
            """)
            rows = []
            for r in cur.fetchall():
                # Map positions schema → frontend-expected field names
                direction = r['direction'] or ''
                rows.append({
                    'id':            r['id'],
                    'ticket':        None,                           # no MT5 ticket on engine positions
                    'symbol':        r['symbol'],
                    'type':          'BUY' if direction == 'LONG' else 'SELL',
                    'volume':        safe_float(r['shares']),
                    'open_price':    safe_float(r['entry_price']),
                    'current_price': safe_float(r['current_price']),
                    'sl':            safe_float(r['stop_loss']),
                    'tp':            safe_float(r['take_profit']),
                    'open_time':     r['entry_time'].isoformat() if r['entry_time'] else None,
                    'profit':        safe_float(r['pnl']),
                    'commission':    0.0,
                    'swap':          0.0,
                    'net_profit':    safe_float(r['pnl']),
                    'signal_id':     r['signal_id'],
                    'kelly_fraction': safe_float(r['kelly_fraction']),
                    'comment':       r['exit_reason'] or '',
                    'source':        'positions',
                })
            conn.close()
            return jsonify(rows)

        except psycopg2.errors.UndefinedTable:
            # positions table not yet created — fall back to trades table
            conn.rollback()
            cur.execute("""
                SELECT id, ticket, symbol, type, volume,
                       open_price, close_price, sl, tp,
                       open_time, profit, commission, swap,
                       net_profit, signal_id, magic, comment, status
                FROM trades WHERE status = 'OPEN' ORDER BY open_time DESC
            """)
            rows = []
            for r in cur.fetchall():
                rows.append({
                    'id':            r['id'],
                    'ticket':        r['ticket'],
                    'symbol':        r['symbol'],
                    'type':          r['type'],
                    'volume':        safe_float(r['volume']),
                    'open_price':    safe_float(r['open_price']),
                    'current_price': safe_float(r['close_price']),
                    'sl':            safe_float(r['sl']),
                    'tp':            safe_float(r['tp']),
                    'open_time':     r['open_time'].isoformat() if r['open_time'] else None,
                    'profit':        safe_float(r['profit']),
                    'commission':    safe_float(r['commission']),
                    'swap':          safe_float(r['swap']),
                    'net_profit':    safe_float(r['net_profit']),
                    'signal_id':     r['signal_id'],
                    'kelly_fraction': None,
                    'comment':       r['comment'] or '',
                    'source':        'trades_fallback',
                })
            conn.close()
            return jsonify(rows)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── TRADE HISTORY ── (A T V)
@app.route('/api/trades')
@require_auth(roles=['admin', 'trader', 'viewer'])
def get_trades():
    limit  = request.args.get('limit', 100, type=int)
    offset = request.args.get('offset', 0, type=int)
    symbol = request.args.get('symbol', None)

    try:
        conn   = get_conn()
        cur    = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        where  = "WHERE status = 'CLOSED'"
        params = []
        if symbol:
            where += " AND symbol = %s"
            params.append(symbol)

        cur.execute(f"""
            SELECT id, ticket, symbol, type, volume,
                   open_price, close_price, sl, tp,
                   open_time, close_time, profit, commission, swap,
                   net_profit, signal_id, magic, comment, status
            FROM trades {where} ORDER BY close_time DESC LIMIT %s OFFSET %s
        """, params + [limit, offset])

        rows = []
        for r in cur.fetchall():
            rows.append({
                'id':          r['id'],
                'ticket':      r['ticket'],
                'symbol':      r['symbol'],
                'type':        r['type'],
                'volume':      safe_float(r['volume']),
                'open_price':  safe_float(r['open_price']),
                'close_price': safe_float(r['close_price']),
                'open_time':   r['open_time'].isoformat() if r['open_time'] else None,
                'close_time':  r['close_time'].isoformat() if r['close_time'] else None,
                'profit':      safe_float(r['profit']),
                'commission':  safe_float(r['commission']),
                'swap':        safe_float(r['swap']),
                'net_profit':  safe_float(r['net_profit']),
                'signal_id':   r['signal_id'],
                'comment':     r['comment'] or '',
                'win':         safe_float(r['net_profit']) > 0,
            })

        cur.execute(f"SELECT COUNT(*) FROM trades {where}", params)
        total = cur.fetchone()[0]
        conn.close()
        return jsonify({'trades': rows, 'total': total, 'limit': limit, 'offset': offset})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── DAILY P&L ── (A T V R)
@app.route('/api/daily_pnl')
@require_auth(roles=ALL_ROLES)
def get_daily_pnl():
    days = request.args.get('days', 30, type=int)
    try:
        conn = get_conn()
        cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT date, trades_count, gross_profit, gross_loss,
                   net_profit, win_rate, balance_eod
            FROM daily_pnl ORDER BY date DESC LIMIT %s
        """, (days,))
        rows = []
        for r in cur.fetchall():
            rows.append({
                'date':         r['date'].isoformat(),
                'trades':       safe_int(r['trades_count']),
                'gross_profit': safe_float(r['gross_profit']),
                'gross_loss':   safe_float(r['gross_loss']),
                'net_profit':   safe_float(r['net_profit']),
                'win_rate':     safe_float(r['win_rate']),
                'balance_eod':  safe_float(r['balance_eod']),
            })
        conn.close()
        return jsonify(rows)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── TRANSACTIONS ── (A T V R)
@app.route('/api/transactions')
@require_auth(roles=ALL_ROLES)
def get_transactions():
    limit = request.args.get('limit', 50, type=int)
    try:
        conn = get_conn()
        cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT id, time, type, amount, balance_after, note
            FROM transactions ORDER BY time DESC LIMIT %s
        """, (limit,))
        rows = []
        for r in cur.fetchall():
            rows.append({
                'id':            r['id'],
                'time':          r['time'].isoformat() if r['time'] else None,
                'type':          r['type'],
                'amount':        safe_float(r['amount']),
                'balance_after': safe_float(r['balance_after']),
                'note':          r['note'] or '',
            })
        conn.close()
        return jsonify(rows)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── EXECUTION LOG ── (A T)
@app.route('/api/execution_log')
@require_auth(roles=['admin', 'trader'])
def get_execution_log():
    limit = request.args.get('limit', 100, type=int)
    try:
        conn = get_conn()
        cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT id, time, signal_id, symbol, action,
                   volume, price, ticket, status, error
            FROM execution_log ORDER BY time DESC LIMIT %s
        """, (limit,))
        rows = []
        for r in cur.fetchall():
            rows.append({
                'id':        r['id'],
                'time':      r['time'].isoformat() if r['time'] else None,
                'signal_id': r['signal_id'],
                'symbol':    r['symbol'],
                'action':    r['action'],
                'volume':    safe_float(r['volume']),
                'price':     safe_float(r['price']),
                'ticket':    r['ticket'],
                'status':    r['status'],
                'error':     r['error'] or '',
            })
        conn.close()
        return jsonify(rows)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── SIGNALS ── (A T)
@app.route('/api/signals')
@require_auth(roles=['admin', 'trader'])
def get_signals():
    limit  = request.args.get('limit', 100, type=int)
    status = request.args.get('status', None)
    try:
        conn   = get_conn()
        cur    = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        where  = ''
        params = []
        if status:
            where = 'WHERE status = %s'
            params.append(status)

        # Include pattern_name + pattern_data if the columns exist (added by trading engine)
        try:
            cur.execute(f"""
                SELECT id, time, symbol, action, price,
                       confidence, kelly_pct, status,
                       pattern_name, pattern_data
                FROM signals {where} ORDER BY time DESC LIMIT %s
            """, params + [limit])
            has_pattern_cols = True
        except psycopg2.errors.UndefinedColumn:
            conn.rollback()
            cur.execute(f"""
                SELECT id, time, symbol, action, price,
                       confidence, kelly_pct, status
                FROM signals {where} ORDER BY time DESC LIMIT %s
            """, params + [limit])
            has_pattern_cols = False

        rows = []
        for r in cur.fetchall():
            rows.append({
                'id':           r['id'],
                'time':         r['time'].isoformat() if r['time'] else None,
                'symbol':       r['symbol'],
                'action':       r['action'],
                'price':        safe_float(r['price']),
                'confidence':   safe_float(r['confidence']),
                'kelly_pct':    safe_float(r['kelly_pct']),
                'status':       r['status'],
                'pattern':      r['pattern_name'] if has_pattern_cols else '',
                'pattern_data': r['pattern_data'] if has_pattern_cols else None,
            })
        conn.close()
        return jsonify(rows)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── EQUITY HISTORY ── (A T V R)
@app.route('/api/equity_history')
@require_auth(roles=ALL_ROLES)
def get_equity_history():
    hours = request.args.get('hours', 24, type=int)
    try:
        conn  = get_conn()
        cur   = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        cur.execute("""
            SELECT time, balance, equity, profit
            FROM account_snapshots WHERE time >= %s ORDER BY time ASC
        """, (since,))
        rows = []
        for r in cur.fetchall():
            rows.append({
                'time':    r['time'].isoformat(),
                'time_ms': int(r['time'].timestamp() * 1000),
                'balance': safe_float(r['balance']),
                'equity':  safe_float(r['equity']),
                'profit':  safe_float(r['profit']),
            })
        conn.close()
        return jsonify(rows)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── SYMBOLS ── (A T V R)
@app.route('/api/symbols')
@require_auth(roles=ALL_ROLES)
def get_symbols():
    try:
        conn = get_conn()
        cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT symbol, bid, ask, spread,
                   EXTRACT(EPOCH FROM (NOW() - last_updated)) AS age_seconds
            FROM current ORDER BY symbol
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
                    'bid':    safe_float(row.get('bid')),
                    'ask':    safe_float(row.get('ask')),
                    'spread': safe_float(row.get('spread')),
                    'age':    safe_float(row.get('age_seconds', 9999)),
                    'live':   bool(row and safe_float(row.get('bid')) > 0)
                })
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── TICKS ── (A T V)
@app.route('/api/ticks/<symbol>')
@require_auth(roles=['admin', 'trader', 'viewer'])
def get_ticks(symbol):
    since_ms = request.args.get('since', 0, type=float)
    limit    = request.args.get('limit', 100, type=int)
    try:
        conn = get_conn()
        cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        if since_ms > 0:
            since_ts = datetime.fromtimestamp(since_ms / 1000.0, tz=timezone.utc)
            cur.execute("""
                SELECT time, bid, ask, spread, volume, buy_volume, sell_volume
                FROM ticks WHERE symbol = %s AND time > %s
                ORDER BY time DESC LIMIT %s
            """, (symbol, since_ts, limit))
        else:
            cur.execute("""
                SELECT time, bid, ask, spread, volume, buy_volume, sell_volume
                FROM ticks WHERE symbol = %s ORDER BY time DESC LIMIT %s
            """, (symbol, limit))
        ticks = []
        for r in cur.fetchall():
            ticks.append({
                'time':     r['time'].isoformat(),
                'time_ms':  int(r['time'].timestamp() * 1000),
                'bid':      safe_float(r['bid']),
                'ask':      safe_float(r['ask']),
                'spread':   safe_float(r['spread']),
                'volume':   safe_int(r['volume']),
                'buy_vol':  safe_int(r['buy_volume']),
                'sell_vol': safe_int(r['sell_volume']),
            })
        conn.close()
        return jsonify({'symbol': symbol, 'ticks': ticks, 'count': len(ticks)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── CURRENT PRICES ── (A T V R)
@app.route('/api/current')
@require_auth(roles=ALL_ROLES)
def get_current():
    try:
        conn = get_conn()
        cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT symbol, bid, ask, spread, last_updated,
                   EXTRACT(EPOCH FROM (NOW() - last_updated)) AS age_seconds
            FROM current WHERE bid > 0 ORDER BY symbol
        """)
        rows = []
        for r in cur.fetchall():
            rows.append({
                'symbol':  r['symbol'],
                'bid':     safe_float(r['bid']),
                'ask':     safe_float(r['ask']),
                'spread':  safe_float(r['spread']),
                'updated': r['last_updated'].isoformat() if r['last_updated'] else None,
                'age':     safe_float(r['age_seconds']),
            })
        conn.close()
        return jsonify(rows)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── STATS ── (A T V R)
@app.route('/api/stats')
@require_auth(roles=ALL_ROLES)
def get_stats():
    try:
        conn = get_conn()
        cur  = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM ticks")
        tick_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM signals")
        signal_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM current WHERE bid > 0")
        live_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM trades WHERE status = 'OPEN'")
        open_trades = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM trades WHERE status = 'CLOSED'")
        closed_trades = cur.fetchone()[0]
        conn.close()
        return jsonify({
            'ticks_total':    tick_count,
            'signals_total':  signal_count,
            'live_symbols':   live_count,
            'open_positions': open_trades,
            'closed_trades':  closed_trades,
            'server_time':    datetime.now().isoformat(),
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── BARS ── (A T V)
@app.route('/api/bars/<symbol>')
@require_auth(roles=['admin', 'trader', 'viewer'])
def get_bars(symbol):
    tf    = request.args.get('tf', 'M5')
    limit = request.args.get('limit', 200, type=int)
    table_name = symbol.lower().replace('.', '').replace('-', '') + '_bars'

    try:
        conn = get_conn()
        cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(f"""
            SELECT time, open, high, low, close, volume
            FROM {table_name} WHERE timeframe = %s ORDER BY time DESC LIMIT %s
        """, (tf, limit))
        bars = []
        for r in cur.fetchall():
            bars.append({
                'time':   r['time'].isoformat() if r['time'] else None,
                'time_s': int(r['time'].timestamp()) if r['time'] else 0,
                'open':   safe_float(r['open']),
                'high':   safe_float(r['high']),
                'low':    safe_float(r['low']),
                'close':  safe_float(r['close']),
                'volume': safe_int(r['volume']),
            })
        bars.reverse()
        conn.close()
        return jsonify({'symbol': symbol, 'tf': tf, 'bars': bars, 'count': len(bars)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ═══════════════════════════════════════════════════════════════
# Serve trading terminal (fixes localStorage on file:// restriction)
# ═══════════════════════════════════════════════════════════════
@app.route('/')
@app.route('/terminal')
def serve_terminal():
    return send_file(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'trading_terminal.html'))


# ═══════════════════════════════════════════════════════════════
if __name__ == '__main__':
    print("=" * 60)
    print("KLDA-HFT Trading API — Compliance Edition")
    print("http://localhost:5002")
    print()
    print("Auth:        POST /api/login  GET /api/me  POST /api/logout")
    print("Users:       GET/POST /api/users  PUT /api/users/<id>")
    print("Compliance:  /api/audit_log  /api/investor_ledger  /api/nav")
    print("             /api/compliance_report")
    print()
    print("Data endpoints (auth required):")
    print("  /api/account  /api/positions  /api/trades  /api/daily_pnl")
    print("  /api/transactions  /api/execution_log  /api/signals")
    print("  /api/equity_history  /api/symbols  /api/ticks/<s>")
    print("  /api/bars/<s>  /api/stats  /api/current")
    print()
    print("pip install PyJWT bcrypt python-dotenv  (if not installed)")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5002, debug=False, threaded=True)
