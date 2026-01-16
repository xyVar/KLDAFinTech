#!/usr/bin/env python3
"""
Check what symbols are available on Pepperstone broker
"""

import MetaTrader5 as mt5

# Connect to MT5
if not mt5.initialize():
    print(f"[ERROR] MT5 initialization failed: {mt5.last_error()}")
    exit(1)

print("=" * 60)
print("CHECKING BROKER SYMBOLS")
print("=" * 60)

# Check for natural gas variants
print("\n[1] NATURAL GAS SYMBOLS:")
gas_variants = ['NATGAS', 'NGAS', 'NG', 'NatGas', 'NATURALGAS', 'XNGUSD']
for symbol in gas_variants:
    info = mt5.symbol_info(symbol)
    if info is not None:
        print(f"  ✅ {symbol} - {info.description}")
    else:
        print(f"  ❌ {symbol} - Not available")

# Check for crude oil variants
print("\n[2] CRUDE OIL SYMBOLS:")
oil_variants = ['CRUDEOIL', 'CRUDE', 'WTI', 'SpotCrude', 'XTIUSD', 'USOIL', 'CL']
for symbol in oil_variants:
    info = mt5.symbol_info(symbol)
    if info is not None:
        print(f"  ✅ {symbol} - {info.description}")
    else:
        print(f"  ❌ {symbol} - Not available")

# Get ALL symbols (to see what's actually available)
print("\n[3] ALL AVAILABLE SYMBOLS WITH 'GAS' OR 'OIL' OR 'CRUDE':")
all_symbols = mt5.symbols_get()
matching = [s for s in all_symbols if any(word in s.name.upper() for word in ['GAS', 'OIL', 'CRUDE', 'WTI', 'NG'])]

if matching:
    for s in matching:
        print(f"  {s.name} - {s.description}")
else:
    print("  No matching symbols found")

mt5.shutdown()
print("\n" + "=" * 60)
