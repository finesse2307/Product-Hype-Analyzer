#!/usr/bin/env python3
"""
Generate visualizations for viral products analysis
Creates charts for presentation and README
"""

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import os

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
colors = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D']

# Create output directory
os.makedirs('visualizations', exist_ok=True)

# Connect to database
conn = sqlite3.connect('viral_products.db')

print("=" * 80)
print("GENERATING VISUALIZATIONS")
print("=" * 80)

# ============================================================================
# Chart 1: Search Interest Over Time (Main Trend Lines)
# ============================================================================
print("\n1. Creating trend lines chart...")

query = """
SELECT 
    p.product_name,
    st.trend_date,
    st.search_interest
FROM social_trends st
JOIN products p ON st.product_id = p.product_id
WHERE st.region = 'US'
    AND st.trend_date >= '2022-01-01'
ORDER BY st.trend_date, p.product_name
"""

df = pd.read_sql(query, conn)
df['trend_date'] = pd.to_datetime(df['trend_date'])

fig, ax = plt.subplots(figsize=(14, 7))

for i, product in enumerate(df['product_name'].unique()):
    product_data = df[df['product_name'] == product]
    ax.plot(product_data['trend_date'], 
            product_data['search_interest'], 
            label=product, 
            linewidth=2.5,
            color=colors[i],
            alpha=0.8)

ax.set_xlabel('Date', fontsize=12, fontweight='bold')
ax.set_ylabel('Search Interest (0-100)', fontsize=12, fontweight='bold')
ax.set_title('Viral Product Search Interest Over Time', fontsize=16, fontweight='bold', pad=20)
ax.legend(loc='upper left', fontsize=11, framealpha=0.9)
ax.grid(True, alpha=0.3)

# Format x-axis
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
plt.xticks(rotation=45)

plt.tight_layout()
plt.savefig('visualizations/01_trend_lines.png', dpi=300, bbox_inches='tight')
print("   ✓ Saved: visualizations/01_trend_lines.png")
plt.close()

# ============================================================================
# Chart 2: Peak Comparison (Bar Chart)
# ============================================================================
print("\n2. Creating peak comparison chart...")

query = """
WITH peaks AS (
    SELECT 
        p.product_name,
        MAX(st.search_interest) as peak_interest,
        AVG(st.search_interest) as avg_interest
    FROM social_trends st
    JOIN products p ON st.product_id = p.product_id
    WHERE st.region = 'US'
    GROUP BY p.product_name
)
SELECT * FROM peaks ORDER BY peak_interest DESC
"""

df = pd.read_sql(query, conn)

fig, ax = plt.subplots(figsize=(10, 6))

x = range(len(df))
width = 0.35

bars1 = ax.bar([i - width/2 for i in x], df['peak_interest'], width, 
               label='Peak Interest', color='#2E86AB', alpha=0.8)
bars2 = ax.bar([i + width/2 for i in x], df['avg_interest'], width,
               label='Average Interest', color='#F18F01', alpha=0.8)

ax.set_xlabel('Product', fontsize=12, fontweight='bold')
ax.set_ylabel('Search Interest', fontsize=12, fontweight='bold')
ax.set_title('Peak vs Average Search Interest by Product', fontsize=16, fontweight='bold', pad=20)
ax.set_xticks(x)
ax.set_xticklabels(df['product_name'], rotation=15, ha='right')
ax.legend(fontsize=11)
ax.grid(True, alpha=0.3, axis='y')

# Add value labels on bars
for bars in [bars1, bars2]:
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}',
                ha='center', va='bottom', fontsize=9)

plt.tight_layout()
plt.savefig('visualizations/02_peak_comparison.png', dpi=300, bbox_inches='tight')
print("   ✓ Saved: visualizations/02_peak_comparison.png")
plt.close()

# ============================================================================
# Chart 3: Market Share Evolution (Stacked Area)
# ============================================================================
print("\n3. Creating market share evolution chart...")

query = """
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
    m.avg_interest,
    ROUND(m.avg_interest * 100.0 / t.total, 2) as market_share_pct
FROM monthly m
JOIN totals t ON m.month = t.month
ORDER BY m.month, m.product_name
"""

df = pd.read_sql(query, conn)
pivot_df = df.pivot(index='month', columns='product_name', values='market_share_pct')

fig, ax = plt.subplots(figsize=(14, 7))

ax.stackplot(range(len(pivot_df)), 
             [pivot_df[col].values for col in pivot_df.columns],
             labels=pivot_df.columns,
             colors=colors,
             alpha=0.8)

ax.set_xlabel('Month', fontsize=12, fontweight='bold')
ax.set_ylabel('Market Share (%)', fontsize=12, fontweight='bold')
ax.set_title('Market Share Evolution (2023-2024)', fontsize=16, fontweight='bold', pad=20)
ax.set_xticks(range(0, len(pivot_df), 2))
ax.set_xticklabels(pivot_df.index[::2], rotation=45, ha='right')
ax.legend(loc='upper left', fontsize=11, framealpha=0.9)
ax.grid(True, alpha=0.3, axis='y')
ax.set_ylim(0, 100)

plt.tight_layout()
plt.savefig('visualizations/03_market_share.png', dpi=300, bbox_inches='tight')
print("   ✓ Saved: visualizations/03_market_share.png")
plt.close()

# ============================================================================
# Chart 4: Retail Event Impact (Before/After)
# ============================================================================
print("\n4. Creating retail event impact chart...")

query = """
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
    WHERE st.region = 'US' AND ABS(days_offset) <= 7
)
SELECT 
    product_name || ' - ' || event_type || ' (' || retailer || ')' as event_label,
    ROUND(AVG(CASE WHEN days_offset < 0 THEN search_interest END), 1) as before_event,
    ROUND(AVG(CASE WHEN days_offset > 0 THEN search_interest END), 1) as after_event,
    ROUND((AVG(CASE WHEN days_offset > 0 THEN search_interest END) - 
           AVG(CASE WHEN days_offset < 0 THEN search_interest END)) * 100.0 /
           AVG(CASE WHEN days_offset < 0 THEN search_interest END), 1) as lift_pct
FROM events
GROUP BY event_id, product_name, event_type, retailer
HAVING before_event IS NOT NULL AND after_event IS NOT NULL
ORDER BY lift_pct DESC
LIMIT 6
"""

df = pd.read_sql(query, conn)

fig, ax = plt.subplots(figsize=(12, 8))

x = range(len(df))
width = 0.35

bars1 = ax.barh([i - width/2 for i in x], df['before_event'], width,
                label='Before Event', color='#95B8D1', alpha=0.8)
bars2 = ax.barh([i + width/2 for i in x], df['after_event'], width,
                label='After Event', color='#2E86AB', alpha=0.8)

ax.set_ylabel('Event', fontsize=12, fontweight='bold')
ax.set_xlabel('Search Interest', fontsize=12, fontweight='bold')
ax.set_title('Retail Event Impact on Search Interest', fontsize=16, fontweight='bold', pad=20)
ax.set_yticks(x)
ax.set_yticklabels([label[:40] + '...' if len(label) > 40 else label 
                     for label in df['event_label']], fontsize=9)
ax.legend(fontsize=11)
ax.grid(True, alpha=0.3, axis='x')

# Add lift percentage labels
for i, (before, after, lift) in enumerate(zip(df['before_event'], df['after_event'], df['lift_pct'])):
    ax.text(max(before, after) + 2, i, f'+{lift}%', 
            va='center', fontsize=9, fontweight='bold', color='green' if lift > 0 else 'red')

plt.tight_layout()
plt.savefig('visualizations/04_event_impact.png', dpi=300, bbox_inches='tight')
print("   ✓ Saved: visualizations/04_event_impact.png")
plt.close()

# ============================================================================
# Chart 5: TikTok Engagement Trends
# ============================================================================
print("\n5. Creating TikTok engagement chart...")

query = """
SELECT 
    p.product_name,
    strftime('%Y-%m', tm.metric_date) as month,
    AVG(tm.avg_engagement_rate) as avg_engagement,
    AVG(tm.sentiment_score) as avg_sentiment
FROM tiktok_metrics tm
JOIN products p ON tm.product_id = p.product_id
WHERE tm.metric_date >= '2023-01-01'
GROUP BY p.product_name, month
ORDER BY month, p.product_name
"""

df = pd.read_sql(query, conn)

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))

# Engagement rate
for i, product in enumerate(df['product_name'].unique()):
    product_data = df[df['product_name'] == product]
    ax1.plot(product_data['month'], 
             product_data['avg_engagement'], 
             label=product,
             marker='o',
             linewidth=2.5,
             color=colors[i],
             alpha=0.8)

ax1.set_xlabel('Month', fontsize=12, fontweight='bold')
ax1.set_ylabel('Engagement Rate (%)', fontsize=12, fontweight='bold')
ax1.set_title('TikTok Engagement Rate Over Time', fontsize=14, fontweight='bold', pad=15)
ax1.legend(loc='best', fontsize=10)
ax1.grid(True, alpha=0.3)
ax1.tick_params(axis='x', rotation=45)

# Sentiment score
for i, product in enumerate(df['product_name'].unique()):
    product_data = df[df['product_name'] == product]
    ax2.plot(product_data['month'], 
             product_data['avg_sentiment'], 
             label=product,
             marker='s',
             linewidth=2.5,
             color=colors[i],
             alpha=0.8)

ax2.set_xlabel('Month', fontsize=12, fontweight='bold')
ax2.set_ylabel('Sentiment Score', fontsize=12, fontweight='bold')
ax2.set_title('TikTok Sentiment Score Over Time', fontsize=14, fontweight='bold', pad=15)
ax2.legend(loc='best', fontsize=10)
ax2.grid(True, alpha=0.3)
ax2.tick_params(axis='x', rotation=45)
ax2.axhline(y=0, color='gray', linestyle='--', linewidth=1, alpha=0.5)

plt.tight_layout()
plt.savefig('visualizations/05_tiktok_trends.png', dpi=300, bbox_inches='tight')
print("   ✓ Saved: visualizations/05_tiktok_trends.png")
plt.close()

# ============================================================================
# Chart 6: Weekly Growth Heatmap
# ============================================================================
print("\n6. Creating growth momentum heatmap...")

query = """
WITH weekly AS (
    SELECT 
        p.product_name,
        st.trend_date,
        st.search_interest,
        LAG(st.search_interest, 7) OVER (PARTITION BY p.product_id ORDER BY st.trend_date) as prev_week
    FROM social_trends st
    JOIN products p ON st.product_id = p.product_id
    WHERE st.region = 'US' AND st.trend_date >= '2023-01-01'
)
SELECT 
    product_name,
    strftime('%Y-%W', trend_date) as week,
    AVG((search_interest - prev_week) * 100.0 / NULLIF(prev_week, 0)) as wow_growth
FROM weekly
WHERE prev_week IS NOT NULL AND prev_week > 0
GROUP BY product_name, week
ORDER BY week, product_name
"""

df = pd.read_sql(query, conn)
df['wow_growth'] = df['wow_growth'].round(1)
pivot_df = df.pivot(index='product_name', columns='week', values='wow_growth')

# Take every 4th week for readability
pivot_df = pivot_df.iloc[:, ::4]

fig, ax = plt.subplots(figsize=(16, 6))

im = ax.imshow(pivot_df.values, cmap='RdYlGn', aspect='auto', vmin=-50, vmax=50)

ax.set_xticks(range(len(pivot_df.columns)))
ax.set_yticks(range(len(pivot_df.index)))
ax.set_xticklabels(pivot_df.columns, rotation=45, ha='right', fontsize=8)
ax.set_yticklabels(pivot_df.index, fontsize=11)

ax.set_xlabel('Week', fontsize=12, fontweight='bold')
ax.set_ylabel('Product', fontsize=12, fontweight='bold')
ax.set_title('Week-over-Week Growth Heatmap (%)', fontsize=16, fontweight='bold', pad=20)

cbar = plt.colorbar(im, ax=ax)
cbar.set_label('Growth %', fontsize=11, fontweight='bold')

plt.tight_layout()
plt.savefig('visualizations/06_growth_heatmap.png', dpi=300, bbox_inches='tight')
print("   ✓ Saved: visualizations/06_growth_heatmap.png")
plt.close()

# ============================================================================
# Summary Dashboard
# ============================================================================
print("\n7. Creating summary dashboard...")

fig = plt.figure(figsize=(16, 10))
gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)

# Get summary stats
query = """
SELECT 
    product_name,
    MAX(search_interest) as peak,
    ROUND(AVG(search_interest), 1) as avg
FROM social_trends st
JOIN products p ON st.product_id = p.product_id
WHERE region = 'US'
GROUP BY product_name
ORDER BY peak DESC
"""
summary_df = pd.read_sql(query, conn)

# Top left - Peak comparison
ax1 = fig.add_subplot(gs[0, 0])
ax1.bar(summary_df['product_name'], summary_df['peak'], color=colors, alpha=0.8)
ax1.set_title('Peak Search Interest', fontsize=12, fontweight='bold')
ax1.set_ylabel('Interest')
ax1.tick_params(axis='x', rotation=15)
ax1.grid(True, alpha=0.3, axis='y')

# Top right - Market share pie (latest month)
ax2 = fig.add_subplot(gs[0, 1])
query = """
WITH latest AS (
    SELECT 
        p.product_name,
        AVG(st.search_interest) as avg_interest
    FROM social_trends st
    JOIN products p ON st.product_id = p.product_id
    WHERE st.region = 'US' 
        AND st.trend_date >= DATE('2024-12-01')
    GROUP BY p.product_name
)
SELECT * FROM latest
"""
pie_df = pd.read_sql(query, conn)
ax2.pie(pie_df['avg_interest'], labels=pie_df['product_name'], autopct='%1.1f%%',
        colors=colors, startangle=90)
ax2.set_title('Current Market Share (Dec 2024)', fontsize=12, fontweight='bold')

# Middle - Trend lines
ax3 = fig.add_subplot(gs[1, :])
query = """
SELECT 
    p.product_name,
    st.trend_date,
    st.search_interest
FROM social_trends st
JOIN products p ON st.product_id = p.product_id
WHERE st.region = 'US' AND st.trend_date >= '2023-01-01'
ORDER BY st.trend_date
"""
trend_df = pd.read_sql(query, conn)
trend_df['trend_date'] = pd.to_datetime(trend_df['trend_date'])

for i, product in enumerate(trend_df['product_name'].unique()):
    product_data = trend_df[trend_df['product_name'] == product]
    ax3.plot(product_data['trend_date'], product_data['search_interest'], 
             label=product, linewidth=2, color=colors[i], alpha=0.8)

ax3.set_title('Search Interest Trends (2023-2024)', fontsize=12, fontweight='bold')
ax3.set_ylabel('Interest')
ax3.legend(loc='upper left', fontsize=9)
ax3.grid(True, alpha=0.3)
ax3.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45)

# Bottom left - Event impact
ax4 = fig.add_subplot(gs[2, 0])
query = """
SELECT 
    CASE 
        WHEN event_type = 'Sellout' THEN 'Sellouts'
        WHEN event_type = 'Launch' THEN 'Launches'
        WHEN event_type = 'Collab' THEN 'Collaborations'
        ELSE event_type
    END as event_category,
    COUNT(*) as count
FROM retail_events
GROUP BY event_category
"""
event_df = pd.read_sql(query, conn)
ax4.barh(event_df['event_category'], event_df['count'], color='#2E86AB', alpha=0.8)
ax4.set_title('Retail Events by Type', fontsize=12, fontweight='bold')
ax4.set_xlabel('Count')
ax4.grid(True, alpha=0.3, axis='x')

# Bottom right - Key metrics
ax5 = fig.add_subplot(gs[2, 1])
ax5.axis('off')

# Calculate key metrics
query = """
WITH weekly AS (
    SELECT 
        (search_interest - LAG(search_interest, 7) OVER (PARTITION BY product_id ORDER BY trend_date)) * 100.0 / 
        LAG(search_interest, 7) OVER (PARTITION BY product_id ORDER BY trend_date) as growth
    FROM social_trends
    WHERE region = 'US' AND search_interest > 0
)
SELECT ROUND(MAX(growth), 0) as max_wow_growth 
FROM weekly
WHERE growth IS NOT NULL
"""
max_growth = pd.read_sql(query, conn)['max_wow_growth'].values[0]

metrics_text = f"""
KEY FINDINGS

• Peak Interest: {summary_df['peak'].max()}/100
  ({summary_df.iloc[0]['product_name']})

• Max Weekly Growth: {max_growth}%

• Total Events Tracked: {event_df['count'].sum()}

• Products Analyzed: 4

• Date Range: 2020-2024

• Total Records: 12,011
"""

ax5.text(0.1, 0.9, metrics_text, transform=ax5.transAxes,
         fontsize=11, verticalalignment='top', fontfamily='monospace',
         bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

fig.suptitle('Viral Product Hype Cycle Analysis - Dashboard', 
             fontsize=18, fontweight='bold', y=0.98)

plt.savefig('visualizations/00_dashboard.png', dpi=300, bbox_inches='tight')
print("   ✓ Saved: visualizations/00_dashboard.png")
plt.close()

conn.close()

print("\n" + "=" * 80)
print("✓ ALL VISUALIZATIONS GENERATED!")
print("=" * 80)
print("\nCreated 7 visualizations in 'visualizations/' directory:")
print("  1. 00_dashboard.png - Summary dashboard")
print("  2. 01_trend_lines.png - Search interest over time")
print("  3. 02_peak_comparison.png - Peak vs average interest")
print("  4. 03_market_share.png - Market share evolution")
print("  5. 04_event_impact.png - Retail event analysis")
print("  6. 05_tiktok_trends.png - TikTok engagement & sentiment")
print("  7. 06_growth_heatmap.png - Week-over-week growth patterns")

print("\nNext: Creating PowerPoint presentation...")
