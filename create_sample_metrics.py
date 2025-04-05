import os
import pandas as pd

# Create sample metrics data with our new fields
data = {
    'ticker': ['AAPL', 'MSFT', 'AMZN', 'GOOG', 'NVDA', 'TSLA', 'META', 'JPM', 'V', 'WMT'],
    'sector': ['Technology'] * 10,
    'pe_ratio': [26.3, 34.2, 62.8, 27.1, 45.3, 58.7, 22.5, 12.8, 28.6, 18.4],
    'eps_growth_12m': [0.12, 0.18, 0.09, 0.15, 0.35, 0.07, 0.22, 0.08, 0.11, 0.05],
    'revenue_growth_yoy': [0.08, 0.15, 0.12, 0.11, 0.42, -0.03, 0.18, 0.05, 0.09, 0.03],
    'momentum_3m': [0.15, 0.22, 0.05, 0.12, 0.48, -0.12, 0.25, 0.11, 0.14, 0.08],
    'volatility': [0.18, 0.15, 0.25, 0.17, 0.32, 0.45, 0.28, 0.12, 0.11, 0.08],
    'volatility_3m': [0.18, 0.15, 0.25, 0.17, 0.32, 0.45, 0.28, 0.12, 0.11, 0.08],
    'market_cap': [2.9e12, 2.7e12, 1.6e12, 1.8e12, 2.2e12, 8e11, 1.1e12, 5.2e11, 4.8e11, 4.2e11],
    'price_to_book': [32.5, 12.8, 15.3, 6.1, 28.4, 22.7, 6.2, 1.8, 11.4, 4.9],
    'price_to_sales': [7.8, 11.2, 2.6, 5.9, 25.3, 8.1, 6.3, 3.2, 16.5, 0.7],
    'forward_pe': [25.1, 32.6, 58.2, 24.8, 39.7, 53.2, 18.9, 11.5, 25.3, 17.2],
    'dividend_yield': [0.005, 0.008, 0, 0, 0.001, 0, 0, 0.03, 0.007, 0.014],
    'price_vs_sma_50': [2.5, 1.8, -0.3, 1.1, 12.5, -3.2, 4.1, 0.5, 1.3, 0.7],
    'price_vs_sma_200': [15.2, 22.1, 8.7, 16.2, 85.3, -8.5, 42.8, 12.5, 18.2, 5.3],
    'rsi': [58, 62, 43, 55, 72, 38, 67, 52, 56, 51],
    'earnings_beat_rate': [85, 92, 75, 88, 95, 62, 78, 82, 90, 70],
    'consensus_score': [0.75, 0.82, 0.65, 0.72, 0.88, 0.45, 0.68, 0.58, 0.76, 0.62]
}

# Create DataFrame
df = pd.DataFrame(data)

# Add scoring columns
df['composite_score'] = [0.82, 0.75, 0.58, 0.62, 0.90, -0.32, 0.65, 0.48, 0.52, 0.35]
df['value_score'] = [0.68, 0.62, 0.45, 0.58, 0.72, -0.25, 0.55, 0.65, 0.52, 0.58]
df['growth_score'] = [0.72, 0.78, 0.62, 0.68, 0.95, -0.15, 0.75, 0.55, 0.65, 0.42]
df['risk_score'] = [0.65, 0.72, 0.52, 0.65, 0.65, -0.45, 0.62, 0.68, 0.72, 0.58]
df['analyst_score'] = [0.85, 0.88, 0.72, 0.78, 0.92, -0.25, 0.78, 0.52, 0.62, 0.52]
df['momentum_score'] = [0.75, 0.82, 0.55, 0.68, 0.95, -0.65, 0.82, 0.45, 0.58, 0.48]

# Add additional metrics
df['debt_equity'] = [1.2, 0.5, 0.8, 0.3, 0.2, 1.5, 0.4, 2.5, 1.1, 0.9]
df['peg_ratio'] = [2.1, 1.8, 6.5, 1.7, 1.3, 7.8, 1.0, 1.6, 2.5, 3.2]
df['roe'] = [145.2, 42.5, 25.3, 28.6, 50.2, 22.5, 28.1, 15.8, 42.6, 22.7]
df['ev_to_ebitda'] = [20.5, 21.8, 35.2, 15.6, 62.8, 42.5, 12.5, 10.2, 25.7, 12.1]
df['analyst_rating_trend'] = ['Up', 'Up', 'Stable', 'Up', 'Up', 'Down', 'Up', 'Stable', 'Stable', 'Down']

# Add mock price data
df['current_price'] = [100.0] * 10
df['daily_change'] = [0.0] * 10
df['daily_change_percent'] = [0.0] * 10
df['weekly_change'] = [0.0] * 10
df['weekly_change_percent'] = [0.0] * 10
df['monthly_change'] = [0.0] * 10
df['monthly_change_percent'] = [0.0] * 10

# Add target price data
df['target_high'] = [125, 430, 180, 190, 120, 180, 480, 205, 290, 180]
df['target_low'] = [90, 350, 140, 150, 80, 120, 350, 160, 230, 150]
df['target_mean'] = [110, 390, 160, 170, 100, 150, 410, 180, 260, 165]
df['target_median'] = [105, 385, 155, 165, 95, 145, 405, 175, 255, 160]
df['price_to_target'] = [10.0, 15.0, 5.0, 8.0, 20.0, -5.0, 12.0, 7.0, 9.0, 6.0]

# Add EPS metrics
df['eps_actual'] = [1.52, 2.35, 0.65, 1.44, 4.02, 0.91, 3.85, 3.12, 1.98, 1.77]
df['eps_estimate'] = [1.43, 2.28, 0.58, 1.35, 3.85, 0.98, 3.65, 2.95, 1.90, 1.65]
df['eps_surprise_percent'] = [6.3, 3.1, 12.1, 6.7, 4.4, -7.1, 5.5, 5.8, 4.2, 7.3]

# Add analyst recommendation details
df['analyst_count'] = [42, 38, 45, 36, 40, 44, 35, 28, 32, 25]
df['strong_buy'] = [15, 18, 10, 14, 22, 8, 12, 5, 10, 6]
df['buy'] = [18, 15, 20, 12, 12, 12, 15, 10, 15, 8]
df['hold'] = [8, 4, 12, 8, 4, 14, 7, 10, 6, 9]
df['sell'] = [1, 1, 2, 2, 2, 6, 1, 2, 1, 2]
df['strong_sell'] = [0, 0, 1, 0, 0, 4, 0, 1, 0, 0]

# Create the data directory structure
os.makedirs('src/data', exist_ok=True)
os.makedirs('src/data/output', exist_ok=True)
os.makedirs('src/data/reasoning', exist_ok=True)

# Save to CSV
df.to_csv('src/data/sample_metrics.csv', index=False)
print(f'Created sample metrics file with {len(df)} rows and {len(df.columns)} columns') 