#!/usr/bin/env python3
"""
Find the correct symbol names for Natural Gas and Crude Oil on Pepperstone broker
"""

import MetaTrader5 as mt5

# Connect
if not mt5.initialize():
    print(f"[ERROR] MT5 init failed: {mt5.last_error()}")
    exit(1)

print("=" * 80)
print("SEARCHING FOR NATURAL GAS AND CRUDE OIL SYMBOLS ON PEPPERSTONE")
print("=" * 80)

# Get ALL symbols from broker
all_symbols = mt5.symbols_get()

print(f"\nTotal symbols available: {len(all_symbols)}")

# Search for natural gas
print("\n[1] NATURAL GAS SYMBOLS:")
print("-" * 80)
gas_symbols = [s for s in all_symbols if any(word in s.name.upper() for word in ['GAS', 'NG', 'NGAS', 'NATURALGAS'])]

if gas_symbols:
    for s in gas_symbols:
        tick = mt5.symbol_info_tick(s.name)
        if tick:
            print(f"  [OK] {s.name:20s} - {s.description:40s} | Bid: {tick.bid:.4f}")
        else:
            print(f"  [OK] {s.name:20s} - {s.description}")
else:
    print("  No natural gas symbols found")

# Search for crude oil
print("\n[2] CRUDE OIL / OIL SYMBOLS:")
print("-" * 80)
oil_symbols = [s for s in all_symbols if any(word in s.name.upper() for word in ['OIL', 'CRUDE', 'WTI', 'BRENT', 'CL', 'USO'])]

if oil_symbols:
    for s in oil_symbols:
        tick = mt5.symbol_info_tick(s.name)
        if tick:
            print(f"  [OK] {s.name:20s} - {s.description:40s} | Bid: {tick.bid:.4f}")
        else:
            print(f"  [OK] {s.name:20s} - {s.description}")
else:
    print("  No crude oil symbols found")

# Search for any energy/commodity symbols
print("\n[3] OTHER ENERGY/COMMODITY SYMBOLS:")
print("-" * 80)
energy_symbols = [s for s in all_symbols if any(word in s.name.upper() for word in ['ENERGY', 'XNG', 'XTI', 'XBRUSD', 'NYMEX'])]

if energy_symbols:
    for s in energy_symbols:
        tick = mt5.symbol_info_tick(s.name)
        if tick:
            print(f"  [OK] {s.name:20s} - {s.description:40s} | Bid: {tick.bid:.4f}")
        else:
            print(f"  [OK] {s.name:20s} - {s.description}")
else:
    print("  No additional energy symbols found")

# Try common commodity symbol patterns
print("\n[4] TESTING COMMON COMMODITY SYMBOL NAMES:")
print("-" * 80)

test_symbols = [
    'NGAS', 'NATGAS', 'NG', 'XNGUSD', 'NATURALGAS',
    'CL', 'CRUDE', 'CRUDEOIL', 'WTI', 'XTIUSD', 'USOIL', 'BRENT', 'UKOIL'
]

for test_sym in test_symbols:
    info = mt5.symbol_info(test_sym)
    if info:
        tick = mt5.symbol_info_tick(test_sym)
        if tick:
            print(f"  [OK] {test_sym:20s} - FOUND! | Bid: {tick.bid:.4f} | Description: {info.description}")
        else:
            print(f"  [OK] {test_sym:20s} - FOUND! | Description: {info.description}")
    else:
        print(f"  [X] {test_sym:20s} - Not available")

mt5.shutdown()

print("\n" + "=" * 80)
print("SEARCH COMPLETE")
print("=" * 80)
