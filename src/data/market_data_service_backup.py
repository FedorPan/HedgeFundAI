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
from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

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
        
        if self.alpaca_key and self.alpaca_secret:
            self.alpaca_trading_client = TradingClient(
                api_key=self.alpaca_key,
                secret_key=self.alpaca_secret,
                paper=True  # Использовать paper trading
            )
            
            self.alpaca_data_client = StockHistoricalDataClient(
                api_key=self.alpaca_key,
                secret_key=self.alpaca_secret
            )
        else:
            self.alpaca_trading_client = None
            self.alpaca_data_client = None
        
        # Управление ограничением запросов API
        self.finnhub_rate_limiter = RateLimiter(calls_per_minute=30)  # Более консервативный лимит
        
        # Кэш для ранжированных S&P500 тикеров
        self.sp500_cache = {}
        
        logger.info(f"MarketDataService инициализирован. Finnhub API: {'доступен' if self.finnhub_client else 'недоступен'}")
    
    def get_sp500_tickers(self, start_rank=201, end_rank=300):
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
            
            # Если нет данных в кэше, вернуть базовую структуру с пустыми данными
            empty_data = self._get_empty_ticker_data(ticker)
            logger.warning(f"Возвращаются пустые данные для {ticker}")
            return empty_data
    
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
        
        with self.finnhub_rate_limiter:
            try:
                # Запрос базовых финансовых показателей
                financials = self.finnhub_client.company_basic_financials(ticker, 'all')
                
                # Запрос профиля компании
                profile = self.finnhub_client.company_profile2(symbol=ticker)
                
                # Извлечение необходимых метрик
                metrics = financials.get('metric', {})
                
                result = {
                    'pe_ratio': metrics.get('peNormalizedAnnual'),
                    'debt_equity': metrics.get('totalDebt/totalEquityAnnual'),
                    'roe': metrics.get('roeRfy'),
                    'peg_ratio': metrics.get('pegNormalizedAnnual'),
                    'market_cap': profile.get('marketCapitalization') if profile else None
                }
                
                # Получение и расчет метрик роста EPS и выручки
                try:
                    # Получение финансовых отчетов за последние несколько кварталов
                    with self.finnhub_rate_limiter:
                        # Получаем earnings для расчета роста EPS
                        earnings_data = self.finnhub_client.company_earnings(ticker, limit=8)
                        
                    if earnings_data and len(earnings_data) >= 5:
                        # Сортируем по периоду (от новых к старым)
                        earnings_data = sorted(earnings_data, key=lambda x: x.get('period', ''), reverse=True)
                        
                        current_eps = earnings_data[0].get('actual')
                        year_ago_eps = earnings_data[4].get('actual')  # 4 квартала назад
                        
                        if current_eps is not None and year_ago_eps is not None and year_ago_eps != 0:
                            eps_growth_12m = (current_eps / year_ago_eps) - 1
                            result['eps_growth_12m'] = eps_growth_12m
                    
                    # Получение данных о росте выручки из финансовых метрик (если доступны)
                    revenue_growth = metrics.get('revenueGrowth')
                    if revenue_growth is not None:
                        result['revenue_growth_yoy'] = revenue_growth
                    else:
                        # Альтернативно пробуем получить выручку из финансовых отчетов
                        with self.finnhub_rate_limiter:
                            revenue_data = self.finnhub_client.company_revenue(ticker, 'quarterly')
                            
                        if revenue_data and 'data' in revenue_data and len(revenue_data['data']) >= 5:
                            revenue_points = revenue_data['data']
                            
                            current_revenue = revenue_points[0].get('revenue')
                            year_ago_revenue = revenue_points[4].get('revenue')
                            
                            if current_revenue is not None and year_ago_revenue is not None and year_ago_revenue != 0:
                                revenue_growth_yoy = (current_revenue / year_ago_revenue) - 1
                                result['revenue_growth_yoy'] = revenue_growth_yoy
                
                except Exception as e:
                    logger.warning(f"Ошибка при получении данных о росте для {ticker}: {e}")
                
                try:
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
            # Получение данных за 3 месяца
            end_timestamp = int(time.time())  # Текущее время в Unix timestamp
            start_timestamp = end_timestamp - (90 * 24 * 60 * 60)  # 90 дней назад
            
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
                # 3-месячная доходность
                if len(df) > 1:
                    first_price = df['close'].iloc[0]
                    last_price = df['close'].iloc[-1]
                    momentum_3m = (last_price / first_price - 1) * 100
                else:
                    momentum_3m = 0
                
                # Волатильность
                if len(df) > 5:
                    daily_returns = df['close'].pct_change().dropna()
                    volatility_3m = daily_returns.std() * (252 ** 0.5) * 100  # Годовая волатильность в %
                else:
                    volatility_3m = 0
                
                # Средний объем за 10 дней
                if len(df) >= 10:
                    avg_volume_10d = df['volume'].tail(10).mean()
                else:
                    avg_volume_10d = df['volume'].mean() if len(df) > 0 else 0
                
                # Изменение с начала года (YTD)
                try:
                    ytd_start_date = datetime(datetime.now().year, 1, 1)
                    ytd_start_timestamp = int(ytd_start_date.timestamp())
                    
                    with self.finnhub_rate_limiter:
                        ytd_candles = self.finnhub_client.stock_candles(
                            ticker,
                            'D',
                            ytd_start_timestamp,
                            end_timestamp
                        )
                    
                    if ytd_candles['s'] == 'ok' and len(ytd_candles['c']) > 1:
                        ytd_first = ytd_candles['c'][0]
                        ytd_last = ytd_candles['c'][-1]
                        price_change_ytd = (ytd_last / ytd_first - 1) * 100
                    else:
                        price_change_ytd = None
                except Exception as e:
                    logger.warning(f"Ошибка при расчете YTD для {ticker}: {e}")
                    price_change_ytd = None
                
                return {
                    'momentum_3m': momentum_3m,
                    'volatility_3m': volatility_3m,
                    'avg_volume_10d': avg_volume_10d,
                    'price_change_ytd': price_change_ytd,
                    'latest_price': last_price if 'last_price' in locals() else None
                }
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
        except Exception as e:
            logger.warning(f"Ошибка при получении целевых цен для {ticker}: {e}")
        
        # Получение рекомендаций аналитиков
        try:
            with self.finnhub_rate_limiter:
                recommendations = self.finnhub_client.recommendation_trends(ticker)
                
                if recommendations and len(recommendations) > 0:
                    latest_rec = recommendations[0]
                    
                    # Расчет общего количества рекомендаций
                    total_recommendations = (
                        latest_rec.get('strongBuy', 0) +
                        latest_rec.get('buy', 0) +
                        latest_rec.get('hold', 0) +
                        latest_rec.get('sell', 0) +
                        latest_rec.get('strongSell', 0)
                    )
                    
                    result['strong_buy'] = latest_rec.get('strongBuy')
                    result['buy'] = latest_rec.get('buy')
                    result['hold'] = latest_rec.get('hold')
                    result['sell'] = latest_rec.get('sell')
                    result['strong_sell'] = latest_rec.get('strongSell')
                    result['total_recommendations'] = total_recommendations
                    
                    # Рассчитываем консенсус-рейтинг (от -1 до 1)
                    if total_recommendations > 0:
                        consensus_score = self._calculate_recommendation_score(latest_rec)
                        result['consensus_score'] = consensus_score
                    
                    # Анализ тренда при наличии предыдущих рекомендаций
                    if len(recommendations) >= 2:
                        current = recommendations[0]
                        previous = recommendations[1]
                        
                        current_score = self._calculate_recommendation_score(current)
                        previous_score = self._calculate_recommendation_score(previous)
                        
                        result['rating_trend'] = current_score - previous_score
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
                    
                    # Расчет surprise в процентах
                    if latest_earnings.get('estimate') and latest_earnings.get('estimate') != 0:
                        surprise_pct = (
                            (latest_earnings.get('actual', 0) - latest_earnings.get('estimate', 0)) / 
                            abs(latest_earnings.get('estimate', 1)) * 100
                        )
                        result['eps_surprise_pct'] = round(surprise_pct, 2)
                    
                    result['eps_quarter'] = latest_earnings.get('period')
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