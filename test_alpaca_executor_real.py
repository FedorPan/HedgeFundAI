#!/usr/bin/env python3
"""
Тестирование AlpacaExecutor с реальными API ключами из .env.
Размещает пендинг-ордера для 5 случайных тикеров из SP500 с ограничением в $10,000.
"""

import os
import time
import json
import random
import logging
import pandas as pd
from dotenv import load_dotenv
from src.trading.alpaca_executor import AlpacaExecutor

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_alpaca_real')

# Загрузка переменных окружения
load_dotenv()

def get_random_tickers(count=5):
    """
    Получает список случайных тикеров из кэшированного списка SP500.
    
    Args:
        count: Количество тикеров для выбора.
        
    Returns:
        Список случайных тикеров.
    """
    try:
        # Загружаем кэшированные тикеры
        cache_file = '.cache/sp500_201_300.json'
        if not os.path.exists(cache_file):
            logger.warning(f"Кэш-файл {cache_file} не найден. Используем предопределенный список.")
            return ["AAPL", "MSFT", "GOOGL", "AMZN", "META"]
        
        with open(cache_file, 'r') as f:
            cached_data = json.load(f)
        
        if 'tickers' not in cached_data or not cached_data['tickers']:
            logger.warning("Некорректные данные в кэше. Используем предопределенный список.")
            return ["AAPL", "MSFT", "GOOGL", "AMZN", "META"]
        
        tickers = cached_data['tickers']
        
        # Выбираем случайные тикеры
        return random.sample(tickers, min(count, len(tickers)))
    except Exception as e:
        logger.error(f"Ошибка при получении тикеров: {e}")
        return ["AAPL", "MSFT", "GOOGL", "AMZN", "META"]  # Запасной вариант

def main():
    logger.info("===== ТЕСТИРОВАНИЕ ALPACA EXECUTOR С РЕАЛЬНЫМИ API КЛЮЧАМИ =====")
    
    # Инициализация AlpacaExecutor с реальными ключами из .env
    alpaca = AlpacaExecutor(is_paper=True)  # Используем paper trading для безопасности
    
    # Проверка инициализации
    if alpaca.simulated_mode:
        logger.error("AlpacaExecutor работает в режиме симуляции. Проверьте настройки API ключей.")
        return
    
    # Получение информации о счете
    logger.info("Получение информации о счете...")
    account_info = alpaca.get_account_info()
    if account_info and 'error' not in account_info:
        logger.info(f"Баланс счета: ${account_info.get('cash', 0):.2f}")
        logger.info(f"Стоимость портфеля: ${account_info.get('portfolio_value', 0):.2f}")
        logger.info(f"Покупательная способность: ${account_info.get('buying_power', 0):.2f}")
    else:
        logger.error(f"Ошибка при получении информации о счете: {account_info.get('error', 'Unknown error')}")
        return
    
    # Отмена всех открытых ордеров перед тестированием
    logger.info("Отмена всех открытых ордеров перед тестированием...")
    cancel_result = alpaca.cancel_all_orders()
    if cancel_result.get('success'):
        logger.info("Все открытые ордера успешно отменены")
    else:
        logger.warning(f"Проблема при отмене ордеров: {cancel_result.get('error', 'Unknown error')}")
    
    # Получение статуса рынка
    market_status = alpaca.check_market_status()
    if market_status and 'error' not in market_status:
        logger.info(f"Рынок {'открыт' if market_status.get('is_open') else 'закрыт'}.")
        if not market_status.get('is_open'):
            logger.info(f"Следующее открытие рынка: {market_status.get('next_open')}")
    else:
        logger.warning(f"Не удалось получить статус рынка: {market_status.get('error', 'Unknown error')}")
    
    # Запрос типа ордеров для тестирования
    order_type = input("Выберите тип ордеров для тестирования (1 - лимитные, 2 - bracket): ")
    use_bracket_orders = order_type == "2"
    
    # Получение случайных тикеров
    test_tickers = get_random_tickers(5)
    logger.info(f"Выбранные тикеры для тестирования: {test_tickers}")
    
    # Общий бюджет и расчет на тикер
    total_budget = 10000.0
    budget_per_ticker = total_budget / len(test_tickers)
    logger.info(f"Общий бюджет: ${total_budget:.2f}, на тикер: ${budget_per_ticker:.2f}")
    
    # Словарь для отслеживания размещенных ордеров
    placed_orders = {}
    total_invested = 0
    
    # Установка параметров stop loss и take profit для bracket ордеров
    take_profit_pct = 0.1  # 10% прибыли
    stop_loss_pct = 0.05   # 5% убытка
    
    if use_bracket_orders:
        logger.info(f"Настройки bracket ордеров: Take Profit = +{take_profit_pct*100:.1f}%, Stop Loss = -{stop_loss_pct*100:.1f}%")
    
    # Размещение ордеров
    for ticker in test_tickers:
        try:
            # Получение текущей цены
            price = alpaca.get_last_trade_price(ticker)
            if not price:
                logger.warning(f"Не удалось получить цену для {ticker}, пропускаем")
                continue
            
            logger.info(f"Текущая цена {ticker}: ${price:.2f}")
            
            # Расчет количества акций в пределах бюджета
            shares = int(budget_per_ticker / price)
            
            if shares == 0:
                logger.warning(f"Цена {ticker} (${price:.2f}) слишком высока для бюджета ${budget_per_ticker:.2f}, пропускаем")
                continue
            
            # Расчет итоговой стоимости
            order_cost = shares * price
            total_invested += order_cost
            
            if use_bracket_orders:
                # Размещение bracket ордера (рыночный ордер с TP/SL)
                logger.info(f"Размещение bracket ордера на покупку {shares} акций {ticker} по рыночной цене ~${price:.2f} (общая стоимость: ${order_cost:.2f})")
                
                order = alpaca.submit_order(
                    ticker=ticker,
                    qty=shares,
                    side='buy',
                    order_type='market',
                    time_in_force='day',
                    take_profit_pct=take_profit_pct,
                    stop_loss_pct=stop_loss_pct
                )
            else:
                # Размещение лимитного ордера
                limit_price = round(price * 0.98, 2)  # На 2% ниже рыночной цены для пендинг-ордеров
                logger.info(f"Размещение лимитного ордера на покупку {shares} акций {ticker} по цене ${limit_price:.2f} (общая стоимость: ${order_cost:.2f})")
                
                order = alpaca.submit_order(
                    ticker=ticker,
                    qty=shares,
                    side='buy',
                    order_type='limit',
                    limit_price=limit_price,
                    time_in_force='day'
                )
            
            if 'error' in order:
                logger.error(f"Ошибка при размещении ордера для {ticker}: {order['error']}")
                continue
            
            logger.info(f"Ордер успешно размещен для {ticker}: ID {order['id']}")
            placed_orders[ticker] = {
                'order_id': order['id'],
                'shares': shares,
                'market_price': price,
                'total_cost': order_cost,
                'status': order['status']
            }
            
            # Добавляем специфичные поля для разных типов ордеров
            if use_bracket_orders:
                if 'take_profit_price' in order:
                    placed_orders[ticker]['take_profit_price'] = order['take_profit_price']
                if 'stop_loss_price' in order:
                    placed_orders[ticker]['stop_loss_price'] = order['stop_loss_price']
            else:
                placed_orders[ticker]['limit_price'] = limit_price
            
        except Exception as e:
            logger.error(f"Ошибка при обработке тикера {ticker}: {e}")
    
    # Проверка статуса размещенных ордеров
    if placed_orders:
        logger.info("Проверка статуса размещенных ордеров через 3 секунды...")
        time.sleep(3)
        
        orders_status = []
        for ticker, order_data in placed_orders.items():
            try:
                status = alpaca.get_order_status(order_data['order_id'])
                if 'error' not in status:
                    status_info = {
                        'ticker': ticker,
                        'status': status['status'],
                        'shares': order_data['shares'],
                        'filled_qty': status.get('filled_qty', 0),
                        'filled_price': status.get('filled_avg_price', None)
                    }
                    
                    # Добавляем специфичные поля для разных типов ордеров
                    if use_bracket_orders:
                        if 'take_profit_price' in order_data:
                            status_info['take_profit'] = order_data['take_profit_price']
                        if 'stop_loss_price' in order_data:
                            status_info['stop_loss'] = order_data['stop_loss_price']
                    else:
                        status_info['limit_price'] = order_data.get('limit_price')
                    
                    orders_status.append(status_info)
                    logger.info(f"Статус ордера {ticker}: {status['status']}")
                else:
                    logger.warning(f"Ошибка при получении статуса ордера {ticker}: {status['error']}")
            except Exception as e:
                logger.error(f"Ошибка при проверке статуса ордера {ticker}: {e}")
        
        # Вывод информации о размещенных ордерах
        logger.info("\n===== ИТОГИ РАЗМЕЩЕНИЯ ОРДЕРОВ =====")
        logger.info(f"Тип ордеров: {'Bracket (рыночные с TP/SL)' if use_bracket_orders else 'Лимитные'}")
        logger.info(f"Размещено ордеров: {len(placed_orders)} из {len(test_tickers)}")
        logger.info(f"Общая потенциальная стоимость: ${total_invested:.2f} из ${total_budget:.2f}")
        
        # Табличный вывод размещенных ордеров
        if orders_status:
            df = pd.DataFrame(orders_status)
            print("\nСтатус размещенных ордеров:")
            print(df.to_string(index=False))
    else:
        logger.warning("Не удалось разместить ни одного ордера")
    
    # Предложение пользователю отменить ордера или оставить их для исполнения
    user_input = input("\nОтменить все размещенные ордера? (y/n): ")
    if user_input.lower() in ['y', 'yes', 'да']:
        logger.info("Отмена всех ордеров...")
        cancel_result = alpaca.cancel_all_orders()
        if cancel_result.get('success'):
            logger.info("Все ордера успешно отменены")
        else:
            logger.warning(f"Проблема при отмене ордеров: {cancel_result.get('error', 'Unknown error')}")
    else:
        logger.info("Ордера оставлены активными для исполнения")
    
    logger.info("===== ТЕСТИРОВАНИЕ ЗАВЕРШЕНО =====")

if __name__ == "__main__":
    main() 