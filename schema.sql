-- ============================================================================
-- Viral Product Hype Cycle Database Schema
-- ============================================================================
-- SQLite database for analyzing social media trends and viral products
-- Covers: Stanley, Owala, Hydro Flask, YETI (2020-2024)
-- ============================================================================

-- Drop existing tables (for fresh start)
DROP TABLE IF EXISTS hype_scores;
DROP TABLE IF EXISTS retail_events;
DROP TABLE IF EXISTS tiktok_metrics;
DROP TABLE IF EXISTS stock_prices;
DROP TABLE IF EXISTS social_trends;
DROP TABLE IF EXISTS products;

-- ============================================================================
-- TABLE: products
-- Description: Master table of viral products and their parent companies
-- ============================================================================
CREATE TABLE products (
    product_id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_name VARCHAR(100) NOT NULL,
    company_name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,              -- e.g., 'Water Bottle', 'Tumbler'
    launch_date DATE,                           -- Product launch date
    initial_price DECIMAL(10,2),                -- Original retail price
    stock_ticker VARCHAR(10),                   -- If publicly traded (NULL for private)
    is_public_company BOOLEAN DEFAULT 0,        -- 1 if company is public, 0 if private
    primary_color_theme VARCHAR(50),            -- e.g., 'Pastel Pink', 'Neon Green'
    unique_feature TEXT,                        -- Key differentiating feature
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    UNIQUE(product_name, company_name)
);

-- Index for faster lookups
CREATE INDEX idx_products_company ON products(company_name);
CREATE INDEX idx_products_ticker ON products(stock_ticker);

-- ============================================================================
-- TABLE: social_trends
-- Description: Google Trends search interest over time
-- ============================================================================
CREATE TABLE social_trends (
    trend_id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    trend_date DATE NOT NULL,
    search_interest INTEGER,                    -- Relative search volume (0-100)
    region VARCHAR(10),                         -- Geographic region (US, CA, UK, etc.)
    related_queries TEXT,                       -- JSON array of related searches
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    
    -- Constraints
    UNIQUE(product_id, trend_date, region),
    CHECK(search_interest >= 0 AND search_interest <= 100)
);

-- Indexes for time series queries
CREATE INDEX idx_trends_date ON social_trends(trend_date);
CREATE INDEX idx_trends_product_date ON social_trends(product_id, trend_date);

-- ============================================================================
-- TABLE: stock_prices
-- Description: Daily stock price data for public companies
-- ============================================================================
CREATE TABLE stock_prices (
    price_id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    price_date DATE NOT NULL,
    open_price DECIMAL(12,4),
    high_price DECIMAL(12,4),
    low_price DECIMAL(12,4),
    close_price DECIMAL(12,4),
    adj_close_price DECIMAL(12,4),             -- Adjusted for splits/dividends
    volume BIGINT,
    market_cap DECIMAL(15,2),                  -- Market capitalization
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    
    -- Constraints
    UNIQUE(product_id, price_date),
    CHECK(volume >= 0),
    CHECK(open_price >= 0 AND close_price >= 0)
);

-- Indexes for performance
CREATE INDEX idx_stock_date ON stock_prices(price_date);
CREATE INDEX idx_stock_product_date ON stock_prices(product_id, price_date);

-- ============================================================================
-- TABLE: tiktok_metrics
-- Description: TikTok engagement data for product-related content
-- ============================================================================
CREATE TABLE tiktok_metrics (
    metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    metric_date DATE NOT NULL,
    hashtag VARCHAR(100),                       -- Primary hashtag (e.g., #owala)
    total_views BIGINT,                         -- Cumulative views for hashtag
    daily_new_posts INTEGER,                    -- New posts that day
    avg_engagement_rate DECIMAL(5,2),           -- Average engagement % (likes+comments/views)
    top_influencer_posts INTEGER,               -- Posts by accounts with >100k followers
    sentiment_score DECIMAL(3,2),               -- -1 to 1 (negative to positive)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    
    -- Constraints
    UNIQUE(product_id, metric_date, hashtag),
    CHECK(total_views >= 0),
    CHECK(avg_engagement_rate >= 0 AND avg_engagement_rate <= 100),
    CHECK(sentiment_score >= -1 AND sentiment_score <= 1)
);

-- Indexes
CREATE INDEX idx_tiktok_date ON tiktok_metrics(metric_date);
CREATE INDEX idx_tiktok_product_date ON tiktok_metrics(product_id, metric_date);
CREATE INDEX idx_tiktok_hashtag ON tiktok_metrics(hashtag);

-- ============================================================================
-- TABLE: retail_events
-- Description: Significant retail and business events
-- ============================================================================
CREATE TABLE retail_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    event_date DATE NOT NULL,
    event_type VARCHAR(50) NOT NULL,            -- 'Launch', 'Sellout', 'Restock', 'Collab', 'PR'
    event_description TEXT,
    retailer VARCHAR(100),                      -- Target, Amazon, Urban Outfitters, etc.
    is_limited_edition BOOLEAN DEFAULT 0,
    estimated_units_sold INTEGER,               -- If available
    resale_premium_pct DECIMAL(5,2),           -- % above retail on resale market
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- Indexes
CREATE INDEX idx_events_date ON retail_events(event_date);
CREATE INDEX idx_events_product ON retail_events(product_id);
CREATE INDEX idx_events_type ON retail_events(event_type);

-- ============================================================================
-- TABLE: hype_scores
-- Description: Calculated composite virality scores
-- ============================================================================
CREATE TABLE hype_scores (
    score_id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    score_date DATE NOT NULL,
    
    -- Component scores (0-100 scale)
    social_media_score DECIMAL(5,2),            -- Based on TikTok metrics
    search_trend_score DECIMAL(5,2),            -- Based on Google Trends
    retail_activity_score DECIMAL(5,2),         -- Based on events/sellouts
    
    -- Composite score
    overall_hype_score DECIMAL(5,2),            -- Weighted average of components
    
    -- Classification
    hype_phase VARCHAR(20),                     -- 'Emerging', 'Growth', 'Peak', 'Decline', 'Maturity'
    days_since_peak INTEGER,                    -- Days since reaching peak score
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    
    -- Constraints
    UNIQUE(product_id, score_date),
    CHECK(overall_hype_score >= 0 AND overall_hype_score <= 100)
);

-- Indexes
CREATE INDEX idx_hype_date ON hype_scores(score_date);
CREATE INDEX idx_hype_product_date ON hype_scores(product_id, score_date);
CREATE INDEX idx_hype_phase ON hype_scores(hype_phase);

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- View: Latest product metrics (most recent data point for each product)
CREATE VIEW v_latest_product_metrics AS
SELECT 
    p.product_id,
    p.product_name,
    p.company_name,
    p.category,
    st.search_interest as latest_search_interest,
    tm.total_views as latest_tiktok_views,
    tm.avg_engagement_rate as latest_engagement_rate,
    hs.overall_hype_score as latest_hype_score,
    hs.hype_phase,
    sp.close_price as latest_stock_price
FROM products p
LEFT JOIN (
    SELECT product_id, search_interest, trend_date
    FROM social_trends st1
    WHERE trend_date = (SELECT MAX(trend_date) FROM social_trends st2 WHERE st2.product_id = st1.product_id)
    AND region = 'US'
) st ON p.product_id = st.product_id
LEFT JOIN (
    SELECT product_id, total_views, avg_engagement_rate, metric_date
    FROM tiktok_metrics tm1
    WHERE metric_date = (SELECT MAX(metric_date) FROM tiktok_metrics tm2 WHERE tm2.product_id = tm1.product_id)
) tm ON p.product_id = tm.product_id
LEFT JOIN (
    SELECT product_id, overall_hype_score, hype_phase, score_date
    FROM hype_scores hs1
    WHERE score_date = (SELECT MAX(score_date) FROM hype_scores hs2 WHERE hs2.product_id = hs1.product_id)
) hs ON p.product_id = hs.product_id
LEFT JOIN (
    SELECT product_id, close_price, price_date
    FROM stock_prices sp1
    WHERE price_date = (SELECT MAX(price_date) FROM stock_prices sp2 WHERE sp2.product_id = sp1.product_id)
) sp ON p.product_id = sp.product_id;

-- View: Product growth rates (week-over-week changes)
CREATE VIEW v_product_growth_rates AS
SELECT 
    p.product_id,
    p.product_name,
    st.trend_date,
    st.search_interest,
    LAG(st.search_interest, 7) OVER (PARTITION BY p.product_id ORDER BY st.trend_date) as prev_week_interest,
    CASE 
        WHEN LAG(st.search_interest, 7) OVER (PARTITION BY p.product_id ORDER BY st.trend_date) > 0 
        THEN ROUND(((st.search_interest - LAG(st.search_interest, 7) OVER (PARTITION BY p.product_id ORDER BY st.trend_date)) * 100.0 / 
                    LAG(st.search_interest, 7) OVER (PARTITION BY p.product_id ORDER BY st.trend_date)), 2)
        ELSE NULL
    END as week_over_week_growth_pct
FROM products p
JOIN social_trends st ON p.product_id = st.product_id
WHERE st.region = 'US';

-- ============================================================================
-- SAMPLE DATA COMMENTS
-- ============================================================================

-- Products to track:
-- 1. Stanley Quencher (Stanley 1913) - Private company
-- 2. Owala FreeSip (Trove Brands) - Private company  
-- 3. Hydro Flask (Helen of Troy - ticker: HELE) - Public parent
-- 4. YETI Tumblers (YETI Holdings - ticker: YETI) - Public company

-- Key dates:
-- Stanley viral explosion: ~Jan 2023
-- Owala peak: ~Mid 2023 - Early 2024
-- Hydro Flask peak: ~2019 (VSCO girl trend)

-- ============================================================================
-- DATA QUALITY CHECKS
-- ============================================================================

-- Check for missing critical data
CREATE VIEW v_data_quality_check AS
SELECT 
    'Products without trends' as check_name,
    COUNT(*) as issue_count
FROM products p
LEFT JOIN social_trends st ON p.product_id = st.product_id
WHERE st.trend_id IS NULL
UNION ALL
SELECT 
    'Trends with invalid interest scores',
    COUNT(*)
FROM social_trends
WHERE search_interest < 0 OR search_interest > 100
UNION ALL
SELECT 
    'Stock prices with zero volume',
    COUNT(*)
FROM stock_prices
WHERE volume = 0;

-- ============================================================================
-- ANALYTICS HELPER FUNCTIONS (Stored as comments for reference)
-- ============================================================================

-- Calculate correlation coefficient (would be used in queries):
-- Pearson correlation = 
--   SUM((x - avg_x) * (y - avg_y)) / 
--   SQRT(SUM((x - avg_x)^2) * SUM((y - avg_y)^2))

-- Calculate moving average (using window function):
-- AVG(metric) OVER (
--   PARTITION BY product_id 
--   ORDER BY date 
--   ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
-- ) as moving_avg_7day

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================

-- Verification query: Count all tables
SELECT 
    name as table_name,
    sql as create_statement
FROM sqlite_master 
WHERE type = 'table'
ORDER BY name;
