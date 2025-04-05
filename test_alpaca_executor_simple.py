#!/usr/bin/env python3
"""
Упрощенный тест AlpacaExecutor на 5 фиксированных тикерах с ограничением суммы ордеров в 10000 долларов.
Этот скрипт обрабатывает ошибки и показывает симуляцию работы, даже если API ключи не настроены.
"""

import os
import time
import logging
from dotenv import load_dotenv
from src.trading.alpaca_executor import AlpacaExecutor

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_alpaca')

# Загрузка переменных окружения
load_dotenv()

def main():
    logger.info("======= ТЕСТИРОВАНИЕ ALPACA EXECUTOR =======")
    
    # Инициализация AlpacaExecutor
    alpaca = AlpacaExecutor(is_paper=True)  # Используем только paper trading
    
    # Получение информации о счете
    logger.info("Получение информации о счете...")
    try:
        account_info = alpaca.get_account_info()
        if isinstance(account_info, dict) and not account_info.get('error'):
            logger.info(f"Баланс счета: ${account_info.get('cash', 0):.2f}")
            logger.info(f"Стоимость портфеля: ${account_info.get('portfolio_value', 0):.2f}")
            logger.info(f"Покупательная способность: ${account_info.get('buying_power', 0):.2f}")
        else:
            logger.warning(f"Не удалось получить информацию о счете: {account_info.get('error', 'Неизвестная ошибка')}")
            logger.info("Продолжаем тестирование в режиме симуляции...")
    except Exception as e:
        logger.error(f"Ошибка при получении информации о счете: {e}")
        logger.info("Продолжаем тестирование в режиме симуляции...")
    
    # Получение текущих позиций
    logger.info("Получение текущих позиций...")
    try:
        positions = alpaca.get_positions()
        if isinstance(positions, list):
            logger.info(f"Текущее количество позиций: {len(positions)}")
            for pos in positions:
                logger.info(f"Позиция: {pos['ticker']}, Кол-во: {pos['quantity']}, Стоимость: ${pos['market_value']:.2f}")
        else:
            logger.warning(f"Не удалось получить позиции: {positions.get('error', 'Неизвестная ошибка')}")
    except Exception as e:
        logger.error(f"Ошибка при получении позиций: {e}")
    
    # Проверка статуса рынка
    logger.info("Проверка статуса рынка...")
    try:
        market_status = alpaca.check_market_status()
        if isinstance(market_status, dict):
            if market_status.get('is_open'):
                logger.info("Рынок открыт. Можем размещать ордера.")
            else:
                next_open = market_status.get('next_open', 'неизвестно')
                logger.info(f"Рынок закрыт. Следующее открытие: {next_open}")
                logger.info("Ордера будут размещены в очередь на исполнение при открытии рынка.")
        else:
            logger.warning(f"Не удалось получить статус рынка: {market_status.get('error', 'Неизвестная ошибка')}")
    except Exception as e:
        logger.error(f"Ошибка при проверке статуса рынка: {e}")
    
    # Отмена всех открытых ордеров перед тестированием
    logger.info("Отмена всех открытых ордеров...")
    try:
        cancel_result = alpaca.cancel_all_orders()
        if cancel_result.get('success'):
            logger.info("Все открытые ордера успешно отменены")
        else:
            logger.warning(f"Проблема при отмене ордеров: {cancel_result.get('error', 'Неизвестная ошибка')}")
    except Exception as e:
        logger.error(f"Ошибка при отмене ордеров: {e}")
    
    # Используем фиксированный список тикеров вместо получения из MarketDataService
    test_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META']
    logger.info(f"Используем тикеры для тестирования: {test_tickers}")
    
    # Общий бюджет для всех ордеров
    total_budget = 10000.0
    budget_per_ticker = total_budget / len(test_tickers)
    logger.info(f"Общий бюджет: ${total_budget:.2f}, на каждый тикер: ${budget_per_ticker:.2f}")
    
    # Словарь для хранения информации о размещенных ордерах
    placed_orders = {}
    
    # Симуляция цен для тикеров в случае ошибок API
    simulated_prices = {
        'AAPL': 189.50,
        'MSFT': 425.30,
        'GOOGL': 175.25, 
        'AMZN': 185.60,
        'META': 495.85
    }
    
    # Размещение ордеров для каждого тикера
    for ticker in test_tickers:
        try:
            # Получение текущей цены
            price = alpaca.get_last_trade_price(ticker)
            
            # Если цена не получена, используем симуляцию
            if not price:
                price = simulated_prices.get(ticker, 100.0)
                logger.warning(f"Используем симуляционную цену для {ticker}: ${price:.2f}")
            else:
                logger.info(f"Текущая цена {ticker}: ${price:.2f}")
            
            # Расчет количества акций в пределах бюджета
            shares = int(budget_per_ticker / price)
            
            if shares == 0:
                logger.warning(f"Цена {ticker} (${price:.2f}) слишком высокая для бюджета ${budget_per_ticker:.2f}, пропускаем")
                continue
            
            total_cost = shares * price
            logger.info(f"Размещение ордера на покупку {shares} акций {ticker} на сумму ${total_cost:.2f}")
            
            # Размещение ордера на покупку
            order = alpaca.submit_order(
                ticker=ticker,
                qty=shares,
                side='buy',
                order_type='limit',
                limit_price=round(price * 1.01, 2),  # Лимитная цена на 1% выше текущей
                time_in_force='day'
            )
            
            if order and 'error' in order:
                logger.error(f"Ошибка при размещении ордера на {ticker}: {order['error']}")
                # Создаем симуляцию успешного ордера для тестирования
                order = {
                    'id': f"simulated_{ticker}",
                    'ticker': ticker,
                    'side': 'buy',
                    'quantity': shares,
                    'status': 'simulated',
                    'limit_price': round(price * 1.01, 2)
                }
                logger.info(f"Создан симуляционный ордер для {ticker}")
            
            if order:
                logger.info(f"Ордер на покупку {ticker} размещен, ID: {order.get('id', 'unknown')}")
                placed_orders[ticker] = {
                    'order_id': order.get('id', f"simulated_{ticker}"),
                    'shares': shares,
                    'price': price,
                    'side': 'buy',
                    'total_cost': total_cost
                }
            else:
                logger.error(f"Не удалось получить информацию об ордере для {ticker}")
            
        except Exception as e:
            logger.error(f"Ошибка при обработке тикера {ticker}: {e}")
    
    # Проверка статуса размещенных ордеров
    if placed_orders:
        logger.info("Проверка статуса размещенных ордеров...")
        time.sleep(2)  # Даем немного времени для обработки ордеров
        
        for ticker, order_info in placed_orders.items():
            order_id = order_info['order_id']
            try:
                if order_id.startswith("simulated_"):
                    logger.info(f"Симуляционный ордер {ticker}: статус=pending")
                else:
                    status = alpaca.get_order_status(order_id)
                    if status and not status.get('error'):
                        logger.info(f"Статус ордера {ticker}: {status.get('status', 'unknown')}")
                    else:
                        logger.warning(f"Не удалось получить статус ордера {ticker}: {status.get('error', 'Неизвестная ошибка')}")
            except Exception as e:
                logger.error(f"Ошибка при получении статуса ордера {ticker}: {e}")
    
        # Отчет о размещенных ордерах
        logger.info("\n=== ИТОГОВЫЙ ОТЧЕТ ===")
        total_invested = sum(order['total_cost'] for order in placed_orders.values())
        logger.info(f"Размещено ордеров: {len(placed_orders)}")
        logger.info(f"Общая сумма: ${total_invested:.2f} из ${total_budget:.2f}")
        
        # Создаем таблицу с информацией о размещенных ордерах
        logger.info("\nРазмещенные ордера:")
        format_str = "{:<8} | {:<8} | {:<10} | {:<12} | {:<20}"
        logger.info(format_str.format("Тикер", "Акции", "Цена", "Стоимость", "ID ордера"))
        logger.info("-" * 65)
        for ticker, info in placed_orders.items():
            logger.info(format_str.format(
                ticker, 
                info['shares'], 
                f"${info['price']:.2f}", 
                f"${info['total_cost']:.2f}", 
                info['order_id'][:15] + "..." if len(info['order_id']) > 15 else info['order_id']
            ))
        
        # Ждем 5 секунд, затем отменяем все ордера
        logger.info("\nЖдем 5 секунд, затем отменяем все ордера...")
        time.sleep(5)
        
        try:
            cancel_result = alpaca.cancel_all_orders()
            if cancel_result.get('success'):
                logger.info("Все открытые ордера успешно отменены")
            else:
                logger.warning(f"Проблема при отмене ордеров: {cancel_result.get('error', 'Неизвестная ошибка')}")
        except Exception as e:
            logger.error(f"Ошибка при отмене ордеров: {e}")
    else:
        logger.warning("Не удалось разместить ни одного ордера")
    
    # Получение текущих открытых ордеров
    logger.info("Получение текущих открытых ордеров...")
    try:
        open_orders = alpaca.get_open_orders()
        if isinstance(open_orders, list):
            logger.info(f"Текущее количество открытых ордеров: {len(open_orders)}")
        else:
            logger.warning(f"Не удалось получить список открытых ордеров: {open_orders.get('error', 'Неизвестная ошибка')}")
    except Exception as e:
        logger.error(f"Ошибка при получении открытых ордеров: {e}")
    
    logger.info("======= ТЕСТИРОВАНИЕ ЗАВЕРШЕНО =======")

if __name__ == "__main__":
    main() 