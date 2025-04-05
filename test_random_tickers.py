#!/usr/bin/env python
import os
import json
import time
import random
from pathlib import Path
from dotenv import load_dotenv
from src.data.market_data_service import MarketDataService

# Загрузка переменных окружения из .env файла
load_dotenv()

def print_ticker_data(data, detailed=False):
    ticker = data['ticker']
    print(f"\n{'=' * 50}")
    print(f"Данные для тикера {ticker}")
    print(f"{'=' * 50}")
    
    # Фундаментальные метрики
    fundamental = data['fundamental']
    print("\nФундаментальные метрики (Finnhub):")
    if fundamental:
        print(f"PE Ratio: {fundamental.get('pe_ratio')}")
        print(f"EPS Growth (12m): {fundamental.get('eps_growth_12m')}") # Рассчитывается из квартальных отчетов
        print(f"Revenue Growth (YoY): {fundamental.get('revenue_growth_yoy')}") # Рассчитывается из квартальных отчетов
        print(f"Debt/Equity: {fundamental.get('debt_equity')}")
        print(f"ROE: {fundamental.get('roe')}")
        print(f"PEG Ratio: {fundamental.get('peg_ratio')}")
        print(f"Market Cap: {fundamental.get('market_cap'):,.0f}" if fundamental.get('market_cap') else "Market Cap: N/A")
        print(f"Analyst Rating Trend: {fundamental.get('analyst_rating_trend')}")
    else:
        print("Фундаментальные данные недоступны")
    
    # Технические метрики
    technical = data['technical']
    print("\nТехнические метрики (Finnhub свечи):")
    if technical:
        print(f"Momentum (3m): {technical.get('momentum_3m')}%")
        print(f"Volatility (3m): {technical.get('volatility_3m')}%")
        print(f"Avg Volume (10d): {technical.get('avg_volume_10d'):,.0f}")
        print(f"Price Change YTD: {technical.get('price_change_ytd')}%" if technical.get('price_change_ytd') else "Price Change YTD: N/A")
        print(f"Latest Price: ${technical.get('latest_price')}")
    else:
        print("Технические данные недоступны")
    
    # Аналитические данные
    analyst = data.get('analyst', {})
    print("\nАналитические оценки (Finnhub):")
    if analyst:
        # Целевые цены
        print(f"Price Target Mean: ${analyst.get('target_mean')}" if analyst.get('target_mean') else "Price Target Mean: N/A")
        print(f"Price Target Range: ${analyst.get('target_low')} - ${analyst.get('target_high')}" if analyst.get('target_low') and analyst.get('target_high') else "Price Target Range: N/A")
        
        # Консенсус
        if analyst.get('consensus_score') is not None:
            consensus = analyst.get('consensus_score')
            label = "Нейтрально"
            if consensus > 0.5:
                label = "Сильно покупать"
            elif consensus > 0.2:
                label = "Покупать"
            elif consensus < -0.5:
                label = "Сильно продавать"
            elif consensus < -0.2:
                label = "Продавать"
            print(f"Analyst Consensus: {label} ({consensus:.2f})")
            
            if analyst.get('total_recommendations'):
                print(f"Based on {analyst.get('total_recommendations')} analysts")
            
            if analyst.get('rating_trend') is not None:
                trend = "стабильный"
                if analyst.get('rating_trend') > 0.1:
                    trend = "улучшается"
                elif analyst.get('rating_trend') < -0.1:
                    trend = "ухудшается"
                print(f"Rating Trend: {trend}")
        
        # EPS surprises
        if analyst.get('eps_actual') is not None and analyst.get('eps_estimate') is not None:
            print(f"Last EPS: Actual ${analyst.get('eps_actual')} vs Estimate ${analyst.get('eps_estimate')}")
            if analyst.get('eps_surprise_pct') is not None:
                surprise = analyst.get('eps_surprise_pct')
                direction = "выше" if surprise > 0 else "ниже"
                print(f"EPS Surprise: {abs(surprise):.2f}% {direction} ожиданий")
    else:
        print("Аналитические данные недоступны")
    
    # Данные недоступны?
    if 'no_data' in data and data['no_data']:
        print("\n⚠️ Данные недоступны ⚠️")
    
    updated_at = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(data['updated_at']))
    print(f"\nПоследнее обновление: {updated_at}")

# Функция для загрузки S&P500 тикеров из кэша
def load_sp500_tickers():
    cache_file = Path(".cache") / "sp500_201_300.json"
    if cache_file.exists():
        with open(cache_file, 'r') as f:
            data = json.load(f)
            return data['tickers']
    else:
        # Если кэш не найден, вернем предопределенный список
        return [
            "FTV", "FOXA", "FOX", "BEN", "FCX", "GRMN", "IT", "GE", "GEHC", "GEV", 
            "GEN", "GNRC", "GD", "GIS", "GM", "GPC", "GILD", "GPN", "GL", "GDDY"
        ]

# Создание сервиса
print("Инициализация MarketDataService с использованием Finnhub API...")
cache_dir = Path(".cache")
service = MarketDataService(cache_dir=cache_dir)

# Загрузка списка тикеров S&P500
all_tickers = load_sp500_tickers()
print(f"Загружено {len(all_tickers)} тикеров из S&P500 (ранги 201-300)")

# Выбор 5 случайных тикеров
random_tickers = random.sample(all_tickers, 5)
print(f"\nВыбрано 5 случайных тикеров для тестирования: {', '.join(random_tickers)}")

# Проверка и подготовка директории для кэша
if not cache_dir.exists():
    cache_dir.mkdir(parents=True)

# Получение данных для каждого тикера
for ticker in random_tickers:
    try:
        print(f"\nПолучение и расчет данных для {ticker}...")
        ticker_data = service.get_ticker_data(ticker)
        print_ticker_data(ticker_data)
        
        # Проверяем наличие рассчитанных метрик роста
        fundamental = ticker_data['fundamental']
        if fundamental:
            if fundamental.get('eps_growth_12m') is not None:
                print(f"✅ EPS Growth успешно рассчитан для {ticker}")
            else:
                print(f"❌ EPS Growth не удалось рассчитать для {ticker}")
                
            if fundamental.get('revenue_growth_yoy') is not None:
                print(f"✅ Revenue Growth успешно рассчитан для {ticker}")
            else:
                print(f"❌ Revenue Growth не удалось рассчитать для {ticker}")
        else:
            print(f"❌ Фундаментальные данные недоступны для {ticker}")
            
    except Exception as e:
        print(f"❌ Ошибка при получении данных для {ticker}: {e}")

print("\nТестирование завершено!") 