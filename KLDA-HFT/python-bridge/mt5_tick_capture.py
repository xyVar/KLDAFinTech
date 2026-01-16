#!/usr/bin/env python3
"""
KLDA-HFT MT5 Tick Capture via Python
Connects to MT5 using Python library and sends ticks to API
BYPASSES MT5 WebRequest permission issues!
"""

import MetaTrader5 as mt5
import requests
import time
from datetime import datetime
import threading

# Configuration
API_URL = "http://localhost:5000/tick/batch"
SYMBOLS = [
    'TSLA.US', 'NVDA.US', 'PLTR.US', 'AMD.US', 'AVGO.US',
    'META.US', 'AAPL.US', 'MSFT.US', 'ORCL.US', 'AMZN.US',
    'CSCO.US', 'GOOG.US', 'INTC.US', 'VIX', 'NAS100',
    'NATGAS', 'CRUDEOIL'
]

# Statistics
stats = {
    'ticks_sent': 0,
    'ticks_failed': 0,
    'batches_sent': 0,
    'errors': 0
}

def connect_mt5():
    """Connect to MetaTrader 5"""
    print("=" * 60)
    print("KLDA-HFT MT5 Python Tick Capture")
    print("=" * 60)

    # Initialize MT5
    if not mt5.initialize():
        print(f"[ERROR] MT5 initialization failed: {mt5.last_error()}")
        return False

    # Get account info
    account_info = mt5.account_info()
    if account_info is None:
        print("[ERROR] Failed to get account info")
        return False

    print(f"[OK] Connected to MT5")
    print(f"  Account: {account_info.login}")
    print(f"  Server: {account_info.server}")
    print(f"  Balance: ${account_info.balance:.2f}")
    print(f"  Leverage: 1:{account_info.leverage}")

    return True

def subscribe_symbols():
    """Subscribe to all symbols"""
    print("\n[SYMBOLS] Subscribing to market data...")

    available = []
    unavailable = []

    for symbol in SYMBOLS:
        # Check if symbol exists
        symbol_info = mt5.symbol_info(symbol)

        if symbol_info is None:
            unavailable.append(symbol)
            continue

        # Enable symbol in MarketWatch
        if not symbol_info.visible:
            if not mt5.symbol_select(symbol, True):
                unavailable.append(symbol)
                continue

        available.append(symbol)
        print(f"  [OK] {symbol}")

    if unavailable:
        print(f"\n[WARNING] Unavailable symbols: {', '.join(unavailable)}")

    print(f"\n[OK] Subscribed to {len(available)} symbols")
    return available

def capture_ticks(symbols):
    """Capture ticks for all symbols"""
    ticks = []

    for symbol in symbols:
        # Get last tick
        tick = mt5.symbol_info_tick(symbol)

        if tick is None:
            continue

        # Convert timestamp to datetime with microseconds
        dt = datetime.fromtimestamp(tick.time)
        microseconds = tick.time_msc % 1000 * 1000
        timestamp = dt.strftime('%Y-%m-%d %H:%M:%S') + f'.{microseconds:06d}'

        # Calculate spread in points
        symbol_info = mt5.symbol_info(symbol)
        point = symbol_info.point
        spread = (tick.ask - tick.bid) / point if point > 0 else 0

        ticks.append({
            'symbol': symbol,
            'bid': tick.bid,
            'ask': tick.ask,
            'spread': spread,
            'volume': tick.volume,
            'flags': tick.flags,
            'timestamp': timestamp
        })

    return ticks

def send_to_api(ticks):
    """Send ticks to API server"""
    if not ticks:
        return

    try:
        payload = {'ticks': ticks}
        response = requests.post(API_URL, json=payload, timeout=5)

        if response.status_code == 200:
            stats['ticks_sent'] += len(ticks)
            stats['batches_sent'] += 1

            if stats['batches_sent'] % 10 == 0:
                print(f"[OK] Sent batch #{stats['batches_sent']} | Total ticks: {stats['ticks_sent']}")
        else:
            stats['ticks_failed'] += len(ticks)
            stats['errors'] += 1
            print(f"[ERROR] API returned {response.status_code}")

    except Exception as e:
        stats['ticks_failed'] += len(ticks)
        stats['errors'] += 1
        print(f"[ERROR] Failed to send ticks: {e}")

def print_stats():
    """Print statistics periodically"""
    while True:
        time.sleep(30)
        print("\n" + "=" * 60)
        print("STATISTICS")
        print("=" * 60)
        print(f"Ticks sent:     {stats['ticks_sent']}")
        print(f"Ticks failed:   {stats['ticks_failed']}")
        print(f"Batches sent:   {stats['batches_sent']}")
        print(f"Errors:         {stats['errors']}")
        print("=" * 60 + "\n")

def main():
    """Main tick capture loop"""
    # Connect to MT5
    if not connect_mt5():
        return

    # Subscribe to symbols
    symbols = subscribe_symbols()

    if not symbols:
        print("[ERROR] No symbols available!")
        return

    print("\n" + "=" * 60)
    print("TICK CAPTURE STARTED")
    print(f"API: {API_URL}")
    print(f"Monitoring: {len(symbols)} symbols")
    print("Press Ctrl+C to stop")
    print("=" * 60 + "\n")

    # Start statistics thread
    stats_thread = threading.Thread(target=print_stats, daemon=True)
    stats_thread.start()

    try:
        while True:
            # Capture ticks for all symbols
            ticks = capture_ticks(symbols)

            # Send to API
            if ticks:
                send_to_api(ticks)

            # Sleep 1 second (captures ~1 batch/second)
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n\n" + "=" * 60)
        print("STOPPING...")
        print("=" * 60)

    finally:
        # Print final stats
        print("\nFINAL STATISTICS:")
        print(f"  Ticks sent:     {stats['ticks_sent']}")
        print(f"  Ticks failed:   {stats['ticks_failed']}")
        print(f"  Batches sent:   {stats['batches_sent']}")
        print(f"  Errors:         {stats['errors']}")

        # Disconnect from MT5
        mt5.shutdown()
        print("\n[OK] Disconnected from MT5")
        print("=" * 60)

if __name__ == '__main__':
    main()
