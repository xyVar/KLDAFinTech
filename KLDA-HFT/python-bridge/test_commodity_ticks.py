#!/usr/bin/env python3
"""
Test - Do NatGas and SpotCrude produce ticks at all?
"""

import MetaTrader5 as mt5
from datetime import datetime, timedelta
import time

# Connect
if not mt5.initialize():
    print(f"[ERROR] MT5 init failed: {mt5.last_error()}")
    exit(1)

print("=" * 80)
print("COMMODITY TICK MONITORING - 30 SECOND TEST")
print("=" * 80)

commodities = ['NatGas', 'SpotCrude']

# Get initial state
initial_ticks = {}
for symbol in commodities:
    tick = mt5.symbol_info_tick(symbol)
    if tick:
        initial_ticks[symbol] = {
            'time': tick.time,
            'bid': tick.bid,
            'ask': tick.ask
        }
        print(f"\n[INITIAL] {symbol}:")
        print(f"  Bid: {tick.bid:.4f}")
        print(f"  Ask: {tick.ask:.4f}")
        print(f"  Time: {datetime.fromtimestamp(tick.time)}")
    else:
        print(f"\n[X] {symbol} - No tick available")

print("\n" + "-" * 80)
print("Monitoring for 30 seconds...")
print("-" * 80)

# Monitor for 30 seconds
for i in range(30):
    time.sleep(1)

    for symbol in commodities:
        current_tick = mt5.symbol_info_tick(symbol)
        if current_tick and symbol in initial_ticks:
            # Check if price or time changed
            if (current_tick.bid != initial_ticks[symbol]['bid'] or
                current_tick.ask != initial_ticks[symbol]['ask'] or
                current_tick.time != initial_ticks[symbol]['time']):

                print(f"\n[{i+1}s] {symbol} - TICK DETECTED!")
                print(f"  Bid: {initial_ticks[symbol]['bid']:.4f} -> {current_tick.bid:.4f}")
                print(f"  Ask: {initial_ticks[symbol]['ask']:.4f} -> {current_tick.ask:.4f}")
                print(f"  Time: {datetime.fromtimestamp(current_tick.time)}")

                # Update initial state
                initial_ticks[symbol] = {
                    'time': current_tick.time,
                    'bid': current_tick.bid,
                    'ask': current_tick.ask
                }

print("\n" + "=" * 80)
print("MONITORING COMPLETE")
print("=" * 80)

# Final state
print("\n[FINAL STATE]")
for symbol in commodities:
    current_tick = mt5.symbol_info_tick(symbol)
    if current_tick and symbol in initial_ticks:
        time_diff = current_tick.time - initial_ticks[symbol]['time']
        print(f"\n{symbol}:")
        print(f"  Current Bid: {current_tick.bid:.4f}")
        print(f"  Current Ask: {current_tick.ask:.4f}")
        if time_diff > 0:
            print(f"  [OK] Price updated during test (last update {time_diff}s ago)")
        else:
            print(f"  [!] NO UPDATES in last 30 seconds")

# Try to get historical ticks
print("\n" + "=" * 80)
print("CHECKING HISTORICAL TICKS (last 5 minutes)")
print("=" * 80)

now = datetime.now()
five_min_ago = now - timedelta(minutes=5)

for symbol in commodities:
    current_tick = mt5.symbol_info_tick(symbol)
    if not current_tick:
        continue

    broker_now = datetime.fromtimestamp(current_tick.time)
    broker_five_min_ago = broker_now - timedelta(minutes=5)

    ticks = mt5.copy_ticks_range(symbol, broker_five_min_ago, broker_now, mt5.COPY_TICKS_ALL)

    if ticks is None:
        print(f"\n{symbol}: copy_ticks_range returned None")
    elif len(ticks) == 0:
        print(f"\n{symbol}: 0 ticks in last 5 minutes [MARKET CLOSED OR VERY SLOW]")
    else:
        print(f"\n{symbol}: {len(ticks)} ticks in last 5 minutes")
        print(f"  First tick: {datetime.fromtimestamp(ticks[0]['time'])}")
        print(f"  Last tick: {datetime.fromtimestamp(ticks[-1]['time'])}")
        print(f"  Average: {len(ticks)/5:.1f} ticks per minute")

mt5.shutdown()

print("\n" + "=" * 80)
