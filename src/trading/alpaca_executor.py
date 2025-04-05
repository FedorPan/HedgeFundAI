import os
import time
import logging
import alpaca_trade_api as tradeapi
from typing import Dict, List, Any, Optional
from datetime import datetime
import threading
import random
from functools import wraps
import uuid

logger = logging.getLogger('alpaca_executor')

# Добавляем утилиту для ограничения частоты вызовов API
class RateLimiter:
    """
    Простое ограничение частоты вызовов для API.
    """
    
    def __init__(self, max_calls: int, period: float):
        """
        Инициализация ограничителя.
        
        Args:
            max_calls: Максимальное число вызовов за период.
            period: Период в секундах.
        """
        self.max_calls = max_calls
        self.period = period
        self.calls = []
        self.lock = threading.Lock()
    
    def __call__(self, func):
        """
        Декоратор для ограничения частоты вызовов.
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            with self.lock:
                now = time.time()
                # Удаляем устаревшие записи о вызовах
                self.calls = [call for call in self.calls if call > now - self.period]
                
                if len(self.calls) >= self.max_calls:
                    # Слишком много вызовов
                    sleep_time = max(0.1, self.calls[0] + self.period - now)
                    sleep_time = max(0.1, sleep_time)  # Минимум 100 мс задержки
                    logger.warning(f"Rate limit hit, sleeping for {sleep_time:.2f} seconds")
                    time.sleep(sleep_time)
                    # После сна пересчитываем время и удаляем устаревшие вызовы
                    now = time.time()
                    self.calls = [call for call in self.calls if call > now - self.period]
                
                # Добавляем текущий вызов
                self.calls.append(now)
                
                return func(*args, **kwargs)
        
        return wrapper

# Добавляем расширенную обработку ошибок
def handle_alpaca_errors(func):
    """
    Декоратор для обработки ошибок Alpaca API с подробным логированием.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except tradeapi.rest.APIError as e:
            # Обработка известных ошибок Alpaca API
            error_code = getattr(e, 'code', 0)
            error_msg = str(e)
            
            if error_code == 40310000: # Недостаточно средств
                logger.error(f"Alpaca API error: Insufficient funds - {error_msg}")
                return {'error': 'insufficient buying power', 'details': error_msg}
            elif error_code == 40010001: # Превышен лимит API
                logger.error(f"Alpaca API error: Rate limit exceeded - {error_msg}")
                # Добавляем случайную задержку от 2 до 5 секунд
                sleep_time = 2 + random.random() * 3
                logger.info(f"Backing off for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
                return {'error': 'API rate limit exceeded', 'details': error_msg}
            elif 'position is not available' in error_msg.lower():
                logger.error(f"Alpaca API error: Position not found - {error_msg}")
                return {'error': 'Position not found', 'details': error_msg}
            else:
                logger.error(f"Alpaca API error: {error_code} - {error_msg}")
                return {'error': f'Alpaca API error: {error_msg}', 'code': error_code}
        except Exception as e:
            # Обработка других исключений
            logger.exception(f"Unexpected error in {func.__name__}: {e}")
            return {'error': str(e), 'exception': type(e).__name__}
    
    return wrapper

class AlpacaExecutor:
    """
    Исполняет торговые операции через Alpaca API.
    
    Этот класс предоставляет интерфейс для:
    - Получения информации о счете и позициях
    - Размещения ордеров (market, limit)
    - Проверки статуса ордеров и рынка
    - Отмены ордеров
    
    Все методы включают логирование и обработку ошибок.
    """
    
    def __init__(self, alpaca_key=None, alpaca_secret=None, is_paper=True, base_url=None):
        """
        Инициализация исполнителя Alpaca.
        
        Args:
            alpaca_key: API ключ Alpaca. Если None, будет взят из переменной окружения ALPACA_API_KEY.
            alpaca_secret: Секретный ключ Alpaca. Если None, будет взят из переменной окружения ALPACA_API_SECRET.
            is_paper: Использовать paper trading (тестовый режим без реальных денег).
            base_url: Базовый URL для API. Если None, будет взят из переменной окружения ALPACA_BASE_URL
                    или использован стандартный URL в зависимости от is_paper.
        """
        # API keys
        self.api_key = alpaca_key or os.environ.get('ALPACA_API_KEY')
        self.api_secret = alpaca_secret or os.environ.get('ALPACA_API_SECRET')
        
        # Отладка API ключей
        logger.info(f"Alpaca API key length: {len(self.api_key) if self.api_key else 'Not set'}")
        logger.info(f"Alpaca API secret length: {len(self.api_secret) if self.api_secret else 'Not set'}")
        
        if not self.api_key or not self.api_secret:
            logger.warning("No Alpaca API keys provided. Using demo keys for paper trading only.")
            self.api_key = "PK1P2VZFOPVMX8ZM52MB"
            self.api_secret = "5daTmDkDqpuwBbXNJpttXMVCbYbVypVW4cJEfXnS"
            is_paper = True
        
        # Base URL - сначала берем из переменной окружения
        self.is_paper = is_paper
        if base_url is None:
            self.base_url = os.environ.get('ALPACA_BASE_URL')
            if not self.base_url:
                self.base_url = "https://paper-api.alpaca.markets" if is_paper else "https://api.alpaca.markets"
        else:
            self.base_url = base_url
            
        # Убираем /v2 из URL, если он присутствует, чтобы избежать дублирования
        if self.base_url and self.base_url.endswith('/v2'):
            self.base_url = self.base_url.rstrip('/v2')
            logger.info(f"Removed /v2 from base URL to avoid duplication")
        
        logger.info(f"Initializing Alpaca with base URL: {self.base_url}, paper trading: {self.is_paper}")
        
        # Инициализируем API клиент
        try:
            self.api = tradeapi.REST(
                self.api_key,
                self.api_secret,
                self.base_url,
                api_version='v2'
            )
            
            # Инициализируем счетчики API вызовов
            self.api_calls = 0
            self.api_errors = 0
            self.last_minute_calls = 0
            self.last_minute_time = time.time()
            
            # Проверяем состояние рынка
            try:
                clock = self.api.get_clock()
                self.market_open = clock.is_open
                next_open = clock.next_open.strftime('%Y-%m-%d %H:%M:%S')
                next_close = clock.next_close.strftime('%Y-%m-%d %H:%M:%S')
                logger.info(f"Market is {'open' if self.market_open else 'closed'}. Next open: {next_open}, next close: {next_close}")
            except Exception as e:
                logger.warning(f"Could not get market status: {e}. Assuming market is closed.")
                self.market_open = False
            
            # Инициализируем API rate limiter
            self.api_call_count = 0
            self.last_api_call = time.time() - 60  # Начинаем с низкого счетчика
            self.api_call_limit = 200  # Alpaca позволяет ~200 вызовов в минуту
            
            # Лимит вызовов API и кэш
            self.positions_cache = []
            self.positions_cache_time = 0
            self.account_cache = None
            self.account_cache_time = 0
            self.orders_cache = []
            self.orders_cache_time = 0
            
            # Устанавливаем кеш интервал
            self.cache_interval = 5  # секунд
            
            # Инициализируем счетчики
            self.execution_count = 0
            self.error_count = 0
            
            # Инициализируем блокировки
            self.api_lock = threading.Lock()
            self.positions_lock = threading.Lock()
            
            self.simulated_mode = False
            logger.info("AlpacaExecutor successfully initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize Alpaca API client: {e}")
            # Продолжаем выполнение, но отмечаем что соединение не установлено
            self.api = None 
            self.simulated_mode = True
            self.market_open = False
            self.api_calls = 0
            self.api_errors = 0
            self.last_minute_calls = 0
            self.last_minute_time = time.time()
            logger.warning("AlpacaExecutor running in simulated mode. No real trading will occur.")
    
    def _track_api_call(self, success: bool = True):
        """
        Отслеживает вызовы API для метрик.
        
        Args:
            success: Был ли вызов API успешным.
        """
        self.api_calls += 1
        if not success:
            self.api_errors += 1
        
        # Сбрасываем счетчики каждый час
        now = time.time()
        if now - self.last_minute_time > 60:
            logger.info(f"API calls in the last minute: {self.api_calls - self.last_minute_calls}, errors: {self.api_errors}")
            self.last_minute_calls = self.api_calls
            self.last_minute_time = now
    
    @handle_alpaca_errors
    def get_account_info(self) -> Dict[str, Any]:
        """
        Получает информацию о торговом счете.
        
        Returns:
            Словарь с информацией о счете, включая:
            - cash: Доступные средства
            - portfolio_value: Общая стоимость портфеля
            - buying_power: Покупательная способность
            - equity: Собственный капитал
            - long_market_value: Стоимость длинных позиций
            - short_market_value: Стоимость коротких позиций
            - status: Статус счета
        """
        try:
            # Проверяем кэш
            now = time.time()
            if self.account_cache and now - self.account_cache_time < self.cache_interval:
                return self.account_cache
            
            account = self.api.get_account()
            self._track_api_call()
            
            account_info = {
                'cash': float(account.cash),
                'portfolio_value': float(account.portfolio_value),
                'buying_power': float(account.buying_power),
                'equity': float(account.equity),
                'long_market_value': float(account.long_market_value),
                'short_market_value': float(account.short_market_value),
                'status': account.status
            }
            
            # Обновляем кэш
            self.account_cache = account_info
            self.account_cache_time = now
            
            return account_info
        except Exception as e:
            self._track_api_call(False)
            logger.error(f"Error getting account info: {e}")
            raise
    
    @handle_alpaca_errors
    def get_positions(self) -> List[Dict[str, Any]]:
        """
        Получает все текущие позиции в портфеле.
        
        Returns:
            Список позиций, где каждая позиция содержит:
            - ticker: Символ тикера
            - quantity: Количество акций
            - side: Сторона позиции ('long' или 'short')
            - market_value: Текущая рыночная стоимость позиции
            - cost_basis: Стоимостная основа
            - unrealized_pl: Нереализованная прибыль/убыток
            - current_price: Текущая цена
            - avg_entry_price: Средняя цена входа
        """
        try:
            # Проверяем кэш
            now = time.time()
            if self.positions_cache and now - self.positions_cache_time < self.cache_interval:
                return self.positions_cache
            
            logger.info("Fetching current positions from Alpaca")
            positions = self.api.list_positions()
            self._track_api_call()
            logger.info(f"Retrieved {len(positions)} positions from Alpaca")
            
            # Обновляем кэш позиций
            formatted_positions = [
                {
                    'ticker': p.symbol,
                    'quantity': float(p.qty),
                    'side': 'long' if float(p.qty) > 0 else 'short',
                    'market_value': float(p.market_value),
                    'cost_basis': float(p.cost_basis),
                    'unrealized_pl': float(p.unrealized_pl),
                    'current_price': float(p.current_price),
                    'avg_entry_price': float(p.avg_entry_price)
                }
                for p in positions
            ]
            
            # Обновляем кэш
            self.positions_cache = formatted_positions
            self.positions_cache_time = now
            
            return formatted_positions
        except Exception as e:
            self._track_api_call(False)
            logger.error(f"Error getting positions: {e}")
            raise
    
    @handle_alpaca_errors
    @RateLimiter(max_calls=50, period=60)  # Отдельный лимит для получения цен
    def get_last_trade_price(self, ticker: str) -> float:
        """
        Получает цену последней сделки для указанного тикера.
        
        Args:
            ticker: Символ тикера для получения цены.
            
        Returns:
            Цена последней сделки или None в случае ошибки.
        """
        try:
            trade = self.api.get_latest_trade(ticker)
            self._track_api_call()
            price = float(trade.price)
            logger.debug(f"Latest price for {ticker}: ${price:.2f}")
            return price
        except Exception as e:
            self._track_api_call(False)
            logger.error(f"Error getting last trade price for {ticker}: {e}")
            return None
    
    @handle_alpaca_errors
    def check_market_status(self) -> Dict[str, Any]:
        """
        Проверяет текущий статус рынка.
        
        Returns:
            Словарь с информацией о состоянии рынка:
            - is_open: Открыт ли рынок
            - next_open: Время следующего открытия
            - next_close: Время следующего закрытия
            - current_time: Текущее время
        """
        try:
            clock = self.api.get_clock()
            self._track_api_call()
            
            self.market_open = clock.is_open
            
            return {
                'is_open': clock.is_open,
                'next_open': clock.next_open.isoformat(),
                'next_close': clock.next_close.isoformat(),
                'current_time': clock.timestamp.isoformat()
            }
        except Exception as e:
            self._track_api_call(False)
            logger.error(f"Error checking market status: {e}")
            # Предполагаем, что рынок закрыт в случае ошибки
            self.market_open = False
            return {
                'is_open': False,
                'error': str(e)
            }
    
    @handle_alpaca_errors
    def submit_order(self, ticker: str, qty: float, side: str, order_type: str = 'market', 
                    time_in_force: str = 'day', limit_price: float = None, 
                    stop_price: float = None, client_order_id: str = None,
                    take_profit_pct: float = None, stop_loss_pct: float = None) -> Dict[str, Any]:
        """
        Размещает ордер на покупку или продажу.
        
        Args:
            ticker: Символ тикера для торговли.
            qty: Количество акций.
            side: Сторона сделки ('buy' или 'sell').
            order_type: Тип ордера ('market', 'limit', 'stop', 'stop_limit').
            time_in_force: Время действия ордера ('day', 'gtc', 'ioc', 'opg', 'cls', 'fok').
            limit_price: Цена для лимитного ордера.
            stop_price: Цена для стоп-ордера.
            client_order_id: Клиентский ID ордера для отслеживания.
            take_profit_pct: Процент прибыли для take-profit (например, 0.1 для +10%).
            stop_loss_pct: Процент убытка для stop-loss (например, 0.05 для -5%).
            
        Returns:
            Словарь с информацией о размещенном ордере или ошибке.
        """
        # Проверяем состояние рынка
        if not self.simulated_mode and not self.market_open and time_in_force not in ['opg', 'cls']:
            market_status = self.check_market_status()
            logger.warning(f"Market is closed. Next open: {market_status.get('next_open')}. "
                          f"Order will be queued for next market open.")
        
        # Генерируем client_order_id если не указан
        if not client_order_id:
            client_order_id = f"order_{uuid.uuid4().hex[:12]}_{side}_{ticker}"
        
        # Получаем текущую цену для расчета TP/SL уровней если требуется
        current_price = None
        is_bracket_order = take_profit_pct is not None or stop_loss_pct is not None
        
        if is_bracket_order:
            current_price = self.get_last_trade_price(ticker)
            if not current_price:
                error_msg = f"Не удалось получить текущую цену для {ticker}. Bracket ордер не может быть создан."
                logger.error(error_msg)
                return {'error': error_msg}
        
        # Логируем детали ордера
        order_details = {
            'ticker': ticker,
            'qty': qty,
            'side': side,
            'type': order_type,
            'time_in_force': time_in_force,
            'limit_price': limit_price,
            'stop_price': stop_price,
            'client_order_id': client_order_id
        }
        
        # Добавляем информацию о TP/SL если указаны
        if is_bracket_order:
            order_details['is_bracket'] = True
            order_details['current_price'] = current_price
            
            if take_profit_pct is not None:
                take_profit_price = round(current_price * (1 + take_profit_pct if side == 'buy' else 1 - take_profit_pct), 2)
                order_details['take_profit_price'] = take_profit_price
                order_details['take_profit_pct'] = take_profit_pct
            
            if stop_loss_pct is not None:
                stop_loss_price = round(current_price * (1 - stop_loss_pct if side == 'buy' else 1 + stop_loss_pct), 2)
                order_details['stop_loss_price'] = stop_loss_price
                order_details['stop_loss_pct'] = stop_loss_pct
                
            logger.info(f"Создание bracket ордера {side} для {ticker} по ${current_price:.2f}:")
            if take_profit_pct is not None:
                logger.info(f"  - Take Profit: ${order_details['take_profit_price']:.2f} ({'+' if side == 'buy' else '-'}{take_profit_pct*100:.1f}%)")
            if stop_loss_pct is not None:
                logger.info(f"  - Stop Loss: ${order_details['stop_loss_price']:.2f} ({'-' if side == 'buy' else '+' }{stop_loss_pct*100:.1f}%)")
        
        logger.info(f"Submitting order: {order_details}")
        
        try:
            # Создаем параметры ордера
            order_params = {
                'symbol': ticker,
                'qty': qty,
                'side': side,
                'type': order_type,
                'time_in_force': time_in_force,
                'client_order_id': client_order_id
            }
            
            # Добавляем цены для limit и stop ордеров
            if order_type in ['limit', 'stop_limit'] and limit_price is not None:
                order_params['limit_price'] = limit_price
            
            if order_type in ['stop', 'stop_limit'] and stop_price is not None:
                order_params['stop_price'] = stop_price
            
            # Настраиваем bracket ордер если требуется
            if is_bracket_order:
                order_params['order_class'] = 'bracket'
                
                # Настройка take profit
                if take_profit_pct is not None:
                    take_profit_price = order_details.get('take_profit_price')
                    order_params['take_profit'] = {
                        'limit_price': take_profit_price
                    }
                
                # Настройка stop loss
                if stop_loss_pct is not None:
                    stop_loss_price = order_details.get('stop_loss_price')
                    order_params['stop_loss'] = {
                        'stop_price': stop_loss_price,
                        'limit_price': stop_loss_price  # Добавляем limit_price для создания stop limit ордера
                    }
            
            # Отправляем ордер
            order = self.api.submit_order(**order_params)
            self._track_api_call()
            
            # Форматируем ответ
            formatted_order = {
                'id': order.id,
                'client_order_id': order.client_order_id,
                'ticker': order.symbol,
                'side': order.side,
                'quantity': float(order.qty) if order.qty else 0,
                'type': order.type,
                'status': order.status,
                'filled_qty': float(order.filled_qty) if order.filled_qty else 0,
                'filled_avg_price': float(order.filled_avg_price) if order.filled_avg_price else None,
                'submitted_at': order.submitted_at.isoformat() if order.submitted_at else None,
                'time_in_force': order.time_in_force
            }
            
            # Добавляем информацию о TP/SL в ответ
            if is_bracket_order:
                formatted_order['is_bracket'] = True
                if take_profit_pct is not None:
                    formatted_order['take_profit_price'] = order_details.get('take_profit_price')
                    formatted_order['take_profit_pct'] = take_profit_pct
                if stop_loss_pct is not None:
                    formatted_order['stop_loss_price'] = order_details.get('stop_loss_price')
                    formatted_order['stop_loss_pct'] = stop_loss_pct
            
            logger.info(f"Order successfully submitted: {formatted_order}")
            return formatted_order
            
        except Exception as e:
            self._track_api_call(False)
            error_msg = f"Error submitting order for {ticker}: {e}"
            logger.error(error_msg)
            return {
                'error': error_msg,
                'details': order_details
            }
    
    @handle_alpaca_errors
    def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """
        Получает статус ордера по его ID.
        
        Args:
            order_id: ID ордера.
            
        Returns:
            Словарь с информацией о статусе ордера.
        """
        try:
            logger.info(f"Checking status of order {order_id}")
            order = self.api.get_order(order_id)
            self._track_api_call()
            
            formatted_order = {
                'id': order.id,
                'client_order_id': order.client_order_id,
                'ticker': order.symbol,
                'side': order.side,
                'quantity': float(order.qty),
                'filled_qty': float(order.filled_qty) if order.filled_qty else 0,
                'filled_avg_price': float(order.filled_avg_price) if order.filled_avg_price and float(order.filled_avg_price) > 0 else None,
                'type': order.type,
                'status': order.status,
                'submitted_at': order.submitted_at.isoformat() if order.submitted_at else None,
                'filled_at': order.filled_at.isoformat() if order.filled_at else None,
                'time_in_force': order.time_in_force
            }
            
            return formatted_order
        except Exception as e:
            self._track_api_call(False)
            error_msg = f"Error getting order status for {order_id}: {e}"
            logger.error(error_msg)
            return {'error': error_msg, 'order_id': order_id}
    
    @handle_alpaca_errors
    def cancel_all_orders(self) -> Dict[str, Any]:
        """
        Отменяет все открытые ордера.
        
        Returns:
            Словарь с информацией о результате отмены ордеров.
        """
        try:
            logger.info("Cancelling all open orders")
            cancelled_orders = self.api.cancel_all_orders()
            self._track_api_call()
            
            logger.info(f"Successfully cancelled all open orders")
            return {
                'success': True,
                'message': 'All orders cancelled successfully'
            }
        except Exception as e:
            self._track_api_call(False)
            error_msg = f"Error cancelling orders: {e}"
            logger.error(error_msg)
            return {'error': error_msg}
    
    @handle_alpaca_errors
    def get_open_orders(self) -> List[Dict[str, Any]]:
        """
        Получает список всех открытых ордеров.
        
        Returns:
            Список словарей с информацией об открытых ордерах.
        """
        try:
            # Проверяем кэш
            now = time.time()
            if self.orders_cache and now - self.orders_cache_time < self.cache_interval:
                return self.orders_cache
                
            logger.info("Fetching open orders from Alpaca")
            orders = self.api.list_orders(status='open')
            self._track_api_call()
            
            formatted_orders = [
                {
                    'id': order.id,
                    'client_order_id': order.client_order_id,
                    'ticker': order.symbol,
                    'side': order.side,
                    'quantity': float(order.qty),
                    'filled_qty': float(order.filled_qty) if order.filled_qty else 0,
                    'type': order.type,
                    'status': order.status,
                    'submitted_at': order.submitted_at.isoformat() if order.submitted_at else None,
                    'time_in_force': order.time_in_force
                }
                for order in orders
            ]
            
            # Обновляем кэш
            self.orders_cache = formatted_orders
            self.orders_cache_time = now
            
            logger.info(f"Found {len(formatted_orders)} open orders")
            return formatted_orders
        except Exception as e:
            self._track_api_call(False)
            error_msg = f"Error getting open orders: {e}"
            logger.error(error_msg)
            return [] 