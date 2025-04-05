import os
import json
import random
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from src.data.market_data_service import MarketDataService
from src.analysis.scoring_engine import ScoringEngine
from src.analysis.ai_reasoner import AIReasoner

# Загружаем переменные окружения
load_dotenv()

def load_tickers_from_cache():
    """Загружает тикеры из кэша SP500"""
    cache_file = Path('.cache/sp500_201_300.json')
    
    if not cache_file.exists():
        raise FileNotFoundError(f"Файл кэша {cache_file} не найден")
    
    with open(cache_file, 'r') as f:
        data = json.load(f)
        tickers = data['tickers']
        print(f"Загружено {len(tickers)} тикеров из кэша SP500")
        return tickers

def check_cached_tickers():
    """Возвращает список тикеров, для которых есть кэшированные данные"""
    cache_dir = Path('.cache')
    if not cache_dir.exists():
        return []
        
    cached_tickers = []
    for file in cache_dir.glob('*.json'):
        ticker = file.stem
        if ticker != 'sp500_201_300' and len(ticker) <= 5:  # Исключаем файл sp500 и другие системные
            cached_tickers.append(ticker)
            
    return cached_tickers

def main():
    """Основная функция для тестирования"""
    # Загружаем тикеры из кэша
    tickers = load_tickers_from_cache()
    
    # Проверяем, для каких тикеров у нас уже есть кэшированные данные
    cached_tickers = check_cached_tickers()
    print(f"Найдено {len(cached_tickers)} тикеров с кэшированными данными")
    
    # Если у нас достаточно кэшированных тикеров, используем их вместо случайных
    sample_tickers = []
    if len(cached_tickers) >= 5:
        sample_tickers = random.sample(cached_tickers, 5)
        print("Используем тикеры из кэша для ускорения тестирования")
    else:
        sample_tickers = random.sample(tickers, 5)
        
    print(f"Выбрано 5 случайных тикеров: {', '.join(sample_tickers)}")
    print("Примечание: В реальном режиме будут использоваться все 100 тикеров из S&P500 (ранги 201-300)")
    
    # Инициализируем MarketDataService для получения данных
    market_data = MarketDataService()
    
    # Создаем DataFrame для хранения всех данных
    all_metrics = []
    
    # Получаем данные по каждому тикеру
    for ticker in sample_tickers:
        print(f"\nПолучение данных для {ticker}...")
        ticker_data = market_data.get_ticker_data(ticker)
        
        # Объединяем данные из разных категорий
        metrics = {
            'ticker': ticker
        }
        
        # Добавляем фундаментальные метрики
        if 'fundamental' in ticker_data:
            metrics.update(ticker_data['fundamental'])
        
        # Добавляем технические метрики
        if 'technical' in ticker_data:
            metrics.update(ticker_data['technical'])
        
        # Добавляем аналитические метрики
        if 'analyst' in ticker_data:
            metrics.update(ticker_data['analyst'])
            
            # Добавляем consensus_score отдельно, если есть
            if 'consensus_score' in ticker_data['analyst']:
                metrics['consensus_score'] = ticker_data['analyst']['consensus_score']
        
        all_metrics.append(metrics)
        print(f"Данные для {ticker} получены")
    
    # Создаем DataFrame из всех метрик
    df = pd.DataFrame(all_metrics)
    print(f"\nСоздан DataFrame с {len(df)} строками и {len(df.columns)} столбцами")
    
    # Выводим список полученных метрик
    print("\nДоступные метрики:")
    for col in df.columns:
        print(f"- {col}")
    
    # Инициализируем ScoringEngine с настройками как в реальном режиме
    engine = ScoringEngine(output_dir='test_output', top_n=5)
    
    # Запускаем скоринг
    print("\nЗапуск скоринга...")
    result = engine.run(df)
    
    # Выводим результаты скоринга
    print("\n=== Результаты скоринга ===")
    scores_df = pd.read_csv('test_output/scoring_results.csv')
    
    # Выводим основные метрики и скоры для каждого тикера
    for ticker in sample_tickers:
        ticker_row = scores_df[scores_df['ticker'] == ticker]
        if not ticker_row.empty:
            print(f"\n{ticker}:")
            
            # Фундаментальные метрики
            print("Фундаментальные метрики:")
            for metric in ['pe_ratio', 'eps_growth_12m', 'revenue_growth_yoy', 'debt_equity', 'roe', 'market_cap']:
                if metric in ticker_row.columns and not pd.isna(ticker_row[metric].values[0]):
                    print(f"  {metric}: {ticker_row[metric].values[0]:.2f}")
            
            # Технические метрики
            print("Технические метрики:")
            for metric in ['momentum_3m', 'volatility_3m', 'latest_price']:
                if metric in ticker_row.columns and not pd.isna(ticker_row[metric].values[0]):
                    print(f"  {metric}: {ticker_row[metric].values[0]:.2f}")
            
            # Аналитические метрики
            print("Аналитические метрики:")
            for metric in ['consensus_score', 'target_mean']:
                if metric in ticker_row.columns and not pd.isna(ticker_row[metric].values[0]):
                    print(f"  {metric}: {ticker_row[metric].values[0]:.2f}")
            
            # Скоры
            print("Скоры:")
            for score in ['value_score', 'growth_score', 'risk_score', 'analyst_score', 'momentum_score', 'composite_score']:
                if score in ticker_row.columns:
                    print(f"  {score}: {ticker_row[score].values[0]:.4f}")
    
    # Выводим рейтинг тикеров по composite_score
    print("\n=== Рейтинг тикеров по composite_score ===")
    ranked_tickers = scores_df.sort_values('composite_score', ascending=False)
    for i, (_, row) in enumerate(ranked_tickers.iterrows(), 1):
        print(f"{i}. {row['ticker']} - composite_score: {row['composite_score']:.4f}")
    
    # Выводим рекомендуемые long/short позиции (для 5 тикеров они будут совпадать)
    with open('test_output/long_short_selection.json', 'r') as f:
        selection = json.load(f)
        
    print("\nРекомендуемые позиции (в тесте на 5 тикерах списки совпадают):")
    print(f"Long (покупать): {', '.join(selection['long'])}")
    print(f"Short (продавать): {', '.join(selection['short'])}")
    
    # Генерируем инвестиционные обоснования с помощью AIReasoner
    print("\n=== Генерация инвестиционных обоснований ===")
    
    # Проверяем наличие OPENAI_API_KEY
    if not os.environ.get('OPENAI_API_KEY'):
        print("API ключ OpenAI не найден. Генерация обоснований недоступна.")
        return
    
    # Инициализируем AIReasoner
    reasoner = AIReasoner(reasoning_dir='test_output/reasoning')
    
    # Создаем side_map на основе selection
    side_map = {}
    for ticker in sample_tickers:
        if ticker in selection['long']:
            side_map[ticker] = 'long'
        else:
            side_map[ticker] = 'short'
    
    # Добавляем rank в DataFrame для использования в промпте
    for i, ticker in enumerate(ranked_tickers['ticker']):
        scores_df.loc[scores_df['ticker'] == ticker, 'rank'] = i + 1
    
    # Оставляем только наши тестовые тикеры для генерации обоснований
    test_df = scores_df[scores_df['ticker'].isin(sample_tickers)]
    
    # Генерируем обоснования для наших тикеров
    print("Генерация обоснований для тикеров...")
    reasonings = reasoner.generate_reasoning_batch(test_df, side_map=side_map)
    
    # Выводим сгенерированные обоснования
    if reasonings:
        print(f"\nСгенерированы обоснования для {len(reasonings)} тикеров:")
        for ticker, text in reasonings.items():
            print(f"\n--- Обоснование для {ticker} ({side_map[ticker]}) ---")
            print(text[:300] + "..." if len(text) > 300 else text)
            print(f"Полный текст сохранен в: test_output/reasoning/{ticker}.md")
    else:
        print("Не удалось сгенерировать обоснования")

if __name__ == "__main__":
    main() 