#!/usr/bin/env python3
"""
Import CSV data into SQLite database
"""

import sqlite3
import pandas as pd

def import_data():
    """Load all CSV files into the database"""
    
    print("=" * 80)
    print("IMPORTING DATA INTO SQLITE DATABASE")
    print("=" * 80)
    
    # Connect to database
    conn = sqlite3.connect('viral_products.db')
    
    # Import products
    print("\n1. Importing products...")
    df = pd.read_csv('products.csv')
    df.to_sql('products', conn, if_exists='append', index=False)
    print(f"   ✓ Loaded {len(df)} products")
    
    # Import social trends
    print("\n2. Importing social trends...")
    df = pd.read_csv('social_trends.csv')
    df.to_sql('social_trends', conn, if_exists='append', index=False)
    print(f"   ✓ Loaded {len(df):,} social trend records")
    
    # Import TikTok metrics
    print("\n3. Importing TikTok metrics...")
    df = pd.read_csv('tiktok_metrics.csv')
    df.to_sql('tiktok_metrics', conn, if_exists='append', index=False)
    print(f"   ✓ Loaded {len(df):,} TikTok metric records")
    
    # Import retail events
    print("\n4. Importing retail events...")
    df = pd.read_csv('retail_events.csv')
    df.to_sql('retail_events', conn, if_exists='append', index=False)
    print(f"   ✓ Loaded {len(df)} retail events")
    
    # Import stock prices
    print("\n5. Importing stock prices...")
    df = pd.read_csv('stock_prices.csv')
    df.to_sql('stock_prices', conn, if_exists='append', index=False)
    print(f"   ✓ Loaded {len(df):,} stock price records")
    
    # Verify data
    print("\n" + "=" * 80)
    print("VERIFYING DATA")
    print("=" * 80)
    
    cursor = conn.cursor()
    
    tables = ['products', 'social_trends', 'tiktok_metrics', 'retail_events', 'stock_prices']
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"{table:20s}: {count:>10,} records")
    
    # Show sample data
    print("\n" + "=" * 80)
    print("SAMPLE DATA - Products")
    print("=" * 80)
    df = pd.read_sql("SELECT * FROM products", conn)
    print(df)
    
    print("\n" + "=" * 80)
    print("SAMPLE DATA - Recent Social Trends")
    print("=" * 80)
    df = pd.read_sql("""
        SELECT p.product_name, st.trend_date, st.search_interest
        FROM social_trends st
        JOIN products p ON st.product_id = p.product_id
        WHERE st.region = 'US'
        ORDER BY st.trend_date DESC
        LIMIT 10
    """, conn)
    print(df)
    
    conn.close()
    
    print("\n" + "=" * 80)
    print("✓ DATA IMPORT COMPLETE!")
    print("=" * 80)
    print("\nDatabase file: viral_products.db")
    print("Ready for SQL analysis!")

if __name__ == "__main__":
    import_data()
