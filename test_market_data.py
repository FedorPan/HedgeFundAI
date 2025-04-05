#!/usr/bin/env python
import os
import json
import time
from pathlib import Path
from dotenv import load_dotenv
from src.data.market_data_service import MarketDataService

# Загрузка переменных окружения из .env файла
load_dotenv()

# Функция для форматирования вывода данных
def print_ticker_data(data, detailed=False):
    ticker = data['ticker']
    print(f"\n{'=' * 50}")
    print(f"Данные для тикера {ticker}")
    print(f"{'=' * 50}")
    
    # Фундаментальные метрики
    fundamental = data['fundamental']
    print("\nФундаментальные метрики:")
    print(f"PE Ratio: {fundamental.get('pe_ratio')}")
    print(f"EPS Growth (12m): {fundamental.get('eps_growth_12m')}")
    print(f"Revenue Growth (YoY): {fundamental.get('revenue_growth_yoy')}")
    print(f"Debt/Equity: {fundamental.get('debt_equity')}")
    print(f"ROE: {fundamental.get('roe')}")
    print(f"PEG Ratio: {fundamental.get('peg_ratio')}")
    print(f"Market Cap: {fundamental.get('market_cap'):,.0f}" if fundamental.get('market_cap') else "Market Cap: N/A")
    print(f"Analyst Rating Trend: {fundamental.get('analyst_rating_trend')}")
    
    # Технические метрики
    technical = data['technical']
    print("\nТехнические метрики (15-мин задержка):")
    print(f"Momentum (3m): {technical.get('momentum_3m')}%")
    print(f"Volatility (3m): {technical.get('volatility_3m')}%")
    print(f"Avg Volume (10d): {technical.get('avg_volume_10d'):,.0f}")
    print(f"Price Change YTD: {technical.get('price_change_ytd')}%" if technical.get('price_change_ytd') else "Price Change YTD: N/A")
    print(f"Latest Price: ${technical.get('latest_price')}")
    
    # Сентимент
    sentiment = data['sentiment']
    print("\nСентимент (симуляция):")
    print(f"Sentiment Score: {sentiment.get('sentiment_score')}")
    print(f"News Mentions: {sentiment.get('news_mentions')}")
    
    # Является ли данные моковыми
    if 'is_mock_data' in data and data['is_mock_data']:
        print("\n⚠️ Используются моковые данные ⚠️")
    
    updated_at = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(data['updated_at']))
    print(f"\nПоследнее обновление: {updated_at}")

# Создание сервиса
cache_dir = Path(".cache")
service = MarketDataService(cache_dir=cache_dir)

# Получение списка тикеров S&P500 (позиции 201-300)
tickers = service.get_sp500_tickers(start_rank=201, end_rank=300)
print(f"Получено {len(tickers)} тикеров: {', '.join(tickers[:10])}...")

# Тест 1: Получение данных для нескольких тикеров
test_tickers = tickers[:5]  # Берем первые 5 тикеров для теста
print(f"\nТестирование получения данных для тикеров: {', '.join(test_tickers)}")

for ticker in test_tickers:
    try:
        ticker_data = service.get_ticker_data(ticker)
        print_ticker_data(ticker_data)
    except Exception as e:
        print(f"Ошибка при получении данных для {ticker}: {e}")

# Тест 2: Принудительное обновление кэша
print("\nТестирование принудительного обновления кэша")
if test_tickers:
    refresh_ticker = test_tickers[0]
    print(f"Обновление данных для {refresh_ticker}...")
    ticker_data = service.get_ticker_data(refresh_ticker, force_refresh=True)
    print_ticker_data(ticker_data)

# Тест 3: Проверка получения данных через кэш
print("\nТестирование получения данных через кэш")
if test_tickers:
    cache_ticker = test_tickers[0]
    start_time = time.time()
    ticker_data = service.get_ticker_data(cache_ticker)
    elapsed = time.time() - start_time
    print(f"Время получения данных из кэша: {elapsed:.4f} секунд")
    
# Тест 4: Получение данных для известного тикера вне списка
print("\nТестирование получения данных для известного тикера вне списка")
extra_ticker = "AAPL"
ticker_data = service.get_ticker_data(extra_ticker)
print_ticker_data(ticker_data)

print("\nТестирование завершено!") 