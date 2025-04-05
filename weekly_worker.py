#!/usr/bin/env python3
"""
Weekly worker для HedgeFundAI.

Этот скрипт автоматизирует полный цикл еженедельного обновления:
1. Обновление рыночных и фундаментальных данных
2. Перерасчёт технических метрик 
3. Генерация reasoning

Может запускаться отдельно или вызываться из других модулей.
"""

import os
import time
import json
import logging
import pandas as pd
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from src.data.market_data_service import MarketDataService
from src.analysis.scoring_engine import ScoringEngine
from src.analysis.ai_reasoner import AIReasoner

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"logs/weekly_update_{datetime.now().strftime('%Y-%m-%d')}.log")
    ]
)
logger = logging.getLogger("weekly_worker")

def ensure_directories():
    """Создаёт необходимые директории, если они отсутствуют."""
    dirs = ["data", "logs", "data/reasoning"]
    for directory in dirs:
        Path(directory).mkdir(exist_ok=True, parents=True)
    logger.info("Необходимые директории созданы")

def update_market_data(force_refresh=False):
    """
    Обновляет рыночные данные через MarketDataService.
    
    Args:
        force_refresh: Принудительное обновление всех данных, игнорируя кэш.
        
    Returns:
        DataFrame: DataFrame с обновленными данными по всем тикерам.
    """
    try:
        logger.info("Начинаем обновление данных для еженедельной ребалансировки")
        
        # Инициализация сервиса
        market_data = MarketDataService()
        
        # Получение списка тикеров для анализа (S&P500 без топ-50)
        tickers = market_data.get_sp500_tickers(start_rank=51, end_rank=500)
        logger.info(f"Получено {len(tickers)} тикеров для обновления")
        
        # Обновление данных по всем тикерам
        all_metrics = []
        success_count = 0
        failed_tickers = []
        
        for ticker in tickers:
            try:
                logger.info(f"Обработка тикера {ticker}...")
                ticker_data = market_data.get_ticker_data(ticker, force_refresh=force_refresh)
                
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
                success_count += 1
                
            except Exception as e:
                logger.error(f"Ошибка при обновлении данных для {ticker}: {str(e)}")
                failed_tickers.append(ticker)
        
        # Создаем DataFrame из всех метрик
        df = pd.DataFrame(all_metrics)
        
        # Сохраняем DataFrame для дальнейшего использования
        df.to_csv('data/market_data_latest.csv', index=False)
        
        # Логируем результаты
        elapsed_time = time.time() - start_time
        logger.info(f"Обновление рыночных данных завершено за {elapsed_time:.2f} секунд")
        logger.info(f"Успешно обновлено {success_count} из {len(tickers)} тикеров")
        
        if failed_tickers:
            logger.warning(f"Не удалось обновить данные для {len(failed_tickers)} тикеров: {', '.join(failed_tickers)}")
        
        return df
    
    except Exception as e:
        logger.error(f"Критическая ошибка при обновлении рыночных данных: {str(e)}")
        return None

def run_scoring(market_data_df, top_n=10):
    """
    Запускает скоринг на основе обновлённых данных.
    
    Args:
        market_data_df: DataFrame с рыночными данными
        top_n: Количество тикеров для long/short позиций
        
    Returns:
        tuple: (DataFrame с результатами скоринга, словарь {'long': [...], 'short': [...]})
    """
    try:
        logger.info(f"Запуск скоринга (top_n={top_n})...")
        start_time = time.time()
        
        # Инициализация скоринг-движка
        engine = ScoringEngine(output_dir='data', top_n=top_n)
        
        # Запуск скоринга
        result = engine.run(market_data_df)
        
        # Загружаем результаты
        scores_df = pd.read_csv('data/scoring_results.csv')
        
        # Загружаем long/short тикеры
        with open('data/long_short_selection.json', 'r') as f:
            selection = json.load(f)
        
        elapsed_time = time.time() - start_time
        logger.info(f"Скоринг завершен за {elapsed_time:.2f} секунд")
        logger.info(f"Long позиции ({len(selection['long'])}): {', '.join(selection['long'])}")
        logger.info(f"Short позиции ({len(selection['short'])}): {', '.join(selection['short'])}")
        
        return scores_df, selection
    
    except Exception as e:
        logger.error(f"Ошибка при выполнении скоринга: {str(e)}")
        return None, None

def generate_reasoning(scores_df, selection):
    """
    Генерирует обоснования для long/short позиций.
    
    Args:
        scores_df: DataFrame с результатами скоринга
        selection: Словарь {'long': [...], 'short': [...]}
        
    Returns:
        dict: Словарь с созданными обоснованиями для каждого тикера
    """
    try:
        # Проверка наличия API ключа OpenAI
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            logger.error("API ключ OpenAI не найден. Генерация reasoning недоступна.")
            return {}
        
        logger.info("Запуск генерации обоснований...")
        start_time = time.time()
        
        # Инициализация AIReasoner
        reasoner = AIReasoner(reasoning_dir='data/reasoning')
        
        # Создаем side_map на основе selection
        side_map = {}
        for ticker in scores_df['ticker']:
            if ticker in selection['long']:
                side_map[ticker] = 'long'
            elif ticker in selection['short']:
                side_map[ticker] = 'short'
        
        # Добавляем rank в DataFrame для использования в промпте
        ranked_tickers = scores_df.sort_values('composite_score', ascending=False)
        for i, ticker in enumerate(ranked_tickers['ticker']):
            scores_df.loc[scores_df['ticker'] == ticker, 'rank'] = i + 1
        
        # Фильтруем только long/short тикеры для генерации обоснований
        selected_tickers = selection['long'] + selection['short']
        selected_df = scores_df[scores_df['ticker'].isin(selected_tickers)]
        
        # Генерируем обоснования
        reasonings = {}
        success_count = 0
        failed_tickers = []
        
        # Пробуем сначала batch-генерацию
        try:
            logger.info(f"Запуск batch-генерации обоснований для {len(selected_tickers)} тикеров...")
            reasonings = reasoner.generate_reasoning_batch(selected_df, side_map=side_map)
            success_count = len(reasonings)
            
            # Проверяем, для каких тикеров не удалось сгенерировать обоснования
            failed_tickers = [ticker for ticker in selected_tickers if ticker not in reasonings]
            
        except Exception as e:
            logger.error(f"Ошибка при batch-генерации обоснований: {str(e)}")
            logger.info("Переключение на индивидуальную генерацию обоснований...")
            
            # Переключаемся на индивидуальную генерацию при ошибке batch
            reasonings = {}
            for _, row in selected_df.iterrows():
                ticker = row['ticker']
                side = side_map.get(ticker, 'unknown')
                
                try:
                    reasoning = reasoner.generate_reasoning_for_ticker(ticker, row, side)
                    if reasoning:
                        reasonings[ticker] = reasoning
                        success_count += 1
                    else:
                        failed_tickers.append(ticker)
                except Exception as e:
                    logger.error(f"Ошибка при генерации обоснования для {ticker}: {str(e)}")
                    failed_tickers.append(ticker)
        
        elapsed_time = time.time() - start_time
        logger.info(f"Генерация обоснований завершена за {elapsed_time:.2f} секунд")
        logger.info(f"Успешно сгенерировано {success_count} из {len(selected_tickers)} обоснований")
        
        if failed_tickers:
            logger.warning(f"Не удалось сгенерировать обоснования для {len(failed_tickers)} тикеров: {', '.join(failed_tickers)}")
        
        return reasonings
    
    except Exception as e:
        logger.error(f"Критическая ошибка при генерации обоснований: {str(e)}")
        return {}

def run_weekly_update(force_refresh=False, top_n=10):
    """
    Запускает полный цикл еженедельного обновления.
    
    Args:
        force_refresh: Принудительное обновление всех данных, игнорируя кэш
        top_n: Количество тикеров для long/short позиций
        
    Returns:
        bool: True в случае успешного выполнения, False в случае ошибки
    """
    logger.info("🔄 Запуск еженедельного обновления данных и обоснований...")
    start_time = time.time()
    
    try:
        # Создаем необходимые директории
        ensure_directories()
        
        # Загружаем переменные окружения
        load_dotenv()
        
        # Шаг 1: Обновление рыночных и фундаментальных данных
        logger.info("Шаг 1: Обновление рыночных и фундаментальных данных")
        market_data_df = update_market_data(force_refresh=force_refresh)
        
        if market_data_df is None or market_data_df.empty:
            logger.error("Не удалось получить рыночные данные. Прерывание процесса.")
            return False
        
        # Шаг 2: Скоринг и ранжирование тикеров
        logger.info("Шаг 2: Скоринг и ранжирование тикеров")
        scores_df, selection = run_scoring(market_data_df, top_n=top_n)
        
        if scores_df is None or selection is None:
            logger.error("Ошибка при выполнении скоринга. Прерывание процесса.")
            return False
        
        # Шаг 3: Генерация reasoning
        logger.info("Шаг 3: Генерация инвестиционных обоснований")
        reasonings = generate_reasoning(scores_df, selection)
        
        # Итог
        elapsed_time = time.time() - start_time
        logger.info(f"✅ Еженедельное обновление завершено за {elapsed_time:.2f} секунд")
        logger.info(f"Обработано {len(market_data_df)} тикеров")
        logger.info(f"Сгенерировано {len(reasonings)} обоснований")
        
        return True
    
    except Exception as e:
        logger.error(f"Критическая ошибка при выполнении еженедельного обновления: {str(e)}")
        elapsed_time = time.time() - start_time
        logger.info(f"❌ Еженедельное обновление прервано через {elapsed_time:.2f} секунд")
        return False

if __name__ == "__main__":
    # Запуск weekly worker непосредственно из командной строки
    import argparse
    
    parser = argparse.ArgumentParser(description='Запуск еженедельного обновления данных')
    parser.add_argument('--force', action='store_true', help='Принудительное обновление всех данных')
    parser.add_argument('--top', type=int, default=10, help='Количество тикеров для long/short позиций')
    args = parser.parse_args()
    
    # Вызов основной функции обновления
    success = run_weekly_update(force_refresh=args.force, top_n=args.top)
    
    # Выход с соответствующим кодом
    exit(0 if success else 1) 