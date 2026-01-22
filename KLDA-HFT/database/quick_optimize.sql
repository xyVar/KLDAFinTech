-- QUICK TSLA OPTIMIZATION - Last 24 hours only

-- Test Mean Reversion with 3 different windows
WITH recent_data AS (
    SELECT *
    FROM tsla_history
    WHERE time > NOW() - INTERVAL '24 hours'
    ORDER BY time
    LIMIT 10000  -- Limit to last 10k ticks for speed
),
window_20 AS (
    SELECT
        20 as window_size,
        bid,
        AVG(bid) OVER (ORDER BY time ROWS BETWEEN 20 PRECEDING AND CURRENT ROW) as ma,
        LEAD(bid, 30) OVER (ORDER BY time) as price_after
    FROM recent_data
),
window_50 AS (
    SELECT
        50 as window_size,
        bid,
        AVG(bid) OVER (ORDER BY time ROWS BETWEEN 50 PRECEDING AND CURRENT ROW) as ma,
        LEAD(bid, 30) OVER (ORDER BY time) as price_after
    FROM recent_data
),
window_100 AS (
    SELECT
        100 as window_size,
        bid,
        AVG(bid) OVER (ORDER BY time ROWS BETWEEN 100 PRECEDING AND CURRENT ROW) as ma,
        LEAD(bid, 30) OVER (ORDER BY time) as price_after
    FROM recent_data
),
all_windows AS (
    SELECT * FROM window_20
    UNION ALL
    SELECT * FROM window_50
    UNION ALL
    SELECT * FROM window_100
),
signals AS (
    SELECT
        window_size,
        ((bid - ma) / ma) * 100 as deviation_pct,
        CASE WHEN price_after > bid * 1.01 THEN 1 ELSE 0 END as is_win
    FROM all_windows
    WHERE ma IS NOT NULL
      AND price_after IS NOT NULL
      AND ((bid - ma) / ma) * 100 < -1.0  -- Signal condition
)
SELECT
    window_size,
    COUNT(*) as total_signals,
    SUM(is_win) as wins,
    ROUND((SUM(is_win)::numeric / COUNT(*)) * 100, 1) as win_rate_pct
FROM signals
GROUP BY window_size
ORDER BY win_rate_pct DESC;
