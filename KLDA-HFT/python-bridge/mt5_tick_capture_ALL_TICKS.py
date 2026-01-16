#!/usr/bin/env python3
"""
KLDA-HFT MT5 Tick Capture - CAPTURE ALL TICKS (not just last one)
"""

import MetaTrader5 as mt5
import requests
import time
from datetime import datetime, timedelta
import threading

# Configuration
API_URL = "http://localhost:5000/tick/batch"
SYMBOLS = [
    'TSLA.US', 'NVDA.US', 'PLTR.US', 'AMD.US', 'AVGO.US',
    'META.US', 'AAPL.US', 'MSFT.US', 'ORCL.US', 'AMZN.US',
    'CSCO.US', 'GOOG.US', 'INTC.US', 'VIX', 'NAS100',
    'NatGas', 'SpotCrude'
]

# Track last timestamp for each symbol (to fetch only NEW ticks)
last_timestamps = {}

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
    print("KLDA-HFT MT5 Tick Capture - ALL TICKS MODE")
    print("=" * 60)

    if not mt5.initialize():
        print(f"[ERROR] MT5 initialization failed: {mt5.last_error()}")
        return False

    account_info = mt5.account_info()
    if account_info is None:
        print("[ERROR] Failed to get account info")
        return False

    print(f"[OK] Connected to MT5")
    print(f"  Account: {account_info.login}")
    print(f"  Server: {account_info.server}")
    print(f"  Balance: ${account_info.balance:.2f}")
    print(f"  Mode: CAPTURE ALL TICKS (not sampling)")

    return True

def subscribe_symbols():
    """Subscribe to all symbols"""
    print("\n[SYMBOLS] Subscribing to market data...")

    available = []
    unavailable = []

    for symbol in SYMBOLS:
        symbol_info = mt5.symbol_info(symbol)

        if symbol_info is None:
            unavailable.append(symbol)
            continue

        if not symbol_info.visible:
            if not mt5.symbol_select(symbol, True):
                unavailable.append(symbol)
                continue

        available.append(symbol)

        # Initialize last timestamp using MT5's last tick time (not system time!)
        last_tick = mt5.symbol_info_tick(symbol)
        if last_tick:
            last_timestamps[symbol] = datetime.fromtimestamp(last_tick.time)
        else:
            # Fallback: use broker's current time
            last_timestamps[symbol] = datetime.fromtimestamp(mt5.symbol_info_tick('NAS100').time if mt5.symbol_info_tick('NAS100') else 0)

        print(f"  [OK] {symbol}")

    if unavailable:
        print(f"\n[WARNING] Unavailable symbols: {', '.join(unavailable)}")

    print(f"\n[OK] Subscribed to {len(available)} symbols")
    return available

def capture_all_ticks(symbols):
    """
    Capture ALL ticks since last check (not just the last one!)
    Uses mt5.copy_ticks_from() to get ALL ticks in time range
    """
    all_ticks = []

    for symbol in symbols:
        # Get BROKER's current time (not system time!)
        current_tick = mt5.symbol_info_tick(symbol)
        if not current_tick:
            continue

        now = datetime.fromtimestamp(current_tick.time)

        # Get last check time for this symbol
        from_time = last_timestamps.get(symbol, now - timedelta(seconds=1))

        # Fetch ALL ticks since last check
        # TICK_ALL = all ticks (quotes + trades)
        ticks_raw = mt5.copy_ticks_range(symbol, from_time, now, mt5.COPY_TICKS_ALL)

        if ticks_raw is None or len(ticks_raw) == 0:
            # No new ticks for this symbol
            continue

        # Update last timestamp to the newest tick time
        last_timestamps[symbol] = datetime.fromtimestamp(ticks_raw[-1]['time'])

        # Convert MT5 ticks to our format
        symbol_info = mt5.symbol_info(symbol)
        point = symbol_info.point if symbol_info else 0.00001

        for tick in ticks_raw:
            # Convert timestamp to datetime with microseconds
            dt = datetime.fromtimestamp(tick['time'])
            microseconds = tick['time_msc'] % 1000 * 1000
            timestamp = dt.strftime('%Y-%m-%d %H:%M:%S') + f'.{microseconds:06d}'

            # Calculate spread in points
            spread = (tick['ask'] - tick['bid']) / point if point > 0 else 0

            all_ticks.append({
                'symbol': symbol,
                'bid': float(tick['bid']),
                'ask': float(tick['ask']),
                'spread': float(spread),
                'volume': int(tick['volume']),
                'flags': int(tick['flags']),
                'timestamp': timestamp
            })

    return all_ticks

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
        else:
            stats['ticks_failed'] += len(ticks)
            print(f"[ERROR] API returned status {response.status_code}")

    except Exception as e:
        stats['errors'] += 1
        stats['ticks_failed'] += len(ticks)
        print(f"[ERROR] Failed to send ticks: {e}")

def print_stats():
    """Print statistics every 10 seconds"""
    while True:
        time.sleep(10)
        print("\n" + "=" * 60)
        print("STATISTICS")
        print("=" * 60)
        print(f"Ticks sent:     {stats['ticks_sent']}")
        print(f"Ticks failed:   {stats['ticks_failed']}")
        print(f"Batches sent:   {stats['batches_sent']}")
        print(f"Errors:         {stats['errors']}")
        print("=" * 60)

def main():
    # Connect to MT5
    if not connect_mt5():
        return

    # Subscribe to symbols
    available_symbols = subscribe_symbols()

    if not available_symbols:
        print("[ERROR] No symbols available")
        return

    # Start statistics thread
    stats_thread = threading.Thread(target=print_stats, daemon=True)
    stats_thread.start()

    print("\n[START] Capturing ALL ticks (every 100ms check)...")
    print("Press Ctrl+C to stop\n")

    # Main capture loop - check every 100ms for new ticks
    try:
        batch_counter = 0
        while True:
            # Capture ALL new ticks since last check
            ticks = capture_all_ticks(available_symbols)

            if ticks:
                # Send to API
                send_to_api(ticks)

                batch_counter += 1
                if batch_counter % 10 == 0:  # Print every 10 batches
                    print(f"[OK] Sent batch #{batch_counter} | {len(ticks)} ticks | Total: {stats['ticks_sent']}")

            # Sleep 100ms before next check (captures up to 10 ticks/second per symbol)
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n[STOP] Shutting down...")
        mt5.shutdown()

if __name__ == "__main__":
    main()
