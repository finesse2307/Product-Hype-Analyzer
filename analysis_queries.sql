-- ============================================================================
-- SQL Analysis Queries for Viral Product Database
-- ============================================================================
-- 10 different analyses showing various SQL techniques
-- ============================================================================

-- ============================================================================
-- ANALYSIS Find Viral Peak Dates
-- Uses: ROW_NUMBER, Window Functions, CTEs
-- ============================================================================

WITH ranked_trends AS (
    SELECT 
        p.product_name,
        st.trend_date,
        st.search_interest,
        ROW_NUMBER() OVER (PARTITION BY p.product_id ORDER BY st.search_interest DESC) as intensity_rank,
        RANK() OVER (PARTITION BY p.product_id ORDER BY st.search_interest DESC) as intensity_rank_with_ties
    FROM social_trends st
    JOIN products p ON st.product_id = p.product_id
    WHERE st.region = 'US'
)
SELECT 
    product_name,
    trend_date as peak_date,
    search_interest as peak_intensity,
    intensity_rank
FROM ranked_trends
WHERE intensity_rank = 1
ORDER BY search_interest DESC;

-- Query finds peak dates for each product


-- ============================================================================
-- ANALYSIS Week-over-Week Growth (Momentum)
-- Uses: LAG, Date math, Percentage calculations
-- ============================================================================

WITH weekly_trends AS (
    SELECT 
        p.product_name,
        st.trend_date,
        st.search_interest,
        LAG(st.search_interest, 7) OVER (
            PARTITION BY p.product_id 
            ORDER BY st.trend_date
        ) as prev_week_interest,
        LAG(st.trend_date, 7) OVER (
            PARTITION BY p.product_id 
            ORDER BY st.trend_date
        ) as prev_week_date
    FROM social_trends st
    JOIN products p ON st.product_id = p.product_id
    WHERE st.region = 'US'
)
SELECT 
    product_name,
    trend_date,
    search_interest,
    prev_week_interest,
    CASE 
        WHEN prev_week_interest > 0 THEN
            ROUND(((search_interest - prev_week_interest) * 100.0 / prev_week_interest), 2)
        ELSE NULL
    END as week_over_week_growth_pct,
    -- Flag explosive growth (>50% week over week)
    CASE
        WHEN prev_week_interest > 0 AND 
             ((search_interest - prev_week_interest) * 100.0 / prev_week_interest) > 50
        THEN 'EXPLOSIVE'
        WHEN prev_week_interest > 0 AND 
             ((search_interest - prev_week_interest) * 100.0 / prev_week_interest) > 20
        THEN 'HIGH'
        WHEN prev_week_interest > 0 AND 
             ((search_interest - prev_week_interest) * 100.0 / prev_week_interest) < -20
        THEN 'DECLINING'
        ELSE 'STABLE'
    END as growth_category
FROM weekly_trends
WHERE prev_week_interest IS NOT NULL
ORDER BY trend_date DESC, search_interest DESC
LIMIT 20;


-- ============================================================================
-- ANALYSIS CORRELATION BETWEEN TIKTOK ENGAGEMENT AND STOCK PRICE
-- Techniques: CTEs, Joins, Statistical calculations, Date matching
-- ============================================================================

WITH tiktok_weekly AS (
    SELECT 
        product_id,
        DATE(metric_date, 'weekday 0', '-6 days') as week_start,
        AVG(avg_engagement_rate) as avg_weekly_engagement,
        SUM(daily_new_posts) as weekly_posts,
        AVG(sentiment_score) as avg_sentiment
    FROM tiktok_metrics
    GROUP BY product_id, week_start
),
stock_weekly AS (
    SELECT 
        product_id,
        DATE(price_date, 'weekday 0', '-6 days') as week_start,
        AVG(close_price) as avg_weekly_price,
        (MAX(close_price) - MIN(close_price)) / MIN(close_price) * 100 as weekly_volatility_pct,
        AVG(volume) as avg_weekly_volume
    FROM stock_prices
    GROUP BY product_id, week_start
)
SELECT 
    p.product_name,
    tw.week_start,
    tw.avg_weekly_engagement,
    tw.weekly_posts,
    tw.avg_sentiment,
    sw.avg_weekly_price,
    sw.weekly_volatility_pct,
    -- Calculate week-over-week changes
    LAG(sw.avg_weekly_price, 1) OVER (PARTITION BY p.product_id ORDER BY tw.week_start) as prev_week_price,
    ROUND((sw.avg_weekly_price - LAG(sw.avg_weekly_price, 1) OVER (
        PARTITION BY p.product_id ORDER BY tw.week_start)) / 
        LAG(sw.avg_weekly_price, 1) OVER (PARTITION BY p.product_id ORDER BY tw.week_start) * 100, 2
    ) as weekly_price_change_pct
FROM tiktok_weekly tw
JOIN stock_weekly sw ON tw.product_id = sw.product_id AND tw.week_start = sw.week_start
JOIN products p ON tw.product_id = p.product_id
WHERE p.is_public_company = 1
ORDER BY tw.week_start DESC, p.product_name
LIMIT 30;


-- ============================================================================
-- ANALYSIS HYPE CYCLE PHASE CLASSIFICATION
-- Techniques: Complex CASE logic, Window functions, Percentile calculations
-- ============================================================================

WITH product_stats AS (
    SELECT 
        product_id,
        MAX(search_interest) as max_interest,
        AVG(search_interest) as avg_interest,
        trend_date as date_of_max
    FROM social_trends
    WHERE region = 'US'
    GROUP BY product_id, search_interest
    HAVING search_interest = MAX(search_interest)
),
current_metrics AS (
    SELECT 
        st.product_id,
        st.trend_date,
        st.search_interest,
        ps.max_interest,
        ps.avg_interest,
        ps.date_of_max,
        -- Calculate days since peak
        JULIANDAY(st.trend_date) - JULIANDAY(ps.date_of_max) as days_from_peak,
        -- Calculate % of peak
        ROUND((st.search_interest * 100.0 / ps.max_interest), 2) as pct_of_peak,
        -- 30-day moving average
        AVG(search_interest) OVER (
            PARTITION BY st.product_id 
            ORDER BY st.trend_date 
            ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) as ma_30,
        -- Momentum (comparing current to 30 days ago)
        st.search_interest - LAG(st.search_interest, 30) OVER (
            PARTITION BY st.product_id 
            ORDER BY st.trend_date
        ) as momentum_30d
    FROM social_trends st
    JOIN product_stats ps ON st.product_id = ps.product_id
    WHERE st.region = 'US'
)
SELECT 
    p.product_name,
    cm.trend_date,
    cm.search_interest,
    cm.pct_of_peak,
    ROUND(cm.ma_30, 2) as ma_30,
    cm.momentum_30d,
    cm.days_from_peak,
    -- Phase classification
    CASE
        WHEN cm.days_from_peak < -90 AND cm.pct_of_peak < 30 THEN 'EMERGING'
        WHEN cm.days_from_peak < 0 AND cm.pct_of_peak >= 30 AND cm.momentum_30d > 0 THEN 'GROWTH'
        WHEN cm.days_from_peak BETWEEN -7 AND 7 AND cm.pct_of_peak >= 90 THEN 'PEAK'
        WHEN cm.days_from_peak > 7 AND cm.days_from_peak < 90 AND cm.pct_of_peak > 50 THEN 'DECLINE'
        WHEN cm.pct_of_peak <= 50 OR cm.days_from_peak >= 90 THEN 'MATURITY'
        ELSE 'TRANSITIONAL'
    END as hype_phase
FROM current_metrics cm
JOIN products p ON cm.product_id = p.product_id
WHERE cm.trend_date >= DATE('2023-01-01')  -- Focus on recent data
ORDER BY cm.trend_date DESC, p.product_name
LIMIT 50;


-- ============================================================================
-- ANALYSIS RETAIL EVENT IMPACT ANALYSIS
-- Techniques: Window functions, Event-based analysis, Before/After comparison
-- ============================================================================

WITH event_windows AS (
    SELECT 
        re.event_id,
        re.product_id,
        re.event_date,
        re.event_type,
        re.retailer,
        re.resale_premium_pct,
        st.trend_date,
        st.search_interest,
        JULIANDAY(st.trend_date) - JULIANDAY(re.event_date) as days_from_event
    FROM retail_events re
    JOIN social_trends st ON re.product_id = st.product_id
    WHERE st.region = 'US'
        AND JULIANDAY(st.trend_date) BETWEEN JULIANDAY(re.event_date) - 7 AND JULIANDAY(re.event_date) + 14
)
SELECT 
    p.product_name,
    ew.event_date,
    ew.event_type,
    ew.retailer,
    ew.resale_premium_pct,
    -- Pre-event average
    ROUND(AVG(CASE WHEN ew.days_from_event < 0 THEN ew.search_interest END), 2) as avg_interest_pre_event,
    -- Post-event average
    ROUND(AVG(CASE WHEN ew.days_from_event > 0 THEN ew.search_interest END), 2) as avg_interest_post_event,
    -- Calculate lift
    ROUND(
        (AVG(CASE WHEN ew.days_from_event > 0 THEN ew.search_interest END) - 
         AVG(CASE WHEN ew.days_from_event < 0 THEN ew.search_interest END)) * 100.0 /
        AVG(CASE WHEN ew.days_from_event < 0 THEN ew.search_interest END), 
        2
    ) as event_lift_pct
FROM event_windows ew
JOIN products p ON ew.product_id = p.product_id
GROUP BY ew.event_id, p.product_name, ew.event_date, ew.event_type, ew.retailer, ew.resale_premium_pct
HAVING avg_interest_pre_event IS NOT NULL AND avg_interest_post_event IS NOT NULL
ORDER BY event_lift_pct DESC;


-- ============================================================================
-- ANALYSIS COMPETITOR COMPARISON - WHO WON THE HYPE WARS?
-- Techniques: Aggregation, Market share calculations, Pivot-like logic
-- ============================================================================

WITH monthly_metrics AS (
    SELECT 
        p.product_name,
        strftime('%Y-%m', st.trend_date) as year_month,
        AVG(st.search_interest) as avg_monthly_interest,
        MAX(st.search_interest) as max_monthly_interest,
        COUNT(*) as days_tracked
    FROM social_trends st
    JOIN products p ON st.product_id = p.product_id
    WHERE st.region = 'US'
        AND st.trend_date >= '2023-01-01'
    GROUP BY p.product_name, year_month
),
total_market AS (
    SELECT 
        year_month,
        SUM(avg_monthly_interest) as total_market_interest
    FROM monthly_metrics
    GROUP BY year_month
)
SELECT 
    mm.year_month,
    mm.product_name,
    mm.avg_monthly_interest,
    mm.max_monthly_interest,
    tm.total_market_interest,
    ROUND((mm.avg_monthly_interest * 100.0 / tm.total_market_interest), 2) as market_share_pct,
    -- Rank products by market share each month
    RANK() OVER (PARTITION BY mm.year_month ORDER BY mm.avg_monthly_interest DESC) as monthly_rank
FROM monthly_metrics mm
JOIN total_market tm ON mm.year_month = tm.year_month
ORDER BY mm.year_month DESC, mm.avg_monthly_interest DESC;


-- ============================================================================
-- ANALYSIS INVESTMENT SIMULATION - OPTIMAL ENTRY/EXIT POINTS
-- Techniques: Subqueries, Min/Max calculations, ROI analysis
-- ============================================================================

WITH stock_signals AS (
    SELECT 
        p.product_name,
        sp.price_date,
        sp.close_price,
        st.search_interest,
        -- Identify local minimums (potential buy points)
        CASE 
            WHEN sp.close_price < LAG(sp.close_price, 1) OVER w 
                 AND sp.close_price < LEAD(sp.close_price, 1) OVER w
            THEN 1 ELSE 0 
        END as is_local_min,
        -- Identify local maximums (potential sell points)
        CASE 
            WHEN sp.close_price > LAG(sp.close_price, 1) OVER w 
                 AND sp.close_price > LEAD(sp.close_price, 1) OVER w
            THEN 1 ELSE 0 
        END as is_local_max
    FROM stock_prices sp
    JOIN products p ON sp.product_id = p.product_id
    LEFT JOIN social_trends st ON sp.product_id = st.product_id 
        AND sp.price_date = st.trend_date 
        AND st.region = 'US'
    WHERE p.is_public_company = 1
    WINDOW w AS (PARTITION BY p.product_id ORDER BY sp.price_date)
)
SELECT 
    product_name,
    -- Buy point (search interest rising, local price minimum)
    MIN(CASE WHEN is_local_min = 1 AND search_interest > 30 THEN price_date END) as suggested_buy_date,
    MIN(CASE WHEN is_local_min = 1 AND search_interest > 30 THEN close_price END) as buy_price,
    -- Sell point (search interest peaked, local price maximum)
    MAX(CASE WHEN is_local_max = 1 AND search_interest > 70 THEN price_date END) as suggested_sell_date,
    MAX(CASE WHEN is_local_max = 1 AND search_interest > 70 THEN close_price END) as sell_price,
    -- Calculate hypothetical return
    ROUND(
        (MAX(CASE WHEN is_local_max = 1 AND search_interest > 70 THEN close_price END) -
         MIN(CASE WHEN is_local_min = 1 AND search_interest > 30 THEN close_price END)) * 100.0 /
        MIN(CASE WHEN is_local_min = 1 AND search_interest > 30 THEN close_price END),
        2
    ) as hypothetical_return_pct
FROM stock_signals
GROUP BY product_name
HAVING buy_price IS NOT NULL AND sell_price IS NOT NULL;


-- ============================================================================
-- ANALYSIS TIKTOK INFLUENCER IMPACT SCORE
-- Techniques: Complex aggregations, Ratios, Rolling calculations
-- ============================================================================

WITH influencer_impact AS (
    SELECT 
        p.product_name,
        tm.metric_date,
        tm.daily_new_posts,
        tm.top_influencer_posts,
        tm.avg_engagement_rate,
        tm.sentiment_score,
        -- Calculate influencer penetration
        ROUND((tm.top_influencer_posts * 100.0 / NULLIF(tm.daily_new_posts, 0)), 2) as influencer_penetration_pct,
        -- Calculate impact score (weighted composite)
        ROUND(
            (tm.avg_engagement_rate * 0.4) + 
            ((tm.top_influencer_posts * 100.0 / NULLIF(tm.daily_new_posts, 0)) * 0.3) +
            ((tm.sentiment_score + 1) * 50 * 0.3),  -- Normalize sentiment to 0-100
            2
        ) as influencer_impact_score,
        -- 4-week moving average of impact
        AVG(
            (tm.avg_engagement_rate * 0.4) + 
            ((tm.top_influencer_posts * 100.0 / NULLIF(tm.daily_new_posts, 0)) * 0.3) +
            ((tm.sentiment_score + 1) * 50 * 0.3)
        ) OVER (
            PARTITION BY p.product_id 
            ORDER BY tm.metric_date 
            ROWS BETWEEN 3 PRECEDING AND CURRENT ROW
        ) as ma_4week_impact
    FROM tiktok_metrics tm
    JOIN products p ON tm.product_id = p.product_id
)
SELECT 
    product_name,
    metric_date,
    daily_new_posts,
    top_influencer_posts,
    influencer_penetration_pct,
    avg_engagement_rate,
    sentiment_score,
    influencer_impact_score,
    ROUND(ma_4week_impact, 2) as ma_4week_impact,
    -- Classify impact level
    CASE 
        WHEN influencer_impact_score >= 70 THEN 'VERY HIGH'
        WHEN influencer_impact_score >= 50 THEN 'HIGH'
        WHEN influencer_impact_score >= 30 THEN 'MODERATE'
        ELSE 'LOW'
    END as impact_level
FROM influencer_impact
ORDER BY metric_date DESC, influencer_impact_score DESC
LIMIT 50;


-- ============================================================================
-- ANALYSIS SATURATION SIGNAL DETECTION
-- Techniques: Multiple CTEs, Trend analysis, Early warning indicators
-- ============================================================================

WITH metrics_3month AS (
    SELECT 
        p.product_id,
        p.product_name,
        DATE('now') as analysis_date,
        -- Current metrics (last 30 days)
        AVG(CASE WHEN st.trend_date >= DATE('now', '-30 days') THEN st.search_interest END) as interest_last_30d,
        AVG(CASE WHEN tm.metric_date >= DATE('now', '-30 days') THEN tm.avg_engagement_rate END) as engagement_last_30d,
        AVG(CASE WHEN tm.metric_date >= DATE('now', '-30 days') THEN tm.sentiment_score END) as sentiment_last_30d,
        -- Previous period (30-60 days ago)
        AVG(CASE WHEN st.trend_date BETWEEN DATE('now', '-60 days') AND DATE('now', '-31 days') 
                 THEN st.search_interest END) as interest_prev_30d,
        AVG(CASE WHEN tm.metric_date BETWEEN DATE('now', '-60 days') AND DATE('now', '-31 days') 
                 THEN tm.avg_engagement_rate END) as engagement_prev_30d,
        AVG(CASE WHEN tm.metric_date BETWEEN DATE('now', '-60 days') AND DATE('now', '-31 days') 
                 THEN tm.sentiment_score END) as sentiment_prev_30d,
        -- Peak values
        MAX(st.search_interest) as all_time_peak_interest,
        MAX(tm.avg_engagement_rate) as all_time_peak_engagement
    FROM products p
    LEFT JOIN social_trends st ON p.product_id = st.product_id AND st.region = 'US'
    LEFT JOIN tiktok_metrics tm ON p.product_id = tm.product_id
    GROUP BY p.product_id, p.product_name
)
SELECT 
    product_name,
    analysis_date,
    ROUND(interest_last_30d, 2) as current_interest,
    ROUND(interest_prev_30d, 2) as previous_interest,
    ROUND(((interest_last_30d - interest_prev_30d) / NULLIF(interest_prev_30d, 0)) * 100, 2) as interest_change_pct,
    ROUND(engagement_last_30d, 2) as current_engagement,
    ROUND(((engagement_last_30d - engagement_prev_30d) / NULLIF(engagement_prev_30d, 0)) * 100, 2) as engagement_change_pct,
    ROUND(sentiment_last_30d, 2) as current_sentiment,
    ROUND(sentiment_last_30d - sentiment_prev_30d, 2) as sentiment_change,
    -- Calculate distance from peak (saturation indicator)
    ROUND((interest_last_30d / all_time_peak_interest) * 100, 2) as pct_of_peak_interest,
    -- Saturation warning flags
    CASE
        WHEN ((interest_last_30d - interest_prev_30d) / NULLIF(interest_prev_30d, 0)) < -15
             AND ((engagement_last_30d - engagement_prev_30d) / NULLIF(engagement_prev_30d, 0)) < -10
        THEN '🔴 HIGH RISK - Declining interest AND engagement'
        WHEN (interest_last_30d / all_time_peak_interest) < 0.3
             AND (sentiment_last_30d - sentiment_prev_30d) < -0.15
        THEN '🟡 MEDIUM RISK - Far from peak with declining sentiment'
        WHEN ((interest_last_30d - interest_prev_30d) / NULLIF(interest_prev_30d, 0)) < -10
        THEN '🟡 MEDIUM RISK - Declining interest'
        ELSE '🟢 LOW RISK - Stable or growing'
    END as saturation_signal
FROM metrics_3month
ORDER BY interest_change_pct ASC;


-- ============================================================================
-- ANALYSIS 10: EXECUTIVE SUMMARY - KEY METRICS DASHBOARD
-- Techniques: Multiple aggregations, Summary statistics, Ranking
-- ============================================================================

-- Summary view combining all key metrics
SELECT 
    'VIRAL PRODUCT HYPE CYCLE ANALYSIS - EXECUTIVE SUMMARY' as report_title,
    DATE('now') as report_date
UNION ALL
SELECT '============================================================', ''
UNION ALL
SELECT 'PRODUCT PERFORMANCE RANKINGS', ''
UNION ALL
SELECT '------------------------------------------------------------', ''
UNION ALL
SELECT 
    RANK() OVER (ORDER BY MAX(search_interest) DESC) || '. ' || product_name as product_ranking,
    'Peak Interest: ' || MAX(search_interest) || ' | Avg: ' || ROUND(AVG(search_interest), 1) as metrics
FROM social_trends st
JOIN products p ON st.product_id = p.product_id
WHERE st.region = 'US'
GROUP BY p.product_name;

-- End of analysis queries
