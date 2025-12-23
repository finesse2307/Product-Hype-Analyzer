# Viral Product Hype Cycle Financial Analyzer

SQL-based analysis of how social media trends impact consumer product sales and market performance.

## Overview

I wanted to understand how products like Stanley cups and Owala bottles go viral on TikTok and what that means financially. This project connects Google Trends data, TikTok metrics, retail events, and stock prices to answer questions like: when do these products peak? How long does the hype last? Can we predict the next viral hit?

**Products analyzed:**
- Stanley Quencher ($45 tumbler)
- Owala FreeSip ($32 water bottle)
- Hydro Flask ($45 water bottle)
- YETI Rambler ($35 tumbler)

## Questions I'm trying to answer

1. When do viral products actually peak?
2. Can social media metrics predict sales spikes?
3. How long before the trend dies out?
4. Do retail events (like Target exclusives) actually drive interest?

## Data

### Database: SQLite (12,011 records)

**social_trends** - 7,308 records of daily Google Trends search interest  
**tiktok_metrics** - 1,036 records of weekly engagement data  
**stock_prices** - 3,654 daily price records for public companies  
**retail_events** - 9 major launches, sellouts, and collaborations  
**products** - 4 product profiles  

Data covers 2020-2024. The TikTok and social data is modeled on publicly reported figures (like #owala hitting 272M views, #stanleycup over 500M).

## Database Schema

Six tables with proper foreign keys and indexes:

```sql
products            -- Basic product info, pricing, company details
social_trends       -- Daily Google Trends data (0-100 scale)
tiktok_metrics      -- Weekly: views, posts, engagement, sentiment
stock_prices        -- Daily OHLC for public companies (YETI, Hydro Flask parent)
retail_events       -- Launch dates, sellouts, resale premiums
hype_scores         -- Calculated composite virality scores
```

See `schema.sql` for full details.

## SQL Analyses

The project includes 10 analysis queries showing different techniques:

1. **Peak Detection** - Find exact viral peak dates using `ROW_NUMBER()`
2. **Momentum Analysis** - Week-over-week growth with `LAG()` 
3. **Market Share** - Monthly competition between products
4. **Event Impact** - Measure search lift from retail events
5. **Hype Phases** - Classify products into lifecycle stages
6. **Stock Correlation** - Compare TikTok metrics to stock prices
7. **Investment Simulation** - Identify theoretical buy/sell points
8. **Influencer Score** - Weighted composite of engagement metrics
9. **Saturation Detection** - Early warning signals for decline
10. **Summary Dashboard** - Executive overview of all metrics

## Key Findings

- Stanley Quencher peaked March 15, 2023 (100/100 search interest)
- Owala FreeSip peaked July 31, 2023 (95/100)
- Saw 800% week-over-week growth during viral surge periods
- Target sellouts drove +15% average search interest lift
- Typical viral cycle: 3-6 months growth, ~7 days at peak, gradual decline
- Products stabilize around 15-20% of peak interest after maturity

## Files

```
schema.sql                  - Database design
analysis_queries.sql        - All 10 analyses with comments
viral_products.db           - SQLite database file
generate_sample_data.py     - Creates realistic test data
import_data.py              - Loads CSVs into database
run_analyses.py             - Executes all queries and exports results
```

## Visualizations & Presentation

**Presentation:** `Viral_Products_Analysis.pptx` (11 slides)
- Professional PowerPoint with all charts
- Key findings and business applications
- SQL techniques showcase
- Ready for interviews/portfolio

**Charts:** 7 visualizations in `visualizations/` folder
1. Executive dashboard - All metrics overview
2. Trend lines - Search interest 2022-2024
3. Peak comparison - Max vs average by product
4. Market share - Monthly evolution chart
5. Event impact - Before/after analysis
6. TikTok engagement - Quality metrics over time
7. Growth heatmap - Week-over-week patterns

All charts are high-resolution PNGs (300 DPI).

## Running the Project

```bash
# Generate data
python3 generate_sample_data.py

# Create database and load data
sqlite3 viral_products.db < schema.sql
python3 import_data.py

# Run all analyses
python3 run_analyses.py

# Generate visualizations
python3 create_visualizations.py

# Create presentation
python3 create_presentation.py
```

Or just explore the pre-built `viral_products.db` file:

```bash
sqlite3 viral_products.db
```

```sql
-- Example: Show current product rankings
SELECT 
    product_name,
    MAX(search_interest) as peak,
    ROUND(AVG(search_interest), 1) as avg
FROM social_trends st
JOIN products p ON st.product_id = p.product_id
WHERE region = 'US'
GROUP BY product_name
ORDER BY peak DESC;
```

## Why This Project?

I wanted something more interesting than the typical "analyze sales data" project. Viral products are everywhere right now - Stanley cups causing stampedes at Target, Owala bottles selling out in minutes. There's real money and business decisions involved, but not much data analysis on the patterns.

The SQL work here goes beyond basic queries - using window functions to detect momentum shifts, CTEs for complex multi-step analysis, and event-based windowing to measure retail impact. It's finance-focused but touches marketing, social media, and consumer behavior too.

## Technical Notes

- Used SQLite for portability (no server setup needed)
- Window functions require SQLite 3.25+ 
- Python scripts need pandas (`pip install pandas`)
- Stock data collection attempted via yfinance but hit network restrictions
- TikTok data is simulated based on publicly reported metrics

## Data Sources

- Google Trends patterns
- News reports on Stanley/Owala viral trends
- Public TikTok metrics (view counts, hashtag mentions)
- Industry reports on market size and retail events
- Stock data patterns for comparable public companies

This is a portfolio/educational project. Data is either public or simulated to match realistic patterns.

---

Built for SQL portfolio demonstration | December 2024
