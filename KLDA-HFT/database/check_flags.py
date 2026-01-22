#!/usr/bin/env python3
"""
Check what tick flags are being received from MT5
"""

import psycopg2

conn = psycopg2.connect(
    host='localhost',
    port=5432,
    database='KLDA-HFT_Database',
    user='postgres',
    password='MyKldaTechnologies2025!'
)

cursor = conn.cursor()

print("=" * 80)
print("TICK FLAGS ANALYSIS")
print("=" * 80)
print("\nMT5 Flag Reference:")
print("  BID (2)    = Bid price changed")
print("  ASK (4)    = Ask price changed")
print("  LAST (8)   = Last price (trade) changed - HAS VOLUME")
print("  VOLUME (16)= Volume available")
print("  BUY (32)   = Buy trade (at ask)")
print("  SELL (64)  = Sell trade (at bid)")
print("=" * 80)

# Check current table
cursor.execute("""
    SELECT symbol, flags, volume, buy_volume, sell_volume, last_updated
    FROM current
    WHERE symbol IN ('NatGas', 'SpotCrude', 'NAS100', 'VIX')
    ORDER BY symbol;
""")

print("\nCURRENT TABLE (Latest Ticks):")
print("-" * 80)
print(f"{'Symbol':<12} {'Flags':<8} {'Volume':<10} {'Buy Vol':<10} {'Sell Vol':<10} {'Updated'}")
print("-" * 80)

for row in cursor.fetchall():
    symbol, flags, volume, buy_vol, sell_vol, last_updated = row

    # Decode flags
    flag_str = []
    if flags & 2:  flag_str.append("BID")
    if flags & 4:  flag_str.append("ASK")
    if flags & 8:  flag_str.append("LAST")
    if flags & 16: flag_str.append("VOL")
    if flags & 32: flag_str.append("BUY")
    if flags & 64: flag_str.append("SELL")

    flags_decoded = f"{flags} ({'+'.join(flag_str)})"

    print(f"{symbol:<12} {flags_decoded:<30} {volume:<10} {buy_vol:<10} {sell_vol:<10} {str(last_updated)[:19]}")

# Check recent history for SpotCrude
print("\n" + "=" * 80)
print("SPOTCRUDE RECENT HISTORY (Last 100 ticks):")
print("=" * 80)

cursor.execute("""
    WITH recent_ticks AS (
        SELECT flags
        FROM spotcrude_history
        ORDER BY time DESC
        LIMIT 100
    )
    SELECT flags, COUNT(*) as count
    FROM recent_ticks
    GROUP BY flags
    ORDER BY count DESC;
""")

print(f"\n{'Flags':<8} {'Count':<8} {'Decoded'}")
print("-" * 80)

for row in cursor.fetchall():
    flags, count = row

    flag_str = []
    if flags & 2:  flag_str.append("BID")
    if flags & 4:  flag_str.append("ASK")
    if flags & 8:  flag_str.append("LAST")
    if flags & 16: flag_str.append("VOL")
    if flags & 32: flag_str.append("BUY")
    if flags & 64: flag_str.append("SELL")

    flags_decoded = '+'.join(flag_str) if flag_str else "NONE"

    print(f"{flags:<8} {count:<8} {flags_decoded}")

# Check if any TRADE ticks exist
cursor.execute("""
    SELECT COUNT(*) as trade_ticks
    FROM spotcrude_history
    WHERE (flags & 8) = 8
    LIMIT 1000;
""")

cursor.execute("""
    WITH recent_ticks AS (
        SELECT flags
        FROM spotcrude_history
        ORDER BY time DESC
        LIMIT 1000
    )
    SELECT COUNT(*) as trade_ticks
    FROM recent_ticks
    WHERE (flags & 8) = 8;
""")

trade_count = cursor.fetchone()[0]

print("\n" + "=" * 80)
print("VERDICT:")
print("=" * 80)

if trade_count == 0:
    print("\n[!] NO TRADE TICKS DETECTED")
    print("    All ticks are QUOTE ticks (bid/ask updates only)")
    print("    Broker is NOT sending executed trade volume")
    print("\nPOSSIBLE REASONS:")
    print("  1. Pepperstone doesn't provide trade volume for CFDs")
    print("  2. MT5 copy_ticks_range() only gets QUOTE ticks for these symbols")
    print("  3. Real trade volume requires different data subscription")
else:
    print(f"\n[OK] Found {trade_count} TRADE ticks in last 1000 ticks")
    print("     Trade volume IS available")

cursor.close()
conn.close()
