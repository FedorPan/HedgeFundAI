import os
import json
import logging
import time
import random
import finnhub
import requests
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

# Try to import Alpaca, but don't fail if it's not available
try:
    from alpaca.trading.client import TradingClient
    from alpaca.data.historical import StockHistoricalDataClient
    from alpaca.data.requests import StockBarsRequest
    from alpaca.data.timeframe import TimeFrame
    ALPACA_AVAILABLE = True
except ImportError:
    logger = logging.getLogger(__name__)
    logger.warning("Alpaca SDK not found. Trading functionality will be limited.")
    ALPACA_AVAILABLE = False

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RateLimiter:
    """Простой ограничитель частоты запросов к API"""
    def __init__(self, calls_per_minute=60):
        self.calls_per_minute = calls_per_minute
        self.min_interval = 60.0 / calls_per_minute
        self.last_call = 0
        
    def __enter__(self):
        elapsed = time.time() - self.last_call
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.last_call = time.time()


class MarketDataService:
    """
    Сервис для сбора и обработки рыночных данных по тикерам.
    
    Получает данные из различных источников (Finnhub), рассчитывает метрики
    и кэширует результаты.
    
    Примечание: Данные о ценах поступают с задержкой из-за ограничений API.
    """
    
    def __init__(self, cache_dir='.cache', ttl_days=1, api_keys=None):
        """
        Инициализация сервиса для сбора рыночных данных.
        
        Args:
            cache_dir: Директория для кэширования данных
            ttl_days: Время жизни кэша в днях
            api_keys: Словарь с API ключами (finnhub)
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True, parents=True)
        
        self.ttl = ttl_days * 86400  # в секундах
        
        # Получение API ключей из параметров или переменных окружения
        self.finnhub_key = api_keys.get('finnhub') if api_keys else os.environ.get('FINNHUB_API_KEY')
        self.alpaca_key = api_keys.get('alpaca_key') if api_keys else os.environ.get('ALPACA_API_KEY')
        self.alpaca_secret = api_keys.get('alpaca_secret') if api_keys else os.environ.get('ALPACA_API_SECRET')
        
        # Инициализация клиентов API
        self.finnhub_client = finnhub.Client(api_key=self.finnhub_key) if self.finnhub_key else None
        
        # Initialize Alpaca clients only if the library is available
        if ALPACA_AVAILABLE and self.alpaca_key and self.alpaca_secret:
            try:
                self.alpaca_trading_client = TradingClient(
                    api_key=self.alpaca_key,
                    secret_key=self.alpaca_secret,
                    paper=True  # Использовать paper trading
                )
                
                self.alpaca_data_client = StockHistoricalDataClient(
                    api_key=self.alpaca_key,
                    secret_key=self.alpaca_secret
                )
            except Exception as e:
                logger.warning(f"Failed to initialize Alpaca clients: {e}")
                self.alpaca_trading_client = None
                self.alpaca_data_client = None
        else:
            self.alpaca_trading_client = None
            self.alpaca_data_client = None
        
        # Управление ограничением запросов API
        self.finnhub_rate_limiter = RateLimiter(calls_per_minute=30)  # Более консервативный лимит
        
        # Кэш для ранжированных S&P500 тикеров
        self.sp500_cache = {}
        
        logger.info(f"MarketDataService инициализирован. Finnhub API: {'доступен' if self.finnhub_client else 'недоступен'}")
    
    def get_sp500_tickers(self, start_rank=51, end_rank=500):
        """
        Получение списка тикеров из S&P500 в заданном диапазоне ранков.
        
        Args:
            start_rank: Начальный ранк (позиция) в S&P500
            end_rank: Конечный ранк (позиция) в S&P500
            
        Returns:
            List[str]: Список тикеров
        """
        cache_key = f"sp500_{start_rank}_{end_rank}"
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        # Проверка кэша
        if cache_file.exists():
            cache_age = time.time() - cache_file.stat().st_mtime
            if cache_age < self.ttl:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    logger.info(f"Загружены тикеры S&P500 из кэша ({len(data['tickers'])} тикеров)")
                    return data['tickers']
        
        try:
            # Используем Wikipedia для получения списка S&P500
            logger.info(f"Получение списка S&P500 тикеров (ранги {start_rank}-{end_rank})...")
            
            # Альтернативный метод - использование pandas для чтения таблицы S&P500 из Wikipedia
            tables = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
            sp500_table = tables[0]
            tickers = sp500_table['Symbol'].tolist()
            
            # Очистка тикеров (удаление точек в некоторых тикерах, которые могут создавать проблемы с API)
            tickers = [ticker.replace('.', '-') for ticker in tickers]
            
            # Фильтруем по ранку
            result_tickers = tickers[start_rank-1:end_rank]
            
            # Сохраняем в кэш
            with open(cache_file, 'w') as f:
                json.dump({
                    'tickers': result_tickers,
                    'timestamp': time.time()
                }, f)
            
            logger.info(f"Получено {len(result_tickers)} тикеров S&P500")
            return result_tickers
        
        except Exception as e:
            logger.error(f"Ошибка при получении S&P500 тикеров: {e}")
            # Fallback - предопределенный список или локально сохраненный
            fallback_tickers = self._get_fallback_tickers()
            logger.info(f"Использование fallback списка тикеров ({len(fallback_tickers)} тикеров)")
            return fallback_tickers
    
    def get_ticker_data(self, ticker, force_refresh=False):
        """
        Получение всех данных по тикеру с использованием кэша.
        
        Args:
            ticker: Тикер акции
            force_refresh: Принудительное обновление данных
            
        Returns:
            Dict: Данные по тикеру
        """
        ticker = ticker.upper()
        cache_file = self.cache_dir / f"{ticker}.json"
        
        # Проверка кэша, если не требуется принудительное обновление
        if not force_refresh and cache_file.exists():
            cache_age = time.time() - cache_file.stat().st_mtime
            if cache_age < self.ttl:
                with open(cache_file, 'r') as f:
                    cached_data = json.load(f)
                    logger.info(f"Данные для {ticker} загружены из кэша")
                    return cached_data
        
        try:
            logger.info(f"Получение данных для {ticker}...")
            
            # Получение данных по тикеру из разных источников
            fundamental_data = self.get_fundamental_metrics(ticker)
            technical_data = self.get_technical_metrics(ticker)
            analyst_data = self.get_analyst_metrics(ticker)
            
            # Объединение данных
            ticker_data = {
                'ticker': ticker,
                'fundamental': fundamental_data,
                'technical': technical_data,
                'analyst': analyst_data,
                'updated_at': time.time()
            }
            
            # Сохранение в кэш
            with open(cache_file, 'w') as f:
                json.dump(ticker_data, f)
            
            logger.info(f"Данные для {ticker} успешно получены и сохранены в кэш")
            return ticker_data
        
        except Exception as e:
            logger.error(f"Ошибка при получении данных для {ticker}: {e}")
            
            # Проверка, есть ли данные в кэше (даже если устаревшие)
            if cache_file.exists():
                with open(cache_file, 'r') as f:
                    cached_data = json.load(f)
                    logger.warning(f"Используются устаревшие данные из кэша для {ticker}")
                    return cached_data
            
            # Если нет данных в кэше, возвращаем пустую структуру
            return self._get_empty_ticker_data(ticker)
    
    def get_fundamental_metrics(self, ticker):
        """
        Получение фундаментальных метрик через Finnhub API.
        
        Args:
            ticker: Тикер акции
            
        Returns:
            Dict: Фундаментальные метрики
        """
        if not self.finnhub_client:
            logger.warning(f"Finnhub API недоступен для {ticker}")
            return {}
        
        result = {}
        
        try:
            # Получение базовых финансовых показателей
            with self.finnhub_rate_limiter:
                basic_financials = self.finnhub_client.company_basic_financials(ticker, 'all')
                
                if basic_financials and 'metric' in basic_financials:
                    metrics = basic_financials['metric']
                    
                    # Базовые коэффициенты
                    result['pe_ratio'] = metrics.get('peBasicExclExtraTTM')
                    result['debt_equity'] = metrics.get('totalDebt/totalEquityQuarterly')
                    result['roe'] = metrics.get('roeTTM')
                    result['peg_ratio'] = metrics.get('pegRatioTTM')
                    result['market_cap'] = metrics.get('marketCapitalization')
                    
                    # Дополнительные коэффициенты оценки
                    result['price_to_book'] = metrics.get('pbQuarterly')
                    result['price_to_sales'] = metrics.get('psNonCyclicalTTM')
                    result['forward_pe'] = metrics.get('forwardPE')
                    result['dividend_yield'] = metrics.get('dividendYieldIndicatedAnnual')
                    result['ev_to_ebitda'] = metrics.get('enterpriseValueOverEBITDA')
                    
                    # Метрики прибыльности
                    result['gross_margin'] = metrics.get('grossMargin5Y')
                    result['operating_margin'] = metrics.get('operatingMarginTTM')
                    result['net_margin'] = metrics.get('netProfitMargin5Y')
                    result['return_on_assets'] = metrics.get('roaTTM')
                    result['return_on_capital'] = metrics.get('roicTTM')
                    
                    # Дополнительные метрики роста
                    result['revenue_growth_5y'] = metrics.get('revenueGrowth5Y')
                    result['eps_growth_5y'] = metrics.get('epsGrowth5Y')
                    
                    logger.info(f"Базовые финансовые метрики получены для {ticker}")
            
            # Получение данных о доходах (квартальные) для расчета роста EPS
            with self.finnhub_rate_limiter:
                financials = self.finnhub_client.financials(ticker, 'ic', 'quarterly')
                
                # Используем новый метод для расчета EPS из финансовых данных
                eps_growth = self.calculate_eps_from_financials(ticker, financials)
                if eps_growth is not None:
                    result['eps_growth_12m'] = eps_growth
                    logger.info(f"Рост EPS рассчитан для {ticker}: {eps_growth:.2f}%")
                
                # Если у нас есть финансовые данные, рассчитаем рост выручки
                if financials and 'financials' in financials and len(financials['financials']) >= 5:
                    financials_data = financials['financials']
                    
                    # Сортировка по дате (от новых к старым)
                    financials_data = sorted(financials_data, key=lambda x: x.get('period', ''), reverse=True)
                    
                    # Расчет роста выручки (YoY)
                    if len(financials_data) >= 5:
                        current_revenue = financials_data[0].get('revenue', None)
                        year_ago_revenue = financials_data[4].get('revenue', None)
                        
                        if current_revenue is not None and year_ago_revenue is not None and year_ago_revenue != 0:
                            result['revenue_growth_yoy'] = ((current_revenue / year_ago_revenue) - 1) * 100
                            logger.info(f"Рост выручки рассчитан для {ticker}: {result['revenue_growth_yoy']:.2f}%")
                    
                    # Расчет роста выручки квартал к кварталу (QoQ)
                    if len(financials_data) >= 2:
                        current_revenue = financials_data[0].get('revenue', None)
                        prev_quarter_revenue = financials_data[1].get('revenue', None)
                        
                        if current_revenue is not None and prev_quarter_revenue is not None and prev_quarter_revenue != 0:
                            result['revenue_growth_qq'] = ((current_revenue / prev_quarter_revenue) - 1) * 100
                            logger.info(f"Рост выручки QoQ рассчитан для {ticker}: {result['revenue_growth_qq']:.2f}%")
            
            # Получение данных о рекомендациях аналитиков для расчета тренда
            try:
                with self.finnhub_rate_limiter:
                    recommendations = self.finnhub_client.recommendation_trends(ticker)
                    if recommendations:
                        # Анализ тренда рекомендаций
                        if len(recommendations) >= 2:
                            current = recommendations[0]
                            previous = recommendations[1]
                            
                            # Простая метрика тренда
                            current_score = self._calculate_recommendation_score(current)
                            previous_score = self._calculate_recommendation_score(previous)
                            
                            result['analyst_rating_trend'] = current_score - previous_score
            except Exception as e:
                logger.warning(f"Ошибка при получении рекомендаций для {ticker}: {e}")
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка при получении фундаментальных метрик для {ticker}: {e}")
            return {}
    
    def calculate_eps_from_financials(self, ticker, financials):
        """
        Рассчитывает рост EPS на основе финансовых данных из API Finnhub.
        
        Этот метод извлекает данные о прибыли на акцию (EPS) из финансовых отчетов 10-Q и 10-K,
        группирует их по кварталам и рассчитывает годовой рост.
        
        Args:
            ticker: Тикер акции
            financials: Данные из ответа Finnhub API financials endpoint
            
        Returns:
            float: Рост EPS в процентах за последние 12 месяцев или None если расчет невозможен
        """
        if not financials or 'financials' not in financials:
            logger.warning(f"Нет финансовых данных для расчета EPS для {ticker}")
            return None
            
        try:
            # Для отладки можно вывести URL запроса
            api_url = f"https://finnhub.io/api/v1/stock/financials?symbol={ticker}&statement=ic&freq=quarterly"
            logger.debug(f"API URL для получения финансовых данных: {api_url}")
            
            financials_data = financials.get('financials', [])
            if not financials_data or len(financials_data) < 5:
                logger.warning(f"Недостаточно финансовых данных для расчета EPS для {ticker} (нужно минимум 5 кварталов)")
                return None
                
            # Сортировка по дате (от новых к старым)
            financials_data = sorted(financials_data, key=lambda x: x.get('period', ''), reverse=True)
            
            # Извлекаем EPS данные из каждого финансового отчета
            eps_values = []
            for quarter_data in financials_data[:8]:  # Берем данные за последние 8 кварталов
                period = quarter_data.get('period')
                
                # Сначала проверяем специфичные ключи для EPS
                eps = None
                
                # Проверяем разные возможные ключи для EPS
                for eps_key in ['dilutedEPS', 'basicEPS', 'epsDiluted', 'eps']:
                    if eps_key in quarter_data and quarter_data[eps_key] is not None:
                        eps = quarter_data[eps_key]
                        logger.debug(f"Найден EPS для {ticker} за {period}: {eps} (ключ: {eps_key})")
                        break
                
                # Если EPS не найден напрямую, попробуем рассчитать из net income и shares outstanding
                if eps is None:
                    net_income = quarter_data.get('netIncome')
                    shares = None
                    
                    # Проверяем разные возможные ключи для количества акций
                    for shares_key in ['weightedAverageShsOut', 'weightedAverageShsOutDil']:
                        if shares_key in quarter_data and quarter_data[shares_key] is not None and quarter_data[shares_key] != 0:
                            shares = quarter_data[shares_key]
                            break
                    
                    if net_income is not None and shares is not None and shares != 0:
                        eps = net_income / shares
                        logger.debug(f"Рассчитан EPS для {ticker} за {period}: {eps} (из net income и shares)")
                
                if eps is not None:
                    eps_values.append({
                        'period': period,
                        'eps': eps
                    })
            
            if len(eps_values) < 5:
                logger.warning(f"Недостаточно данных EPS для {ticker} (найдено только {len(eps_values)} кварталов)")
                return None
            
            # Группируем данные по кварталам для сравнения год к году
            current_quarter = eps_values[0]
            year_ago_quarter = None
            
            # Ищем квартал годом ранее
            current_period = current_quarter['period']
            for value in eps_values[1:]:
                # Проверяем совпадение квартала (Q1/Q2/Q3/Q4)
                if current_period[-2:] == value['period'][-2:] and int(current_period[:4]) - 1 == int(value['period'][:4]):
                    year_ago_quarter = value
                    break
            
            # Если не найден точный квартал, берем примерно 4-й квартал назад
            if year_ago_quarter is None and len(eps_values) >= 5:
                year_ago_quarter = eps_values[4]
                logger.debug(f"Используем приблизительный год назад для {ticker}: {year_ago_quarter['period']}")
            
            # Рассчитываем рост EPS
            if year_ago_quarter is not None:
                current_eps = current_quarter['eps']
                year_ago_eps = year_ago_quarter['eps']
                
                if year_ago_eps != 0:
                    eps_growth = ((current_eps / year_ago_eps) - 1) * 100
                    
                    # Ограничение экстремальных значений (например, восстановление после убытков)
                    if eps_growth > 500:
                        eps_growth = 500
                    elif eps_growth < -500:
                        eps_growth = -500
                    
                    logger.info(f"Рост EPS для {ticker}: {eps_growth:.2f}% ({current_period} vs {year_ago_quarter['period']})")
                    return eps_growth
                else:
                    logger.warning(f"EPS год назад равен нулю для {ticker}, невозможно рассчитать рост")
                    return None
            else:
                logger.warning(f"Не найден сопоставимый квартал год назад для {ticker}")
                return None
                
        except Exception as e:
            logger.error(f"Ошибка при расчете EPS для {ticker}: {str(e)}")
            return None
    
    def get_technical_metrics(self, ticker):
        """
        Получение технических метрик через Finnhub API (свечные графики).
        
        Args:
            ticker: Тикер акции
            
        Returns:
            Dict: Технические метрики
        """
        if not self.finnhub_client:
            logger.warning(f"Finnhub API недоступен для {ticker}")
            return {}
        
        try:
            # Получение данных за 200 дней (для расчета MA200)
            end_timestamp = int(time.time())  # Текущее время в Unix timestamp
            start_timestamp = end_timestamp - (250 * 24 * 60 * 60)  # 250 дней назад для обеспечения достаточных данных
            
            # Получение дневных свечей
            with self.finnhub_rate_limiter:
                candles = self.finnhub_client.stock_candles(
                    ticker,
                    'D',  # Дневные свечи
                    start_timestamp, 
                    end_timestamp
                )
            
            # Проверка статуса ответа
            if candles['s'] == 'ok' and len(candles['c']) > 0:
                # Преобразуем данные в DataFrame
                df = pd.DataFrame({
                    'timestamp': pd.to_datetime(candles['t'], unit='s'),
                    'open': candles['o'],
                    'high': candles['h'],
                    'low': candles['l'],
                    'close': candles['c'],
                    'volume': candles['v']
                })
                
                # Сортировка по дате
                df = df.sort_values('timestamp')
                
                # Расчет метрик
                result = {}
                
                # Последняя цена закрытия
                last_price = df['close'].iloc[-1] if len(df) > 0 else None
                result['latest_price'] = last_price
                
                # 3-месячная доходность (последние ~90 дней)
                if len(df) > 90:
                    first_price = df['close'].iloc[-90]
                    momentum_3m = (last_price / first_price - 1) * 100
                    result['momentum_3m'] = momentum_3m
                elif len(df) > 1:
                    # Используем что есть, если нет полных 90 дней
                    first_price = df['close'].iloc[0]
                    momentum_3m = (last_price / first_price - 1) * 100
                    result['momentum_3m'] = momentum_3m
                
                # Волатильность
                if len(df) > 20:  # Минимум 20 дней для расчета волатильности
                    daily_returns = df['close'].pct_change().dropna()
                    volatility_3m = daily_returns.tail(90).std() * (252 ** 0.5) * 100  # Годовая волатильность в %
                    result['volatility_3m'] = volatility_3m
                    # Добавляем поле для соответствия фронтенду
                    result['volatility'] = volatility_3m
                
                # Средний объем за 10 дней
                if len(df) >= 10:
                    avg_volume_10d = df['volume'].tail(10).mean()
                    result['avg_volume_10d'] = avg_volume_10d
                    # Добавляем поле для соответствия фронтенду
                    result['avgVolume10d'] = avg_volume_10d
                elif len(df) > 0:
                    avg_volume_10d = df['volume'].mean()
                    result['avg_volume_10d'] = avg_volume_10d
                    # Добавляем поле для соответствия фронтенду
                    result['avgVolume10d'] = avg_volume_10d
                
                # Расчет скользящих средних
                if len(df) >= 50:
                    # 50-дневная скользящая средняя
                    df['sma_50'] = df['close'].rolling(window=50).mean()
                    sma_50 = df['sma_50'].iloc[-1]
                    result['sma_50'] = sma_50
                    
                    price_to_sma_50 = ((last_price / sma_50) - 1) * 100 if sma_50 > 0 else None
                    result['price_to_sma_50'] = price_to_sma_50
                    
                    # Добавляем поля для соответствия фронтенду
                    result['price_vs_sma_50'] = price_to_sma_50
                    result['priceVsSma50'] = price_to_sma_50
                    
                    logger.debug(f"Цена к SMA50 для {ticker}: {price_to_sma_50:.2f}%")
                
                if len(df) >= 200:
                    # 200-дневная скользящая средняя
                    df['sma_200'] = df['close'].rolling(window=200).mean()
                    sma_200 = df['sma_200'].iloc[-1]
                    result['sma_200'] = sma_200
                    
                    price_to_sma_200 = ((last_price / sma_200) - 1) * 100 if sma_200 > 0 else None
                    result['price_to_sma_200'] = price_to_sma_200
                    
                    # Добавляем поля для соответствия фронтенду
                    result['price_vs_sma_200'] = price_to_sma_200
                    result['priceVsSma200'] = price_to_sma_200
                    
                    logger.debug(f"Цена к SMA200 для {ticker}: {price_to_sma_200:.2f}%")
                
                # Расчет RSI (14-дневный)
                if len(df) >= 15:  # Нужно минимум 15 дней для 14-дневного RSI
                    try:
                        # Расчет изменений
                        delta = df['close'].diff()
                        
                        # Получение положительных и отрицательных изменений
                        gain = delta.where(delta > 0, 0)
                        loss = -delta.where(delta < 0, 0)
                        
                        # Расчет среднего за 14 дней
                        avg_gain = gain.rolling(window=14).mean()
                        avg_loss = loss.rolling(window=14).mean()
                        
                        # Расчет относительной силы
                        rs = avg_gain / avg_loss
                        
                        # Расчет RSI
                        rsi = 100 - (100 / (1 + rs))
                        
                        # Получение последнего значения RSI
                        last_rsi = rsi.iloc[-1]
                        result['rsi_14'] = last_rsi
                        result['rsi'] = last_rsi  # Для соответствия фронтенду
                        logger.debug(f"RSI(14) для {ticker}: {last_rsi:.2f}")
                    except Exception as e:
                        logger.warning(f"Ошибка при расчете RSI для {ticker}: {e}")
                
                # Изменение с начала года (YTD)
                try:
                    ytd_start_date = datetime(datetime.now().year, 1, 1)
                    ytd_data = df[df['timestamp'] >= ytd_start_date]
                    
                    if not ytd_data.empty and len(ytd_data) > 1:
                        ytd_first = ytd_data['close'].iloc[0]
                        ytd_last = ytd_data['close'].iloc[-1]
                        price_change_ytd = (ytd_last / ytd_first - 1) * 100
                        result['price_change_ytd'] = price_change_ytd
                        result['priceChangeYtd'] = price_change_ytd  # Для соответствия фронтенду
                except Exception as e:
                    logger.warning(f"Ошибка при расчете YTD для {ticker}: {e}")
                
                return result
            else:
                logger.warning(f"Нет данных о свечах для {ticker} или ошибка в ответе API")
                return {}
        
        except Exception as e:
            logger.error(f"Ошибка при получении технических метрик для {ticker}: {e}")
            return {}
    
    def get_analyst_metrics(self, ticker):
        """
        Получение аналитических метрик через Finnhub API (price target, рекомендации).
        
        Args:
            ticker: Тикер акции
            
        Returns:
            Dict: Аналитические метрики
        """
        if not self.finnhub_client:
            logger.warning(f"Finnhub API недоступен для {ticker}")
            return {}
        
        result = {}
        
        # Получение данных о целевых ценах аналитиков
        try:
            with self.finnhub_rate_limiter:
                price_targets = self.finnhub_client.price_target(ticker)
                
                if price_targets:
                    result['target_high'] = price_targets.get('targetHigh')
                    result['target_low'] = price_targets.get('targetLow')
                    result['target_mean'] = price_targets.get('targetMean')
                    result['target_median'] = price_targets.get('targetMedian')
                    result['last_updated'] = price_targets.get('lastUpdated')
                    
                    # Расчет разницы между текущей ценой и целевой
                    technical_metrics = self.get_technical_metrics(ticker)
                    current_price = technical_metrics.get('latest_price')
                    target_price = price_targets.get('targetMean')
                    
                    if current_price and target_price and current_price > 0:
                        price_to_target = ((target_price / current_price) - 1) * 100
                        result['price_to_target'] = price_to_target
                        logger.debug(f"Цена к целевой для {ticker}: {price_to_target:.2f}%")
        except Exception as e:
            logger.warning(f"Ошибка при получении целевых цен для {ticker}: {e}")
        
        # Получение рекомендаций аналитиков
        try:
            with self.finnhub_rate_limiter:
                recommendations = self.finnhub_client.recommendation_trends(ticker)
                
                if recommendations and len(recommendations) > 0:
                    latest_rec = recommendations[0]
                    
                    # Сохраняем детальную разбивку рекомендаций
                    result['strong_buy'] = latest_rec.get('strongBuy', 0)
                    result['buy'] = latest_rec.get('buy', 0)
                    result['hold'] = latest_rec.get('hold', 0)
                    result['sell'] = latest_rec.get('sell', 0)
                    result['strong_sell'] = latest_rec.get('strongSell', 0)
                    
                    # Обновляем имена полей для соответствия фронтенду
                    result['strongBuy'] = result['strong_buy']
                    result['strongSell'] = result['strong_sell']
                    
                    # Расчет общего количества рекомендаций
                    total_recommendations = (
                        result['strong_buy'] +
                        result['buy'] +
                        result['hold'] +
                        result['sell'] +
                        result['strong_sell']
                    )
                    
                    result['analyst_count'] = total_recommendations
                    result['total_recommendations'] = total_recommendations
                    
                    # Рассчитываем консенсус-рейтинг (от -1 до 1)
                    if total_recommendations > 0:
                        consensus_score = self._calculate_recommendation_score(latest_rec)
                        result['consensus_score'] = consensus_score
                        
                        # Определяем словесный рейтинг на основе скора
                        if consensus_score > 0.6:
                            result['consensus_rating'] = "Strong Buy"
                        elif consensus_score > 0.2:
                            result['consensus_rating'] = "Buy"
                        elif consensus_score > -0.2:
                            result['consensus_rating'] = "Hold"
                        elif consensus_score > -0.6:
                            result['consensus_rating'] = "Sell"
                        else:
                            result['consensus_rating'] = "Strong Sell"
                    
                    # Анализ тренда при наличии предыдущих рекомендаций
                    if len(recommendations) >= 2:
                        current = recommendations[0]
                        previous = recommendations[1]
                        
                        current_score = self._calculate_recommendation_score(current)
                        previous_score = self._calculate_recommendation_score(previous)
                        
                        result['rating_trend'] = current_score - previous_score
                        
                        # Оценка направления тренда
                        if result['rating_trend'] > 0.1:
                            result['rating_trend_direction'] = "Improving"
                        elif result['rating_trend'] < -0.1:
                            result['rating_trend_direction'] = "Deteriorating"
                        else:
                            result['rating_trend_direction'] = "Stable"
                            
                            # Добавляем поле trend для соответствия фронтенду
                            result['trend'] = result['rating_trend_direction']
        except Exception as e:
            logger.warning(f"Ошибка при получении рекомендаций для {ticker}: {e}")
        
        # Получение оценок доходов (earnings surprises)
        try:
            with self.finnhub_rate_limiter:
                earnings = self.finnhub_client.company_earnings(ticker)
                
                if earnings and len(earnings) > 0:
                    # Берем последний квартал
                    latest_earnings = earnings[0]
                    
                    result['eps_actual'] = latest_earnings.get('actual')
                    result['eps_estimate'] = latest_earnings.get('estimate')
                    result['eps_quarter'] = latest_earnings.get('period')
                    
                    # Расчет surprise в процентах
                    if latest_earnings.get('estimate') and latest_earnings.get('estimate') != 0:
                        surprise_pct = (
                            (latest_earnings.get('actual', 0) - latest_earnings.get('estimate', 0)) / 
                            abs(latest_earnings.get('estimate', 1)) * 100
                        )
                        result['eps_surprise_pct'] = round(surprise_pct, 2)
                        result['eps_surprise_percent'] = result['eps_surprise_pct']  # Для соответствия фронтенду
                    
                    # Историю сюрпризов - последние 4 квартала
                    if len(earnings) >= 4:
                        surprise_history = []
                        beat_count = 0
                        
                        for i in range(min(4, len(earnings))):
                            q_data = earnings[i]
                            actual = q_data.get('actual')
                            estimate = q_data.get('estimate')
                            period = q_data.get('period')
                            
                            if actual is not None and estimate is not None and estimate != 0:
                                q_surprise = (actual - estimate) / abs(estimate) * 100
                                surprise_history.append({
                                    'period': period,
                                    'surprise_pct': round(q_surprise, 2)
                                })
                                
                                if actual > estimate:
                                    beat_count += 1
                        
                        result['eps_surprise_history'] = surprise_history
                        result['earnings_beat_rate'] = (beat_count / len(surprise_history) * 100) if surprise_history else 0
                        result['beat_rate'] = result['earnings_beat_rate']  # Для соответствия фронтенду
        except Exception as e:
            logger.warning(f"Ошибка при получении данных о доходах для {ticker}: {e}")
        
        return result
    
    def get_universe_data(self, tickers=None, force_refresh=False):
        """
        Получение данных для всех тикеров из вселенной.
        
        Args:
            tickers: Список тикеров (если None, будут использованы тикеры из S&P500 201-300)
            force_refresh: Принудительное обновление данных
            
        Returns:
            Dict[str, Dict]: Данные по всем тикерам
        """
        if tickers is None:
            tickers = self.get_sp500_tickers()
        
        logger.info(f"Получение данных для {len(tickers)} тикеров...")
        
        result = {}
        for ticker in tickers:
            try:
                ticker_data = self.get_ticker_data(ticker, force_refresh=force_refresh)
                result[ticker] = ticker_data
            except Exception as e:
                logger.error(f"Ошибка при получении данных для {ticker}: {e}")
        
        logger.info(f"Данные получены для {len(result)} из {len(tickers)} тикеров")
        return result
    
    # Вспомогательные методы
    
    def _get_fallback_tickers(self):
        """Возвращает предопределенный список тикеров S&P500 (ранги 201-300)"""
        return [
            "CBRE", "FANG", "MLM", "DAL", "MOH", "XYL", "ROL", "SWK", "AVY", "HOLX",
            "CHD", "LKQ", "WHR", "BBY", "DFS", "DOV", "SWKS", "JBHT", "SYF", "FDS",
            "LDOS", "PAYC", "UDR", "EXPD", "HPE", "DGX", "MRO", "ZBRA", "NDSN", "TSCO",
            "CF", "CTLT", "WDC", "WAT", "CMA", "PFG", "RCL", "BF.B", "BXP", "AKAM",
            "CLX", "TDY", "PKI", "VAR", "GL", "AAL", "FBHS", "CE", "RE", "WAB",
            "TFX", "STE", "RF", "COO", "BIO", "NLOK", "TER", "CHRW", "VRSN", "TAP",
            "HAS", "QRVO", "MOS", "GRMN", "BWA", "MHK", "STX", "PHM", "AOS", "ROK",
            "HST", "SNA", "NWL", "PWR", "WYNN", "LNT", "AAP", "LNC", "J", "NVR",
            "JKHY", "PNR", "WU", "PTC", "CRL", "CPB", "FFIV", "HSIC", "ALLE", "LUMN",
            "HBI", "HWM", "NWSA", "SEE", "DVA", "IRM", "PBCT", "DISH", "AIZ", "LYV"
        ]

    def _get_empty_ticker_data(self, ticker):
        """Создает пустую структуру данных для тикера"""
        return {
            'ticker': ticker,
            'fundamental': {},
            'technical': {},
            'analyst': {},
            'updated_at': time.time(),
            'no_data': True
        }

    def _calculate_recommendation_score(self, rec_data):
        """Рассчитывает числовой скор для рекомендаций аналитиков"""
        strong_buy = rec_data.get('strongBuy', 0)
        buy = rec_data.get('buy', 0)
        hold = rec_data.get('hold', 0)
        sell = rec_data.get('sell', 0)
        strong_sell = rec_data.get('strongSell', 0)
        
        total = strong_buy + buy + hold + sell + strong_sell
        if total == 0:
            return 0
        
        # Взвешенный скор от -1 до 1
        score = (strong_buy * 1.0 + buy * 0.5 + hold * 0 + sell * -0.5 + strong_sell * -1.0) / total
        return score 