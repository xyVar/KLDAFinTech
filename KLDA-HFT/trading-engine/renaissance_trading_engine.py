#!/usr/bin/env python3
"""
Renaissance Trading Engine - Autonomous Trading System
Does NOT rely on MT5 EA - algo controls everything independently
"""

import MetaTrader5 as mt5
import psycopg2
from psycopg2.extras import execute_batch
import time
from datetime import datetime
import json

# Database Configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'KLDA-HFT_Database',
    'user': 'postgres',
    'password': 'MyKldaTechnologies2025!'
}

# Trading Parameters
INITIAL_CAPITAL = 10000.0
RISK_PER_TRADE = 0.02  # 2%
TARGET_PROFIT_PCT = 0.005  # 0.5%
STOP_LOSS_PCT = 0.01  # 1%
MAX_POSITIONS = 4  # Max concurrent positions

# Renaissance Thresholds (Commodities-optimized)
MEAN_REV_THRESHOLD = -0.2
SPREAD_VOL_THRESHOLD = 50.0
HMM_TREND_THRESHOLD = 0.1
MAX_TX_COST = 20.0
MAX_KELLY_PCT = 2.0

# Symbols to trade (LIVE markets only)
TRADE_SYMBOLS = ['NAS100', 'SpotCrude', 'NatGas', 'VIX']

class RenaissanceTradingEngine:
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.account_balance = INITIAL_CAPITAL
        self.open_positions = {}
        self.closed_trades = []

        print("=" * 80)
        print("RENAISSANCE TRADING ENGINE - INITIALIZING")
        print("=" * 80)

    def connect_database(self):
        """Connect to PostgreSQL"""
        print("\n[1/3] Connecting to database...")
        self.conn = psycopg2.connect(**DB_CONFIG)
        self.cursor = self.conn.cursor()

        # Create positions table if not exists
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS positions (
                id SERIAL PRIMARY KEY,
                symbol VARCHAR(20) NOT NULL,
                entry_time TIMESTAMP NOT NULL,
                entry_price DOUBLE PRECISION NOT NULL,
                shares DOUBLE PRECISION NOT NULL,
                position_size DOUBLE PRECISION NOT NULL,
                stop_loss DOUBLE PRECISION NOT NULL,
                take_profit DOUBLE PRECISION NOT NULL,
                status VARCHAR(20) DEFAULT 'OPEN',
                exit_time TIMESTAMP,
                exit_price DOUBLE PRECISION,
                pnl DOUBLE PRECISION,
                mt5_ticket BIGINT
            );
        """)

        self.conn.commit()
        print("    [OK] Database connected")

    def connect_mt5(self):
        """Connect to MetaTrader 5"""
        print("\n[2/3] Connecting to MT5...")

        if not mt5.initialize():
            print(f"    [ERROR] MT5 initialization failed: {mt5.last_error()}")
            return False

        account_info = mt5.account_info()
        if account_info is None:
            print("    [ERROR] Failed to get account info")
            return False

        print(f"    [OK] Connected to MT5")
        print(f"         Account: {account_info.login}")
        print(f"         Balance: ${account_info.balance:.2f}")
        print(f"         Server: {account_info.server}")

        return True

    def load_open_positions(self):
        """Load existing open positions from database"""
        print("\n[3/3] Loading open positions...")

        self.cursor.execute("""
            SELECT id, symbol, entry_time, entry_price, shares, position_size,
                   stop_loss, take_profit, mt5_ticket
            FROM positions
            WHERE status = 'OPEN'
            ORDER BY entry_time DESC;
        """)

        rows = self.cursor.fetchall()

        for row in rows:
            pos_id, symbol, entry_time, entry_price, shares, position_size, stop_loss, take_profit, mt5_ticket = row

            self.open_positions[symbol] = {
                'id': pos_id,
                'entry_time': entry_time,
                'entry_price': entry_price,
                'shares': shares,
                'position_size': position_size,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'mt5_ticket': mt5_ticket
            }

        print(f"    [OK] Loaded {len(self.open_positions)} open positions")

    def get_current_metrics(self, symbol):
        """Get Renaissance metrics from database (calculated by C++ backend)"""
        self.cursor.execute("""
            SELECT bid, ask, spread, last_updated
            FROM current
            WHERE symbol = %s;
        """, (symbol,))

        row = self.cursor.fetchone()
        if not row:
            return None

        bid, ask, spread, last_updated = row

        # Check if data is fresh (< 60 seconds old)
        self.cursor.execute("SELECT EXTRACT(EPOCH FROM (NOW() - %s)) as age;", (last_updated,))
        age = self.cursor.fetchone()[0]

        if age > 60:
            return None  # Data too old

        # Get historical ticks for calculations
        table_name = f"{symbol.lower()}_history"

        # Mean Reversion
        self.cursor.execute(f"""
            WITH recent AS (
                SELECT bid FROM {table_name}
                ORDER BY time DESC LIMIT 50
            )
            SELECT AVG(bid) as ma50 FROM recent;
        """)
        ma50 = self.cursor.fetchone()[0]
        mean_rev = ((bid - ma50) / ma50) * 100.0 if ma50 else 0

        # Spread Volatility
        self.cursor.execute(f"""
            WITH recent AS (
                SELECT spread FROM {table_name}
                ORDER BY time DESC LIMIT 100
            )
            SELECT AVG(spread) as avg_spread FROM recent;
        """)
        avg_spread = self.cursor.fetchone()[0]
        spread_vol = ((spread - avg_spread) / avg_spread) * 100.0 if avg_spread else 0

        # HMM Regime
        self.cursor.execute(f"""
            WITH recent AS (
                SELECT bid FROM {table_name}
                ORDER BY time DESC LIMIT 200
            ),
            recent_100 AS (
                SELECT bid FROM {table_name}
                ORDER BY time DESC LIMIT 100
            ),
            older_100 AS (
                SELECT bid FROM {table_name}
                ORDER BY time DESC LIMIT 200 OFFSET 100
            )
            SELECT AVG(r.bid) as recent_avg, AVG(o.bid) as older_avg
            FROM recent_100 r, older_100 o;
        """)
        recent_avg, older_avg = self.cursor.fetchone()
        trend_pct = ((recent_avg - older_avg) / older_avg) * 100.0 if older_avg else 0
        regime = 'BULLISH' if trend_pct > HMM_TREND_THRESHOLD else 'BEARISH' if trend_pct < -HMM_TREND_THRESHOLD else 'NEUTRAL'

        # Transaction Cost
        tx_cost = spread / 2.0 + 0.10

        # Check all conditions
        signal = (
            mean_rev < MEAN_REV_THRESHOLD and
            spread_vol < SPREAD_VOL_THRESHOLD and
            regime == 'BULLISH' and
            tx_cost < MAX_TX_COST
        )

        return {
            'bid': bid,
            'ask': ask,
            'spread': spread,
            'mean_rev': mean_rev,
            'spread_vol': spread_vol,
            'regime': regime,
            'tx_cost': tx_cost,
            'signal': signal
        }

    def open_position(self, symbol, metrics):
        """Place BUY order via MT5 and track in database"""
        print(f"\n[SIGNAL] {symbol} - ENTER_LONG")
        print(f"         Mean Rev: {metrics['mean_rev']:.2f}%")
        print(f"         Regime: {metrics['regime']}")
        print(f"         TX Cost: ${metrics['tx_cost']:.2f}")

        # Calculate position size
        position_size = self.account_balance * RISK_PER_TRADE
        entry_price = metrics['ask']
        shares = position_size / entry_price

        stop_loss_price = entry_price * (1.0 - STOP_LOSS_PCT)
        take_profit_price = entry_price * (1.0 + TARGET_PROFIT_PCT)

        # Prepare MT5 order
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            print(f"    [ERROR] Symbol {symbol} not found")
            return False

        # Normalize lot size
        lot_size = shares
        min_lot = symbol_info.volume_min
        max_lot = symbol_info.volume_max
        lot_step = symbol_info.volume_step

        lot_size = max(min_lot, min(max_lot, round(lot_size / lot_step) * lot_step))

        # Place order
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot_size,
            "type": mt5.ORDER_TYPE_BUY,
            "price": entry_price,
            "sl": stop_loss_price,
            "tp": take_profit_price,
            "deviation": 10,
            "magic": 20260120,
            "comment": "Renaissance 5M",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        result = mt5.order_send(request)

        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"    [ERROR] Order failed: {result.retcode} - {result.comment}")
            return False

        # Store position in database
        self.cursor.execute("""
            INSERT INTO positions
            (symbol, entry_time, entry_price, shares, position_size, stop_loss, take_profit, mt5_ticket)
            VALUES (%s, NOW(), %s, %s, %s, %s, %s, %s)
            RETURNING id;
        """, (symbol, entry_price, lot_size, position_size, stop_loss_price, take_profit_price, result.order))

        pos_id = self.cursor.fetchone()[0]
        self.conn.commit()

        # Track locally
        self.open_positions[symbol] = {
            'id': pos_id,
            'entry_time': datetime.now(),
            'entry_price': entry_price,
            'shares': lot_size,
            'position_size': position_size,
            'stop_loss': stop_loss_price,
            'take_profit': take_profit_price,
            'mt5_ticket': result.order
        }

        print(f"    [OK] Position opened")
        print(f"         MT5 Ticket: {result.order}")
        print(f"         Entry: ${entry_price:.2f}")
        print(f"         Size: {lot_size} shares (${position_size:.2f})")
        print(f"         Stop Loss: ${stop_loss_price:.2f} ({STOP_LOSS_PCT*100}%)")
        print(f"         Take Profit: ${take_profit_price:.2f} ({TARGET_PROFIT_PCT*100}%)")

        return True

    def check_exit(self, symbol, position, current_price):
        """Check if position should be closed"""
        pnl = (current_price - position['entry_price']) * position['shares']
        pnl_pct = ((current_price - position['entry_price']) / position['entry_price']) * 100.0

        # Check TP
        if current_price >= position['take_profit']:
            return 'TP', pnl, pnl_pct

        # Check SL
        if current_price <= position['stop_loss']:
            return 'SL', pnl, pnl_pct

        return None, pnl, pnl_pct

    def close_position(self, symbol, reason, pnl, pnl_pct):
        """Close position via MT5 and update database"""
        position = self.open_positions[symbol]

        print(f"\n[EXIT] {symbol} - {reason}")
        print(f"       P&L: ${pnl:.2f} ({pnl_pct:+.2f}%)")

        # Close via MT5
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": position['shares'],
            "type": mt5.ORDER_TYPE_SELL,
            "position": position['mt5_ticket'],
            "magic": 20260120,
            "comment": f"Close {reason}",
        }

        result = mt5.order_send(request)

        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"    [ERROR] Close failed: {result.retcode}")
            return False

        # Update database
        self.cursor.execute("""
            UPDATE positions
            SET status = 'CLOSED',
                exit_time = NOW(),
                exit_price = %s,
                pnl = %s
            WHERE id = %s;
        """, (result.price, pnl, position['id']))

        self.conn.commit()

        # Update account balance
        self.account_balance += pnl

        # Remove from tracking
        del self.open_positions[symbol]

        print(f"    [OK] Position closed")
        print(f"         Exit Price: ${result.price:.2f}")
        print(f"         New Balance: ${self.account_balance:.2f}")

        return True

    def run(self):
        """Main trading loop"""
        print("\n" + "=" * 80)
        print("STARTING TRADING ENGINE")
        print("=" * 80)
        print(f"Symbols: {', '.join(TRADE_SYMBOLS)}")
        print(f"Max Positions: {MAX_POSITIONS}")
        print(f"Risk Per Trade: {RISK_PER_TRADE*100}%")
        print("Press Ctrl+C to stop\n")

        update_count = 0

        try:
            while True:
                update_count += 1

                # Check existing positions
                for symbol in list(self.open_positions.keys()):
                    metrics = self.get_current_metrics(symbol)
                    if metrics:
                        exit_reason, pnl, pnl_pct = self.check_exit(symbol, self.open_positions[symbol], metrics['bid'])

                        if exit_reason:
                            self.close_position(symbol, exit_reason, pnl, pnl_pct)

                # Look for new entry signals (if not at max positions)
                if len(self.open_positions) < MAX_POSITIONS:
                    for symbol in TRADE_SYMBOLS:
                        if symbol in self.open_positions:
                            continue  # Already have position

                        metrics = self.get_current_metrics(symbol)

                        if metrics and metrics['signal']:
                            self.open_position(symbol, metrics)

                # Status update every 60 seconds
                if update_count % 60 == 0:
                    print(f"[{update_count}] Balance: ${self.account_balance:.2f} | Open: {len(self.open_positions)} | {datetime.now().strftime('%H:%M:%S')}")

                time.sleep(1)

        except KeyboardInterrupt:
            print("\n[STOP] Shutting down...")

        finally:
            self.cursor.close()
            self.conn.close()
            mt5.shutdown()
            print("[OK] Trading engine stopped")

if __name__ == "__main__":
    engine = RenaissanceTradingEngine()
    engine.connect_database()

    if engine.connect_mt5():
        engine.load_open_positions()
        engine.run()
