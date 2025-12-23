#!/usr/bin/env python3
"""
Stock Data Collection Script
Downloads historical stock price data for water bottle companies and competitors
Uses yfinance library to access Yahoo Finance data
"""

import pandas as pd
from datetime import datetime, timedelta
import sys

try:
    import yfinance as yf
except ImportError:
    print("Installing yfinance...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "yfinance", "--break-system-packages"])
    import yfinance as yf

# Define companies to track
TICKERS = {
    'YETI': 'YETI Holdings Inc - YETI Tumblers & Coolers',
    'HELE': 'Helen of Troy Ltd - Parent of Hydro Flask',
    'NWL': 'Newell Brands - Stanley parent (pre-acquisition)',
    'TPX': 'Tempur Sealy - Comparable consumer goods',
}

# Date range
START_DATE = '2020-01-01'
END_DATE = datetime.now().strftime('%Y-%m-%d')

def download_stock_data(ticker, name, start_date, end_date):
    """
    Download historical stock data for a given ticker
    
    Args:
        ticker: Stock ticker symbol
        name: Company name/description
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
    
    Returns:
        DataFrame with stock price data
    """
    print(f"\nDownloading {ticker} - {name}")
    print(f"Date range: {start_date} to {end_date}")
    
    try:
        # Download data
        stock = yf.Ticker(ticker)
        df = stock.history(start=start_date, end=end_date)
        
        if df.empty:
            print(f"  WARNING: No data found for {ticker}")
            return None
        
        # Add ticker and company info
        df['ticker'] = ticker
        df['company_name'] = name
        df['date'] = df.index
        
        # Reset index
        df = df.reset_index(drop=True)
        
        # Reorder columns
        df = df[['date', 'ticker', 'company_name', 'Open', 'High', 'Low', 
                'Close', 'Volume']]
        
        print(f"  ✓ Downloaded {len(df)} trading days")
        print(f"  Date range: {df['date'].min()} to {df['date'].max()}")
        print(f"  Latest close: ${df['Close'].iloc[-1]:.2f}")
        
        return df
        
    except Exception as e:
        print(f"  ERROR downloading {ticker}: {e}")
        return None

def calculate_additional_metrics(df):
    """
    Calculate additional financial metrics
    
    Args:
        df: DataFrame with OHLC data
        
    Returns:
        DataFrame with additional metrics
    """
    if df is None or df.empty:
        return df
    
    # Daily returns
    df['daily_return_pct'] = df['Close'].pct_change() * 100
    
    # 7-day and 30-day moving averages
    df['ma_7'] = df['Close'].rolling(window=7).mean()
    df['ma_30'] = df['Close'].rolling(window=30).mean()
    
    # Volatility (30-day rolling standard deviation of returns)
    df['volatility_30d'] = df['daily_return_pct'].rolling(window=30).std()
    
    # Price momentum (% change from 30 days ago)
    df['momentum_30d'] = ((df['Close'] - df['Close'].shift(30)) / df['Close'].shift(30)) * 100
    
    # Volume momentum (current vs 30-day average)
    df['avg_volume_30d'] = df['Volume'].rolling(window=30).mean()
    df['volume_ratio'] = df['Volume'] / df['avg_volume_30d']
    
    return df

def main():
    """Main execution function"""
    
    print("=" * 80)
    print("VIRAL PRODUCT HYPE CYCLE - STOCK DATA COLLECTION")
    print("=" * 80)
    
    all_data = []
    
    # Download data for each ticker
    for ticker, name in TICKERS.items():
        df = download_stock_data(ticker, name, START_DATE, END_DATE)
        if df is not None:
            df = calculate_additional_metrics(df)
            all_data.append(df)
    
    if not all_data:
        print("\n❌ ERROR: No data was downloaded successfully")
        return
    
    # Combine all data
    combined_df = pd.concat(all_data, ignore_index=True)
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total records: {len(combined_df):,}")
    print(f"Tickers collected: {combined_df['ticker'].nunique()}")
    print(f"\nData by ticker:")
    print(combined_df.groupby('ticker').size())
    
    # Save to CSV
    output_file = 'stock_prices_raw.csv'
    combined_df.to_csv(output_file, index=False)
    print(f"\n✓ Data saved to: {output_file}")
    
    # Display sample
    print("\n" + "=" * 80)
    print("SAMPLE DATA (First 5 rows)")
    print("=" * 80)
    print(combined_df.head())
    
    # Display recent data
    print("\n" + "=" * 80)
    print("RECENT DATA (Last 5 rows)")
    print("=" * 80)
    print(combined_df.tail())
    
    # Key statistics
    print("\n" + "=" * 80)
    print("KEY STATISTICS BY TICKER")
    print("=" * 80)
    
    stats = combined_df.groupby('ticker').agg({
        'Close': ['first', 'last', 'min', 'max'],
        'Volume': 'mean',
        'daily_return_pct': ['mean', 'std']
    }).round(2)
    
    print(stats)
    
    # Calculate total returns
    print("\n" + "=" * 80)
    print("TOTAL RETURNS (Start to End)")
    print("=" * 80)
    
    for ticker in combined_df['ticker'].unique():
        ticker_data = combined_df[combined_df['ticker'] == ticker].sort_values('date')
        if len(ticker_data) > 1:
            start_price = ticker_data['Close'].iloc[0]
            end_price = ticker_data['Close'].iloc[-1]
            total_return = ((end_price - start_price) / start_price) * 100
            print(f"{ticker:6s}: {total_return:+7.2f}% (${start_price:.2f} → ${end_price:.2f})")
    
    print("\n" + "=" * 80)
    print("✓ STOCK DATA COLLECTION COMPLETE")
    print("=" * 80)
    
    return combined_df

if __name__ == "__main__":
    df = main()
