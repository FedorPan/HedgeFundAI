#!/usr/bin/env python3
"""
Модуль управления портфелем (PortfolioManager).

Отвечает за:
- Синхронизацию с Alpaca для получения текущих позиций
- Расчет необходимых ордеров для ребалансировки
- Управление TP/SL уровнями для позиций
- Передачу ордеров на исполнение через AlpacaExecutor

Связывает аналитическую часть (scoring) с торговым исполнением.
"""

import os
import json
import logging
import math
import time
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional
from decimal import Decimal, ROUND_DOWN

from src.trading.alpaca_executor import AlpacaExecutor

# Настройка логирования
logger = logging.getLogger('portfolio_manager')

class PortfolioManager:
    """
    Менеджер портфеля для управления позициями и ребалансировки.
    
    Основные задачи:
    - Синхронизация с текущими позициями в Alpaca
    - Расчет плана ребалансировки на основе целевого портфеля
    - Настройка и применение TP/SL уровней
    - Исполнение плана ребалансировки через AlpacaExecutor
    """
    
    def __init__(self, 
                 alpaca_executor: AlpacaExecutor = None,
                 default_tp_sl_config: Dict[str, float] = None,
                 per_ticker_config_path: str = None,
                 config_dir: str = '.config',
                 history_dir: str = '.history'):
        """
        Инициализация менеджера портфеля.
        
        Args:
            alpaca_executor: Инстанс AlpacaExecutor для исполнения сделок
            default_tp_sl_config: Настройки TP/SL по умолчанию
            per_ticker_config_path: Путь к файлу с индивидуальными настройками TP/SL
            config_dir: Директория для хранения конфигурационных файлов
            history_dir: Директория для хранения истории ребалансировок
        """
        # Настройка AlpacaExecutor
        self.alpaca = alpaca_executor or AlpacaExecutor(is_paper=True)
        
        # Настройки TP/SL по умолчанию
        self.default_tp_sl_config = default_tp_sl_config or {
            "take_profit_pct": 0.10,  # +10%
            "stop_loss_pct": 0.05     # -5%
        }
        
        # Директория конфигурации
        self.config_dir = config_dir
        os.makedirs(self.config_dir, exist_ok=True)
        
        # Директория истории
        self.history_dir = history_dir
        os.makedirs(self.history_dir, exist_ok=True)
        
        # Индивидуальные настройки TP/SL для тикеров
        self.per_ticker_config_path = per_ticker_config_path or os.path.join(
            self.config_dir, 'ticker_tp_sl_config.json'
        )
        self.per_ticker_config = self._load_per_ticker_config()
        
        # Состояние портфеля
        self.current_positions = {}
        self.account_info = {}
        self.last_sync_time = 0
        
        # История ребалансировок
        self.last_rebalance_timestamp = 0
        self.previous_portfolio = {}
        self.rebalance_history = []
        self._load_rebalance_history()
        
        # Инициализация
        logger.info("PortfolioManager initialized")
        self.sync_with_alpaca()
    
    def _load_per_ticker_config(self) -> Dict[str, Dict[str, float]]:
        """
        Загружает индивидуальные настройки TP/SL для тикеров из файла.
        
        Returns:
            Словарь с настройками для каждого тикера.
        """
        if not os.path.exists(self.per_ticker_config_path):
            logger.info(f"Per-ticker TP/SL config file not found at {self.per_ticker_config_path}. "
                      f"Using default settings only.")
            return {}
        
        try:
            with open(self.per_ticker_config_path, 'r') as f:
                config = json.load(f)
            
            logger.info(f"Loaded TP/SL configurations for {len(config)} tickers")
            return config
        except Exception as e:
            logger.error(f"Error loading per-ticker TP/SL configs: {e}")
            return {}
    
    def _load_rebalance_history(self) -> None:
        """
        Загружает историю ребалансировок из файла.
        """
        history_path = os.path.join(self.history_dir, 'rebalance_history.json')
        if not os.path.exists(history_path):
            logger.info(f"Rebalance history file not found at {history_path}. "
                      f"Starting with empty history.")
            return
        
        try:
            with open(history_path, 'r') as f:
                history_data = json.load(f)
            
            self.rebalance_history = history_data.get('history', [])
            self.last_rebalance_timestamp = history_data.get('last_timestamp', 0)
            
            if self.last_rebalance_timestamp > 0:
                logger.info(f"Loaded rebalance history with {len(self.rebalance_history)} entries. "
                          f"Last rebalance: {self.get_last_rebalance_time(format_str='%Y-%m-%d %H:%M:%S')}")
        except Exception as e:
            logger.error(f"Error loading rebalance history: {e}")
    
    def _save_rebalance_history(self) -> bool:
        """
        Сохраняет историю ребалансировок в файл.
        
        Returns:
            True если сохранение успешно, иначе False.
        """
        history_path = os.path.join(self.history_dir, 'rebalance_history.json')
        try:
            history_data = {
                'last_timestamp': self.last_rebalance_timestamp,
                'history': self.rebalance_history
            }
            
            with open(history_path, 'w') as f:
                json.dump(history_data, f, indent=2)
            
            logger.info(f"Saved rebalance history with {len(self.rebalance_history)} entries")
            return True
        except Exception as e:
            logger.error(f"Error saving rebalance history: {e}")
            return False
    
    def save_per_ticker_config(self) -> bool:
        """
        Сохраняет индивидуальные настройки TP/SL для тикеров в файл.
        
        Returns:
            True если сохранение успешно, иначе False.
        """
        try:
            with open(self.per_ticker_config_path, 'w') as f:
                json.dump(self.per_ticker_config, f, indent=2)
            
            logger.info(f"Saved TP/SL configurations for {len(self.per_ticker_config)} tickers")
            return True
        except Exception as e:
            logger.error(f"Error saving per-ticker TP/SL configs: {e}")
            return False
    
    def update_ticker_config(self, ticker: str, tp_pct: float = None, sl_pct: float = None) -> bool:
        """
        Обновляет индивидуальные настройки TP/SL для указанного тикера.
        
        Args:
            ticker: Символ тикера
            tp_pct: Процент Take Profit
            sl_pct: Процент Stop Loss
            
        Returns:
            True если обновление успешно, иначе False.
        """
        if ticker not in self.per_ticker_config:
            self.per_ticker_config[ticker] = {}
        
        if tp_pct is not None:
            self.per_ticker_config[ticker]["take_profit_pct"] = tp_pct
        
        if sl_pct is not None:
            self.per_ticker_config[ticker]["stop_loss_pct"] = sl_pct
        
        logger.info(f"Updated TP/SL config for {ticker}: TP={tp_pct}, SL={sl_pct}")
        return self.save_per_ticker_config()
    
    def sync_with_alpaca(self) -> bool:
        """
        Синхронизирует текущее состояние портфеля с Alpaca.
        
        Returns:
            True если синхронизация успешна, иначе False.
        """
        try:
            logger.info("Syncing portfolio with Alpaca...")
            
            # Получаем информацию о счете
            account_info = self.alpaca.get_account_info()
            if 'error' in account_info:
                logger.error(f"Failed to get account info: {account_info['error']}")
                return False
            
            # Получаем текущие позиции
            positions = self.alpaca.get_positions()
            if positions is None:
                logger.error("Failed to get positions from Alpaca")
                return False
            
            # Обновляем внутреннее состояние
            self.account_info = account_info
            
            # Конвертируем список позиций в словарь для удобства доступа
            self.current_positions = {
                p['ticker']: {
                    'quantity': p['quantity'],
                    'market_value': p['market_value'],
                    'side': p['side'],
                    'avg_entry_price': p['avg_entry_price'],
                    'current_price': p['current_price']
                }
                for p in positions
            }
            
            logger.info(f"Successfully synced portfolio: {len(self.current_positions)} positions, "
                      f"portfolio value: ${account_info.get('portfolio_value', 0):.2f}")
            return True
            
        except Exception as e:
            logger.exception(f"Error syncing with Alpaca: {e}")
            return False
    
    def get_tp_sl_config(self, ticker: str) -> Tuple[float, float]:
        """
        Возвращает настройки TP/SL для указанного тикера.
        
        Args:
            ticker: Символ тикера
            
        Returns:
            Кортеж (take_profit_pct, stop_loss_pct)
        """
        ticker_config = self.per_ticker_config.get(ticker, {})
        
        # Получаем значения с fallback на дефолтные настройки
        tp_pct = ticker_config.get("take_profit_pct", self.default_tp_sl_config["take_profit_pct"])
        sl_pct = ticker_config.get("stop_loss_pct", self.default_tp_sl_config["stop_loss_pct"])
        
        return tp_pct, sl_pct
    
    def calculate_shares_to_buy(self, ticker: str, target_value: float) -> int:
        """
        Рассчитывает количество акций для покупки на основе целевой стоимости.
        
        Args:
            ticker: Символ тикера
            target_value: Целевая стоимость позиции
            
        Returns:
            Количество акций для покупки (целое число)
        """
        # Получаем последнюю цену
        price = self.alpaca.get_last_trade_price(ticker)
        if not price or price <= 0:
            logger.warning(f"Invalid price for {ticker}: {price}")
            return 0
        
        # Рассчитываем количество акций
        shares = target_value / price
        
        # Округляем до целого числа акций вниз
        return int(shares)
    
    def calculate_rebalance_plan(self, target_portfolio: Dict[str, Dict[str, Any]], 
                                total_value: float) -> List[Dict[str, Any]]:
        """
        Рассчитывает план ребалансировки портфеля.
        
        Args:
            target_portfolio: Целевой портфель {ticker: {"side": "long"/"short", "weight": float}}
            total_value: Общая стоимость портфеля для расчета целевых позиций
            
        Returns:
            Список действий для ребалансировки
        """
        logger.info(f"Calculating rebalance plan for portfolio with total value: ${total_value:.2f}")
        
        # Обновляем текущие позиции
        self.sync_with_alpaca()
        
        rebalance_actions = []
        
        # Проверяем каждый тикер в целевом портфеле
        for ticker, target in target_portfolio.items():
            target_side = target.get("side", "long")
            target_weight = float(target.get("weight", 0))
            
            # Рассчитываем целевую стоимость позиции
            target_value = total_value * target_weight
            
            # Получаем текущую позицию
            current_position = self.current_positions.get(ticker, None)
            
            # Определяем направление и объем сделки
            if current_position is None:
                # Новая позиция, нужно купить/открыть шорт
                target_shares = self.calculate_shares_to_buy(ticker, target_value)
                
                if target_shares > 0:
                    action = {
                        "ticker": ticker,
                        "action": "open",
                        "side": target_side,
                        "shares": target_shares,
                        "estimated_value": target_value
                    }
                    rebalance_actions.append(action)
                    logger.info(f"Plan to open {target_side} position for {ticker}: {target_shares} shares")
            else:
                # Существующая позиция, нужно изменить
                current_side = current_position["side"]
                current_shares = abs(current_position["quantity"])
                current_value = current_position["market_value"]
                
                # Рассчитываем целевое количество акций
                target_shares = self.calculate_shares_to_buy(ticker, target_value)
                
                if target_side != current_side:
                    # Изменение стороны: закрываем текущую позицию, открываем новую
                    close_action = {
                        "ticker": ticker,
                        "action": "close",
                        "side": current_side,
                        "shares": current_shares,
                        "estimated_value": current_value
                    }
                    rebalance_actions.append(close_action)
                    logger.info(f"Plan to close {current_side} position for {ticker}: {current_shares} shares")
                    
                    if target_shares > 0:
                        open_action = {
                            "ticker": ticker,
                            "action": "open",
                            "side": target_side,
                            "shares": target_shares,
                            "estimated_value": target_value
                        }
                        rebalance_actions.append(open_action)
                        logger.info(f"Plan to open {target_side} position for {ticker}: {target_shares} shares")
                
                else:
                    # Та же сторона, но возможно разный объем
                    if target_shares > current_shares:
                        # Увеличиваем позицию
                        add_shares = target_shares - current_shares
                        action = {
                            "ticker": ticker,
                            "action": "add",
                            "side": target_side,
                            "shares": add_shares,
                            "estimated_value": add_shares * current_position["current_price"]
                        }
                        rebalance_actions.append(action)
                        logger.info(f"Plan to add to {target_side} position for {ticker}: {add_shares} shares")
                    
                    elif target_shares < current_shares:
                        # Уменьшаем позицию
                        reduce_shares = current_shares - target_shares
                        action = {
                            "ticker": ticker,
                            "action": "reduce",
                            "side": target_side,
                            "shares": reduce_shares,
                            "estimated_value": reduce_shares * current_position["current_price"]
                        }
                        rebalance_actions.append(action)
                        logger.info(f"Plan to reduce {target_side} position for {ticker}: {reduce_shares} shares")
        
        # Проверяем позиции, которых нет в целевом портфеле
        for ticker, position in self.current_positions.items():
            if ticker not in target_portfolio:
                # Закрываем позицию
                action = {
                    "ticker": ticker,
                    "action": "close",
                    "side": position["side"],
                    "shares": abs(position["quantity"]),
                    "estimated_value": position["market_value"]
                }
                rebalance_actions.append(action)
                logger.info(f"Plan to close {position['side']} position for {ticker}: {abs(position['quantity'])} shares (not in target portfolio)")
        
        logger.info(f"Rebalance plan contains {len(rebalance_actions)} actions")
        return rebalance_actions
    
    def rebalance(self, target_portfolio: Dict[str, Dict[str, Any]], 
                 total_value: float = None) -> Dict[str, Any]:
        """
        Выполняет ребалансировку портфеля согласно целевому распределению.
        
        Args:
            target_portfolio: Целевой портфель {ticker: {"side": "long"/"short", "weight": float}}
            total_value: Общая стоимость портфеля для расчета целевых позиций.
                        Если None, используется текущая стоимость портфеля.
            
        Returns:
            Результаты ребалансировки
        """
        # Синхронизируем данные с Alpaca
        if not self.sync_with_alpaca():
            return {"success": False, "error": "Failed to sync with Alpaca"}
        
        # Сохраняем текущее состояние для сравнения
        self.previous_portfolio = {
            "positions": self.current_positions.copy(),
            "account_info": self.account_info.copy(),
            "timestamp": time.time()
        }
        
        # Если общая стоимость не указана, используем текущую стоимость портфеля
        if total_value is None:
            total_value = float(self.account_info.get("portfolio_value", 0))
            logger.info(f"Using current portfolio value: ${total_value:.2f}")
        
        # Рассчитываем план ребалансировки
        rebalance_plan = self.calculate_rebalance_plan(target_portfolio, total_value)
        
        # Результаты исполнения ребалансировки
        results = {
            "success": True,
            "actions_planned": len(rebalance_plan),
            "actions_executed": 0,
            "orders": [],
            "target_portfolio": target_portfolio,
            "total_value": total_value,
            "timestamp": time.time()
        }
        
        # Выполняем каждое действие из плана
        for action in rebalance_plan:
            ticker = action["ticker"]
            action_type = action["action"]
            side = action["side"]
            shares = action["shares"]
            
            # Пропускаем действия с нулевым количеством акций
            if shares <= 0:
                logger.warning(f"Skipping {action_type} {side} for {ticker} - zero shares")
                continue
            
            # Определяем сторону ордера для Alpaca
            order_side = None
            if action_type in ["open", "add"]:
                order_side = "buy" if side == "long" else "sell"
            elif action_type in ["close", "reduce"]:
                order_side = "sell" if side == "long" else "buy"
            
            if not order_side:
                logger.error(f"Invalid action/side combination: {action_type}/{side}")
                continue
            
            # Получаем TP/SL конфигурацию для тикера
            tp_pct, sl_pct = self.get_tp_sl_config(ticker)
            
            # Добавляем TP/SL только для открытия новых позиций или добавления к существующим
            use_tp_sl = action_type in ["open", "add"]
            
            # Размещаем ордер через AlpacaExecutor
            try:
                logger.info(f"Placing {order_side} order for {ticker}: {shares} shares "
                          f"({action_type} {side})" +
                          (f" with TP={tp_pct*100:.1f}%, SL={sl_pct*100:.1f}%" if use_tp_sl else ""))
                
                order_params = {
                    "ticker": ticker,
                    "qty": shares,
                    "side": order_side,
                    "order_type": "market",
                    "time_in_force": "day"
                }
                
                # Добавляем TP/SL только при открытии или добавлении к позиции
                if use_tp_sl:
                    order_params["take_profit_pct"] = tp_pct
                    order_params["stop_loss_pct"] = sl_pct
                
                # Размещаем ордер
                order_result = self.alpaca.submit_order(**order_params)
                
                # Обрабатываем результат
                if 'error' in order_result:
                    logger.error(f"Error placing order for {ticker}: {order_result['error']}")
                    results["orders"].append({
                        "ticker": ticker,
                        "action": action_type,
                        "side": side,
                        "shares": shares,
                        "status": "failed",
                        "error": order_result['error']
                    })
                else:
                    logger.info(f"Successfully placed order for {ticker}: {order_result['id']}")
                    results["actions_executed"] += 1
                    results["orders"].append({
                        "ticker": ticker,
                        "action": action_type,
                        "side": side,
                        "shares": shares,
                        "status": "success",
                        "order_id": order_result['id'],
                        "order_status": order_result['status']
                    })
                    
                    # Добавляем информацию о TP/SL если применимо
                    if use_tp_sl:
                        results["orders"][-1]["take_profit_pct"] = tp_pct
                        results["orders"][-1]["stop_loss_pct"] = sl_pct
                
            except Exception as e:
                logger.exception(f"Exception placing order for {ticker}: {e}")
                results["orders"].append({
                    "ticker": ticker,
                    "action": action_type,
                    "side": side,
                    "shares": shares,
                    "status": "failed",
                    "error": str(e)
                })
        
        # Обновляем статус успешности
        results["success"] = results["actions_executed"] > 0 or results["actions_planned"] == 0
        
        # Синхронизируем состояние после ребалансировки
        self.sync_with_alpaca()
        
        # Обновляем дату последней ребалансировки и сохраняем в историю
        if results["success"]:
            self.last_rebalance_timestamp = results["timestamp"]
            
            # Добавляем в историю
            if len(self.rebalance_history) >= 10:
                # Ограничиваем историю 10 последними ребалансировками
                self.rebalance_history = self.rebalance_history[-9:]
            
            # Упрощенная версия результатов для истории
            history_entry = {
                "timestamp": self.last_rebalance_timestamp,
                "total_value": total_value,
                "actions_executed": results["actions_executed"],
                "tickers": list(target_portfolio.keys())
            }
            self.rebalance_history.append(history_entry)
            
            # Сохраняем историю
            self._save_rebalance_history()
        
        logger.info(f"Rebalance completed: {results['actions_executed']}/{results['actions_planned']} actions executed successfully")
        logger.info(f"Rebalance timestamp: {self.get_last_rebalance_time(format_str='%Y-%m-%d %H:%M:%S')}")
        
        return results
    
    def get_last_rebalance_time(self, format_str: str = '%d %b %Y') -> str:
        """
        Возвращает дату и время последней ребалансировки в читаемом формате.
        
        Args:
            format_str: Строка формата для datetime.strftime()
            
        Returns:
            Форматированная дата/время последней ребалансировки или "Never" если ребалансировки не было
        """
        if self.last_rebalance_timestamp <= 0:
            return "Never"
        
        dt = datetime.fromtimestamp(self.last_rebalance_timestamp)
        return dt.strftime(format_str)
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """
        Возвращает сводку по текущему портфелю.
        
        Returns:
            Словарь с информацией о портфеле
        """
        # Синхронизируем данные с Alpaca
        self.sync_with_alpaca()
        
        # Рассчитываем общую стоимость портфеля
        portfolio_value = float(self.account_info.get("portfolio_value", 0))
        
        # Сводка по сторонам (long/short)
        long_value = sum(p["market_value"] for p in self.current_positions.values() 
                        if p["side"] == "long")
        short_value = sum(p["market_value"] for p in self.current_positions.values() 
                        if p["side"] == "short")
        
        # Формируем сводку
        summary = {
            "portfolio_value": portfolio_value,
            "cash": float(self.account_info.get("cash", 0)),
            "long_exposure": long_value,
            "short_exposure": short_value,
            "long_positions": len([p for p in self.current_positions.values() if p["side"] == "long"]),
            "short_positions": len([p for p in self.current_positions.values() if p["side"] == "short"]),
            "last_rebalance": self.get_last_rebalance_time(),
            "last_rebalance_timestamp": self.last_rebalance_timestamp,
            "positions": [
                {
                    "ticker": ticker,
                    "side": position["side"],
                    "quantity": position["quantity"],
                    "market_value": position["market_value"],
                    "current_price": position["current_price"],
                    "avg_entry_price": position["avg_entry_price"],
                    "weight": position["market_value"] / portfolio_value if portfolio_value > 0 else 0
                }
                for ticker, position in self.current_positions.items()
            ]
        }
        
        return summary
    
    def get_portfolio_delta(self) -> Dict[str, Any]:
        """
        Рассчитывает изменения в портфеле с момента последней ребалансировки.
        
        Returns:
            Словарь с информацией об изменениях в портфеле
        """
        if not self.previous_portfolio:
            return {
                "success": False,
                "error": "No previous portfolio data available"
            }
        
        # Синхронизируем данные с Alpaca
        self.sync_with_alpaca()
        
        # Получаем текущее состояние
        current_value = float(self.account_info.get("portfolio_value", 0))
        previous_value = float(self.previous_portfolio.get("account_info", {}).get("portfolio_value", 0))
        
        # Рассчитываем изменение стоимости портфеля
        value_change = current_value - previous_value
        value_change_pct = (value_change / previous_value * 100) if previous_value > 0 else 0
        
        # Сравниваем позиции
        previous_positions = self.previous_portfolio.get("positions", {})
        position_changes = []
        
        # Проверяем текущие позиции
        for ticker, current_pos in self.current_positions.items():
            if ticker in previous_positions:
                # Изменение существующей позиции
                prev_pos = previous_positions[ticker]
                value_change = current_pos["market_value"] - prev_pos["market_value"]
                pct_change = (value_change / prev_pos["market_value"] * 100) if prev_pos["market_value"] > 0 else 0
                
                position_changes.append({
                    "ticker": ticker,
                    "side": current_pos["side"],
                    "current_value": current_pos["market_value"],
                    "previous_value": prev_pos["market_value"],
                    "value_change": value_change,
                    "pct_change": pct_change,
                    "current_price": current_pos["current_price"],
                    "previous_price": prev_pos["current_price"],
                    "type": "existing"
                })
            else:
                # Новая позиция
                position_changes.append({
                    "ticker": ticker,
                    "side": current_pos["side"],
                    "current_value": current_pos["market_value"],
                    "previous_value": 0,
                    "value_change": current_pos["market_value"],
                    "pct_change": 100,
                    "current_price": current_pos["current_price"],
                    "type": "new"
                })
        
        # Проверяем закрытые позиции
        for ticker, prev_pos in previous_positions.items():
            if ticker not in self.current_positions:
                position_changes.append({
                    "ticker": ticker,
                    "side": prev_pos["side"],
                    "current_value": 0,
                    "previous_value": prev_pos["market_value"],
                    "value_change": -prev_pos["market_value"],
                    "pct_change": -100,
                    "previous_price": prev_pos["current_price"],
                    "type": "closed"
                })
        
        # Сортируем изменения по абсолютному изменению
        position_changes.sort(key=lambda x: abs(x["value_change"]), reverse=True)
        
        return {
            "success": True,
            "current_value": current_value,
            "previous_value": previous_value,
            "value_change": value_change,
            "value_change_pct": value_change_pct,
            "current_timestamp": time.time(),
            "previous_timestamp": self.previous_portfolio.get("timestamp", 0),
            "position_changes": position_changes
        } 