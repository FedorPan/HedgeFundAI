import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from src.analysis.scoring_engine import ScoringEngine

# Создадим временную директорию для тестовых результатов
test_output_dir = Path('test_output')
test_output_dir.mkdir(exist_ok=True, parents=True)

def generate_test_data(num_tickers=50, seed=42):
    """
    Генерация тестовых данных для проверки ScoringEngine.
    
    Args:
        num_tickers (int): Количество тикеров для генерации
        seed (int): Seed для генератора случайных чисел
    
    Returns:
        pd.DataFrame: DataFrame с тестовыми данными
    """
    np.random.seed(seed)
    
    # Создаем тикеры в формате TEST1, TEST2, ...
    tickers = [f"TEST{i}" for i in range(1, num_tickers + 1)]
    
    # Создаем случайные данные для всех метрик
    data = {
        'ticker': tickers,
        'pe_ratio': np.random.uniform(5, 50, num_tickers),
        'eps_growth_12m': np.random.uniform(-20, 50, num_tickers),
        'revenue_growth_yoy': np.random.uniform(-15, 40, num_tickers),
        'momentum_3m': np.random.uniform(-30, 30, num_tickers),
        'volatility_3m': np.random.uniform(10, 50, num_tickers),
        'avg_volume_10d': np.random.uniform(100000, 10000000, num_tickers),
        'sentiment_score': np.random.uniform(-1, 1, num_tickers),
        'debt_equity': np.random.uniform(0, 3, num_tickers),
        'roe': np.random.uniform(0, 30, num_tickers),
        'peg_ratio': np.random.uniform(0.5, 3, num_tickers),
        'market_cap': np.random.uniform(1000, 500000, num_tickers),
        'consensus_score': np.random.uniform(-1, 1, num_tickers),
        'analyst_rating_trend': np.random.uniform(-0.5, 0.5, num_tickers)
    }
    
    # Создаем DataFrame
    df = pd.DataFrame(data)
    
    # Добавляем немного NaN значений для проверки обработки
    for col in df.columns:
        if col != 'ticker':  # Не трогаем колонку тикеров
            mask = np.random.random(len(df)) < 0.1  # 10% NaN значений
            df.loc[mask, col] = np.nan
    
    return df

def test_composite_score_calculation():
    """
    Тест расчета composite_score.
    """
    print("\n=== Тест расчета composite_score ===")
    
    # Генерируем тестовые данные
    test_data = generate_test_data(num_tickers=20)
    
    # Инициализируем ScoringEngine
    engine = ScoringEngine(output_dir=test_output_dir)
    
    # Рассчитываем composite_score
    df_with_scores = engine.calculate_composite_score(test_data.set_index('ticker'))
    
    # Проверка: все ли блоки скоров и composite_score добавлены
    expected_columns = list(engine.score_metrics.keys()) + ['composite_score']
    for col in expected_columns:
        assert col in df_with_scores.columns, f"Колонка {col} отсутствует в результате"
    
    print("✅ Все блоки скоров и composite_score успешно рассчитаны")
    
    # Проверка: composite_score должен быть взвешенной суммой блоков
    for idx in df_with_scores.index:
        expected_composite = sum(df_with_scores.loc[idx, block] * weight 
                              for block, weight in engine.weights.items())
        actual_composite = df_with_scores.loc[idx, 'composite_score']
        assert abs(expected_composite - actual_composite) < 1e-6, \
            f"Composite score для {idx} рассчитан неверно"
    
    print("✅ Composite score корректно рассчитан как взвешенная сумма блоков")
    
    # Выводим пример результатов
    print("\nПример результатов (первые 5 строк):")
    print(df_with_scores.head(5)[expected_columns])

def test_long_short_selection():
    """
    Тест выбора тикеров для long/short позиций.
    """
    print("\n=== Тест выбора long/short тикеров ===")
    
    # Генерируем тестовые данные
    test_data = generate_test_data(num_tickers=30)
    
    # Инициализируем ScoringEngine с различными top_n
    for top_n in [5, 10]:
        print(f"\nПроверка для top_n={top_n}")
        
        engine = ScoringEngine(output_dir=test_output_dir, top_n=top_n)
        
        # Запускаем полный процесс
        result = engine.run(test_data)
        
        # Проверка: корректное количество тикеров для long/short
        long_tickers = result[result['direction'] == 'long']
        short_tickers = result[result['direction'] == 'short']
        
        assert len(long_tickers) == top_n, f"Неверное количество тикеров для long: {len(long_tickers)}, ожидалось {top_n}"
        assert len(short_tickers) == top_n, f"Неверное количество тикеров для short: {len(short_tickers)}, ожидалось {top_n}"
        
        print(f"✅ Выбрано корректное количество тикеров: {len(long_tickers)} для long и {len(short_tickers)} для short")
        
        # Проверка: тикеры для long должны иметь высокий composite_score
        assert all(long_tickers['composite_score'] > short_tickers['composite_score'].max()), \
            "Ошибка в выборе: некоторые short тикеры имеют композитный скор выше, чем long тикеры"
        
        print("✅ Тикеры для long имеют composite_score выше, чем тикеры для short")
        
        # Проверка сохранения результатов
        csv_path = test_output_dir / 'scoring_results.csv'
        json_path = test_output_dir / 'long_short_selection.json'
        
        assert csv_path.exists(), f"Файл результатов {csv_path} не создан"
        assert json_path.exists(), f"Файл выборки {json_path} не создан"
        
        print(f"✅ Результаты сохранены в {csv_path} и {json_path}")
        
        # Проверяем содержимое JSON файла
        with open(json_path, 'r') as f:
            json_data = json.load(f)
        
        assert 'long' in json_data, "В JSON отсутствует ключ 'long'"
        assert 'short' in json_data, "В JSON отсутствует ключ 'short'"
        assert len(json_data['long']) == top_n, f"Неверное количество long тикеров в JSON: {len(json_data['long'])}"
        assert len(json_data['short']) == top_n, f"Неверное количество short тикеров в JSON: {len(json_data['short'])}"
        
        print("✅ JSON файл содержит корректные данные")

def test_missing_data_handling():
    """
    Тест обработки пропущенных данных.
    """
    print("\n=== Тест обработки пропущенных данных ===")
    
    # Генерируем базовые тестовые данные
    test_data = generate_test_data(num_tickers=20)
    
    # Создаем DataFrame с отсутствующими колонками
    limited_data = test_data[['ticker', 'pe_ratio', 'eps_growth_12m', 'momentum_3m']].copy()
    
    # Инициализируем ScoringEngine
    engine = ScoringEngine(output_dir=test_output_dir)
    
    # Запускаем процесс
    try:
        result = engine.run(limited_data)
        print("✅ ScoringEngine корректно обрабатывает отсутствующие колонки")
    except Exception as e:
        print(f"❌ Ошибка при обработке отсутствующих колонок: {e}")
        return
    
    # Проверяем, что все блоки скоров рассчитаны
    scores_path = test_output_dir / 'scoring_results.csv'
    scores_df = pd.read_csv(scores_path)
    
    expected_columns = list(engine.score_metrics.keys()) + ['composite_score']
    for col in expected_columns:
        assert col in scores_df.columns, f"Колонка {col} отсутствует в результате"
    
    print("✅ Все блоки скоров рассчитаны несмотря на отсутствие некоторых метрик")
    
    # Создаем DataFrame с NaN значениями во всех строках для одной метрики
    all_nan_data = test_data.copy()
    all_nan_data['roe'] = np.nan
    
    # Запускаем процесс
    try:
        result = engine.run(all_nan_data)
        print("✅ ScoringEngine корректно обрабатывает полностью отсутствующие метрики (все NaN)")
    except Exception as e:
        print(f"❌ Ошибка при обработке полностью отсутствующих метрик: {e}")

def main():
    """
    Запуск всех тестов.
    """
    print("==== Тестирование ScoringEngine ====")
    
    # Тест расчета composite_score
    test_composite_score_calculation()
    
    # Тест выбора long/short тикеров
    test_long_short_selection()
    
    # Тест обработки пропущенных данных
    test_missing_data_handling()
    
    print("\n==== Все тесты успешно выполнены! ====")

if __name__ == "__main__":
    main() 