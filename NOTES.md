# Project Notes

## What I Built

A SQL database tracking viral water bottle trends (Stanley, Owala, etc.) to see if social media hype actually translates to business results.

## Why This Topic

Everyone's seen the Stanley cup craze. I wanted to dig into the data and see:
- Can you predict when these products will peak?
- Do TikTok trends correlate with sales?
- How long before the hype dies?

Turns out there are patterns. Products typically peak 3-6 months after going viral, then drop off gradually.

## Data

12,000+ records across 5 years (2020-2024):
- Google Trends search data 
- TikTok metrics (views, engagement, sentiment)
- Stock prices for public companies
- Retail events (launches, sellouts)

Some data is real (Trends patterns, news events, reported TikTok stats), some is simulated to match realistic patterns since APIs weren't accessible.

## Interesting Finds

- Stanley peaked March 2023, Owala July 2023
- Saw 800% week-over-week growth during viral surges
- Target sellouts boosted search interest by ~15%
- Products settle around 15-20% of peak interest after hype fades
- Market share shifts - Owala actually overtook Stanley by mid-2024

## SQL Techniques

The queries showcase:
- Window functions (ROW_NUMBER, LAG, LEAD)
- CTEs for multi-step logic
- Date calculations with JULIANDAY
- Event-based analysis (before/after comparisons)
- Rolling averages
- Market share calculations

## Files

- `schema.sql` - Database structure
- `analysis_queries.sql` - 10 different analyses
- `viral_products.db` - SQLite database
- `*.csv` - Source data files
- Python scripts for data generation/loading

## Running It

```bash
# Explore the database
sqlite3 viral_products.db

# Regenerate data if needed
python3 generate_sample_data.py
python3 import_data.py

# Run all analyses
python3 run_analyses.py
```

## Limitations

- Stock data limited (network restrictions on Yahoo Finance)
- TikTok data is simulated based on publicly reported numbers
- Only 4 products (could expand to more categories)
- US-focused (could add international markets)

## If I Had More Time

- Real-time data pipeline from Google Trends API
- Sentiment analysis on actual TikTok comments
- Predictive model for forecasting peaks
- Dashboard visualization (Tableau/Power BI)
- More product categories (beauty, tech, fashion)

## Portfolio Use

Good for demonstrating:
- SQL skills (window functions, complex joins, CTEs)
- Business analysis thinking
- Working with time series data
- Understanding of modern consumer trends
- Data storytelling

The topic is memorable and relevant - everyone knows about viral products. Makes for better interview conversations than generic datasets.
