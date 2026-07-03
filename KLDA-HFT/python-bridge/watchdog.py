#!/usr/bin/env python3
"""
KLDA-HFT bridge watchdog.

Monitors the tick feed and restarts ONLY the bridge when it stalls.

Design notes (hard-won):
- Kills bridge processes surgically, matched by command line via WMI —
  never `taskkill /IM python.exe`, which nukes every Python process on
  the machine (MCP servers, running backtests, this watchdog itself).
- The bridge writes to Postgres directly; there is no Flask receiver in
  the current pipeline, so none is monitored or started.
- Freshness = MAX(last_updated) in `current` ADVANCING between checks.
  Timestamps are broker time (UTC+3), so "NOW() - last_updated" is
  offset by hours and useless as an absolute age; the high-water mark
  advancing is timezone-immune.
- DB host is 127.0.0.1, not localhost: ::1 can be claimed by a WSL
  postgres relay with different credentials.

Run:  python watchdog.py   (leave running; logs to watchdog.log)
"""
import subprocess
import sys
import time
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

import psycopg2

BRIDGE_DIR = Path(__file__).resolve().parent
BRIDGE_SCRIPT = 'mt5_tick_capture_ALL_TICKS.py'
LOG_PATH = BRIDGE_DIR / 'watchdog.log'

DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 5432,
    'database': 'KLDA-HFT_Database',
    'user': 'postgres',
    'password': 'MyKldaTechnologies2025!',
    'connect_timeout': 10,
}

CHECK_EVERY_SEC = 60
STALL_CHECKS = 3           # restart after N consecutive checks with no new ticks
MIN_RESTART_GAP_SEC = 600  # never restart more often than this (weekends stall harmlessly)

log = logging.getLogger('watchdog')
log.setLevel(logging.INFO)
_fmt = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
for h in (RotatingFileHandler(LOG_PATH, maxBytes=5 * 1024 * 1024, backupCount=3, encoding='utf-8'),
          logging.StreamHandler(sys.stdout)):
    h.setFormatter(_fmt)
    log.addHandler(h)

bridge_child = None  # our own Popen handle, if we spawned one


def db_high_water():
    """Return MAX(last_updated) from `current`, or None on DB trouble."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute('SELECT MAX(last_updated) FROM current')
        hw = cur.fetchone()[0]
        conn.close()
        return hw
    except Exception as e:
        log.error(f'DB check failed: {e}')
        return None


def find_bridge_pids():
    """PIDs of any python process running the bridge script (ours or orphaned)."""
    try:
        out = subprocess.run(
            ['powershell', '-NoProfile', '-Command',
             "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
             f"Where-Object {{ $_.CommandLine -like '*{BRIDGE_SCRIPT}*' }} | "
             "Select-Object -ExpandProperty ProcessId"],
            capture_output=True, text=True, timeout=30)
        return [int(p) for p in out.stdout.split()]
    except Exception as e:
        log.error(f'process scan failed: {e}')
        return []


def kill_bridge():
    """Kill bridge processes ONLY — matched by command line, by PID."""
    global bridge_child
    if bridge_child and bridge_child.poll() is None:
        bridge_child.kill()
    bridge_child = None
    for pid in find_bridge_pids():
        log.info(f'killing bridge pid {pid}')
        subprocess.run(['taskkill', '/F', '/PID', str(pid)],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def start_bridge():
    global bridge_child
    log.info('starting bridge')
    # bridge does its own file logging; discard the console stream
    bridge_child = subprocess.Popen(
        [sys.executable, BRIDGE_SCRIPT], cwd=str(BRIDGE_DIR),
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def restart_bridge():
    kill_bridge()
    time.sleep(3)
    start_bridge()


def main():
    log.info('=' * 60)
    log.info('KLDA-HFT watchdog up (bridge-only, surgical kills)')
    log.info('=' * 60)

    pids = find_bridge_pids()
    if pids:
        log.info(f'bridge already running (pid {pids}), adopting — will monitor')
    else:
        start_bridge()

    last_hw = None
    stalled = 0
    last_restart = 0.0

    while True:
        try:
            time.sleep(CHECK_EVERY_SEC)

            # a child we spawned dying is an immediate restart, no vote needed
            if bridge_child and bridge_child.poll() is not None:
                log.error(f'bridge child exited (code {bridge_child.returncode})')
                restart_bridge()
                last_restart = time.time()
                stalled = 0
                continue

            hw = db_high_water()
            if hw is not None and hw != last_hw:
                if stalled:
                    log.info('feed recovered')
                last_hw = hw
                stalled = 0
                continue

            stalled += 1
            log.warning(f'no new ticks ({stalled}/{STALL_CHECKS}) high-water={hw}')
            if stalled >= STALL_CHECKS:
                if time.time() - last_restart < MIN_RESTART_GAP_SEC:
                    log.warning('stall persists but inside restart cool-down '
                                '(market closed?) — waiting')
                else:
                    log.error('feed stalled — restarting bridge')
                    restart_bridge()
                    last_restart = time.time()
                stalled = 0

        except KeyboardInterrupt:
            log.info('watchdog stopping (bridge left running)')
            break
        except Exception as e:
            log.error(f'watchdog loop error: {e}')


if __name__ == '__main__':
    main()
