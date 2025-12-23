#!/usr/bin/env python3
"""
Generate Realistic Sample Data for Viral Product Analysis
Based on actual trends from Stanley, Owala, Hydro Flask, and YETI
Uses real reported dates and patterns
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# Set seed for reproducibility
np.random.seed(42)
random.seed(42)

def generate_date_range(start_date, end_date):
    """Generate list of dates between start and end"""
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    return dates.tolist()

def generate_hype_cycle_pattern(dates, peak_date, peak_value=100, 
                                pre_peak_months=6, post_peak_months=12):
    """
    Generate realistic hype cycle pattern
    
    Args:
        dates: List of dates
        peak_date: Date of peak virality
        peak_value: Maximum value at peak
        pre_peak_months: Months from start to peak
        post_peak_months: Months from peak to maturity
    
    Returns:
        Dictionary mapping dates to values
    """
    pattern = {}
    peak_datetime = pd.to_datetime(peak_date)
    
    for date in dates:
        current_datetime = pd.to_datetime(date)
        days_from_peak = (current_datetime - peak_datetime).days
        
        if days_from_peak < -180:  # Before growth phase
            # Slow initial growth
            base = 5 + random.uniform(-2, 2)
            pattern[date] = max(0, base)
            
        elif days_from_peak < 0:  # Pre-peak growth
            # Exponential growth toward peak
            progress = (days_from_peak + 180) / 180
            value = 5 + (peak_value - 5) * (progress ** 2)
            noise = random.uniform(-5, 5)
            pattern[date] = max(0, min(100, value + noise))
            
        elif days_from_peak == 0:  # Peak
            pattern[date] = peak_value
            
        else:  # Post-peak decline
            # Slower decay, then plateau
            if days_from_peak < 90:
                # Fast initial decline
                decay = peak_value * np.exp(-days_from_peak / 60)
                pattern[date] = max(20, decay + random.uniform(-5, 5))
            elif days_from_peak < 180:
                # Moderate decline
                decay = 40 * np.exp(-(days_from_peak - 90) / 90)
                pattern[date] = max(15, 20 + decay + random.uniform(-3, 3))
            else:
                # Plateau at maturity
                base = 15 + random.uniform(-3, 3)
                pattern[date] = max(5, base)
    
    return pattern

# Product definitions based on real data
PRODUCTS = {
    'Stanley Quencher': {
        'company': 'Stanley 1913',
        'category': 'Tumbler',
        'launch_date': '2016-01-01',
        'price': 45.00,
        'viral_peak': '2023-03-15',  # Based on search data
        'color_theme': 'Pastel Pink',
        'feature': 'Handle + Straw + 40oz capacity',
        'peak_intensity': 100
    },
    'Owala FreeSip': {
        'company': 'Trove Brands',
        'category': 'Water Bottle',
        'launch_date': '2020-03-01',
        'price': 32.00,
        'viral_peak': '2023-08-01',  # Based on reported trends
        'color_theme': 'Multi-color combinations',
        'feature': 'Dual-function spout (sip or chug)',
        'peak_intensity': 95
    },
    'Hydro Flask': {
        'company': 'Helen of Troy',
        'category': 'Water Bottle',
        'launch_date': '2009-01-01',
        'price': 44.95,
        'viral_peak': '2019-08-01',  # VSCO girl trend peak
        'color_theme': 'Pastel colors',
        'feature': 'TempShield insulation',
        'peak_intensity': 90,
        'stock_ticker': 'HELE'
    },
    'YETI Rambler': {
        'company': 'YETI Holdings',
        'category': 'Tumbler',
        'launch_date': '2014-01-01',
        'price': 35.00,
        'viral_peak': '2020-06-01',  # Steady popularity
        'color_theme': 'Outdoor/rugged colors',
        'feature': 'MagSlider lid + durability',
        'peak_intensity': 85,
        'stock_ticker': 'YETI'
    }
}

def generate_products_data():
    """Generate products table data"""
    products = []
    for idx, (name, info) in enumerate(PRODUCTS.items(), start=1):
        products.append({
            'product_id': idx,
            'product_name': name,
            'company_name': info['company'],
            'category': info['category'],
            'launch_date': info['launch_date'],
            'initial_price': info['price'],
            'stock_ticker': info.get('stock_ticker', None),
            'is_public_company': 1 if info.get('stock_ticker') else 0,
            'primary_color_theme': info['color_theme'],
            'unique_feature': info['feature']
        })
    return pd.DataFrame(products)

def generate_social_trends_data(products_df):
    """Generate Google Trends-style data"""
    all_trends = []
    
    for _, product in products_df.iterrows():
        product_info = PRODUCTS[product['product_name']]
        
        # Generate dates from 2020 to 2024
        dates = generate_date_range('2020-01-01', '2024-12-31')
        
        # Generate hype cycle pattern
        pattern = generate_hype_cycle_pattern(
            dates, 
            product_info['viral_peak'],
            peak_value=product_info['peak_intensity']
        )
        
        # Create records
        for date, search_interest in pattern.items():
            all_trends.append({
                'product_id': product['product_id'],
                'trend_date': date,
                'search_interest': int(search_interest),
                'region': 'US'
            })
    
    return pd.DataFrame(all_trends)

def generate_tiktok_metrics(products_df):
    """Generate TikTok engagement metrics"""
    all_metrics = []
    
    for _, product in products_df.iterrows():
        product_info = PRODUCTS[product['product_name']]
        peak_date = pd.to_datetime(product_info['viral_peak'])
        
        # Generate weekly data from launch to end of 2024
        start = pd.to_datetime(product_info['launch_date'])
        dates = pd.date_range(start=max(start, pd.to_datetime('2020-01-01')), 
                             end='2024-12-31', freq='W')
        
        hashtag_map = {
            'Stanley Quencher': '#stanleycup',
            'Owala FreeSip': '#owala',
            'Hydro Flask': '#hydroflask',
            'YETI Rambler': '#yeti'
        }
        
        base_views = {
            'Stanley Quencher': 500000000,  # 500M+ reported
            'Owala FreeSip': 272000000,  # 272M reported
            'Hydro Flask': 150000000,
            'YETI Rambler': 100000000
        }
        
        cumulative_views = 0
        
        for date in dates:
            days_from_peak = (date - peak_date).days
            
            # Calculate daily engagement based on hype cycle
            if days_from_peak < -90:
                daily_posts = random.randint(50, 200)
                engagement_rate = random.uniform(2.5, 4.0)
                daily_views = random.randint(100000, 500000)
            elif days_from_peak < 0:
                # Ramp up to peak
                daily_posts = random.randint(200, 1000)
                engagement_rate = random.uniform(4.0, 6.5)
                daily_views = random.randint(500000, 2000000)
            elif days_from_peak < 30:
                # At peak
                daily_posts = random.randint(800, 2000)
                engagement_rate = random.uniform(6.0, 8.5)
                daily_views = random.randint(2000000, 5000000)
            elif days_from_peak < 180:
                # Decline
                daily_posts = random.randint(300, 800)
                engagement_rate = random.uniform(3.5, 5.5)
                daily_views = random.randint(800000, 2000000)
            else:
                # Maturity
                daily_posts = random.randint(100, 300)
                engagement_rate = random.uniform(2.0, 3.5)
                daily_views = random.randint(200000, 800000)
            
            cumulative_views += daily_views * 7  # Weekly accumulation
            
            # Sentiment (more positive during growth, more critical at peak/decline)
            if days_from_peak < -30:
                sentiment = random.uniform(0.6, 0.85)
            elif days_from_peak < 30:
                sentiment = random.uniform(0.75, 0.95)
            elif days_from_peak < 180:
                sentiment = random.uniform(0.4, 0.7)
            else:
                sentiment = random.uniform(0.5, 0.75)
            
            all_metrics.append({
                'product_id': product['product_id'],
                'metric_date': date,
                'hashtag': hashtag_map[product['product_name']],
                'total_views': min(cumulative_views, base_views[product['product_name']]),
                'daily_new_posts': daily_posts,
                'avg_engagement_rate': round(engagement_rate, 2),
                'top_influencer_posts': int(daily_posts * 0.15),
                'sentiment_score': round(sentiment, 2)
            })
    
    return pd.DataFrame(all_metrics)

def generate_retail_events(products_df):
    """Generate retail event data"""
    events = []
    event_id = 1
    
    # Stanley events
    events.extend([
        {
            'event_id': event_id, 'product_id': 1, 'event_date': '2023-01-15',
            'event_type': 'Sellout', 'event_description': 'Valentine\'s Day pink sold out nationwide',
            'retailer': 'Target', 'is_limited_edition': 1, 'estimated_units_sold': 50000,
            'resale_premium_pct': 150.0
        },
        {
            'event_id': event_id+1, 'product_id': 1, 'event_date': '2023-11-24',
            'event_type': 'Sellout', 'event_description': 'Black Friday release - stampede reported',
            'retailer': 'Target', 'is_limited_edition': 1, 'estimated_units_sold': 75000,
            'resale_premium_pct': 200.0
        },
        {
            'event_id': event_id+2, 'product_id': 1, 'event_date': '2024-02-01',
            'event_type': 'Collab', 'event_description': 'Starbucks collaboration release',
            'retailer': 'Starbucks', 'is_limited_edition': 1, 'estimated_units_sold': 100000,
            'resale_premium_pct': 180.0
        }
    ])
    event_id += 3
    
    # Owala events
    events.extend([
        {
            'event_id': event_id, 'product_id': 2, 'event_date': '2023-06-15',
            'event_type': 'Launch', 'event_description': 'Bowala exclusive colorway launch',
            'retailer': 'Urban Outfitters', 'is_limited_edition': 1, 'estimated_units_sold': 30000,
            'resale_premium_pct': 250.0
        },
        {
            'event_id': event_id+1, 'product_id': 2, 'event_date': '2023-09-01',
            'event_type': 'Sellout', 'event_description': 'All Target exclusives sold out in under 1 hour',
            'retailer': 'Target', 'is_limited_edition': 1, 'estimated_units_sold': 45000,
            'resale_premium_pct': 200.0
        },
        {
            'event_id': event_id+2, 'product_id': 2, 'event_date': '2024-03-15',
            'event_type': 'Collab', 'event_description': 'Disney collaboration announced',
            'retailer': 'Disney Store', 'is_limited_edition': 1, 'estimated_units_sold': 60000,
            'resale_premium_pct': 175.0
        }
    ])
    event_id += 3
    
    # Hydro Flask events
    events.extend([
        {
            'event_id': event_id, 'product_id': 3, 'event_date': '2019-08-15',
            'event_type': 'PR', 'event_description': 'VSCO girl trend peak - featured in NYT',
            'retailer': None, 'is_limited_edition': 0, 'estimated_units_sold': None,
            'resale_premium_pct': 50.0
        },
        {
            'event_id': event_id+1, 'product_id': 3, 'event_date': '2019-12-01',
            'event_type': 'Sellout', 'event_description': 'Holiday colors sold out',
            'retailer': 'REI', 'is_limited_edition': 1, 'estimated_units_sold': 40000,
            'resale_premium_pct': 75.0
        }
    ])
    event_id += 2
    
    # YETI events
    events.extend([
        {
            'event_id': event_id, 'product_id': 4, 'event_date': '2020-07-04',
            'event_type': 'Launch', 'event_description': 'Limited edition USA flag collection',
            'retailer': 'YETI.com', 'is_limited_edition': 1, 'estimated_units_sold': 25000,
            'resale_premium_pct': 80.0
        }
    ])
    
    return pd.DataFrame(events)

def generate_stock_prices(products_df):
    """Generate realistic stock price data for public companies"""
    all_prices = []
    
    # Only for public companies
    public_products = products_df[products_df['stock_ticker'].notna()]
    
    dates = generate_date_range('2020-01-01', '2024-12-31')
    
    for _, product in public_products.iterrows():
        product_info = PRODUCTS[product['product_name']]
        peak_date = pd.to_datetime(product_info['viral_peak'])
        
        # Base prices (realistic for these companies)
        if product['stock_ticker'] == 'YETI':
            base_price = 45.0
            volatility = 0.025
        else:  # HELE
            base_price = 85.0
            volatility = 0.020
        
        current_price = base_price
        
        for date in dates:
            # Market trending
            days_from_peak = (pd.to_datetime(date) - peak_date).days
            
            # Viral product effect on stock
            if -90 < days_from_peak < 90:
                trend = 0.0015  # Positive trend during viral period
            else:
                trend = 0.0003  # Normal growth
            
            # Random walk with drift
            daily_return = np.random.normal(trend, volatility)
            current_price = current_price * (1 + daily_return)
            
            # Add some noise for OHLC
            noise = current_price * 0.01
            open_price = current_price + np.random.uniform(-noise, noise)
            high_price = max(open_price, current_price) + abs(np.random.uniform(0, noise))
            low_price = min(open_price, current_price) - abs(np.random.uniform(0, noise))
            close_price = current_price
            
            # Volume (higher during volatile periods)
            base_volume = 2000000 if product['stock_ticker'] == 'YETI' else 500000
            if -30 < days_from_peak < 60:
                volume = int(base_volume * random.uniform(1.5, 2.5))
            else:
                volume = int(base_volume * random.uniform(0.8, 1.2))
            
            all_prices.append({
                'product_id': product['product_id'],
                'price_date': date,
                'open_price': round(open_price, 2),
                'high_price': round(high_price, 2),
                'low_price': round(low_price, 2),
                'close_price': round(close_price, 2),
                'adj_close_price': round(close_price, 2),
                'volume': volume,
                'market_cap': round(close_price * 100000000, 2)  # Approximate market cap
            })
    
    return pd.DataFrame(all_prices)

def main():
    """Generate all data"""
    print("=" * 80)
    print("GENERATING VIRAL PRODUCT HYPE CYCLE DATA")
    print("=" * 80)
    
    # Generate products
    print("\n1. Generating products data...")
    products_df = generate_products_data()
    print(f"   ✓ Created {len(products_df)} products")
    
    # Generate social trends
    print("\n2. Generating Google Trends data...")
    trends_df = generate_social_trends_data(products_df)
    print(f"   ✓ Created {len(trends_df):,} trend records")
    
    # Generate TikTok metrics
    print("\n3. Generating TikTok metrics...")
    tiktok_df = generate_tiktok_metrics(products_df)
    print(f"   ✓ Created {len(tiktok_df):,} TikTok records")
    
    # Generate retail events
    print("\n4. Generating retail events...")
    events_df = generate_retail_events(products_df)
    print(f"   ✓ Created {len(events_df)} retail events")
    
    # Generate stock prices
    print("\n5. Generating stock price data...")
    stock_df = generate_stock_prices(products_df)
    print(f"   ✓ Created {len(stock_df):,} stock price records")
    
    # Save all data
    print("\n6. Saving data to CSV files...")
    products_df.to_csv('products.csv', index=False)
    trends_df.to_csv('social_trends.csv', index=False)
    tiktok_df.to_csv('tiktok_metrics.csv', index=False)
    events_df.to_csv('retail_events.csv', index=False)
    stock_df.to_csv('stock_prices.csv', index=False)
    
    print("   ✓ products.csv")
    print("   ✓ social_trends.csv")
    print("   ✓ tiktok_metrics.csv")
    print("   ✓ retail_events.csv")
    print("   ✓ stock_prices.csv")
    
    # Display summary
    print("\n" + "=" * 80)
    print("DATA GENERATION SUMMARY")
    print("=" * 80)
    print(f"\nProducts: {len(products_df)}")
    print(products_df[['product_name', 'company_name', 'initial_price', 'stock_ticker']])
    
    print(f"\n\nSocial Trends: {len(trends_df):,} records")
    print(f"Date range: {trends_df['trend_date'].min()} to {trends_df['trend_date'].max()}")
    
    print(f"\nTikTok Metrics: {len(tiktok_df):,} records")
    print(f"Total views tracked: {tiktok_df['total_views'].max():,}")
    
    print(f"\nRetail Events: {len(events_df)}")
    print(events_df[['event_date', 'event_type', 'retailer']].head(10))
    
    print(f"\nStock Prices: {len(stock_df):,} records")
    if len(stock_df) > 0:
        print(f"Price range: ${stock_df['close_price'].min():.2f} - ${stock_df['close_price'].max():.2f}")
    
    print("\n" + "=" * 80)
    print("✓ DATA GENERATION COMPLETE!")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Review the CSV files")
    print("2. Load data into SQLite database")
    print("3. Run SQL analysis queries")

if __name__ == "__main__":
    main()
