#!/usr/bin/env python3
"""
KLDA-HFT shared config loader.

Reads KLDA-HFT/config/trading_config.json — the single source of truth for:
  - paper_mode        (one flag, consumed by broker_adapter_mt5 + signal_generator)
  - execution_path    ('order_router' or 'klda_engine' — only one may consume signals)
  - thresholds        (per-symbol signal thresholds; 'default' + symbol overrides)

Usage:
    from config_loader import get_config, paper_mode, execution_path, thresholds_for
"""
import json
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent.parent / 'config' / 'trading_config.json'

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
