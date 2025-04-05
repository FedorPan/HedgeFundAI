#!/usr/bin/env python3
"""
Тестирование AlpacaExecutor на 5 тикерах с ограничением суммы ордеров в 10000 долларов.
"""

import os
import time
import random
import logging
import pandas as pd
from dotenv import load_dotenv
from src.trading.alpaca_executor import AlpacaExecutor
from src.data.market_data_service import MarketDataService

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_alpaca')

# Загрузка переменных окружения
load_dotenv()

def main():
    # Инициализация AlpacaExecutor
    alpaca = AlpacaExecutor(is_paper=True)  # Используем только paper trading
    
    # Получение информации о счете
    logger.info("Получение информации о счете...")
    account_info = alpaca.get_account_info()
    logger.info(f"Баланс счета: ${account_info['cash']:.2f}")
    logger.info(f"Стоимость портфеля: ${account_info['portfolio_value']:.2f}")
    logger.info(f"Покупательная способность: ${account_info['buying_power']:.2f}")
    
    # Получение текущих позиций
    logger.info("Получение текущих позиций...")
    positions = alpaca.get_positions()
    logger.info(f"Текущее количество позиций: {len(positions)}")
    for pos in positions:
        logger.info(f"Позиция: {pos['ticker']}, Кол-во: {pos['quantity']}, Стоимость: ${pos['market_value']:.2f}")
    
    # Проверка статуса рынка
    market_status = alpaca.check_market_status()
    if market_status['is_open']:
        logger.info("Рынок открыт. Можем размещать ордера.")
    else:
        logger.info(f"Рынок закрыт. Следующее открытие: {market_status['next_open']}")
        logger.info("Ордера будут размещены в очередь на исполнение при открытии рынка.")
    
    # Отмена всех открытых ордеров перед тестированием
    logger.info("Отмена всех открытых ордеров...")
    cancel_result = alpaca.cancel_all_orders()
    if cancel_result.get('success'):
        logger.info("Все открытые ордера успешно отменены")
    else:
        logger.warning(f"Проблема при отмене ордеров: {cancel_result.get('error')}")
    
    # Получение списка тикеров
    logger.info("Получение списка тикеров для тестирования...")
    market_data = MarketDataService()
    sp500_tickers = market_data.get_sp500_tickers(start_rank=201, end_rank=300)
    
    # Выбор 5 случайных тикеров
    test_tickers = random.sample(sp500_tickers, 5)
    logger.info(f"Выбраны тикеры для тестирования: {test_tickers}")
    
    # Общий бюджет для всех ордеров
    total_budget = 10000.0
    budget_per_ticker = total_budget / len(test_tickers)
    
    # Словарь для хранения информации о размещенных ордерах
    placed_orders = {}
    
    # Размещение ордеров для каждого тикера
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
            
            if 'error' in order:
                logger.error(f"Ошибка при размещении ордера на {ticker}: {order['error']}")
                continue
            
            logger.info(f"Ордер на покупку {ticker} успешно размещен, ID: {order['id']}")
            placed_orders[ticker] = {
                'order_id': order['id'],
                'shares': shares,
                'price': price,
                'side': 'buy',
                'total_cost': total_cost
            }
            
        except Exception as e:
            logger.error(f"Ошибка при обработке тикера {ticker}: {e}")
    
    # Проверка статуса размещенных ордеров
    if placed_orders:
        logger.info("Проверка статуса размещенных ордеров...")
        time.sleep(5)  # Даем немного времени для обработки ордеров
        
        for ticker, order_info in placed_orders.items():
            order_id = order_info['order_id']
            try:
                status = alpaca.get_order_status(order_id)
                logger.info(f"Статус ордера {ticker}: {status['status']}")
                logger.info(f"Детали ордера: {status}")
            except Exception as e:
                logger.error(f"Ошибка при получении статуса ордера {ticker}: {e}")
    
        # Отчет о размещенных ордерах
        logger.info("\n=== Итоговый отчет ===")
        total_invested = sum(order['total_cost'] for order in placed_orders.values())
        logger.info(f"Размещено ордеров: {len(placed_orders)}")
        logger.info(f"Общая сумма: ${total_invested:.2f} из ${total_budget:.2f}")
        
        # Создание DataFrame с информацией о размещенных ордерах
        df = pd.DataFrame([
            {
                'ticker': ticker,
                'shares': info['shares'],
                'price': info['price'],
                'total_cost': info['total_cost'],
                'order_id': info['order_id']
            }
            for ticker, info in placed_orders.items()
        ])
        
        logger.info("\nРазмещенные ордера:")
        print(df.to_string(index=False))
        
        # Ждем 10 секунд, затем отменяем все ордера (если не в учебных целях)
        logger.info("\nЖдем 10 секунд, затем отменяем все ордера...")
        time.sleep(10)
        
        cancel_result = alpaca.cancel_all_orders()
        if cancel_result.get('success'):
            logger.info("Все открытые ордера успешно отменены")
        else:
            logger.warning(f"Проблема при отмене ордеров: {cancel_result.get('error')}")
    else:
        logger.warning("Не удалось разместить ни одного ордера")
    
    # Получение текущих открытых ордеров
    open_orders = alpaca.get_open_orders()
    logger.info(f"Текущее количество открытых ордеров: {len(open_orders)}")

if __name__ == "__main__":
    main() 