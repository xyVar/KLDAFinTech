#!/usr/bin/env python3
"""Test MT5 connection"""

import MetaTrader5 as mt5
import sys

print("Testing MT5 connection...")
print("=" * 60)

# Initialize MT5
if not mt5.initialize():
    print(f"[ERROR] MT5 initialization failed")
    print(f"Error code: {mt5.last_error()}")
    print("\nPossible causes:")
    print("1. MetaTrader 5 is not installed")
    print("2. MetaTrader 5 is not running")
    print("3. You need to open MT5 and log in first")
    sys.exit(1)

print("[OK] MT5 initialized successfully!")

# Get account info
account = mt5.account_info()
if account is None:
    print("[ERROR] Failed to get account info")
    print("Make sure you're logged into an MT5 account")
    mt5.shutdown()
    sys.exit(1)

print("\n[ACCOUNT INFO]")
print(f"  Login: {account.login}")
print(f"  Server: {account.server}")
print(f"  Balance: ${account.balance:.2f}")
print(f"  Equity: ${account.equity:.2f}")
print(f"  Leverage: 1:{account.leverage}")

# Test symbol access
print("\n[TESTING SYMBOLS]")
test_symbols = ['TSLA.US', 'NVDA.US', 'AAPL.US']

for symbol in test_symbols:
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is not None:
        tick = mt5.symbol_info_tick(symbol)
        if tick:
            print(f"  [OK] {symbol}: Bid={tick.bid}, Ask={tick.ask}")
        else:
            print(f"  [WARN] {symbol}: Info available but no tick data")
    else:
        print(f"  [FAIL] {symbol}: Not available")

print("\n" + "=" * 60)
print("[SUCCESS] MT5 connection test completed!")
print("=" * 60)

mt5.shutdown()
