import os
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Union

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ScoringEngine:
    """
    Движок скоринга для ранжирования тикеров на основе мультифакторной модели.
    
    Принимает DataFrame с метриками, нормализовать их, рассчитывать composite_score и возвращать топ/боттом тикеры для long/short позиций.
    """
    
    def __init__(self, output_dir='data', 
                 weights=None, 
                 normalize_method='zscore', 
                 top_n=10,
                 use_ai_recommendations=True):
        """
        Инициализация движка скоринга.
        
        Args:
            output_dir (str): Директория для сохранения результатов
            weights (dict): Словарь с весами для каждого блока скоров
            normalize_method (str): Метод нормализации ('zscore' или 'minmax')
            top_n (int): Количество тикеров для отбора в top/bottom
            use_ai_recommendations (bool): Использовать ли рекомендации AI при отборе тикеров
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
        # Веса для каждого блока скоров (по умолчанию равны)
        self.weights = weights or {
            'value_score': 0.25,
            'growth_score': 0.25,
            'risk_score': 0.2,
            'analyst_score': 0.15,
            'momentum_score': 0.15
        }
        
        # Проверка корректности весов (сумма должна быть равна 1)
        if abs(sum(self.weights.values()) - 1.0) > 0.0001:
            logger.warning(f"Сумма весов ({sum(self.weights.values())}) не равна 1.0. Нормализуем веса.")
            weight_sum = sum(self.weights.values())
            self.weights = {k: v / weight_sum for k, v in self.weights.items()}
        
        self.normalize_method = normalize_method
        self.top_n = top_n
        self.use_ai_recommendations = use_ai_recommendations
        
        # Словари для указания направления нормализации
        # True = больше значение лучше, False = меньше значение лучше
        self.metrics_direction = {
            'pe_ratio': False,           # Ниже P/E лучше
            'eps_growth_12m': True,      # Выше рост EPS лучше
            'revenue_growth_yoy': True,  # Выше рост выручки лучше
            'momentum_3m': True,         # Выше моментум лучше
            'volatility_3m': False,      # Ниже волатильность лучше
            'avg_volume_10d': True,      # Выше объем лучше (ликвидность)
            'sentiment_score': True,     # Выше сентимент лучше
            'debt_equity': False,        # Ниже D/E лучше
            'roe': True,                 # Выше ROE лучше
            'peg_ratio': False,          # Ниже PEG лучше
            'market_cap': None,          # Нейтрально (используется для фильтрации)
            'consensus_score': True,     # Выше консенсус аналитиков лучше
            'analyst_rating_trend': True, # Положительный тренд рейтингов лучше
            
            # Дополнительные метрики оценки
            'price_to_book': False,      # Ниже P/B лучше
            'price_to_sales': False,     # Ниже P/S лучше
            'forward_pe': False,         # Ниже Forward P/E лучше
            'dividend_yield': True,      # Выше дивидендная доходность лучше
            'ev_to_ebitda': False,       # Ниже EV/EBITDA лучше
            
            # Технические индикаторы
            'price_change_ytd': True,    # Выше изменение цены с начала года лучше
            'price_vs_sma_50': True,     # Выше отношение цены к SMA(50) лучше для роста
            'price_vs_sma_200': True,    # Выше отношение цены к SMA(200) лучше для роста
            'rsi': None,                 # RSI нейтрален (70+ перекуплен, 30- перепродан)
            
            # Метрики по аналитикам
            'strong_buy': True,          # Больше рекомендаций Strong Buy лучше
            'buy': True,                 # Больше рекомендаций Buy лучше
            'hold': None,                # Hold нейтрален
            'sell': False,               # Меньше рекомендаций Sell лучше
            'strong_sell': False,        # Меньше рекомендаций Strong Sell лучше
            'target_to_price': True,     # Выше отношение целевой цены к текущей лучше
            'eps_surprise_percent': True, # Выше положительный сюрприз EPS лучше
            'earnings_beat_rate': True   # Выше процент превышения ожиданий лучше
        }
        
        # Группировка метрик по блокам скоров
        self.score_metrics = {
            'value_score': ['pe_ratio', 'peg_ratio', 'roe', 'price_to_book', 'price_to_sales', 'ev_to_ebitda', 'dividend_yield'],
            'growth_score': ['eps_growth_12m', 'revenue_growth_yoy', 'forward_pe'],
            'risk_score': ['volatility_3m', 'debt_equity', 'rsi', 'earnings_beat_rate'],
            'analyst_score': ['consensus_score', 'analyst_rating_trend', 'strong_buy', 'buy', 'sell', 'strong_sell', 'target_to_price', 'eps_surprise_percent'],
            'momentum_score': ['momentum_3m', 'price_change_ytd', 'price_vs_sma_50', 'price_vs_sma_200']
        }
        
        # Соответствие между сторонами позиции и рекомендациями AI
        self.recommendation_map = {
            'long': ['BUY'],
            'short': ['SELL']
        }
        
        logger.info(f"ScoringEngine инициализирован с top_n={top_n}, метод нормализации={normalize_method}, use_ai_recommendations={use_ai_recommendations}")
    
    def normalize(self, df, column, direction=True):
        """
        Нормализация колонки в DataFrame.
        
        Args:
            df (pd.DataFrame): DataFrame с данными
            column (str): Название колонки для нормализации
            direction (bool): True если выше значение лучше, False если ниже лучше
            
        Returns:
            np.array: Нормализованные значения
        """
        if column not in df.columns:
            logger.warning(f"Колонка {column} отсутствует в данных. Возвращаем нулевые значения.")
            return np.zeros(len(df))
        
        # Игнорируем NaN значения при расчете статистик
        values = df[column].dropna()
        
        if len(values) == 0:
            logger.warning(f"Все значения в колонке {column} - NaN. Возвращаем нулевые значения.")
            return np.zeros(len(df))
        
        # Заполняем NaN средними значениями для нормализации
        filled_values = df[column].fillna(values.mean())
        
        if self.normalize_method == 'zscore':
            # Z-score нормализация: (x - mean) / std
            mean = values.mean()
            std = values.std()
            if std == 0:
                logger.warning(f"Стандартное отклонение для {column} равно 0. Используем сырые значения.")
                normalized = filled_values - mean
            else:
                normalized = (filled_values - mean) / std
        elif self.normalize_method == 'minmax':
            # Min-max нормализация: (x - min) / (max - min)
            min_val = values.min()
            max_val = values.max()
            if max_val == min_val:
                logger.warning(f"Минимум и максимум для {column} равны. Используем нулевые значения.")
                normalized = np.zeros(len(df))
            else:
                normalized = (filled_values - min_val) / (max_val - min_val)
                
        # Инвертируем значения если меньшее значение лучше
        if not direction:
            normalized = -normalized
            
        return normalized
    
    def calculate_block_score(self, df, block_name):
        """
        Расчет блока скора (например, value_score) на основе группы метрик.
        
        Args:
            df (pd.DataFrame): DataFrame с данными
            block_name (str): Название блока скора
            
        Returns:
            pd.Series: Рассчитанный блок скора
        """
        if block_name not in self.score_metrics:
            logger.error(f"Неизвестный блок скора: {block_name}")
            return pd.Series(0, index=df.index)
        
        metrics = self.score_metrics[block_name]
        
        # Нормализуем каждую метрику блока
        normalized_metrics = []
        for metric in metrics:
            if metric in df.columns:
                direction = self.metrics_direction.get(metric, True)
                normalized = self.normalize(df, metric, direction)
                normalized_metrics.append(normalized)
        
        if not normalized_metrics:
            logger.warning(f"Блок {block_name} не содержит доступных метрик. Возвращаем нулевые значения.")
            return pd.Series(0, index=df.index)
        
        # Рассчитываем среднее по всем нормализованным метрикам блока
        block_score = sum(normalized_metrics) / len(normalized_metrics)
        
        return pd.Series(block_score, index=df.index)
    
    def calculate_composite_score(self, df):
        """
        Расчет итогового composite_score на основе всех блоков скоров.
        
        Args:
            df (pd.DataFrame): DataFrame с данными
            
        Returns:
            pd.DataFrame: DataFrame с добавленными блоками скоров и composite_score
        """
        result_df = df.copy()
        
        # Рассчитываем каждый блок скора
        for block_name in self.score_metrics.keys():
            result_df[block_name] = self.calculate_block_score(df, block_name)
            logger.debug(f"Рассчитан блок {block_name}")
        
        # Рассчитываем composite_score как взвешенное среднее блоков
        composite_score = pd.Series(0, index=df.index)
        for block_name, weight in self.weights.items():
            composite_score += result_df[block_name] * weight
        
        result_df['composite_score'] = composite_score
        
        return result_df
    
    def select_long_short(self, df, ai_recommendations: Optional[Dict[str, str]] = None):
        """
        Выбор top/bottom тикеров на основе composite_score.
        Опционально фильтрует тикеры по рекомендациям AI.
        
        Args:
            df (pd.DataFrame): DataFrame с рассчитанными скорами
            ai_recommendations (Dict[str, str], optional): Словарь с рекомендациями AI (BUY/SELL/HOLD)
            
        Returns:
            pd.DataFrame: DataFrame с выбранными тикерами и direction (long/short)
        """
        # Сортируем по composite_score
        sorted_df = df.sort_values('composite_score', ascending=False)
        
        # Если используем AI рекомендации
        if self.use_ai_recommendations and ai_recommendations:
            # Добавляем рекомендации AI к DataFrame
            sorted_df_with_index = sorted_df.reset_index()
            sorted_df_with_index['ai_recommendation'] = sorted_df_with_index['ticker'].map(
                lambda x: ai_recommendations.get(x.upper(), 'HOLD')
            )
            
            # Фильтруем тикеры для long - берем только с рекомендацией BUY
            long_candidates = sorted_df_with_index[
                sorted_df_with_index['ai_recommendation'].isin(self.recommendation_map['long'])
            ]
            
            # Фильтруем тикеры для short - берем только с рекомендацией SELL
            short_candidates = sorted_df_with_index[
                sorted_df_with_index['ai_recommendation'].isin(self.recommendation_map['short'])
            ].sort_values('composite_score')  # Сортируем в обратном порядке для short
            
            # Выбираем top N для long из отфильтрованных кандидатов
            top_n = min(self.top_n, len(long_candidates))
            if top_n == 0:
                logger.warning("Не найдено подходящих тикеров для long позиций согласно AI рекомендациям")
                top_tickers = pd.DataFrame()
            else:
                top_tickers = long_candidates.head(top_n).copy()
                top_tickers['direction'] = 'long'
            
            # Выбираем bottom N для short из отфильтрованных кандидатов
            bottom_n = min(self.top_n, len(short_candidates))
            if bottom_n == 0:
                logger.warning("Не найдено подходящих тикеров для short позиций согласно AI рекомендациям")
                bottom_tickers = pd.DataFrame()
            else:
                bottom_tickers = short_candidates.head(bottom_n).copy()
                bottom_tickers['direction'] = 'short'
            
            # Если недостаточно тикеров с AI рекомендациями, логируем предупреждение
            if top_n < self.top_n:
                logger.warning(f"Найдено только {top_n} тикеров для long (требуется {self.top_n})")
            if bottom_n < self.top_n:
                logger.warning(f"Найдено только {bottom_n} тикеров для short (требуется {self.top_n})")
        else:
            # Если не используем AI рекомендации, просто берем top и bottom N
            top_n = min(self.top_n, len(sorted_df))
            top_tickers = sorted_df.head(top_n).reset_index().copy()
            top_tickers['direction'] = 'long'
            
            bottom_tickers = sorted_df.tail(top_n).reset_index().copy()
            bottom_tickers['direction'] = 'short'
        
        # Объединяем top и bottom
        result_df = pd.concat([top_tickers, bottom_tickers], ignore_index=True)
        
        logger.info(f"Выбрано {len(top_tickers)} тикеров для long и {len(bottom_tickers)} для short")
        
        return result_df
    
    def run(self, data, ai_recommendations: Optional[Dict[str, str]] = None):
        """
        Запуск полного процесса скоринга.
        
        Args:
            data: Путь к CSV файлу или DataFrame с данными
            ai_recommendations: Словарь с рекомендациями AI (BUY/SELL/HOLD)
            
        Returns:
            pd.DataFrame: DataFrame с выбранными тикерами и direction
        """
        # Загружаем данные если передан путь к файлу
        if isinstance(data, str):
            logger.info(f"Загрузка данных из файла: {data}")
            df = pd.read_csv(data)
        else:
            logger.info("Использование переданного DataFrame")
            df = data
        
        # Проверяем наличие колонки ticker
        if 'ticker' not in df.columns:
            logger.error("В данных отсутствует колонка 'ticker'")
            raise ValueError("В данных отсутствует колонка 'ticker'")
        
        # Устанавливаем ticker в качестве индекса
        df = df.set_index('ticker')
        
        logger.info(f"Данные загружены: {len(df)} тикеров")
        
        # Рассчитываем скоры
        logger.info("Расчет composite_score...")
        scores_df = self.calculate_composite_score(df)
        
        # Выбираем long/short тикеры с учетом AI рекомендаций
        logger.info(f"Выбор long/short тикеров{' с учетом AI рекомендаций' if self.use_ai_recommendations and ai_recommendations else ''}...")
        selection_df = self.select_long_short(scores_df, ai_recommendations)
        
        # Сохраняем результаты
        self.save_results(scores_df.reset_index(), selection_df)
        
        return selection_df
    
    def save_results(self, scores_df, selection_df):
        """
        Сохранение результатов в CSV и JSON.
        
        Args:
            scores_df (pd.DataFrame): DataFrame с рассчитанными скорами
            selection_df (pd.DataFrame): DataFrame с выбранными тикерами
        """
        # Сохраняем полные результаты в CSV
        csv_path = self.output_dir / 'scoring_results.csv'
        scores_df.to_csv(csv_path, index=False)
        logger.info(f"Результаты скоринга сохранены в {csv_path}")
        
        # Сохраняем long/short выборку в JSON
        json_path = self.output_dir / 'long_short_selection.json'
        
        # Формируем структуру для JSON
        result = {
            'timestamp': pd.Timestamp.now().isoformat(),
            'long': selection_df[selection_df['direction'] == 'long']['ticker'].tolist(),
            'short': selection_df[selection_df['direction'] == 'short']['ticker'].tolist(),
            'details': selection_df.to_dict(orient='records')
        }
        
        with open(json_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        logger.info(f"Long/short выборка сохранена в {json_path}")


def main():
    """
    Запуск скоринга как скрипта.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Скоринг тикеров на основе мультифакторной модели')
    parser.add_argument('--input', '-i', required=True, help='Путь к CSV файлу с данными')
    parser.add_argument('--output', '-o', default='data', help='Директория для сохранения результатов')
    parser.add_argument('--normalize', '-n', default='zscore', choices=['zscore', 'minmax'], 
                        help='Метод нормализации')
    parser.add_argument('--top', '-t', type=int, default=10, help='Количество тикеров для отбора')
    parser.add_argument('--use-ai', '-a', action='store_true', help='Использовать рекомендации AI')
    
    args = parser.parse_args()
    
    logger.info(f"Запуск скоринга с параметрами: {args}")
    
    # Создаем и запускаем движок скоринга
    engine = ScoringEngine(
        output_dir=args.output, 
        normalize_method=args.normalize, 
        top_n=args.top,
        use_ai_recommendations=args.use_ai
    )
    
    # Если нужны AI рекомендации, создаем и инициализируем AIReasoner
    ai_recommendations = None
    if args.use_ai:
        try:
            from ai_reasoner import AIReasoner
            reasoner = AIReasoner()
            # Загружаем все кэшированные рекомендации
            cached_reasonings = reasoner.get_all_cached_reasoning()
            # Извлекаем только рекомендации
            ai_recommendations = {ticker: data.get('recommendation', 'HOLD') 
                                for ticker, data in cached_reasonings.items()}
            logger.info(f"Загружено {len(ai_recommendations)} AI рекомендаций")
        except Exception as e:
            logger.error(f"Ошибка при инициализации AIReasoner: {e}")
            logger.warning("Скоринг будет выполнен без учета AI рекомендаций")
    
    # Запускаем скоринг с AI рекомендациями, если они доступны
    result = engine.run(args.input, ai_recommendations)
    
    # Выводим результаты
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


if __name__ == "__main__":
    main() 