#!/usr/bin/env python3
"""
Debug script - Check which symbols are ACTUALLY ticking right now
"""

import MetaTrader5 as mt5
import time
from datetime import datetime

SYMBOLS = [
    'TSLA.US', 'NVDA.US', 'PLTR.US', 'AMD.US', 'AVGO.US',
    'META.US', 'AAPL.US', 'MSFT.US', 'ORCL.US', 'AMZN.US',
    'CSCO.US', 'GOOG.US', 'INTC.US', 'VIX', 'NAS100',
    'NATGAS', 'CRUDEOIL'
]

# Connect to MT5
if not mt5.initialize():
    print(f"[ERROR] MT5 initialization failed: {mt5.last_error()}")
    exit(1)

print("=" * 80)
print("BROKER TICK DEBUG - WHICH SYMBOLS ARE TICKING RIGHT NOW?")
print("=" * 80)

# First check - Get last tick for each symbol
print("\n[1] CHECKING LAST TICK FOR EACH SYMBOL:")
print("-" * 80)

for symbol in SYMBOLS:
    tick = mt5.symbol_info_tick(symbol)

    if tick is None:
        print(f"[X] {symbol:15s} - Symbol not found on broker")
    else:
        tick_time = datetime.fromtimestamp(tick.time)
        now = datetime.now()
        seconds_ago = (now - tick_time).total_seconds()

        if seconds_ago < 10:
            status = "[LIVE]"
        elif seconds_ago < 3600:
            status = "[RECENT]"
        else:
            status = "[OLD]"

        print(f"{status} {symbol:15s} - Bid: {tick.bid:10.2f} | Ask: {tick.ask:10.2f} | {seconds_ago:.0f}s ago")

# Second check - Monitor for 10 seconds and count new ticks
print("\n\n[2] MONITORING LIVE TICK FLOW (10 seconds)...")
print("-" * 80)
print("Counting new ticks per symbol...")

# Store initial timestamps
initial_timestamps = {}
for symbol in SYMBOLS:
    tick = mt5.symbol_info_tick(symbol)
    if tick:
        initial_timestamps[symbol] = tick.time

# Wait 10 seconds
time.sleep(10)

# Check how many NEW ticks each symbol received
print("\n[3] RESULTS - TICKS RECEIVED IN LAST 10 SECONDS:")
print("-" * 80)

for symbol in SYMBOLS:
    tick = mt5.symbol_info_tick(symbol)

    if tick is None:
        print(f"[X] {symbol:15s} - Symbol not available")
    elif symbol not in initial_timestamps:
        print(f"[X] {symbol:15s} - No initial tick")
    else:
        # Check if timestamp changed
        if tick.time > initial_timestamps[symbol]:
            time_diff = tick.time - initial_timestamps[symbol]
            print(f"[LIVE] {symbol:15s} - LIVE TICKING! ({time_diff:.1f}s of new data)")
        else:
            tick_time = datetime.fromtimestamp(tick.time)
            now = datetime.now()
            seconds_ago = (now - tick_time).total_seconds()
            print(f"[OLD] {symbol:15s} - NO NEW TICKS (last tick was {seconds_ago/3600:.1f} hours ago)")

# Third check - Get trading session info
print("\n\n[4] BROKER TRADING SESSIONS:")
print("-" * 80)

for symbol in SYMBOLS:
    info = mt5.symbol_info(symbol)
    if info:
        # Check if symbol is tradeable right now
        if info.trade_mode == mt5.SYMBOL_TRADE_MODE_FULL:
            trade_status = "[TRADEABLE]"
        elif info.trade_mode == mt5.SYMBOL_TRADE_MODE_CLOSEONLY:
            trade_status = "[CLOSE ONLY]"
        else:
            trade_status = "[NOT TRADEABLE]"

        print(f"{trade_status} {symbol:15s} - Session: {info.session_deals} | Volume: {info.volume}")

mt5.shutdown()

print("\n" + "=" * 80)
print("DEBUG COMPLETE")
print("=" * 80)
