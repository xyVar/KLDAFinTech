#!/usr/bin/env python3
"""
KLDA-HFT Hourly Health Check with Email Alerts
Monitors database tick ingestion and system health
Sends email if issues detected

  python hourly_health_check.py            hourly check (+ email on alert)
  python hourly_health_check.py --report   full stack health report (no email):
      MT5 account (demo?), broker clock, feed advancing, ticks/sec + last tick
      per symbol, DB row counts, processes (bridge/watchdog/API/paper chain),
      API + dashboard HTTP, live_ticks.json age, backups, disk space
"""

import psycopg2
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import subprocess
import sys
import time
from pathlib import Path

# ==================== CONFIGURATION ====================
EMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'sender_email': 'your-email@gmail.com',  # UPDATE THIS
    'sender_password': 'your-app-password',   # UPDATE THIS (use app password, not real password)
    'recipient_email': 'your-email@gmail.com' # UPDATE THIS
}

DB_CONFIG = {
    'host': '127.0.0.1',  # not localhost: ::1 can hit the WSL postgres relay
    'database': 'KLDA-HFT_Database',
    'user': 'postgres',
    'password': 'MyKldaTechnologies2025!'
}

ALERT_THRESHOLDS = {
    'min_ticks_per_hour': 100,  # Alert if < 100 ticks/hour for any symbol
    'max_staleness_minutes': 15,  # Alert if no new ticks for 15 minutes
    'min_disk_space_pct': 10       # Alert if disk space < 10%
}

# =======================================================

def send_email(subject, body, is_html=False):
    """Send email alert"""
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = EMAIL_CONFIG['sender_email']
        msg['To'] = EMAIL_CONFIG['recipient_email']

        if is_html:
            msg.attach(MIMEText(body, 'html'))
        else:
            msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port']) as server:
            server.starttls()
            server.login(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['sender_password'])
            server.send_message(msg)

        print(f"[OK] Email sent: {subject}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to send email: {e}")
        return False


def check_database_health():
    """Check database connection and tick ingestion"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Check TimescaleDB
        cursor.execute("SELECT extname, extversion FROM pg_extension WHERE extname = 'timescaledb';")
        ts_result = cursor.fetchone()
        if not ts_result:
            return {'status': 'ERROR', 'message': 'TimescaleDB not installed'}

        # Check tick ingestion (last hour) for each symbol
        symbols = ['tsla', 'nvda', 'pltr', 'amd', 'avgo', 'meta', 'aapl', 'msft',
                   'orcl', 'amzn', 'csco', 'goog', 'intc', 'vix', 'nas100', 'natgas', 'spotcrude']

        tick_stats = []
        alerts = []
        total_ticks_last_hour = 0

        for symbol in symbols:
            try:
                cursor.execute(f"""
                    SELECT
                        COUNT(*) as ticks_last_hour,
                        MAX(time) as latest_tick,
                        EXTRACT(EPOCH FROM (NOW() - MAX(time))) as seconds_ago
                    FROM {symbol}_history
                    WHERE time >= NOW() - INTERVAL '1 hour';
                """)
                result = cursor.fetchone()
                ticks_count, latest_tick, seconds_ago = result

                total_ticks_last_hour += ticks_count

                # Check if data is stale
                if seconds_ago and seconds_ago > (ALERT_THRESHOLDS['max_staleness_minutes'] * 60):
                    # Only alert for 24/7 markets (VIX, NAS100, commodities)
                    if symbol in ['vix', 'nas100', 'natgas', 'spotcrude']:
                        alerts.append(f"⚠️ {symbol.upper()}: No new ticks for {int(seconds_ago/60)} minutes")

                # Check if ingestion rate is too low
                if symbol in ['vix', 'nas100', 'natgas', 'spotcrude']:
                    if ticks_count < ALERT_THRESHOLDS['min_ticks_per_hour']:
                        alerts.append(f"⚠️ {symbol.upper()}: Only {ticks_count} ticks in last hour (expected > {ALERT_THRESHOLDS['min_ticks_per_hour']})")

                tick_stats.append({
                    'symbol': symbol.upper(),
                    'ticks_last_hour': ticks_count,
                    'latest_tick': latest_tick.strftime('%Y-%m-%d %H:%M:%S') if latest_tick else 'N/A',
                    'seconds_ago': int(seconds_ago) if seconds_ago else 0
                })

            except Exception as e:
                alerts.append(f"❌ {symbol.upper()}: Database query failed - {str(e)}")

        # Check database size
        cursor.execute("SELECT pg_size_pretty(pg_database_size('KLDA-HFT_Database'));")
        db_size = cursor.fetchone()[0]

        # Check disk space
        import shutil
        disk_usage = shutil.disk_usage("C:\\")
        disk_free_pct = (disk_usage.free / disk_usage.total) * 100
        if disk_free_pct < ALERT_THRESHOLDS['min_disk_space_pct']:
            alerts.append(f"🔴 CRITICAL: Disk space low ({disk_free_pct:.1f}% free)")

        cursor.close()
        conn.close()

        return {
            'status': 'ERROR' if alerts else 'OK',
            'tick_stats': tick_stats,
            'total_ticks_last_hour': total_ticks_last_hour,
            'db_size': db_size,
            'disk_free_pct': disk_free_pct,
            'alerts': alerts
        }

    except Exception as e:
        return {'status': 'ERROR', 'message': f'Database connection failed: {str(e)}', 'alerts': [f'❌ Database: {str(e)}']}


def check_flask_api():
    """Check Flask API health"""
    try:
        # trading_api.py (port 5002) has no /health route; '/' serves the terminal
        response = requests.get('http://127.0.0.1:5002/', timeout=5)
        if response.status_code == 200:
            return {'status': 'OK', 'data': {}}
        else:
            return {'status': 'ERROR', 'message': f'HTTP {response.status_code}'}
    except Exception as e:
        return {'status': 'ERROR', 'message': str(e)}


def generate_report(db_health, flask_status):
    """Generate health check report"""
    status_emoji = "✅" if db_health['status'] == 'OK' and flask_status['status'] == 'OK' else "⚠️"

    report = f"""
KLDA-HFT HOURLY HEALTH CHECK - {status_emoji} {db_health['status']}
{'=' * 70}
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

TICK INGESTION (Last Hour):
{'-' * 70}
"""

    # Add tick statistics
    for stat in db_health.get('tick_stats', [])[:10]:  # Show first 10 symbols
        status_icon = "✅" if stat['seconds_ago'] < 300 else "⏸️" if stat['seconds_ago'] < 3600 else "❌"
        report += f"{stat['symbol']:<12} {stat['ticks_last_hour']:>6,} ticks | Latest: {stat['latest_tick']} {status_icon}\n"

    report += f"\nTotal Ticks (Last Hour): {db_health.get('total_ticks_last_hour', 0):,}\n"

    report += f"""
SYSTEM STATUS:
{'-' * 70}
Flask API:       {flask_status['status']} {'✅' if flask_status['status'] == 'OK' else '❌'}
Database:        {db_health['status']} {'✅' if db_health['status'] == 'OK' else '❌'}
Database Size:   {db_health.get('db_size', 'Unknown')}
Disk Space Free: {db_health.get('disk_free_pct', 0):.1f}% {'✅' if db_health.get('disk_free_pct', 0) > 10 else '🔴'}

"""

    # Add alerts section
    if db_health.get('alerts'):
        report += f"ALERTS:\n{'-' * 70}\n"
        for alert in db_health['alerts']:
            report += f"{alert}\n"
    else:
        report += "ALERTS:\nNone - All systems operational! ✅\n"

    report += "\n" + "=" * 70 + "\n"
    return report


def main():
    """Main health check routine"""
    print(f"\n[START] KLDA-HFT Hourly Health Check - {datetime.now()}")

    # Check database
    db_health = check_database_health()

    # Check Flask API
    flask_status = check_flask_api()

    # Generate report
    report = generate_report(db_health, flask_status)

    # Print to console
    print(report)

    # Send email if there are alerts
    if db_health['status'] == 'ERROR' or flask_status['status'] == 'ERROR':
        subject = f"[KLDA-HFT] ⚠️ ALERT - Health Check Failed"
        send_email(subject, report)
        print("[ALERT] Email sent to administrator")
    else:
        # Optional: Send success email too (comment out if too many emails)
        # subject = f"[KLDA-HFT] ✅ Health Check - All Systems Operational"
        # send_email(subject, report)
        print("[OK] All systems healthy - No alert sent")

    print(f"[DONE] Health check complete\n")
    return 0 if db_health['status'] == 'OK' else 1


# ==================== FULL STACK REPORT (--report) ====================
KLDA_ROOT  = Path(__file__).resolve().parent.parent
BACKUP_DIR = KLDA_ROOT.parent / 'backups'           # same as database/backup_db.py
PROCESSES  = {                                       # matched on command line, like watchdog.py
    'tick bridge':      'mt5_tick_capture_ALL_TICKS.py',
    'watchdog':         'watchdog.py',
    'trading API':      'trading_api.py',
    'signal generator': 'signal_generator.py',
    'order router':     'order_router.py',
    'reconciler':       'reconciler.py',
    'dashboard server': 'http.server 8082',
}


def _age(seconds):
    if seconds is None:
        return 'n/a'
    seconds = int(seconds)
    return f"{seconds}s" if seconds < 120 else f"{seconds // 60}m" if seconds < 7200 else f"{seconds / 3600:.1f}h"


def report_mt5(w):
    w("MT5 ACCOUNT / BROKER CLOCK")
    try:
        import MetaTrader5 as mt5
    except ImportError:
        w("  MetaTrader5 module not installed"); return
    if not mt5.initialize():
        w(f"  ❌ MT5 initialize failed: {mt5.last_error()} (terminal running + logged in?)"); return
    try:
        acc = mt5.account_info()
        if acc is None:
            w("  ❌ not logged in")
        else:
            mode = {0: 'DEMO', 1: 'CONTEST', 2: 'REAL'}.get(acc.trade_mode, acc.trade_mode)
            w(f"  {'✅' if mode == 'DEMO' else '⚠️'} login {acc.login} @ {acc.server}  mode={mode}  "
              f"trade_allowed={acc.trade_allowed}  balance={acc.balance:.2f} {acc.currency}  leverage=1:{acc.leverage}")
        sys.path.insert(0, str(KLDA_ROOT / 'trading-engine'))
        from config_loader import broker_utc_offset_hours
        cfg_off = broker_utc_offset_hours()
        ticks = [mt5.symbol_info_tick(s.name) for s in (mt5.symbols_get(visible=True) or [])]
        newest = max((t.time for t in ticks if t), default=None)
        if newest:
            lag = time.time() - newest      # tick.time is broker wall clock encoded as epoch
            obs = round(-lag / 3600 * 2) / 2
            w(f"  broker clock: observed UTC{obs:+g} (newest tick), config rule UTC{cfg_off:+g} "
              f"{'✅' if obs == cfg_off else '⚠️ MISMATCH — fix broker_time in config/trading_config.json'}")
    finally:
        mt5.shutdown()


def report_db(w):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Feed advancing? (broker-time high-water mark must move — never NOW()-last_updated)
    cur.execute("SELECT MAX(last_updated) FROM current")
    hw1 = cur.fetchone()[0]
    time.sleep(10)
    cur.execute("SELECT MAX(last_updated) FROM current")
    hw2 = cur.fetchone()[0]
    w("TICK FEED")
    w(f"  {'✅ advancing' if hw1 and hw2 and hw2 > hw1 else '❌ NOT advancing'}: "
      f"MAX(current.last_updated) {hw1} -> {hw2} over 10s")

    # Per-symbol rate over the last 60s of broker time, anchored on the feed high-water mark.
    # The window bound is passed as a constant so TimescaleDB only scans the newest chunk.
    hw = hw2 or hw1
    rows = []
    if hw:
        cur.execute("""
            SELECT c.symbol, c.last_updated, COALESCE(k.n60, 0),
                   EXTRACT(EPOCH FROM %s - c.last_updated)
            FROM current c
            LEFT JOIN (SELECT symbol, COUNT(*) AS n60 FROM ticks
                       WHERE time > %s - INTERVAL '60 seconds' GROUP BY symbol) k
                   ON k.symbol = c.symbol
            ORDER BY c.symbol
        """, (hw, hw))
        rows = cur.fetchall()
    w("")
    w(f"PER SYMBOL ({len(rows)} in `current`; rate = ticks in last 60s of feed time / 60)")
    w(f"  {'symbol':<14}{'ticks/sec':>10}  {'last tick (broker)':<28}{'behind feed':>12}")
    for sym, last, n60, behind in rows:
        flag = '✅' if n60 else ('⏸️' if behind is not None and behind < 3600 else '❌')
        w(f"  {sym:<14}{n60 / 60:>10.2f}  {str(last):<28}{_age(behind):>12} {flag}")

    w("")
    w("DB ROW COUNTS")
    try:
        cur.execute("SELECT approximate_row_count('ticks')")
        w(f"  {'ticks (approx)':<22}{cur.fetchone()[0]:>15,}")
    except Exception as e:
        conn.rollback(); w(f"  ticks: approximate_row_count failed ({e})")
    for table in ('current', 'signals', 'paper_positions', 'paper_orders', 'trades', 'positions'):
        try:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            w(f"  {table:<22}{cur.fetchone()[0]:>15,}")
        except Exception:
            conn.rollback(); w(f"  {table:<22}{'(missing)':>15}")
    cur.execute("SELECT pg_size_pretty(pg_database_size(current_database()))")
    w(f"  {'database size':<22}{cur.fetchone()[0]:>15}")
    conn.close()


def report_processes(w):
    w("PROCESSES")
    try:
        out = subprocess.run(
            ['powershell', '-NoProfile', '-Command',
             "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine } | "
             "ForEach-Object { \"$($_.ProcessId)`t$($_.CommandLine)\" }"],
            capture_output=True, text=True, timeout=30).stdout
    except Exception as e:
        w(f"  could not list processes: {e}"); return
    for label, needle in PROCESSES.items():
        pids = [l.split('\t', 1)[0] for l in out.splitlines()
                if needle in l and 'hourly_health_check' not in l]
        w(f"  {'✅' if pids else '❌'} {label:<18} {'pid ' + ','.join(pids) if pids else 'NOT RUNNING'}")


def report_http_files(w):
    w("ENDPOINTS / FILES")
    for label, url in (('trading API :5002', 'http://127.0.0.1:5002/'),
                       ('dashboard :8082', 'http://127.0.0.1:8082/live_ticker.html')):
        try:
            code = requests.get(url, timeout=5).status_code
            w(f"  {'✅' if code == 200 else '❌'} {label:<20} HTTP {code}")
        except Exception as e:
            w(f"  ❌ {label:<20} {type(e).__name__}")
    lt = KLDA_ROOT / 'cpp-backend' / 'live_ticks.json'
    age = time.time() - lt.stat().st_mtime if lt.exists() else None
    w(f"  {'✅' if age is not None and age < 10 else '❌'} live_ticks.json      updated {_age(age)} ago"
      f"{'' if age is not None and age < 10 else ' (C++ live_tracker not writing — dashboard is stale)'}")

    w("")
    w("BACKUPS")
    for label, pattern in (('base dump', 'base_*.dump'), ('tick archive', 'ticks/ticks_*.csv.gz')):
        files = sorted(BACKUP_DIR.glob(pattern), key=lambda f: f.stat().st_mtime)
        if files:
            f = files[-1]; age = time.time() - f.stat().st_mtime
            w(f"  {'✅' if age < 26 * 3600 else '❌'} {label:<14} {f.name}  {f.stat().st_size / 1e6:,.1f} MB  {_age(age)} old")
        else:
            w(f"  ❌ {label:<14} none in {BACKUP_DIR}")


def full_report():
    try:
        sys.stdout.reconfigure(errors='replace')   # Windows console code pages choke on emoji
    except Exception:
        pass
    lines = []
    w = lines.append
    w("=" * 78)
    w(f"KLDA-HFT FULL HEALTH REPORT — {datetime.now():%Y-%m-%d %H:%M:%S} (PC time)")
    w("=" * 78)
    for section in (report_mt5, report_db, report_processes, report_http_files):
        try:
            section(w)
        except Exception as e:
            w(f"  ❌ {section.__name__} failed: {e}")
        w("")
    import shutil
    du = shutil.disk_usage(KLDA_ROOT.anchor)
    w("DISK")
    w(f"  {KLDA_ROOT.anchor} {du.free / 1e9:,.1f} GB free of {du.total / 1e9:,.1f} GB "
      f"({du.free / du.total * 100:.1f}%) {'✅' if du.free / du.total > 0.10 else '🔴'}")
    w("=" * 78)
    report = "\n".join(lines)
    print(report)
    out = KLDA_ROOT / 'reports' / f"health_{datetime.now():%Y-%m-%d_%H%M}.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report + "\n", encoding='utf-8')
    print(f"[saved] {out}")
    return 0


if __name__ == "__main__":
    if '--report' in sys.argv:
        sys.exit(full_report())
    sys.exit(main())
