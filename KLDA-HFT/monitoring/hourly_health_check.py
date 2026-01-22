#!/usr/bin/env python3
"""
KLDA-HFT Hourly Health Check with Email Alerts
Monitors database tick ingestion and system health
Sends email if issues detected
"""

import psycopg2
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import sys

# ==================== CONFIGURATION ====================
EMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'sender_email': 'your-email@gmail.com',  # UPDATE THIS
    'sender_password': 'your-app-password',   # UPDATE THIS (use app password, not real password)
    'recipient_email': 'your-email@gmail.com' # UPDATE THIS
}

DB_CONFIG = {
    'host': 'localhost',
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
        response = requests.get('http://localhost:5000/health', timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {'status': 'OK', 'data': data}
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


if __name__ == "__main__":
    sys.exit(main())
