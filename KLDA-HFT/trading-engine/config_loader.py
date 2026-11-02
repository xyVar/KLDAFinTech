#!/usr/bin/env python3
"""
KLDA-HFT shared config loader.

Reads KLDA-HFT/config/trading_config.json — the single source of truth for:
  - paper_mode        (one flag, consumed by broker_adapter_mt5 + signal_generator)
  - execution_path    ('order_router' or 'klda_engine' — only one may consume signals)
  - thresholds        (per-symbol signal thresholds + exit geometry; 'default' + symbol overrides)
  - broker_time       (how to derive broker server time from UTC)
  - intraday          (broker-time entry cutoff and end-of-day close)

and KLDA-HFT/config/validated_patterns.json — the live-order allowlist.

Usage:
    from config_loader import get_config, paper_mode, execution_path, thresholds_for
    from config_loader import is_validated, broker_now, to_broker_time, intraday_times
"""
import json
from datetime import datetime, time as dtime, timedelta, timezone
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent.parent / 'config' / 'trading_config.json'
VALIDATED_PATH = Path(__file__).resolve().parent.parent / 'config' / 'validated_patterns.json'

# PROTOCOL gate — an allowlist entry that does not clear this is ignored.
GATE_MIN_OCCURRENCES = 100
GATE_MIN_WIN_RATE    = 0.51
GATE_MAX_P_VALUE     = 0.05

_cache = None


def get_config() -> dict:
    global _cache
    if _cache is None:
        with open(CONFIG_PATH, encoding='utf-8') as f:
            _cache = json.load(f)
    return _cache


def reload_config() -> dict:
    global _cache
    _cache = None
    return get_config()


def paper_mode() -> bool:
    return bool(get_config().get('paper_mode', True))


def execution_path() -> str:
    return get_config().get('execution_path', 'order_router')


def thresholds_for(symbol: str) -> dict:
    """Default thresholds merged with the symbol's overrides (if any)."""
    th = get_config().get('thresholds', {})
    merged = dict(th.get('default', {}))
    override = th.get(symbol, {})
    merged.update({k: v for k, v in override.items() if not k.startswith('_')})
    return merged


# ── Live-order allowlist ──────────────────────────────────────────────────────
def is_validated(symbol: str, pattern: str | None = None) -> tuple[bool, str]:
    """
    True only if config/validated_patterns.json lists `symbol` under 'validated'
    with stats that clear the PROTOCOL gate (and a matching pattern, if given).
    Re-read on every call so the file cannot be stale; any read error = refuse.
    """
    try:
        with open(VALIDATED_PATH, encoding='utf-8') as f:
            entry = json.load(f).get('validated', {}).get(symbol)
    except Exception as e:
        return False, f"validated_patterns.json unreadable: {e}"
    if not entry:
        return False, f"{symbol} not in validated_patterns.json"
    if pattern and entry.get('pattern') != pattern:
        return False, f"{symbol}: validated pattern is {entry.get('pattern')}, signal is {pattern}"
    try:
        ok = (int(entry['occurrences'])   >= GATE_MIN_OCCURRENCES and
              float(entry['win_rate'])    >= GATE_MIN_WIN_RATE and
              float(entry['p_value'])     <  GATE_MAX_P_VALUE and
              float(entry['net_pnl_pct']) >  0)
    except (KeyError, TypeError, ValueError) as e:
        return False, f"{symbol}: incomplete gate stats ({e})"
    if not ok:
        return False, f"{symbol}: listed but stats do not clear the gate"
    return True, 'validated'


# ── Broker time ───────────────────────────────────────────────────────────────
def broker_utc_offset_hours(at_utc: datetime | None = None) -> float:
    """Broker server UTC offset at `at_utc` (default now)."""
    bt = get_config().get('broker_time', {})
    at_utc = at_utc or datetime.now(timezone.utc)
    if bt.get('rule', 'ny_close') == 'ny_close':
        try:
            from zoneinfo import ZoneInfo  # on Windows needs: pip install tzdata
            ny = at_utc.astimezone(ZoneInfo('America/New_York')).utcoffset()
            return ny.total_seconds() / 3600 + 7
        except Exception:
            pass
    return float(bt.get('utc_offset_hours', 3))


def to_broker_time(dt: datetime) -> datetime:
    """Aware datetime -> naive broker wall-clock time."""
    utc = dt.astimezone(timezone.utc)
    return (utc + timedelta(hours=broker_utc_offset_hours(utc))).replace(tzinfo=None)


def broker_now() -> datetime:
    """Current broker wall-clock time (naive), independent of the PC's timezone."""
    return to_broker_time(datetime.now(timezone.utc))


def _hhmm(s: str) -> dtime:
    h, m = s.split(':')
    return dtime(int(h), int(m))


def intraday_times() -> tuple[dtime, dtime]:
    """(no_new_entries_after, close_all_at) as broker-time times."""
    it = get_config().get('intraday', {})
    return (_hhmm(it.get('no_new_entries_after', '23:30')),
            _hhmm(it.get('close_all_at', '23:45')))
