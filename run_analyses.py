#!/usr/bin/env python3
"""
Execute SQL analyses and generate report outputs
"""

import sqlite3
import pandas as pd
import os

def run_analysis(conn, query_name, query):
    """Run a query and return results as DataFrame"""
    try:
        df = pd.read_sql(query, conn)
        return df
    except Exception as e:
        print(f"   ERROR in {query_name}: {e}")
        return None

def main():
    """Execute all analyses"""
    
    print("=" * 80)
    print("RUNNING VIRAL PRODUCT HYPE CYCLE ANALYSES")
    print("=" * 80)
    
    # Connect to database
    conn = sqlite3.connect('viral_products.db')
    
    # Create outputs directory
    os.makedirs('analysis_results', exist_ok=True)
    
    # ========================================================================
    # ANALYSIS 1: Peak Detection
    # ========================================================================
    print("\n📊 Analysis 1: Viral Peak Detection")
    query1 = """
    WITH ranked_trends AS (
        SELECT 
            p.product_name,
            st.trend_date,
            st.search_interest,
            ROW_NUMBER() OVER (PARTITION BY p.product_id ORDER BY st.search_interest DESC) as intensity_rank
        FROM social_trends st
        JOIN products p ON st.product_id = p.product_id
        WHERE st.region = 'US'
    )
    SELECT 
        product_name,
        trend_date as peak_date,
        search_interest as peak_intensity
    FROM ranked_trends
    WHERE intensity_rank = 1
    ORDER BY search_interest DESC;
    """
    df1 = run_analysis(conn, "Peak Detection", query1)
    if df1 is not None:
        print(df1.to_string(index=False))
        df1.to_csv('analysis_results/01_peak_detection.csv', index=False)
        print("   ✓ Saved to analysis_results/01_peak_detection.csv")
    
    # ========================================================================
    # ANALYSIS 2: Momentum Analysis  
    # ========================================================================
    print("\n📊 Analysis 2: Viral Momentum (Recent High-Growth Periods)")
    query2 = """
    WITH weekly_trends AS (
        SELECT 
            p.product_name,
            st.trend_date,
            st.search_interest,
            LAG(st.search_interest, 7) OVER (
                PARTITION BY p.product_id 
                ORDER BY st.trend_date
            ) as prev_week_interest
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
        CASE
            WHEN prev_week_interest > 0 AND 
                 ((search_interest - prev_week_interest) * 100.0 / prev_week_interest) > 50
            THEN 'EXPLOSIVE'
            WHEN prev_week_interest > 0 AND 
                 ((search_interest - prev_week_interest) * 100.0 / prev_week_interest) > 20
            THEN 'HIGH'
            ELSE 'STABLE'
        END as growth_category
    FROM weekly_trends
    WHERE prev_week_interest IS NOT NULL
        AND ((search_interest - prev_week_interest) * 100.0 / prev_week_interest) > 50
    ORDER BY week_over_week_growth_pct DESC
    LIMIT 15;
    """
    df2 = run_analysis(conn, "Momentum Analysis", query2)
    if df2 is not None:
        print(df2.to_string(index=False))
        df2.to_csv('analysis_results/02_momentum_analysis.csv', index=False)
        print("   ✓ Saved to analysis_results/02_momentum_analysis.csv")
    
    # ========================================================================
    # ANALYSIS 3: Market Share Competition
    # ========================================================================
    print("\n📊 Analysis 3: Monthly Market Share Competition (2023-2024)")
    query3 = """
    WITH monthly_metrics AS (
        SELECT 
            p.product_name,
            strftime('%Y-%m', st.trend_date) as year_month,
            AVG(st.search_interest) as avg_monthly_interest
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
        ROUND(mm.avg_monthly_interest, 2) as avg_interest,
        ROUND((mm.avg_monthly_interest * 100.0 / tm.total_market_interest), 2) as market_share_pct,
        RANK() OVER (PARTITION BY mm.year_month ORDER BY mm.avg_monthly_interest DESC) as monthly_rank
    FROM monthly_metrics mm
    JOIN total_market tm ON mm.year_month = tm.year_month
    ORDER BY mm.year_month DESC, mm.avg_monthly_interest DESC
    LIMIT 24;
    """
    df3 = run_analysis(conn, "Market Share", query3)
    if df3 is not None:
        print(df3.to_string(index=False))
        df3.to_csv('analysis_results/03_market_share.csv', index=False)
        print("   ✓ Saved to analysis_results/03_market_share.csv")
    
    # ========================================================================
    # ANALYSIS 4: Retail Event Impact
    # ========================================================================
    print("\n📊 Analysis 4: Retail Event Impact Analysis")
    query4 = """
    WITH event_windows AS (
        SELECT 
            re.event_id,
            re.product_id,
            re.event_date,
            re.event_type,
            re.retailer,
            re.resale_premium_pct,
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
        ROUND(AVG(CASE WHEN ew.days_from_event < 0 THEN ew.search_interest END), 2) as avg_interest_before,
        ROUND(AVG(CASE WHEN ew.days_from_event > 0 THEN ew.search_interest END), 2) as avg_interest_after,
        ROUND(
            (AVG(CASE WHEN ew.days_from_event > 0 THEN ew.search_interest END) - 
             AVG(CASE WHEN ew.days_from_event < 0 THEN ew.search_interest END)) * 100.0 /
            NULLIF(AVG(CASE WHEN ew.days_from_event < 0 THEN ew.search_interest END), 0), 
            2
        ) as event_lift_pct
    FROM event_windows ew
    JOIN products p ON ew.product_id = p.product_id
    GROUP BY ew.event_id, p.product_name, ew.event_date, ew.event_type, ew.retailer, ew.resale_premium_pct
    HAVING avg_interest_before IS NOT NULL AND avg_interest_after IS NOT NULL
    ORDER BY event_lift_pct DESC;
    """
    df4 = run_analysis(conn, "Event Impact", query4)
    if df4 is not None:
        print(df4.to_string(index=False))
        df4.to_csv('analysis_results/04_event_impact.csv', index=False)
        print("   ✓ Saved to analysis_results/04_event_impact.csv")
    
    # ========================================================================
    # ANALYSIS 5: Stock Performance During Viral Periods
    # ========================================================================
    print("\n📊 Analysis 5: Stock Performance During Peak Virality")
    query5 = """
    WITH peak_periods AS (
        SELECT 
            product_id,
            DATE(trend_date) as peak_start
        FROM social_trends
        WHERE region = 'US' 
            AND search_interest >= 70
        GROUP BY product_id, DATE(trend_date)
    ),
    stock_performance AS (
        SELECT 
            p.product_name,
            p.stock_ticker,
            pp.peak_start,
            sp.close_price,
            LAG(sp.close_price, 30) OVER (PARTITION BY p.product_id ORDER BY sp.price_date) as price_30d_ago,
            sp.volume,
            AVG(sp.volume) OVER (
                PARTITION BY p.product_id 
                ORDER BY sp.price_date 
                ROWS BETWEEN 60 PRECEDING AND 31 PRECEDING
            ) as avg_volume_prev_month
        FROM peak_periods pp
        JOIN products p ON pp.product_id = p.product_id
        JOIN stock_prices sp ON p.product_id = sp.product_id 
            AND sp.price_date = pp.peak_start
        WHERE p.is_public_company = 1
    )
    SELECT 
        product_name,
        stock_ticker,
        peak_start,
        ROUND(close_price, 2) as price_at_peak,
        ROUND(price_30d_ago, 2) as price_30d_before,
        ROUND(((close_price - price_30d_ago) / NULLIF(price_30d_ago, 0)) * 100, 2) as price_change_30d_pct,
        ROUND(volume / NULLIF(avg_volume_prev_month, 0), 2) as volume_vs_avg_ratio
    FROM stock_performance
    WHERE price_30d_ago IS NOT NULL
    ORDER BY price_change_30d_pct DESC
    LIMIT 10;
    """
    df5 = run_analysis(conn, "Stock Performance", query5)
    if df5 is not None:
        print(df5.to_string(index=False))
        df5.to_csv('analysis_results/05_stock_performance.csv', index=False)
        print("   ✓ Saved to analysis_results/05_stock_performance.csv")
    
    # ========================================================================
    # ANALYSIS 6: TikTok Engagement Trends
    # ========================================================================
    print("\n📊 Analysis 6: TikTok Engagement Quality Metrics")
    query6 = """
    SELECT 
        p.product_name,
        strftime('%Y-%m', tm.metric_date) as month,
        ROUND(AVG(tm.avg_engagement_rate), 2) as avg_engagement,
        ROUND(AVG(tm.sentiment_score), 2) as avg_sentiment,
        ROUND(AVG(tm.top_influencer_posts * 100.0 / NULLIF(tm.daily_new_posts, 0)), 2) as influencer_penetration_pct,
        SUM(tm.daily_new_posts) as total_posts
    FROM tiktok_metrics tm
    JOIN products p ON tm.product_id = p.product_id
    WHERE tm.metric_date >= '2023-01-01'
    GROUP BY p.product_name, month
    ORDER BY month DESC, avg_engagement DESC
    LIMIT 20;
    """
    df6 = run_analysis(conn, "TikTok Engagement", query6)
    if df6 is not None:
        print(df6.to_string(index=False))
        df6.to_csv('analysis_results/06_tiktok_engagement.csv', index=False)
        print("   ✓ Saved to analysis_results/06_tiktok_engagement.csv")
    
    # ========================================================================
    # Generate Summary Report
    # ========================================================================
    print("\n📊 Generating Executive Summary...")
    
    summary = []
    summary.append("=" * 80)
    summary.append("VIRAL PRODUCT HYPE CYCLE ANALYSIS - EXECUTIVE SUMMARY")
    summary.append("=" * 80)
    summary.append(f"Report Date: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
    summary.append("")
    
    # Product rankings
    rankings_query = """
    SELECT 
        product_name,
        MAX(search_interest) as peak_interest,
        ROUND(AVG(search_interest), 2) as avg_interest
    FROM social_trends st
    JOIN products p ON st.product_id = p.product_id
    WHERE st.region = 'US'
    GROUP BY p.product_name
    ORDER BY peak_interest DESC;
    """
    rankings_df = pd.read_sql(rankings_query, conn)
    
    summary.append("PRODUCT PERFORMANCE RANKINGS")
    summary.append("-" * 80)
    for idx, row in rankings_df.iterrows():
        summary.append(f"{idx+1}. {row['product_name']:<20} Peak: {row['peak_interest']:>3} | Avg: {row['avg_interest']:>5.1f}")
    
    summary.append("")
    summary.append("KEY INSIGHTS")
    summary.append("-" * 80)
    
    # Get peak dates
    if df1 is not None and not df1.empty:
        stanley_peak = df1[df1['product_name'] == 'Stanley Quencher']['peak_date'].values[0] if 'Stanley Quencher' in df1['product_name'].values else 'N/A'
        owala_peak = df1[df1['product_name'] == 'Owala FreeSip']['peak_date'].values[0] if 'Owala FreeSip' in df1['product_name'].values else 'N/A'
        
        summary.append(f"• Stanley Quencher peaked on: {stanley_peak}")
        summary.append(f"• Owala FreeSip peaked on: {owala_peak}")
    
    if df2 is not None and not df2.empty:
        max_growth = df2['week_over_week_growth_pct'].max()
        summary.append(f"• Maximum week-over-week growth observed: {max_growth:.1f}%")
    
    if df4 is not None and not df4.empty:
        best_event = df4.iloc[0]
        summary.append(f"• Most effective retail event: {best_event['event_type']} at {best_event['retailer']} (+{best_event['event_lift_pct']:.1f}% lift)")
    
    summary.append("")
    summary.append("=" * 80)
    
    # Save summary
    summary_text = "\n".join(summary)
    with open('analysis_results/EXECUTIVE_SUMMARY.txt', 'w') as f:
        f.write(summary_text)
    
    print(summary_text)
    print("\n✓ Saved to analysis_results/EXECUTIVE_SUMMARY.txt")
    
    conn.close()
    
    print("\n" + "=" * 80)
    print("✓ ALL ANALYSES COMPLETE!")
    print("=" * 80)
    print(f"\nResults saved in: analysis_results/")
    print("\nGenerated files:")
    for file in sorted(os.listdir('analysis_results')):
        print(f"  • {file}")

if __name__ == "__main__":
    main()
