import os
import time
import logging
import schedule
import threading
from datetime import datetime, timedelta
from pathlib import Path
import traceback
import sys

# Добавляем корневую директорию проекта в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.utils.db.models import AssetRepository
from src.data.market_data_service import MarketDataService
from src.analysis.ai_reasoner import AIReasoner
from src.analysis.scoring_engine import ScoringEngine

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(Path(__file__).parent.parent.parent.parent / "logs" / "scheduler.log")
    ]
)
logger = logging.getLogger("scheduler")

class DataUpdateScheduler:
    """Планировщик обновления данных"""
    
    def __init__(self):
        """Инициализация планировщика"""
        self.repository = AssetRepository()
        self.market_data = MarketDataService()
        self.ai_reasoner = AIReasoner()
        self.scoring_engine = ScoringEngine()
        self.running = False
        self.thread = None
        
        # Создаем директорию для логов, если ее нет
        logs_dir = Path(__file__).parent.parent.parent.parent / "logs"
        if not logs_dir.exists():
            logs_dir.mkdir(parents=True, exist_ok=True)
    
    def update_market_data(self):
        """Обновляет рыночные данные для всех активов"""
        try:
            logger.info("Начато обновление рыночных данных")
            update_id = self.repository.log_data_update("market_data", "started")
            
            # Получаем все тикеры
            tickers = self.market_data.get_tickers()
            total = len(tickers)
            success_count = 0
            
            for i, ticker in enumerate(tickers):
                try:
                    logger.info(f"Обработка тикера {i+1}/{total}: {ticker}")
                    
                    # Получаем данные для тикера
                    ticker_data = self.market_data.get_ticker_data(ticker, force_refresh=True)
                    
                    if ticker_data:
                        # Сохраняем базовую информацию об активе
                        self.repository.save_asset(
                            ticker=ticker,
                            name=ticker_data.get('name', f"{ticker} Inc."),
                            sector=ticker_data.get('sector', '')
                        )
                        
                        # Преобразуем ключи в snake_case для базы данных
                        metrics = {}
                        mapping = {
                            'price': 'price',
                            'change': 'change',
                            'changePercent': 'change_percent',
                            'marketCap': 'market_cap',
                            'peRatio': 'pe_ratio',
                            'epsGrowth': 'eps_growth',
                            'revenueGrowth': 'revenue_growth',
                            'volatility3m': 'volatility_3m',
                            'debtEquity': 'debt_equity',
                            'momentum3m': 'momentum_3m',
                            'consensusScore': 'analyst_consensus'
                        }
                        
                        for key, db_key in mapping.items():
                            metrics[db_key] = ticker_data.get(key)
                        
                        # Сохраняем метрики
                        self.repository.save_metrics(ticker, metrics)
                        success_count += 1
                
                except Exception as e:
                    logger.error(f"Ошибка при обработке тикера {ticker}: {str(e)}")
                    logger.debug(traceback.format_exc())
            
            logger.info(f"Обновление рыночных данных завершено. Успешно обработано {success_count}/{total} тикеров")
            self.repository.log_data_update(
                "market_data", 
                "completed", 
                f"Processed {success_count}/{total} tickers"
            )
        
        except Exception as e:
            logger.error(f"Ошибка при обновлении рыночных данных: {str(e)}")
            logger.debug(traceback.format_exc())
            self.repository.log_data_update(
                "market_data", 
                "failed", 
                f"Error: {str(e)}"
            )
    
    def update_ai_recommendations(self):
        """Обновляет рекомендации AI для всех активов"""
        try:
            logger.info("Начато обновление рекомендаций AI")
            update_id = self.repository.log_data_update("ai_recommendations", "started")
            
            # Получаем все активы
            assets = self.repository.get_all_assets()
            total = len(assets)
            success_count = 0
            
            for i, asset in enumerate(assets):
                ticker = asset['ticker']
                try:
                    logger.info(f"Обработка рекомендации AI {i+1}/{total}: {ticker}")
                    
                    # Получаем метрики для тикера
                    metrics = self.repository.get_latest_metrics(ticker)
                    
                    if metrics:
                        # Получаем рекомендацию AI
                        ai_data = self.ai_reasoner.get_recommendation(ticker, force_refresh=True)
                        
                        if ai_data and 'recommendation' in ai_data:
                            # Сохраняем рекомендацию
                            self.repository.save_ai_recommendation(
                                ticker=ticker,
                                recommendation=ai_data.get('recommendation'),
                                reasoning=ai_data.get('reasoning', ''),
                                score=ai_data.get('score')
                            )
                            success_count += 1
                
                except Exception as e:
                    logger.error(f"Ошибка при получении рекомендации AI для {ticker}: {str(e)}")
                    logger.debug(traceback.format_exc())
            
            logger.info(f"Обновление рекомендаций AI завершено. Успешно обработано {success_count}/{total} активов")
            self.repository.log_data_update(
                "ai_recommendations", 
                "completed", 
                f"Processed {success_count}/{total} assets"
            )
        
        except Exception as e:
            logger.error(f"Ошибка при обновлении рекомендаций AI: {str(e)}")
            logger.debug(traceback.format_exc())
            self.repository.log_data_update(
                "ai_recommendations", 
                "failed", 
                f"Error: {str(e)}"
            )
    
    def update_scoring(self):
        """Обновляет результаты скоринга"""
        try:
            logger.info("Начато обновление результатов скоринга")
            update_id = self.repository.log_data_update("scoring", "started")
            
            # Получаем результаты скоринга
            scoring_results = self.scoring_engine.run_scoring(force=True)
            
            if scoring_results and 'success' in scoring_results and scoring_results['success']:
                # Сохраняем результаты скоринга
                self.repository.save_scoring_result("scoring", scoring_results)
                logger.info(f"Обновление результатов скоринга успешно завершено. Обработано {scoring_results.get('count', 0)} активов")
                self.repository.log_data_update(
                    "scoring", 
                    "completed", 
                    f"Processed {scoring_results.get('count', 0)} assets"
                )
            else:
                logger.error(f"Ошибка при получении результатов скоринга: {scoring_results.get('error', 'Unknown error')}")
                self.repository.log_data_update(
                    "scoring", 
                    "failed", 
                    f"Error: {scoring_results.get('error', 'Unknown error')}"
                )
        
        except Exception as e:
            logger.error(f"Ошибка при обновлении результатов скоринга: {str(e)}")
            logger.debug(traceback.format_exc())
            self.repository.log_data_update(
                "scoring", 
                "failed", 
                f"Error: {str(e)}"
            )
    
    def run_full_update(self):
        """Запускает полный цикл обновления данных"""
        logger.info("Запущен полный цикл обновления данных")
        
        # Обновляем рыночные данные
        self.update_market_data()
        
        # Обновляем рекомендации AI
        self.update_ai_recommendations()
        
        # Обновляем результаты скоринга
        self.update_scoring()
        
        logger.info("Полный цикл обновления данных завершен")
    
    def run_schedule(self):
        """Запускает планировщик в режиме расписания"""
        while self.running:
            schedule.run_pending()
            time.sleep(1)
    
    def start(self):
        """Запускает планировщик"""
        if self.running:
            logger.warning("Планировщик уже запущен")
            return
        
        self.running = True
        
        # Настройка расписания - каждое воскресенье в 2 часа ночи
        schedule.every().sunday.at("02:00").do(self.run_full_update)
        
        # Запускаем планировщик в отдельном потоке
        self.thread = threading.Thread(target=self.run_schedule, daemon=True)
        self.thread.start()
        
        logger.info("Планировщик запущен")
    
    def stop(self):
        """Останавливает планировщик"""
        if not self.running:
            logger.warning("Планировщик не запущен")
            return
        
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        
        logger.info("Планировщик остановлен")
    
    def run_once(self):
        """Запускает однократное обновление данных"""
        self.run_full_update()

if __name__ == "__main__":
    # Получаем аргументы командной строки
    import argparse
    
    parser = argparse.ArgumentParser(description="Управление планировщиком обновления данных")
    parser.add_argument('--action', choices=['start', 'once'], default='once',
                        help='Действие: start - запустить планировщик, once - разовое обновление')
    
    args = parser.parse_args()
    
    scheduler = DataUpdateScheduler()
    
    if args.action == 'start':
        scheduler.start()
        # Поддерживаем планировщик активным
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            scheduler.stop()
    else:
        scheduler.run_once() 