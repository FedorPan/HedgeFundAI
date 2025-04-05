#!/usr/bin/env python3
"""
Комплексное тестирование системы управления портфелем HedgeFundAI.

Этот скрипт тестирует полную цепочку работы системы:
1. Загрузка 20 случайных тикеров из кэша SP500
2. Формирование случайного целевого портфеля (long/short)
3. Ребалансировка через PortfolioManager
4. Размещение ордеров через AlpacaExecutor с TP/SL
5. Печать результатов
"""

import os
import json
import random
import logging
import pandas as pd
from typing import Dict, List, Any
from datetime import datetime
from dotenv import load_dotenv

from src.trading.alpaca_executor import AlpacaExecutor
from src.trading.portfolio_manager import PortfolioManager

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_portfolio')

# Загрузка переменных окружения
load_dotenv()

def get_random_tickers(count=20, cache_file='.cache/sp500_201_300.json'):
    """
    Получает список случайных тикеров из кэшированного списка SP500.
    
    Args:
        count: Количество тикеров для выбора.
        cache_file: Путь к кэш-файлу с тикерами.
        
    Returns:
        Список случайных тикеров.
    """
    try:
        # Загружаем кэшированные тикеры
        if not os.path.exists(cache_file):
            logger.warning(f"Кэш-файл {cache_file} не найден. Используем предопределенный список.")
            predefined_tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "JPM", "V", "JNJ", "WMT",
                                 "PG", "HD", "BAC", "MA", "DIS", "NFLX", "INTC", "VZ", "T", "KO"]
            return random.sample(predefined_tickers, min(count, len(predefined_tickers)))
        
        with open(cache_file, 'r') as f:
            cached_data = json.load(f)
        
        if 'tickers' not in cached_data or not cached_data['tickers']:
            logger.warning("Некорректные данные в кэше. Используем предопределенный список.")
            predefined_tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "JPM", "V", "JNJ", "WMT",
                                 "PG", "HD", "BAC", "MA", "DIS", "NFLX", "INTC", "VZ", "T", "KO"]
            return random.sample(predefined_tickers, min(count, len(predefined_tickers)))
        
        tickers = cached_data['tickers']
        
        # Выбираем случайные тикеры
        return random.sample(tickers, min(count, len(tickers)))
    except Exception as e:
        logger.error(f"Ошибка при получении тикеров: {e}")
        predefined_tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "JPM", "V", "JNJ", "WMT",
                             "PG", "HD", "BAC", "MA", "DIS", "NFLX", "INTC", "VZ", "T", "KO"]
        return random.sample(predefined_tickers, min(count, len(predefined_tickers)))

def create_target_portfolio(tickers: List[str], long_ratio=0.6) -> Dict[str, Dict[str, Any]]:
    """
    Создает целевой портфель из списка тикеров, случайно распределяя их на long и short.
    
    Args:
        tickers: Список тикеров для включения в портфель
        long_ratio: Доля тикеров для long позиций (0-1)
        
    Returns:
        Целевой портфель в формате словаря
    """
    # Определяем количество тикеров для long и short
    num_long = int(len(tickers) * long_ratio)
    
    # Перемешиваем тикеры
    random.shuffle(tickers)
    
    # Создаем списки long и short тикеров
    long_tickers = tickers[:num_long]
    short_tickers = tickers[num_long:]
    
    # Рассчитываем веса (равные веса)
    weight_per_ticker = 1.0 / len(tickers)
    
    # Создаем целевой портфель
    target_portfolio = {}
    
    # Добавляем long позиции
    for ticker in long_tickers:
        target_portfolio[ticker] = {
            "side": "long",
            "weight": weight_per_ticker
        }
    
    # Добавляем short позиции
    for ticker in short_tickers:
        target_portfolio[ticker] = {
            "side": "short",
            "weight": weight_per_ticker
        }
    
    return target_portfolio

def print_portfolio_details(target_portfolio: Dict[str, Dict[str, Any]]):
    """
    Выводит детали целевого портфеля.
    
    Args:
        target_portfolio: Целевой портфель
    """
    print("\n=== ЦЕЛЕВОЙ ПОРТФЕЛЬ ===")
    
    # Создаем DataFrame для удобного вывода
    portfolio_data = []
    for ticker, data in target_portfolio.items():
        portfolio_data.append({
            "ticker": ticker,
            "side": data["side"],
            "weight": data["weight"]
        })
    
    df = pd.DataFrame(portfolio_data)
    
    # Выводим сводку
    long_positions = df[df['side'] == 'long']
    short_positions = df[df['side'] == 'short']
    
    print(f"Всего позиций: {len(df)}")
    print(f"Long позиций: {len(long_positions)} (вес: {long_positions['weight'].sum():.2f})")
    print(f"Short позиций: {len(short_positions)} (вес: {short_positions['weight'].sum():.2f})")
    
    # Выводим детали
    print("\nРаспределение позиций:")
    df['weight'] = df['weight'].apply(lambda x: f"{x:.1%}")
    print(df.to_string(index=False))

def print_rebalance_results(results: Dict[str, Any]):
    """
    Выводит результаты ребалансировки.
    
    Args:
        results: Результаты ребалансировки от PortfolioManager
    """
    print("\n=== РЕЗУЛЬТАТЫ РЕБАЛАНСИРОВКИ ===")
    print(f"Статус: {'Успешно' if results.get('success', False) else 'Ошибка'}")
    print(f"Запланировано действий: {results.get('actions_planned', 0)}")
    print(f"Выполнено действий: {results.get('actions_executed', 0)}")
    
    # Выводим детали по ордерам
    if 'orders' in results and results['orders']:
        print("\nРазмещенные ордера:")
        
        # Преобразуем в DataFrame для удобного вывода
        orders_data = []
        for order in results['orders']:
            order_data = {
                "ticker": order["ticker"],
                "действие": order["action"],
                "сторона": order["side"],
                "акции": order["shares"],
                "статус": order["status"]
            }
            
            # Добавляем TP/SL если есть
            if "take_profit_pct" in order:
                order_data["TP"] = f"{order['take_profit_pct']*100:.1f}%"
            
            if "stop_loss_pct" in order:
                order_data["SL"] = f"{order['stop_loss_pct']*100:.1f}%"
            
            orders_data.append(order_data)
        
        df = pd.DataFrame(orders_data)
        print(df.to_string(index=False))
    
    # Выводим ошибки если есть
    failed_orders = [order for order in results.get('orders', []) if order.get('status') == 'failed']
    if failed_orders:
        print("\nОшибки при размещении ордеров:")
        for order in failed_orders:
            print(f"- {order['ticker']}: {order.get('error', 'Неизвестная ошибка')}")

def print_portfolio_summary(portfolio_summary: Dict[str, Any]):
    """
    Выводит сводку по текущему портфелю.
    
    Args:
        portfolio_summary: Сводка по портфелю от PortfolioManager
    """
    print("\n=== ТЕКУЩИЙ ПОРТФЕЛЬ ===")
    print(f"Стоимость портфеля: ${portfolio_summary.get('portfolio_value', 0):.2f}")
    print(f"Наличные: ${portfolio_summary.get('cash', 0):.2f}")
    print(f"Long-экспозиция: ${portfolio_summary.get('long_exposure', 0):.2f}")
    print(f"Short-экспозиция: ${portfolio_summary.get('short_exposure', 0):.2f}")
    print(f"Long-позиций: {portfolio_summary.get('long_positions', 0)}")
    print(f"Short-позиций: {portfolio_summary.get('short_positions', 0)}")
    
    # Выводим детали по позициям
    if 'positions' in portfolio_summary and portfolio_summary['positions']:
        print("\nПозиции:")
        
        # Преобразуем в DataFrame для удобного вывода
        positions_data = []
        for position in portfolio_summary['positions']:
            positions_data.append({
                "ticker": position["ticker"],
                "side": position["side"],
                "quantity": position["quantity"],
                "price": f"${position['current_price']:.2f}",
                "value": f"${position['market_value']:.2f}",
                "weight": f"{position['weight']:.1%}"
            })
        
        df = pd.DataFrame(positions_data)
        print(df.to_string(index=False))

def main():
    """
    Основная функция для тестирования системы управления портфелем.
    """
    logger.info("===== ТЕСТИРОВАНИЕ СИСТЕМЫ УПРАВЛЕНИЯ ПОРТФЕЛЕМ =====")
    
    # Определяем параметры теста
    num_tickers = 20
    total_value = 100000.0  # $100,000
    
    # 1. Загружаем случайные тикеры
    logger.info(f"Выбираем {num_tickers} случайных тикеров из SP500...")
    tickers = get_random_tickers(num_tickers)
    logger.info(f"Выбранные тикеры: {tickers}")
    
    # 2. Создаем целевой портфель
    logger.info("Создаем целевой портфель...")
    target_portfolio = create_target_portfolio(tickers, long_ratio=0.7)
    print_portfolio_details(target_portfolio)
    
    # 3. Инициализируем AlpacaExecutor и PortfolioManager
    logger.info("Инициализация AlpacaExecutor и PortfolioManager...")
    alpaca = AlpacaExecutor(is_paper=True)
    
    # Проверяем состояние рынка
    market_status = alpaca.check_market_status()
    if market_status and 'error' not in market_status:
        logger.info(f"Рынок {'открыт' if market_status.get('is_open') else 'закрыт'}.")
        if not market_status.get('is_open'):
            logger.info(f"Следующее открытие рынка: {market_status.get('next_open')}")
    
    # Создаем специфичные TP/SL настройки для некоторых тикеров
    per_ticker_config = {}
    for ticker in random.sample(tickers, 5):  # Выбираем 5 случайных тикеров
        per_ticker_config[ticker] = {
            "take_profit_pct": round(random.uniform(0.08, 0.20), 2),
            "stop_loss_pct": round(random.uniform(0.03, 0.10), 2)
        }
    
    # Сохраняем конфигурацию в файл
    os.makedirs('.config', exist_ok=True)
    with open('.config/ticker_tp_sl_config.json', 'w') as f:
        json.dump(per_ticker_config, f, indent=2)
    
    portfolio_manager = PortfolioManager(
        alpaca_executor=alpaca,
        per_ticker_config_path='.config/ticker_tp_sl_config.json'
    )
    
    # 4. Получаем текущий статус портфеля до ребалансировки
    logger.info("Получаем текущее состояние портфеля...")
    portfolio_summary_before = portfolio_manager.get_portfolio_summary()
    
    # 5. Спрашиваем, выполнять ли реальную ребалансировку
    print("\n=== ВАЖНО ===")
    print(f"Вы собираетесь выполнить ребалансировку портфеля с целевым распределением для {num_tickers} тикеров")
    print(f"Общая сумма инвестиций: ${total_value:.2f}")
    execute = input("Выполнить ребалансировку? (y/n): ")
    
    if execute.lower() != 'y':
        logger.info("Ребалансировка отменена пользователем")
        return
    
    # 6. Выполняем ребалансировку
    logger.info(f"Выполняем ребалансировку портфеля на сумму ${total_value:.2f}...")
    results = portfolio_manager.rebalance(target_portfolio, total_value)
    
    # 7. Выводим результаты
    print_rebalance_results(results)
    
    # 8. Получаем обновленный статус портфеля
    logger.info("Получаем обновленное состояние портфеля...")
    portfolio_summary_after = portfolio_manager.get_portfolio_summary()
    print_portfolio_summary(portfolio_summary_after)
    
    # 9. Спрашиваем, отменить ли все ордера
    cancel_orders = input("\nОтменить все размещенные ордера? (y/n): ")
    if cancel_orders.lower() == 'y':
        logger.info("Отмена всех ордеров...")
        cancel_result = alpaca.cancel_all_orders()
        if cancel_result.get('success'):
            logger.info("Все ордера успешно отменены")
        else:
            logger.warning(f"Проблема при отмене ордеров: {cancel_result.get('error', 'Unknown error')}")
    
    # 10. Завершение теста
    logger.info("===== ТЕСТИРОВАНИЕ ЗАВЕРШЕНО =====")

if __name__ == "__main__":
    main() 