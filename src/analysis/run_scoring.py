#!/usr/bin/env python3
"""
Скрипт для запуска ScoringEngine с интеграцией AIReasoner.
Анализирует тикеры и генерирует long/short рекомендации, учитывая AI рекомендации.
"""

import os
import sys
import logging
import pandas as pd
from pathlib import Path

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Добавляем корневую директорию проекта в путь импорта
current_dir = Path(__file__).parent
root_dir = current_dir.parent
sys.path.append(str(root_dir))

# Импортируем наши модули
from analysis.scoring_engine import ScoringEngine
from analysis.ai_reasoner import AIReasoner

def main():
    """
    Основная функция для запуска скоринга с интеграцией AI.
    """
    # Путь к данным
    data_path = root_dir / "data" / "sample_metrics.csv"
    
    # Проверяем существование файла
    if not data_path.exists():
        logger.error(f"Файл с данными не найден: {data_path}")
        sys.exit(1)
    
    # Загружаем данные
    try:
        df = pd.read_csv(data_path)
        logger.info(f"Загружено {len(df)} тикеров из файла {data_path}")
    except Exception as e:
        logger.error(f"Ошибка при загрузке данных: {e}")
        sys.exit(1)
    
    # Инициализируем AIReasoner
    reasoning_dir = root_dir / "data" / "reasoning"
    logger.info(f"Инициализация AIReasoner, директория: {reasoning_dir}")
    reasoner = AIReasoner(reasoning_dir=reasoning_dir)
    
    # Пытаемся получить все кэшированные рекомендации
    try:
        cached_reasonings = reasoner.get_all_cached_reasoning()
        # Извлекаем только рекомендации
        ai_recommendations = {ticker: data.get('recommendation', 'HOLD') 
                            for ticker, data in cached_reasonings.items()}
        logger.info(f"Загружено {len(ai_recommendations)} AI рекомендаций")
    except Exception as e:
        logger.error(f"Ошибка при работе с AIReasoner: {e}")
        ai_recommendations = {}
    
    # Выводим загруженные рекомендации
    if ai_recommendations:
        print("\nЗагруженные AI рекомендации:")
        for ticker, rec in ai_recommendations.items():
            print(f"{ticker}: {rec}")
    
    # Инициализируем ScoringEngine
    output_dir = root_dir / "data" / "output"
    output_dir.mkdir(exist_ok=True, parents=True)
    
    logger.info(f"Инициализация ScoringEngine, директория результатов: {output_dir}")
    engine = ScoringEngine(
        output_dir=output_dir,
        normalize_method='zscore',
        top_n=5,  # Берем топ-5 для примера
        use_ai_recommendations=True  # Включаем учет рекомендаций AI
    )
    
    # Запускаем скоринг с учетом AI рекомендаций
    logger.info(f"Запуск скоринга для {len(df)} тикеров")
    result = engine.run(df, ai_recommendations)
    
    # Выводим результаты
    print("\nРезультаты скоринга с учетом AI рекомендаций:")
    print("\nTop tickers (long):")
    long_df = result[result['direction'] == 'long']
    if 'ai_recommendation' in long_df.columns:
        print(long_df[['ticker', 'composite_score', 'ai_recommendation']].to_string(index=False))
    else:
        print(long_df[['ticker', 'composite_score']].to_string(index=False))
    
    print("\nBottom tickers (short):")
    short_df = result[result['direction'] == 'short']
    if 'ai_recommendation' in short_df.columns:
        print(short_df[['ticker', 'composite_score', 'ai_recommendation']].to_string(index=False))
    else:
        print(short_df[['ticker', 'composite_score']].to_string(index=False))
    
    # Запускаем скоринг БЕЗ учета AI рекомендаций для сравнения
    logger.info("Запуск скоринга без учета AI рекомендаций (для сравнения)")
    engine_no_ai = ScoringEngine(
        output_dir=output_dir,
        normalize_method='zscore',
        top_n=5,
        use_ai_recommendations=False
    )
    result_no_ai = engine_no_ai.run(df)
    
    # Выводим результаты без учета AI
    print("\nРезультаты скоринга БЕЗ учета AI рекомендаций (для сравнения):")
    print("\nTop tickers (long):")
    print(result_no_ai[result_no_ai['direction'] == 'long'][['ticker', 'composite_score']].to_string(index=False))
    
    print("\nBottom tickers (short):")
    print(result_no_ai[result_no_ai['direction'] == 'short'][['ticker', 'composite_score']].to_string(index=False))
    
    # Сравниваем результаты
    long_with_ai = set(long_df['ticker'].values)
    long_without_ai = set(result_no_ai[result_no_ai['direction'] == 'long']['ticker'].values)
    
    short_with_ai = set(short_df['ticker'].values)
    short_without_ai = set(result_no_ai[result_no_ai['direction'] == 'short']['ticker'].values)
    
    print("\nСравнение результатов:")
    print(f"Тикеры в long только с учетом AI: {long_with_ai - long_without_ai}")
    print(f"Тикеры в long только без учета AI: {long_without_ai - long_with_ai}")
    print(f"Тикеры в short только с учетом AI: {short_with_ai - short_without_ai}")
    print(f"Тикеры в short только без учета AI: {short_without_ai - short_with_ai}")
    
    logger.info("Скоринг успешно завершен")

if __name__ == "__main__":
    main()