#!/usr/bin/env python3
"""
KLDA-HFT nightly backup.

Strategy (C: has ~20 GB free, ticks table is ~357M rows and append-only):
1. BASE dump nightly: pg_dump -Fc of the whole DB EXCLUDING ticks data
   (schema included). Small — bars/signals/trades/config. Keep last 7.
2. TICKS archive incrementally: each fully-elapsed day of `ticks` is
   exported once to ticks_YYYY-MM-DD.csv.gz and never touched again.
   Restoring = restore base dump, then COPY the day files back in.

Run nightly via Task Scheduler; safe to run manually any time (idempotent).
"""
import gzip
import subprocess
import sys
import logging
from datetime import date
from pathlib import Path

import psycopg2

PG_DUMP = r'C:\Program Files\PostgreSQL\16\bin\pg_dump.exe'
BACKUP_DIR = Path(r'C:\Users\PC\Desktop\KLDAFinTech\backups')
KEEP_BASE_DUMPS = 7

DB = dict(host='127.0.0.1', port=5432, database='KLDA-HFT_Database',
          user='postgres', password='MyKldaTechnologies2025!')

BACKUP_DIR.mkdir(exist_ok=True)
(BACKUP_DIR / 'ticks').mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s',
    handlers=[logging.FileHandler(BACKUP_DIR / 'backup.log', encoding='utf-8'),
              logging.StreamHandler(sys.stdout)])
log = logging.getLogger('backup')


def base_dump():
    out = BACKUP_DIR / f'base_{date.today():%Y%m%d}.dump'
    if out.exists():
        log.info(f'base dump {out.name} already exists, skipping')
        return
    log.info(f'base dump -> {out.name} (schema + all data except ticks rows)')
    r = subprocess.run(
        [PG_DUMP, '-h', DB['host'], '-p', str(DB['port']), '-U', DB['user'],
         '-Fc', '--exclude-table-data=ticks', '-f', str(out), DB['database']],
        env={'PGPASSWORD': DB['password'], 'SystemRoot': r'C:\Windows'},
        capture_output=True, text=True, timeout=3600)
    if r.returncode != 0:
        log.error(f'pg_dump failed: {r.stderr.strip()[:500]}')
        out.unlink(missing_ok=True)
        return
    log.info(f'base dump done ({out.stat().st_size / 1e6:.0f} MB)')
    # prune
    dumps = sorted(BACKUP_DIR.glob('base_*.dump'))
    for old in dumps[:-KEEP_BASE_DUMPS]:
        log.info(f'pruning {old.name}')
        old.unlink()


def archive_tick_days():
    """Export each fully-elapsed day of ticks exactly once."""
    conn = psycopg2.connect(**DB)
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT time::date FROM ticks WHERE time::date < CURRENT_DATE ORDER BY 1")
    days = [r[0] for r in cur.fetchall()]
    for d in days:
        out = BACKUP_DIR / 'ticks' / f'ticks_{d}.csv.gz'
        if out.exists():
            continue
        tmp = out.with_suffix('.gz.part')
        log.info(f'archiving ticks {d} ...')
        try:
            with gzip.open(tmp, 'wt', newline='') as f:
                cur.copy_expert(
                    f"COPY (SELECT * FROM ticks WHERE time >= '{d}' AND "
                    f"time < '{d}'::date + interval '1 day' ORDER BY time) "
                    "TO STDOUT WITH CSV HEADER", f)
            tmp.rename(out)
            log.info(f'  {out.name} ({out.stat().st_size / 1e6:.0f} MB)')
        except Exception as e:
            log.error(f'  failed for {d}: {e}')
            tmp.unlink(missing_ok=True)
    conn.close()


def main():
    log.info('=== backup run start ===')
    base_dump()
    archive_tick_days()
    total = sum(f.stat().st_size for f in BACKUP_DIR.rglob('*') if f.is_file())
    log.info(f'=== backup run done, backup dir total {total / 1e9:.2f} GB ===')


if __name__ == '__main__':
    main()
