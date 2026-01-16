-- ============================================
-- KLDA-HFT TRACKING QUERIES
-- How to track everything from price tick → trading decision
-- ============================================

-- ============================================
-- 1. TRACK INCOMING TICKS (Raw price data)
-- ============================================

-- See last 10 ticks for TSLA
SELECT
    time,
    symbol,
    bid,
    ask,
    spread,
    volume
FROM ticks
WHERE symbol = 'TSLA.US-24'
ORDER BY time DESC
LIMIT 10;

-- Count ticks per minute (monitor data feed health)
SELECT
    time_bucket('1 minute', time) as minute,
    symbol,
    COUNT(*) as tick_count
FROM ticks
WHERE time >= NOW() - INTERVAL '1 hour'
GROUP BY minute, symbol
ORDER BY minute DESC, symbol;

-- ============================================
-- 2. TRACK BAR FORMATION (OHLCV)
-- ============================================

-- See today's bars for TSLA on D1 timeframe
SELECT
    time,
    symbol,
    timeframe,
    open,
    high,
    low,
    close,
    volume
FROM bars
WHERE symbol = 'TSLA.US-24'
  AND timeframe = 'D1'
  AND time >= CURRENT_DATE
ORDER BY time DESC;

-- See latest bar for all assets on H1
SELECT
    symbol,
    time,
    open,
    high,
    low,
    close,
    volume
FROM bars
WHERE timeframe = 'H1'
  AND time = (SELECT MAX(time) FROM bars WHERE timeframe = 'H1')
ORDER BY symbol;

-- ============================================
-- 3. TRACK INDICATORS (MA, RSI, HMM)
-- ============================================

-- Current indicators for TSLA with mean reversion signal
SELECT
    b.time,
    b.symbol,
    b.close as current_price,
    i.ma20,
    i.ma50,
    i.rsi14,
    i.atr14,
    i.bb_lower,
    i.bb_upper,
    i.hmm_state,
    i.hmm_confidence,
    CASE
        WHEN b.close < i.bb_lower THEN '🔴 OVERSOLD - BUY SIGNAL'
        WHEN b.close > i.bb_upper THEN '🔵 OVERBOUGHT - SELL SIGNAL'
        WHEN b.close < i.ma20 THEN '⚠️ BELOW MA20'
        ELSE '✓ NORMAL'
    END as status
FROM bars b
JOIN indicators i ON b.symbol = i.symbol
    AND b.time = i.time
    AND b.timeframe = i.timeframe
WHERE b.symbol = 'TSLA.US-24'
  AND b.timeframe = 'D1'
ORDER BY b.time DESC
LIMIT 1;

-- Find all assets currently below MA20 (potential buy signals)
SELECT
    b.symbol,
    b.close as current_price,
    i.ma20,
    ((b.close - i.ma20) / i.ma20 * 100) as deviation_pct,
    i.rsi14,
    i.hmm_state
FROM bars b
JOIN indicators i ON b.symbol = i.symbol
    AND b.time = i.time
    AND b.timeframe = i.timeframe
WHERE b.timeframe = 'D1'
  AND b.time = (SELECT MAX(time) FROM bars WHERE timeframe = 'D1')
  AND b.close < i.ma20
ORDER BY deviation_pct ASC;

-- ============================================
-- 4. TRACK PATTERN DETECTIONS (Signals)
-- ============================================

-- All signals generated today
SELECT
    time,
    symbol,
    signal_type,
    direction,
    confidence,
    entry_price,
    stop_loss,
    take_profit,
    position_size,
    expected_value
FROM signals
WHERE time >= CURRENT_DATE
ORDER BY confidence DESC, time DESC;

-- Count signals by type today
SELECT
    signal_type,
    COUNT(*) as count,
    AVG(confidence) as avg_confidence,
    SUM(expected_value) as total_expected_value
FROM signals
WHERE time >= CURRENT_DATE
GROUP BY signal_type
ORDER BY count DESC;

-- Find high-confidence signals (>52% win rate)
SELECT
    time,
    symbol,
    signal_type,
    direction,
    confidence,
    entry_price,
    stop_loss,
    take_profit,
    expected_value
FROM signals
WHERE confidence > 0.52
  AND time >= CURRENT_DATE
ORDER BY confidence DESC, expected_value DESC;

-- ============================================
-- 5. TRACK EXECUTED TRADES
-- ============================================

-- All open positions right now
SELECT
    trade_id,
    symbol,
    direction,
    entry_price,
    entry_time,
    stop_loss,
    take_profit,
    position_size,
    (SELECT close FROM bars WHERE symbol = trades.symbol AND timeframe = 'M5' ORDER BY time DESC LIMIT 1) as current_price,
    ((SELECT close FROM bars WHERE symbol = trades.symbol AND timeframe = 'M5' ORDER BY time DESC LIMIT 1) - entry_price) * position_size as unrealized_pnl
FROM trades
WHERE status = 'OPEN'
ORDER BY entry_time DESC;

-- Trades closed today
SELECT
    trade_id,
    symbol,
    direction,
    entry_price,
    exit_price,
    pnl,
    pnl_pct,
    holding_period_seconds / 3600.0 as holding_hours,
    status
FROM trades
WHERE status IN ('CLOSED', 'STOPPED_OUT', 'TAKE_PROFIT')
  AND exit_time >= CURRENT_DATE
ORDER BY exit_time DESC;

-- Best trades today (highest P&L)
SELECT
    symbol,
    direction,
    entry_price,
    exit_price,
    pnl,
    pnl_pct,
    holding_period_seconds / 3600.0 as holding_hours
FROM trades
WHERE status = 'CLOSED'
  AND exit_time >= CURRENT_DATE
  AND pnl > 0
ORDER BY pnl DESC
LIMIT 10;

-- Worst trades today
SELECT
    symbol,
    direction,
    entry_price,
    exit_price,
    pnl,
    pnl_pct,
    holding_period_seconds / 3600.0 as holding_hours
FROM trades
WHERE status = 'CLOSED'
  AND exit_time >= CURRENT_DATE
  AND pnl < 0
ORDER BY pnl ASC
LIMIT 10;

-- ============================================
-- 6. TRACK REAL-TIME PORTFOLIO
-- ============================================

-- Entire portfolio state
SELECT
    symbol,
    position,
    avg_entry_price,
    current_price,
    unrealized_pnl,
    realized_pnl_today,
    (unrealized_pnl / (avg_entry_price * ABS(position))) * 100 as unrealized_pnl_pct,
    updated_at
FROM portfolio
WHERE position != 0
ORDER BY unrealized_pnl DESC;

-- Portfolio summary
SELECT * FROM get_portfolio_summary();

-- ============================================
-- 7. TRACK WIN RATE (Renaissance: 50.75%)
-- ============================================

-- Today's win rate
SELECT * FROM get_win_rate(CURRENT_DATE);

-- This week's win rate
SELECT * FROM get_win_rate(CURRENT_DATE - INTERVAL '7 days');

-- This month's win rate
SELECT * FROM get_win_rate(CURRENT_DATE - INTERVAL '30 days');

-- Win rate by symbol (find which assets work best)
SELECT
    symbol,
    COUNT(*) as total_trades,
    SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins,
    ROUND(AVG(CASE WHEN pnl > 0 THEN 1.0 ELSE 0.0 END), 4) as win_rate,
    SUM(pnl) as total_pnl
FROM trades
WHERE status = 'CLOSED'
  AND exit_time >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY symbol
HAVING COUNT(*) >= 10  -- Only show assets with 10+ trades
ORDER BY win_rate DESC;

-- Win rate by signal type (find which patterns work best)
SELECT
    s.signal_type,
    COUNT(*) as total_trades,
    SUM(CASE WHEN t.pnl > 0 THEN 1 ELSE 0 END) as wins,
    ROUND(AVG(CASE WHEN t.pnl > 0 THEN 1.0 ELSE 0.0 END), 4) as win_rate,
    AVG(s.confidence) as avg_predicted_confidence,
    SUM(t.pnl) as total_pnl
FROM trades t
JOIN signals s ON t.signal_id = s.signal_id
WHERE t.status = 'CLOSED'
  AND t.exit_time >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY s.signal_type
ORDER BY win_rate DESC;

-- ============================================
-- 8. TRACK PERFORMANCE METRICS
-- ============================================

-- Today's performance summary
SELECT
    period,
    total_trades,
    winning_trades,
    losing_trades,
    win_rate,
    gross_pnl,
    net_pnl,
    total_commission,
    total_slippage,
    sharpe_ratio,
    max_drawdown
FROM performance
WHERE period = 'DAILY'
  AND time >= CURRENT_DATE;

-- Hourly performance today
SELECT
    time,
    total_trades,
    win_rate,
    net_pnl,
    total_commission
FROM performance_hourly
WHERE time >= CURRENT_DATE
ORDER BY time DESC;

-- Weekly performance trend
SELECT
    date_trunc('week', time) as week,
    SUM(total_trades) as total_trades,
    AVG(win_rate) as avg_win_rate,
    SUM(net_pnl) as total_pnl,
    AVG(sharpe_ratio) as avg_sharpe
FROM performance
WHERE period = 'DAILY'
  AND time >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY week
ORDER BY week DESC;

-- ============================================
-- 9. TRACK "THE DEVIL" (Transaction Costs)
-- ============================================
-- Renaissance: "I'm not sure we're the best at all aspects of trading,
-- but we're the best at estimating the cost of a trade"

-- Total transaction costs today
SELECT
    SUM(commission) as total_commission,
    SUM(slippage) as total_slippage,
    SUM(commission + slippage) as total_cost,
    SUM(pnl) as gross_pnl,
    SUM(pnl) - SUM(commission + slippage) as net_pnl,
    (SUM(commission + slippage) / SUM(pnl)) * 100 as cost_pct_of_profit
FROM trades
WHERE exit_time >= CURRENT_DATE
  AND status = 'CLOSED'
  AND pnl > 0;

-- Average transaction cost per trade by symbol
SELECT
    symbol,
    COUNT(*) as trades,
    AVG(commission) as avg_commission,
    AVG(slippage) as avg_slippage,
    AVG(commission + slippage) as avg_total_cost
FROM trades
WHERE status = 'CLOSED'
  AND exit_time >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY symbol
ORDER BY avg_total_cost DESC;

-- ============================================
-- 10. MONITOR DATA PIPELINE HEALTH
-- ============================================

-- Check if data is flowing (last update time per table)
SELECT
    'ticks' as table_name,
    MAX(time) as last_update,
    COUNT(*) as total_rows,
    NOW() - MAX(time) as time_since_last_update
FROM ticks
UNION ALL
SELECT
    'bars',
    MAX(time),
    COUNT(*),
    NOW() - MAX(time)
FROM bars
UNION ALL
SELECT
    'signals',
    MAX(time),
    COUNT(*),
    NOW() - MAX(time)
FROM signals
UNION ALL
SELECT
    'trades',
    MAX(time),
    COUNT(*),
    NOW() - MAX(time)
FROM trades;

-- Database size by table
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- ============================================
-- QUICK DASHBOARD QUERY
-- ============================================

-- Single query to see everything at once
WITH current_stats AS (
    SELECT
        COUNT(*) as open_positions,
        SUM(unrealized_pnl) as total_unrealized_pnl
    FROM portfolio
    WHERE position != 0
),
today_performance AS (
    SELECT
        total_trades,
        win_rate,
        net_pnl,
        total_commission
    FROM performance
    WHERE period = 'DAILY'
      AND time >= CURRENT_DATE
),
recent_signals AS (
    SELECT COUNT(*) as signals_last_hour
    FROM signals
    WHERE time >= NOW() - INTERVAL '1 hour'
)
SELECT
    cs.open_positions,
    cs.total_unrealized_pnl,
    tp.total_trades as trades_today,
    tp.win_rate as win_rate_today,
    tp.net_pnl as pnl_today,
    tp.total_commission as commission_today,
    rs.signals_last_hour
FROM current_stats cs
CROSS JOIN today_performance tp
CROSS JOIN recent_signals rs;
