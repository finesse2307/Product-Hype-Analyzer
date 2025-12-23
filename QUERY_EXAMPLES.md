# SQL Query Examples

Some queries I found useful while exploring the data.

## Finding Viral Peaks

```sql
-- When did each product hit its max search interest?
WITH ranked AS (
    SELECT 
        p.product_name,
        st.trend_date,
        st.search_interest,
        ROW_NUMBER() OVER (PARTITION BY p.product_id ORDER BY st.search_interest DESC) as rank
    FROM social_trends st
    JOIN products p ON st.product_id = p.product_id
    WHERE st.region = 'US'
)
SELECT product_name, trend_date as peak_date, search_interest
FROM ranked
WHERE rank = 1;
```

## Growth Momentum

```sql
-- Find periods of explosive growth (>100% week-over-week)
WITH weekly AS (
    SELECT 
        p.product_name,
        st.trend_date,
        st.search_interest,
        LAG(st.search_interest, 7) OVER (PARTITION BY p.product_id ORDER BY st.trend_date) as prev_week
    FROM social_trends st
    JOIN products p ON st.product_id = p.product_id
    WHERE st.region = 'US'
)
SELECT 
    product_name,
    trend_date,
    search_interest,
    prev_week,
    ROUND((search_interest - prev_week) * 100.0 / prev_week, 1) as growth_pct
FROM weekly
WHERE prev_week > 0 
    AND (search_interest - prev_week) * 100.0 / prev_week > 100
ORDER BY growth_pct DESC
LIMIT 20;
```

## Market Share Over Time

```sql
-- Monthly market share competition
WITH monthly AS (
    SELECT 
        p.product_name,
        strftime('%Y-%m', st.trend_date) as month,
        AVG(st.search_interest) as avg_interest
    FROM social_trends st
    JOIN products p ON st.product_id = p.product_id
    WHERE st.region = 'US' AND st.trend_date >= '2023-01-01'
    GROUP BY p.product_name, month
),
totals AS (
    SELECT month, SUM(avg_interest) as total
    FROM monthly
    GROUP BY month
)
SELECT 
    m.month,
    m.product_name,
    ROUND(m.avg_interest, 1) as avg_interest,
    ROUND(m.avg_interest * 100.0 / t.total, 1) as market_share_pct
FROM monthly m
JOIN totals t ON m.month = t.month
ORDER BY m.month DESC, m.avg_interest DESC;
```

## Retail Event Impact

```sql
-- Did retail events actually boost search interest?
WITH events AS (
    SELECT 
        re.event_id,
        p.product_name,
        re.event_date,
        re.event_type,
        re.retailer,
        st.search_interest,
        JULIANDAY(st.trend_date) - JULIANDAY(re.event_date) as days_offset
    FROM retail_events re
    JOIN products p ON re.product_id = p.product_id
    JOIN social_trends st ON p.product_id = st.product_id
    WHERE st.region = 'US'
        AND ABS(days_offset) <= 7
)
SELECT 
    product_name,
    event_date,
    event_type,
    retailer,
    ROUND(AVG(CASE WHEN days_offset < 0 THEN search_interest END), 1) as before_event,
    ROUND(AVG(CASE WHEN days_offset > 0 THEN search_interest END), 1) as after_event,
    ROUND((AVG(CASE WHEN days_offset > 0 THEN search_interest END) - 
           AVG(CASE WHEN days_offset < 0 THEN search_interest END)) * 100.0 /
           AVG(CASE WHEN days_offset < 0 THEN search_interest END), 1) as lift_pct
FROM events
GROUP BY event_id, product_name, event_date, event_type, retailer
ORDER BY lift_pct DESC;
```

## TikTok Engagement Quality

```sql
-- Which products have the best engagement on TikTok?
SELECT 
    p.product_name,
    strftime('%Y-%m', tm.metric_date) as month,
    ROUND(AVG(tm.avg_engagement_rate), 2) as avg_engagement,
    ROUND(AVG(tm.sentiment_score), 2) as sentiment,
    SUM(tm.daily_new_posts) as total_posts
FROM tiktok_metrics tm
JOIN products p ON tm.product_id = p.product_id
WHERE tm.metric_date >= '2023-01-01'
GROUP BY p.product_name, month
ORDER BY month DESC, avg_engagement DESC
LIMIT 20;
```

## Stock Price During Viral Peaks

```sql
-- How did stock prices move during high search interest?
SELECT 
    p.product_name,
    p.stock_ticker,
    st.trend_date,
    st.search_interest,
    sp.close_price,
    sp.volume
FROM social_trends st
JOIN products p ON st.product_id = p.product_id
LEFT JOIN stock_prices sp ON p.product_id = sp.product_id AND st.trend_date = sp.price_date
WHERE st.region = 'US'
    AND st.search_interest >= 70
    AND p.is_public_company = 1
ORDER BY st.trend_date DESC;
```

## 30-Day Rolling Average

```sql
-- Smooth out daily noise with moving average
SELECT 
    p.product_name,
    st.trend_date,
    st.search_interest,
    ROUND(AVG(st.search_interest) OVER (
        PARTITION BY p.product_id 
        ORDER BY st.trend_date 
        ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ), 1) as ma_30
FROM social_trends st
JOIN products p ON st.product_id = p.product_id
WHERE st.region = 'US'
    AND st.trend_date >= '2023-01-01'
ORDER BY st.trend_date DESC, p.product_name
LIMIT 50;
```

## Head-to-Head Comparison

```sql
-- Which product was trending each day?
WITH daily AS (
    SELECT 
        trend_date,
        MAX(CASE WHEN product_name = 'Stanley Quencher' THEN search_interest END) as stanley,
        MAX(CASE WHEN product_name = 'Owala FreeSip' THEN search_interest END) as owala,
        MAX(CASE WHEN product_name = 'Hydro Flask' THEN search_interest END) as hydroflask,
        MAX(CASE WHEN product_name = 'YETI Rambler' THEN search_interest END) as yeti
    FROM social_trends st
    JOIN products p ON st.product_id = p.product_id
    WHERE region = 'US'
    GROUP BY trend_date
)
SELECT 
    trend_date,
    stanley, owala, hydroflask, yeti,
    CASE
        WHEN stanley >= GREATEST(owala, hydroflask, yeti) THEN 'Stanley'
        WHEN owala >= GREATEST(stanley, hydroflask, yeti) THEN 'Owala'
        WHEN hydroflask >= GREATEST(stanley, owala, yeti) THEN 'Hydro Flask'
        ELSE 'YETI'
    END as leader
FROM daily
WHERE trend_date >= '2023-01-01'
ORDER BY trend_date DESC
LIMIT 30;
```

## Exporting Results

```sql
-- In SQLite CLI:
.mode csv
.headers on
.output my_results.csv

-- Run your query here
SELECT * FROM products;

.output stdout
```

## Notes

- Use `.mode column` in SQLite for better readability
- Window functions need SQLite 3.25+
- Some queries can be slow on large date ranges - add WHERE clauses to filter
- The `GREATEST()` function picks the max of multiple values
