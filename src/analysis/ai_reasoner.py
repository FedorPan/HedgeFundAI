import os
import json
import logging
import time
import pandas as pd
from openai import OpenAI
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Union, Optional, Tuple

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AIReasoner:
    """
    Генерирует инвестиционные обоснования для тикеров с использованием OpenAI API.
    
    Принимает DataFrame или список словарей с метриками тикеров и генерирует
    текстовое обоснование для каждого тикера в выборке.
    """
    
    def __init__(self, reasoning_dir: str = 'data/reasoning', ttl_days: int = 7, api_key: Optional[str] = None):
        """
        Инициализация AI Reasoner.
        
        Args:
            reasoning_dir: Директория для сохранения обоснований
            ttl_days: Срок действия кэша в днях
            api_key: API ключ OpenAI (если None, используется из переменных окружения)
        """
        self.reasoning_dir = Path(reasoning_dir)
        self.reasoning_dir.mkdir(exist_ok=True, parents=True)
        
        self.ttl = ttl_days * 86400  # в секундах
        
        # Инициализация OpenAI API
        self.api_key = api_key or os.environ.get('OPENAI_API_KEY')
        if not self.api_key:
            logger.warning("API ключ OpenAI не найден. Генерация reasoning будет недоступна.")
            self.client = None
        else:
            # Updated client initialization for compatibility
            self.client = OpenAI(api_key=self.api_key)
        
        logger.info(f"AIReasoner инициализирован. Директория: {self.reasoning_dir}, TTL: {ttl_days} дней")
    
    def _check_api_key(self) -> bool:
        """Проверяет наличие API ключа."""
        if not self.api_key:
            raise ValueError("API ключ OpenAI не найден. Установите его в переменной окружения OPENAI_API_KEY или при инициализации AIReasoner.")
        if not self.client:
            # Updated client initialization for compatibility
            self.client = OpenAI(api_key=self.api_key)
        return True
    
    def get_cached_reasoning(self, ticker: str) -> Optional[Dict]:
        """
        Получает кэшированное обоснование для тикера, если оно существует и не устарело.
        
        Args:
            ticker: Тикер акции
            
        Returns:
            Optional[Dict]: Словарь с обоснованием и рекомендацией или None, если кэш не найден или устарел
        """
        ticker = ticker.upper()
        cache_file = self.reasoning_dir / f"{ticker}.json"
        
        if not cache_file.exists():
            # Проверяем старый формат .md файлов
            old_cache_file = self.reasoning_dir / f"{ticker}.md"
            if old_cache_file.exists():
                # Проверка срока действия кэша
                cache_age = time.time() - old_cache_file.stat().st_mtime
                if cache_age > self.ttl:
                    logger.info(f"Обоснование для {ticker} устарело (возраст: {cache_age/86400:.1f} дней)")
                    return None
                
                # Загрузка старого формата и конвертация
                with open(old_cache_file, 'r') as f:
                    content = f.read()
                    logger.info(f"Загружено устаревшее кэшированное обоснование для {ticker}")
                    # Преобразуем в новый формат
                    recommendation = self._extract_recommendation_from_text(content)
                    result = {
                        'ticker': ticker,
                        'text': content,
                        'recommendation': recommendation,
                        'generated_at': datetime.fromtimestamp(old_cache_file.stat().st_mtime).isoformat()
                    }
                    # Сохраняем в новом формате
                    self.cache_reasoning_json(ticker, result)
                    return result
            return None
        
        # Проверка срока действия кэша
        cache_age = time.time() - cache_file.stat().st_mtime
        if cache_age > self.ttl:
            logger.info(f"Обоснование для {ticker} устарело (возраст: {cache_age/86400:.1f} дней)")
            return None
        
        # Загрузка кэшированного обоснования в JSON
        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)
                logger.info(f"Загружено кэшированное обоснование для {ticker}")
                return data
        except json.JSONDecodeError:
            logger.error(f"Ошибка декодирования JSON для {ticker}")
            return None
    
    def cache_reasoning(self, ticker: str, text: str) -> bool:
        """
        Сохраняет обоснование в кэш в старом формате .md (для обратной совместимости).
        
        Args:
            ticker: Тикер акции
            text: Текст обоснования
            
        Returns:
            bool: True если успешно сохранено
        """
        ticker = ticker.upper()
        cache_file = self.reasoning_dir / f"{ticker}.md"
        
        # Создаем директорию, если она не существует
        self.reasoning_dir.mkdir(exist_ok=True, parents=True)
        
        # Форматируем текст как Markdown с заголовком и датой
        formatted_text = f"# Investment Rationale: {ticker}\n\n"
        formatted_text += f"*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
        formatted_text += text
        
        # Сохраняем в файл
        try:
            with open(cache_file, 'w') as f:
                f.write(formatted_text)
            logger.info(f"Обоснование для {ticker} сохранено в {cache_file}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при сохранении обоснования для {ticker}: {e}")
            return False
    
    def cache_reasoning_json(self, ticker: str, data: Dict) -> bool:
        """
        Сохраняет обоснование в кэш в формате JSON.
        
        Args:
            ticker: Тикер акции
            data: Словарь с обоснованием и рекомендацией
            
        Returns:
            bool: True если успешно сохранено
        """
        ticker = ticker.upper()
        cache_file = self.reasoning_dir / f"{ticker}.json"
        
        # Создаем директорию, если она не существует
        self.reasoning_dir.mkdir(exist_ok=True, parents=True)
        
        # Сохраняем в файл
        try:
            with open(cache_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Обоснование для {ticker} сохранено в JSON: {cache_file}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при сохранении JSON обоснования для {ticker}: {e}")
            return False
    
    def _extract_recommendation_from_text(self, text: str) -> str:
        """
        Извлекает рекомендацию из текста обоснования.
        Пытается определить BUY/SELL/HOLD на основе текста.
        
        Args:
            text: Текст обоснования
            
        Returns:
            str: 'BUY', 'SELL', или 'HOLD'
        """
        text_lower = text.lower()
        if "long position" in text_lower or "buy" in text_lower or "strong buy" in text_lower:
            return "BUY"
        elif "short position" in text_lower or "sell" in text_lower or "strong sell" in text_lower:
            return "SELL"
        else:
            return "HOLD"
    
    def generate_reasoning_for_ticker(self, ticker: str, metrics: Dict, side: str, force_refresh: bool = False) -> Optional[Dict]:
        """
        Генерирует обоснование для конкретного тикера.
        
        Args:
            ticker: Тикер акции
            metrics: Словарь с метриками тикера
            side: Сторона позиции ('long' или 'short')
            force_refresh: Принудительное обновление, даже если кэш не устарел
            
        Returns:
            Optional[Dict]: Словарь с обоснованием и рекомендацией или None в случае ошибки
        """
        ticker = ticker.upper()
        
        # Проверяем наличие API ключа
        self._check_api_key()
        
        # Проверяем кэш, если не требуется принудительное обновление
        if not force_refresh:
            cached = self.get_cached_reasoning(ticker)
            if cached:
                return cached
        
        # Формируем промпт для OpenAI
        prompt = self._create_reasoning_prompt(ticker, metrics, side)
        
        try:
            # Вызываем OpenAI API используя новый клиент
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a professional investment analyst in a hedge fund."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=600,
                temperature=0.7
            )
            
            # Извлекаем текст ответа
            if response and response.choices and len(response.choices) > 0:
                reasoning_text = response.choices[0].message.content.strip()
                
                # Извлекаем рекомендацию из текста
                recommendation = self._extract_recommendation_from_text(reasoning_text)
                
                # Формируем результат
                result = {
                    "ticker": ticker,
                    "text": reasoning_text,
                    "recommendation": recommendation,
                    "generated_at": datetime.now().isoformat()
                }
                
                # Кэшируем результат
                self.cache_reasoning_json(ticker, result)
                # Для обратной совместимости сохраняем и в старом формате
                self.cache_reasoning(ticker, reasoning_text)
                
                logger.info(f"Сгенерировано обоснование для {ticker} ({len(reasoning_text)} символов, рекомендация: {recommendation})")
                return result
            else:
                logger.error(f"Неожиданный формат ответа от OpenAI API для {ticker}")
                return None
                
        except Exception as e:
            logger.error(f"Ошибка при генерации обоснования для {ticker}: {e}")
            return None
    
    def generate_reasoning_batch(self, data: Union[pd.DataFrame, List[Dict]], side_map: Optional[Dict[str, str]] = None) -> Dict[str, Dict]:
        """
        Генерирует обоснования для всех тикеров в DataFrame или списке словарей.
        
        Args:
            data: DataFrame или список словарей с метриками тикеров
            side_map: Словарь соответствия тикеров и сторон позиции (long/short)
                      Если None, определяется на основе composite_score
            
        Returns:
            Dict[str, Dict]: Словарь с обоснованиями и рекомендациями для каждого тикера
        """
        # Проверяем наличие API ключа
        self._check_api_key()
        
        # Преобразуем DataFrame в список словарей, если нужно
        if isinstance(data, pd.DataFrame):
            records = data.to_dict('records')
        else:
            records = data
        
        results = {}
        
        # Определяем side, если не указан явно
        if side_map is None:
            side_map = {}
            for record in records:
                ticker = record.get('ticker', '')
                if not ticker:
                    continue
                    
                # Определяем сторону позиции на основе composite_score
                if 'composite_score' in record:
                    side_map[ticker] = 'long' if record['composite_score'] > 0 else 'short'
                else:
                    # Если нет composite_score, используем 'unknown'
                    side_map[ticker] = 'unknown'
        
        # Генерируем обоснования для каждого тикера
        for record in records:
            ticker = record.get('ticker', '')
            if not ticker:
                continue
            
            side = side_map.get(ticker, 'unknown')
            
            reasoning_result = self.generate_reasoning_for_ticker(ticker, record, side)
            if reasoning_result:
                results[ticker] = reasoning_result
        
        logger.info(f"Сгенерированы обоснования для {len(results)} из {len(records)} тикеров")
        return results
    
    def update_reasoning_file(self, ticker: str, text: str, recommendation: str = None) -> bool:
        """
        Обновляет файл обоснования для тикера вручную.
        
        Args:
            ticker: Тикер акции
            text: Новый текст обоснования
            recommendation: Рекомендация (BUY/SELL/HOLD)
            
        Returns:
            bool: True если успешно обновлено
        """
        ticker = ticker.upper()
        if recommendation is None:
            recommendation = self._extract_recommendation_from_text(text)
        
        result = {
            "ticker": ticker,
            "text": text,
            "recommendation": recommendation,
            "generated_at": datetime.now().isoformat()
        }
        
        # Сохраняем в обоих форматах
        self.cache_reasoning_json(ticker, result)
        self.cache_reasoning(ticker, text)
        
        return True
    
    def _create_reasoning_prompt(self, ticker: str, metrics: Dict, side: str) -> str:
        """
        Создает промпт для OpenAI API.
        
        Args:
            ticker: Тикер акции
            metrics: Словарь с метриками тикера
            side: Сторона позиции ('long' или 'short')
            
        Returns:
            str: Сформированный промпт
        """
        # Определение позиции тикера в рейтинге (заглушка, просто для примера)
        rank = metrics.get('rank', 'N/A')
        total_universe = 100  # Размер S&P 500 (201-300)
        
        # Извлекаем метрики, с заменой None на 'N/A'
        # Фундаментальные метрики
        pe_ratio = metrics.get('pe_ratio', 'N/A')
        eps_growth_12m = metrics.get('eps_growth_12m', 'N/A')
        revenue_growth_yoy = metrics.get('revenue_growth_yoy', 'N/A')
        peg_ratio = metrics.get('peg_ratio', 'N/A')
        roe = metrics.get('roe', 'N/A')
        price_to_book = metrics.get('price_to_book', 'N/A')
        price_to_sales = metrics.get('price_to_sales', 'N/A')
        forward_pe = metrics.get('forward_pe', 'N/A')
        dividend_yield = metrics.get('dividend_yield', 'N/A')
        ev_to_ebitda = metrics.get('ev_to_ebitda', 'N/A')
        debt_equity = metrics.get('debt_equity', 'N/A')
        
        # Технические индикаторы
        momentum_3m = metrics.get('momentum_3m', 'N/A')
        volatility_3m = metrics.get('volatility_3m', 'N/A')
        avg_volume_10d = metrics.get('avg_volume_10d', 'N/A')
        price_change_ytd = metrics.get('price_change_ytd', 'N/A')
        rsi = metrics.get('rsi', 'N/A')
        price_vs_sma_50 = metrics.get('price_vs_sma_50', 'N/A')
        price_vs_sma_200 = metrics.get('price_vs_sma_200', 'N/A')
        
        # Аналитические метрики
        sentiment_score = metrics.get('sentiment_score', 'N/A')
        market_cap = metrics.get('market_cap', 'N/A')
        consensus_score = metrics.get('consensus_score', 'N/A')
        analyst_rating_trend = metrics.get('analyst_rating_trend', 'N/A')
        target_high = metrics.get('target_high', 'N/A')
        target_low = metrics.get('target_low', 'N/A')
        target_mean = metrics.get('target_mean', 'N/A')
        price_to_target = metrics.get('price_to_target', 'N/A')
        eps_surprise_percent = metrics.get('eps_surprise_percent', 'N/A')
        earnings_beat_rate = metrics.get('earnings_beat_rate', 'N/A')
        
        # Количество рекомендаций аналитиков
        strong_buy = metrics.get('strong_buy', 'N/A')
        buy = metrics.get('buy', 'N/A')
        hold = metrics.get('hold', 'N/A')
        sell = metrics.get('sell', 'N/A')
        strong_sell = metrics.get('strong_sell', 'N/A')
        analyst_count = metrics.get('analyst_count', 'N/A')
        
        # Форматируем числовые значения для более читаемого вывода
        for key, value in metrics.items():
            if isinstance(value, float):
                if abs(value) > 1000000:
                    metrics[key] = f"{value/1000000:.2f}M"
                elif abs(value) > 1000:
                    metrics[key] = f"{value/1000:.2f}K"
                else:
                    metrics[key] = f"{value:.2f}"
        
        # Создаем промпт
        prompt = f"""You are an investment analyst in a hedge fund running a long/short market-neutral equity strategy. For the stock {ticker}, which ranks #{rank} in the {side} selection out of {total_universe} tickers, write a 5-7 sentence investment rationale.

Base your analysis on the following metrics:

Fundamental Metrics:
- P/E Ratio: {pe_ratio}
- Forward P/E: {forward_pe}
- PEG Ratio: {peg_ratio}
- Price/Book: {price_to_book}
- Price/Sales: {price_to_sales}
- EV/EBITDA: {ev_to_ebitda}
- Dividend Yield: {dividend_yield}
- ROE: {roe}
- EPS Growth (12M): {eps_growth_12m}
- Revenue Growth YoY: {revenue_growth_yoy}
- Debt/Equity: {debt_equity}

Technical Indicators:
- Momentum (3M): {momentum_3m}
- Volatility (3M): {volatility_3m}
- RSI: {rsi}
- Price vs SMA50: {price_vs_sma_50}
- Price vs SMA200: {price_vs_sma_200}
- Price Change YTD: {price_change_ytd}
- Avg Volume (10D): {avg_volume_10d}

Analyst Metrics:
- Consensus Score: {consensus_score}
- Analyst Rating Trend: {analyst_rating_trend}
- Target Price (Mean): {target_mean}
- Price to Target Ratio: {price_to_target}
- EPS Surprise %: {eps_surprise_percent}
- Earnings Beat Rate: {earnings_beat_rate}
- Analyst Count: {analyst_count}
- Strong Buy: {strong_buy}
- Buy: {buy}
- Hold: {hold}
- Sell: {sell}
- Strong Sell: {strong_sell}

Other:
- Sentiment Score: {sentiment_score}
- Market Cap: {market_cap} USD

Be specific about how this stock compares to the rest of the universe (above-average, low volatility, strong upside drivers, etc).
Evaluate both the fundamental and technical picture, with particular attention to the valuation, growth prospects, and recent price momentum.
Consider analyst opinions but form your own assessment based on all data points.
Avoid generic statements. Output should be institutional and suitable for an internal investment memo.

IMPORTANT: End your analysis with a clear recommendation - either "RECOMMENDATION: BUY", "RECOMMENDATION: SELL", or "RECOMMENDATION: HOLD" based on your conclusion."""
        
        return prompt
    
    def get_all_cached_reasoning(self) -> Dict[str, Dict]:
        """
        Получает все кэшированные обоснования.
        
        Returns:
            Dict[str, Dict]: Словарь с обоснованиями для каждого тикера
        """
        results = {}
        
        # Проверяем новый формат .json
        for file in self.reasoning_dir.glob('*.json'):
            ticker = file.stem.upper()
            
            # Проверка срока действия кэша
            cache_age = time.time() - file.stat().st_mtime
            if cache_age > self.ttl:
                continue
            
            try:
                with open(file, 'r') as f:
                    data = json.load(f)
                    results[ticker] = data
            except json.JSONDecodeError:
                logger.error(f"Ошибка декодирования JSON для {ticker}")
        
        # Проверяем старый формат .md, если тикер ещё не загружен
        for file in self.reasoning_dir.glob('*.md'):
            ticker = file.stem.upper()
            
            if ticker in results:
                continue
                
            # Проверка срока действия кэша
            cache_age = time.time() - file.stat().st_mtime
            if cache_age > self.ttl:
                continue
            
            # Загрузка кэшированного обоснования
            with open(file, 'r') as f:
                content = f.read()
                recommendation = self._extract_recommendation_from_text(content)
                results[ticker] = {
                    'ticker': ticker,
                    'text': content,
                    'recommendation': recommendation,
                    'generated_at': datetime.fromtimestamp(file.stat().st_mtime).isoformat()
                }
        
        logger.info(f"Загружено {len(results)} кэшированных обоснований")
        return results
    
    def get_recommendations(self, tickers: List[str], force_refresh: bool = False) -> Dict[str, str]:
        """
        Получает только рекомендации (BUY/SELL/HOLD) для списка тикеров.
        
        Args:
            tickers: Список тикеров
            force_refresh: Принудительное обновление, даже если кэш не устарел
            
        Returns:
            Dict[str, str]: Словарь с рекомендациями для каждого тикера
        """
        results = {}
        
        for ticker in tickers:
            ticker = ticker.upper()
            cached = self.get_cached_reasoning(ticker)
            
            if cached and not force_refresh:
                results[ticker] = cached.get('recommendation', 'HOLD')
            else:
                # Если нет кэша или нужно обновление, пока возвращаем HOLD
                # Реальные данные должны быть загружены через generate_reasoning_for_ticker
                results[ticker] = 'HOLD'
        
        return results 