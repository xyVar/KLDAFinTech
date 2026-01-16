#!/usr/bin/env python3
"""Debug MT5 tick structure"""

import MetaTrader5 as mt5

mt5.initialize()

# Get a real tick from AAPL
symbol = 'AAPL.US'
tick = mt5.symbol_info_tick(symbol)

print("=" * 60)
print(f"MT5 TICK STRUCTURE FOR {symbol}")
print("=" * 60)

if tick:
    print(f"\nTime:         {tick.time}")
    print(f"Time MSC:     {tick.time_msc}")
    print(f"Bid:          {tick.bid}")
    print(f"Ask:          {tick.ask}")
    print(f"Last:         {tick.last}")
    print(f"Volume:       {tick.volume}")
    print(f"Flags:        {tick.flags}")
    print(f"Volume Real:  {tick.volume_real}")

    # Decode flags
    print(f"\nFLAGS BREAKDOWN (value={tick.flags}):")
    print(f"  BID flag (1):  {bool(tick.flags & 1)}")
    print(f"  ASK flag (2):  {bool(tick.flags & 2)}")
    print(f"  LAST flag (4): {bool(tick.flags & 4)}")
    print(f"  VOLUME flag (8): {bool(tick.flags & 8)}")
    print(f"  BUY flag (16):   {bool(tick.flags & 16)}")
    print(f"  SELL flag (32):  {bool(tick.flags & 32)}")

    print("\nMT5 DOCUMENTATION:")
    print("  TICK_FLAG_BID = 2")
    print("  TICK_FLAG_ASK = 4")
    print("  TICK_FLAG_LAST = 8")
    print("  TICK_FLAG_VOLUME = 16")
    print("  TICK_FLAG_BUY = 32")
    print("  TICK_FLAG_SELL = 64")

    # What flags=6 means
    if tick.flags == 6:
        print(f"\n[ANALYSIS] flags=6 means:")
        print(f"  BID flag (2) + ASK flag (4) = 6")
        print(f"  This is a QUOTE UPDATE (both bid and ask changed)")
        print(f"  NOT a trade execution!")
else:
    print("[ERROR] Could not get tick")

mt5.shutdown()
