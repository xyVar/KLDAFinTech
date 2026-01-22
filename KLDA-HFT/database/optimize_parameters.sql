-- TSLA PARAMETER OPTIMIZATION
-- Find optimal tick windows for each Renaissance metric

-- ============================================
-- 1. MEAN REVERSION - Test Different Windows
-- ============================================
SELECT 'MEAN_REVERSION_OPTIMIZATION' as metric;

WITH window_tests AS (
    -- Test 10-tick window
    SELECT
        10 as window_size,
        time,
        bid,
        AVG(bid) OVER (ORDER BY time ROWS BETWEEN 10 PRECEDING AND CURRENT ROW) as ma,
        ((bid - AVG(bid) OVER (ORDER BY time ROWS BETWEEN 10 PRECEDING AND CURRENT ROW))
         / AVG(bid) OVER (ORDER BY time ROWS BETWEEN 10 PRECEDING AND CURRENT ROW)) * 100 as deviation_pct,
        LEAD(bid, 50) OVER (ORDER BY time) as price_50_ticks_later
    FROM tsla_history
    WHERE time > NOW() - INTERVAL '7 days'  -- Last 7 days only

    UNION ALL

    -- Test 20-tick window
    SELECT
        20 as window_size,
        time,
        bid,
        AVG(bid) OVER (ORDER BY time ROWS BETWEEN 20 PRECEDING AND CURRENT ROW) as ma,
        ((bid - AVG(bid) OVER (ORDER BY time ROWS BETWEEN 20 PRECEDING AND CURRENT ROW))
         / AVG(bid) OVER (ORDER BY time ROWS BETWEEN 20 PRECEDING AND CURRENT ROW)) * 100 as deviation_pct,
        LEAD(bid, 50) OVER (ORDER BY time) as price_50_ticks_later
    FROM tsla_history
    WHERE time > NOW() - INTERVAL '7 days'

    UNION ALL

    -- Test 50-tick window
    SELECT
        50 as window_size,
        time,
        bid,
        AVG(bid) OVER (ORDER BY time ROWS BETWEEN 50 PRECEDING AND CURRENT ROW) as ma,
        ((bid - AVG(bid) OVER (ORDER BY time ROWS BETWEEN 50 PRECEDING AND CURRENT ROW))
         / AVG(bid) OVER (ORDER BY time ROWS BETWEEN 50 PRECEDING AND CURRENT ROW)) * 100 as deviation_pct,
        LEAD(bid, 50) OVER (ORDER BY time) as price_50_ticks_later
    FROM tsla_history
    WHERE time > NOW() - INTERVAL '7 days'

    UNION ALL

    -- Test 100-tick window
    SELECT
        100 as window_size,
        time,
        bid,
        AVG(bid) OVER (ORDER BY time ROWS BETWEEN 100 PRECEDING AND CURRENT ROW) as ma,
        ((bid - AVG(bid) OVER (ORDER BY time ROWS BETWEEN 100 PRECEDING AND CURRENT ROW))
         / AVG(bid) OVER (ORDER BY time ROWS BETWEEN 100 PRECEDING AND CURRENT ROW)) * 100 as deviation_pct,
        LEAD(bid, 50) OVER (ORDER BY time) as price_50_ticks_later
    FROM tsla_history
    WHERE time > NOW() - INTERVAL '7 days'
),
signal_performance AS (
    SELECT
        window_size,
        COUNT(*) as total_signals,
        SUM(CASE WHEN deviation_pct < -1.0 AND price_50_ticks_later > bid * 1.015 THEN 1 ELSE 0 END) as winning_trades,
        SUM(CASE WHEN deviation_pct < -1.0 AND price_50_ticks_later <= bid * 1.015 THEN 1 ELSE 0 END) as losing_trades,
        AVG(CASE WHEN deviation_pct < -1.0 AND price_50_ticks_later > bid * 1.015
            THEN ((price_50_ticks_later - bid) / bid) * 100
            ELSE NULL END) as avg_win_pct,
        AVG(CASE WHEN deviation_pct < -1.0 AND price_50_ticks_later <= bid * 1.015
            THEN ((price_50_ticks_later - bid) / bid) * 100
            ELSE NULL END) as avg_loss_pct
    FROM window_tests
    WHERE deviation_pct < -1.0  -- Only count when signal triggers
      AND price_50_ticks_later IS NOT NULL
    GROUP BY window_size
)
SELECT
    window_size,
    total_signals,
    winning_trades,
    losing_trades,
    ROUND((winning_trades::numeric / NULLIF(total_signals, 0)) * 100, 2) as win_rate_pct,
    ROUND(avg_win_pct, 2) as avg_win_pct,
    ROUND(avg_loss_pct, 2) as avg_loss_pct,
    ROUND((winning_trades::numeric / NULLIF(total_signals, 0)) * avg_win_pct +
          (losing_trades::numeric / NULLIF(total_signals, 0)) * avg_loss_pct, 2) as expected_value_pct
FROM signal_performance
ORDER BY win_rate_pct DESC;


-- ============================================
-- 2. ORDER FLOW - Test Different Windows
-- ============================================
SELECT '';
SELECT 'ORDER_FLOW_OPTIMIZATION' as metric;

WITH window_tests AS (
    -- Test 50-tick window
    SELECT
        50 as window_size,
        time,
        bid,
        SUM(buy_volume) OVER (ORDER BY time ROWS BETWEEN 50 PRECEDING AND CURRENT ROW) as total_buy,
        SUM(sell_volume) OVER (ORDER BY time ROWS BETWEEN 50 PRECEDING AND CURRENT ROW) as total_sell,
        SUM(buy_volume) OVER (ORDER BY time ROWS BETWEEN 50 PRECEDING AND CURRENT ROW) -
        SUM(sell_volume) OVER (ORDER BY time ROWS BETWEEN 50 PRECEDING AND CURRENT ROW) as net_flow,
        LEAD(bid, 50) OVER (ORDER BY time) as price_50_ticks_later
    FROM tsla_history
    WHERE time > NOW() - INTERVAL '7 days'

    UNION ALL

    -- Test 100-tick window
    SELECT
        100 as window_size,
        time,
        bid,
        SUM(buy_volume) OVER (ORDER BY time ROWS BETWEEN 100 PRECEDING AND CURRENT ROW) as total_buy,
        SUM(sell_volume) OVER (ORDER BY time ROWS BETWEEN 100 PRECEDING AND CURRENT ROW) as total_sell,
        SUM(buy_volume) OVER (ORDER BY time ROWS BETWEEN 100 PRECEDING AND CURRENT ROW) -
        SUM(sell_volume) OVER (ORDER BY time ROWS BETWEEN 100 PRECEDING AND CURRENT ROW) as net_flow,
        LEAD(bid, 50) OVER (ORDER BY time) as price_50_ticks_later
    FROM tsla_history
    WHERE time > NOW() - INTERVAL '7 days'

    UNION ALL

    -- Test 200-tick window
    SELECT
        200 as window_size,
        time,
        bid,
        SUM(buy_volume) OVER (ORDER BY time ROWS BETWEEN 200 PRECEDING AND CURRENT ROW) as total_buy,
        SUM(sell_volume) OVER (ORDER BY time ROWS BETWEEN 200 PRECEDING AND CURRENT ROW) as total_sell,
        SUM(buy_volume) OVER (ORDER BY time ROWS BETWEEN 200 PRECEDING AND CURRENT ROW) -
        SUM(sell_volume) OVER (ORDER BY time ROWS BETWEEN 200 PRECEDING AND CURRENT ROW) as net_flow,
        LEAD(bid, 50) OVER (ORDER BY time) as price_50_ticks_later
    FROM tsla_history
    WHERE time > NOW() - INTERVAL '7 days'

    UNION ALL

    -- Test 500-tick window
    SELECT
        500 as window_size,
        time,
        bid,
        SUM(buy_volume) OVER (ORDER BY time ROWS BETWEEN 500 PRECEDING AND CURRENT ROW) as total_buy,
        SUM(sell_volume) OVER (ORDER BY time ROWS BETWEEN 500 PRECEDING AND CURRENT ROW) as total_sell,
        SUM(buy_volume) OVER (ORDER BY time ROWS BETWEEN 500 PRECEDING AND CURRENT ROW) -
        SUM(sell_volume) OVER (ORDER BY time ROWS BETWEEN 500 PRECEDING AND CURRENT ROW) as net_flow,
        LEAD(bid, 50) OVER (ORDER BY time) as price_50_ticks_later
    FROM tsla_history
    WHERE time > NOW() - INTERVAL '7 days'
),
signal_performance AS (
    SELECT
        window_size,
        COUNT(*) as total_signals,
        SUM(CASE WHEN net_flow > 1000 AND price_50_ticks_later > bid * 1.015 THEN 1 ELSE 0 END) as winning_trades,
        SUM(CASE WHEN net_flow > 1000 AND price_50_ticks_later <= bid * 1.015 THEN 1 ELSE 0 END) as losing_trades
    FROM window_tests
    WHERE net_flow > 1000  -- Signal threshold
      AND price_50_ticks_later IS NOT NULL
    GROUP BY window_size
)
SELECT
    window_size,
    total_signals,
    winning_trades,
    losing_trades,
    ROUND((winning_trades::numeric / NULLIF(total_signals, 0)) * 100, 2) as win_rate_pct
FROM signal_performance
ORDER BY win_rate_pct DESC;


-- ============================================
-- 3. HMM REGIME - Test Different Windows
-- ============================================
SELECT '';
SELECT 'HMM_REGIME_OPTIMIZATION' as metric;

WITH window_tests AS (
    -- Test 20-tick window
    SELECT
        20 as window_size,
        time,
        bid,
        AVG(bid) OVER (ORDER BY time ROWS BETWEEN 10 PRECEDING AND CURRENT ROW) as recent_avg,
        AVG(bid) OVER (ORDER BY time ROWS BETWEEN 20 PRECEDING AND 11 PRECEDING) as older_avg,
        LEAD(bid, 50) OVER (ORDER BY time) as price_50_ticks_later
    FROM tsla_history
    WHERE time > NOW() - INTERVAL '7 days'

    UNION ALL

    -- Test 50-tick window
    SELECT
        50 as window_size,
        time,
        bid,
        AVG(bid) OVER (ORDER BY time ROWS BETWEEN 25 PRECEDING AND CURRENT ROW) as recent_avg,
        AVG(bid) OVER (ORDER BY time ROWS BETWEEN 50 PRECEDING AND 26 PRECEDING) as older_avg,
        LEAD(bid, 50) OVER (ORDER BY time) as price_50_ticks_later
    FROM tsla_history
    WHERE time > NOW() - INTERVAL '7 days'

    UNION ALL

    -- Test 100-tick window
    SELECT
        100 as window_size,
        time,
        bid,
        AVG(bid) OVER (ORDER BY time ROWS BETWEEN 50 PRECEDING AND CURRENT ROW) as recent_avg,
        AVG(bid) OVER (ORDER BY time ROWS BETWEEN 100 PRECEDING AND 51 PRECEDING) as older_avg,
        LEAD(bid, 50) OVER (ORDER BY time) as price_50_ticks_later
    FROM tsla_history
    WHERE time > NOW() - INTERVAL '7 days'
),
regime_signals AS (
    SELECT
        window_size,
        time,
        bid,
        recent_avg,
        older_avg,
        ((recent_avg - older_avg) / older_avg) * 100 as trend_pct,
        CASE
            WHEN ((recent_avg - older_avg) / older_avg) * 100 > 0.3 THEN 'BULLISH'
            WHEN ((recent_avg - older_avg) / older_avg) * 100 < -0.3 THEN 'BEARISH'
            ELSE 'NEUTRAL'
        END as regime,
        price_50_ticks_later
    FROM window_tests
    WHERE recent_avg IS NOT NULL
      AND older_avg IS NOT NULL
),
signal_performance AS (
    SELECT
        window_size,
        COUNT(*) as total_signals,
        SUM(CASE WHEN regime = 'BULLISH' AND price_50_ticks_later > bid * 1.015 THEN 1 ELSE 0 END) as winning_trades,
        SUM(CASE WHEN regime = 'BULLISH' AND price_50_ticks_later <= bid * 1.015 THEN 1 ELSE 0 END) as losing_trades
    FROM regime_signals
    WHERE regime = 'BULLISH'
      AND price_50_ticks_later IS NOT NULL
    GROUP BY window_size
)
SELECT
    window_size,
    total_signals,
    winning_trades,
    losing_trades,
    ROUND((winning_trades::numeric / NULLIF(total_signals, 0)) * 100, 2) as win_rate_pct
FROM signal_performance
ORDER BY win_rate_pct DESC;


-- ============================================
-- 4. SPREAD VOLATILITY - Test Different Windows
-- ============================================
SELECT '';
SELECT 'SPREAD_VOLATILITY_OPTIMIZATION' as metric;

WITH window_tests AS (
    -- Test 50-tick window
    SELECT
        50 as window_size,
        time,
        bid,
        spread,
        AVG(spread) OVER (ORDER BY time ROWS BETWEEN 50 PRECEDING AND CURRENT ROW) as avg_spread,
        LEAD(bid, 50) OVER (ORDER BY time) as price_50_ticks_later
    FROM tsla_history
    WHERE time > NOW() - INTERVAL '7 days'

    UNION ALL

    -- Test 100-tick window
    SELECT
        100 as window_size,
        time,
        bid,
        spread,
        AVG(spread) OVER (ORDER BY time ROWS BETWEEN 100 PRECEDING AND CURRENT ROW) as avg_spread,
        LEAD(bid, 50) OVER (ORDER BY time) as price_50_ticks_later
    FROM tsla_history
    WHERE time > NOW() - INTERVAL '7 days'

    UNION ALL

    -- Test 200-tick window
    SELECT
        200 as window_size,
        time,
        bid,
        spread,
        AVG(spread) OVER (ORDER BY time ROWS BETWEEN 200 PRECEDING AND CURRENT ROW) as avg_spread,
        LEAD(bid, 50) OVER (ORDER BY time) as price_50_ticks_later
    FROM tsla_history
    WHERE time > NOW() - INTERVAL '7 days'
),
signal_performance AS (
    SELECT
        window_size,
        COUNT(*) as total_signals,
        SUM(CASE WHEN ((spread - avg_spread) / avg_spread) * 100 > 15
                 AND price_50_ticks_later > bid * 1.015 THEN 1 ELSE 0 END) as winning_trades,
        SUM(CASE WHEN ((spread - avg_spread) / avg_spread) * 100 > 15
                 AND price_50_ticks_later <= bid * 1.015 THEN 1 ELSE 0 END) as losing_trades
    FROM window_tests
    WHERE ((spread - avg_spread) / avg_spread) * 100 > 15  -- Signal threshold
      AND price_50_ticks_later IS NOT NULL
    GROUP BY window_size
)
SELECT
    window_size,
    total_signals,
    winning_trades,
    losing_trades,
    ROUND((winning_trades::numeric / NULLIF(total_signals, 0)) * 100, 2) as win_rate_pct
FROM signal_performance
ORDER BY win_rate_pct DESC;
