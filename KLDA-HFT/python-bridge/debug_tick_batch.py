#!/usr/bin/env python3
"""
Debug - Check what symbols are in the tick batches being sent
"""

import MetaTrader5 as mt5
from datetime import datetime, timedelta

SYMBOLS = [
    'TSLA.US', 'NVDA.US', 'PLTR.US', 'AMD.US', 'AVGO.US',
    'META.US', 'AAPL.US', 'MSFT.US', 'ORCL.US', 'AMZN.US',
    'CSCO.US', 'GOOG.US', 'INTC.US', 'VIX', 'NAS100',
    'NatGas', 'SpotCrude'
]

# Connect to MT5
if not mt5.initialize():
    print(f"[ERROR] MT5 init failed: {mt5.last_error()}")
    exit(1)

print("=" * 80)
print("DEBUG: Capturing one batch of ticks")
print("=" * 80)

all_ticks = []
last_timestamps = {}

for symbol in SYMBOLS:
    # Get current tick to establish broker time
    current_tick = mt5.symbol_info_tick(symbol)
    if not current_tick:
        print(f"[X] {symbol:15s} - No current tick available")
        continue

    now = datetime.fromtimestamp(current_tick.time)
    from_time = now - timedelta(seconds=5)  # Last 5 seconds

    # Fetch ticks
    ticks_raw = mt5.copy_ticks_range(symbol, from_time, now, mt5.COPY_TICKS_ALL)

    if ticks_raw is None:
        print(f"[X] {symbol:15s} - copy_ticks_range returned None")
        continue
    elif len(ticks_raw) == 0:
        print(f"[!] {symbol:15s} - 0 ticks in last 5 seconds")
        continue
    else:
        print(f"[OK] {symbol:15s} - {len(ticks_raw)} ticks | Bid: {ticks_raw[-1]['bid']:.4f} | Ask: {ticks_raw[-1]['ask']:.4f}")

        # Add to batch
        for tick in ticks_raw:
            all_ticks.append({
                'symbol': symbol,
                'bid': float(tick['bid']),
                'ask': float(tick['ask']),
                'time': datetime.fromtimestamp(tick['time'])
            })

print("\n" + "=" * 80)
print(f"TOTAL TICKS CAPTURED: {len(all_ticks)}")
print("=" * 80)

# Group by symbol
from collections import Counter
symbol_counts = Counter([t['symbol'] for t in all_ticks])

print("\nTICKS PER SYMBOL:")
for symbol, count in sorted(symbol_counts.items()):
    print(f"  {symbol:15s}: {count} ticks")

# Show NatGas and SpotCrude details
print("\n" + "=" * 80)
print("NATGAS AND SPOTCRUDE DETAILS:")
print("=" * 80)

natgas_ticks = [t for t in all_ticks if t['symbol'] == 'NatGas']
if natgas_ticks:
    print(f"\n[OK] NatGas - {len(natgas_ticks)} ticks captured:")
    for tick in natgas_ticks[:3]:  # Show first 3
        print(f"  Bid: {tick['bid']:.4f} | Ask: {tick['ask']:.4f} | Time: {tick['time']}")
else:
    print("\n[X] NatGas - NO TICKS CAPTURED!")

spotcrude_ticks = [t for t in all_ticks if t['symbol'] == 'SpotCrude']
if spotcrude_ticks:
    print(f"\n[OK] SpotCrude - {len(spotcrude_ticks)} ticks captured:")
    for tick in spotcrude_ticks[:3]:  # Show first 3
        print(f"  Bid: {tick['bid']:.4f} | Ask: {tick['ask']:.4f} | Time: {tick['time']}")
else:
    print("\n[X] SpotCrude - NO TICKS CAPTURED!")

mt5.shutdown()

print("\n" + "=" * 80)
