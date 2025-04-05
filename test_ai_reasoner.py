import os
import json
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from src.analysis.ai_reasoner import AIReasoner
from src.data.market_data_service import MarketDataService
from src.analysis.scoring_engine import ScoringEngine

# Загружаем переменные окружения
load_dotenv()

def test_ai_reasoner_single_ticker():
    """Тестирование генерации reasoning для одного тикера"""
    # Тестовые данные для одного тикера
    ticker = "AAPL"
    metrics = {
        "ticker": ticker,
        "pe_ratio": 28.5,
        "eps_growth_12m": 15.2,
        "revenue_growth_yoy": 8.1,
        "peg_ratio": 1.5,
        "roe": 28.5,
        "momentum_3m": 12.3,
        "volatility_3m": 18.4,
        "avg_volume_10d": 85000000,
        "debt_equity": 1.2,
        "sentiment_score": 0.75,
        "market_cap": 2800000000000,
        "rank": 1,
        "composite_score": 0.85
    }
    
    # Инициализируем AIReasoner
    reasoner = AIReasoner(reasoning_dir='test_output/reasoning')
    
    # Генерируем обоснование
    print(f"\nТестирование генерации reasoning для одного тикера: {ticker}")
    reasoning = reasoner.generate_reasoning_for_ticker(ticker, metrics, side="long", force_refresh=True)
    
    if reasoning:
        print(f"Сгенерировано обоснование ({len(reasoning)} символов)")
        print("Начало обоснования:")
        print("---")
        print(reasoning[:200] + "..." if len(reasoning) > 200 else reasoning)
        print("---")
        
        # Проверяем наличие файла
        reasoning_file = Path(f"test_output/reasoning/{ticker}.md")
        if reasoning_file.exists():
            print(f"Файл сохранен: {reasoning_file}")
            return True
    
    print("Ошибка при генерации reasoning")
    return False

def test_cached_reasoning():
    """Тестирование кэширования reasoning"""
    # Тестовые данные
    ticker = "AAPL"
    metrics = {
        "ticker": ticker,
        "pe_ratio": 28.5,
        "composite_score": 0.85
    }
    
    # Инициализируем AIReasoner
    reasoner = AIReasoner(reasoning_dir='test_output/reasoning', ttl_days=7)
    
    # Проверяем наличие кэшированного обоснования
    print(f"\nТестирование кэширования reasoning для {ticker}")
    cached = reasoner.get_cached_reasoning(ticker)
    
    if cached:
        print(f"Найдено кэшированное обоснование ({len(cached)} символов)")
        print("Будет использовано существующее обоснование")
    else:
        print(f"Кэшированное обоснование не найдено или устарело, генерируем новое")
        reasoning = reasoner.generate_reasoning_for_ticker(ticker, metrics, side="long")
        if reasoning:
            print(f"Сгенерировано новое обоснование ({len(reasoning)} символов)")
    
    # Пробуем получить обоснование снова (должно быть из кэша)
    reasoning = reasoner.generate_reasoning_for_ticker(ticker, metrics, side="long")
    if reasoning:
        print(f"Получено обоснование ({len(reasoning)} символов)")
        return True
    
    print("Ошибка при получении/генерации reasoning")
    return False

def test_batch_reasoning_with_market_data():
    """Тестирование генерации reasoning для нескольких тикеров из реальных данных"""
    # Получаем данные из MarketDataService
    market_data = MarketDataService()
    
    # Выбираем 3 случайных тикера из S&P500
    tickers = market_data.get_sp500_tickers()[0:3]  # Берем первые 3 для быстроты
    print(f"\nТестирование batch reasoning на тикерах: {', '.join(tickers)}")
    
    # Получаем данные по выбранным тикерам
    all_metrics = []
    for ticker in tickers:
        ticker_data = market_data.get_ticker_data(ticker)
        
        # Объединяем данные из разных категорий
        metrics = {'ticker': ticker}
        
        # Добавляем фундаментальные метрики
        if 'fundamental' in ticker_data:
            metrics.update(ticker_data['fundamental'])
        
        # Добавляем технические метрики
        if 'technical' in ticker_data:
            metrics.update(ticker_data['technical'])
        
        # Добавляем аналитические метрики
        if 'analyst' in ticker_data:
            metrics.update(ticker_data['analyst'])
        
        all_metrics.append(metrics)
    
    # Создаем DataFrame
    df = pd.DataFrame(all_metrics)
    
    # Вычисляем composite_score с помощью ScoringEngine
    engine = ScoringEngine(output_dir='test_output')
    result_df = engine.run(df)
    
    # Инициализируем AIReasoner
    reasoner = AIReasoner(reasoning_dir='test_output/reasoning')
    
    # Получаем список long и short тикеров
    with open('test_output/long_short_selection.json', 'r') as f:
        selection = json.load(f)
    
    # Создаем side_map на основе выбора long/short
    side_map = {}
    for ticker in tickers:
        if ticker in selection['long']:
            side_map[ticker] = 'long'
        elif ticker in selection['short']:
            side_map[ticker] = 'short'
        else:
            side_map[ticker] = 'unknown'
    
    # Генерируем batch reasoning
    scores_df = pd.read_csv('test_output/scoring_results.csv')
    reasonings = reasoner.generate_reasoning_batch(scores_df, side_map=side_map)
    
    if reasonings:
        print(f"Сгенерированы обоснования для {len(reasonings)} из {len(tickers)} тикеров")
        return True
    
    print("Ошибка при генерации batch reasoning")
    return False

def main():
    """Основная функция для тестирования"""
    print("=== Тестирование AIReasoner ===")
    
    # Создаем директорию для выходных данных
    Path('test_output/reasoning').mkdir(exist_ok=True, parents=True)
    
    # Тест 1: Генерация reasoning для одного тикера
    success1 = test_ai_reasoner_single_ticker()
    
    # Тест 2: Проверка кэширования
    success2 = test_cached_reasoning()
    
    # Тест 3: Batch reasoning с реальными данными
    success3 = test_batch_reasoning_with_market_data()
    
    # Итоги тестирования
    print("\n=== Результаты тестирования ===")
    print(f"1. Генерация reasoning для одного тикера: {'Успешно' if success1 else 'Неудача'}")
    print(f"2. Проверка кэширования: {'Успешно' if success2 else 'Неудача'}")
    print(f"3. Batch reasoning с реальными данными: {'Успешно' if success3 else 'Неудача'}")

if __name__ == "__main__":
    main() 