#!/usr/bin/env python3
"""
Test - Can we capture ticks for TSLA right now?
"""

import MetaTrader5 as mt5
from datetime import datetime, timedelta

# Connect
if not mt5.initialize():
    print(f"[ERROR] MT5 init failed: {mt5.last_error()}")
    exit(1)

print("=" * 60)
print("TEST: Capturing TSLA ticks")
print("=" * 60)

symbol = 'TSLA.US'

# Test 1: Get last tick
print("\n[TEST 1] Get last tick:")
last_tick = mt5.symbol_info_tick(symbol)
if last_tick:
    print(f"  Bid: {last_tick.bid}")
    print(f"  Ask: {last_tick.ask}")
    print(f"  Time: {datetime.fromtimestamp(last_tick.time)}")
else:
    print("  [ERROR] No tick")

# Test 2: Try to get ticks from last 5 seconds
print("\n[TEST 2] Get ticks from last 5 seconds:")
now = datetime.now()
from_time = now - timedelta(seconds=5)

print(f"  From: {from_time}")
print(f"  To: {now}")

ticks = mt5.copy_ticks_range(symbol, from_time, now, mt5.COPY_TICKS_ALL)

if ticks is None:
    print(f"  [ERROR] copy_ticks_range returned None")
    print(f"  Error: {mt5.last_error()}")
elif len(ticks) == 0:
    print(f"  [WARNING] 0 ticks returned")
else:
    print(f"  [OK] Got {len(ticks)} ticks!")
    for i, tick in enumerate(ticks[:5]):  # Show first 5
        tick_time = datetime.fromtimestamp(tick['time'])
        print(f"    Tick {i+1}: {tick['bid']:.2f}/{tick['ask']:.2f} at {tick_time}")

# Test 3: Try with utcnow instead
print("\n[TEST 3] Try with UTC time:")
now_utc = datetime.utcnow()
from_utc = now_utc - timedelta(seconds=5)

print(f"  From (UTC): {from_utc}")
print(f"  To (UTC): {now_utc}")

ticks_utc = mt5.copy_ticks_range(symbol, from_utc, now_utc, mt5.COPY_TICKS_ALL)

if ticks_utc is None:
    print(f"  [ERROR] Returned None")
elif len(ticks_utc) == 0:
    print(f"  [WARNING] 0 ticks")
else:
    print(f"  [OK] Got {len(ticks_utc)} ticks with UTC!")

mt5.shutdown()
print("\n" + "=" * 60)
