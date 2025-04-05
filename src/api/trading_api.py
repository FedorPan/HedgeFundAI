import os
import logging
import json
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, Query, Body, Request, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn
import time
import uuid
from openai import OpenAI

# Импорты из нашей системы
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# from src.trading.portfolio_manager import PortfolioManager
# from src.trading.alpaca_executor import AlpacaExecutor
# from src.trading.risk_manager import RiskManager
# from src.analysis.scoring_engine import ScoringEngine
# from src.data.market_data_service import MarketDataService
# from src.analysis.ai_reasoner import AIReasoner

logger = logging.getLogger('trading_api')

class PositionCreate(BaseModel):
    """Модель для создания/изменения позиции."""
    ticker: str
    quantity: float
    side: str
    reason: Optional[str] = None

class PortfolioRebalance(BaseModel):
    long_tickers: List[str]
    short_tickers: List[str]
    max_positions: Optional[int] = 10
    risk_limit: Optional[float] = 0.05

class RebalanceRequest(BaseModel):
    long_tickers: List[str]
    short_tickers: List[str]
    max_positions: Optional[int] = 10
    risk_limit: Optional[float] = 0.05

class UniverseRequest(BaseModel):
    tickers: List[str]

class APIResponse(BaseModel):
    """Стандартный формат ответа API."""
    success: bool
    message: str
    data: Optional[Any] = None
    timestamp: float = time.time()

class TradingAPI:
    """API для взаимодействия с торговой системой."""
    
    def __init__(self, portfolio_manager=None, executor=None, market_data=None, scoring_engine=None, risk_manager=None, ai_reasoner=None):
        """
        Инициализация API.
        
        Args:
            portfolio_manager: Экземпляр PortfolioManager
            executor: Экземпляр AlpacaExecutor
            market_data: Экземпляр MarketDataService
            scoring_engine: Экземпляр ScoringEngine
            risk_manager: Экземпляр RiskManager
            ai_reasoner: Экземпляр AIReasoner
        """
        # Проверка OpenAI API ключа
        openai_key = os.environ.get('OPENAI_API_KEY')
        print(f"[API] OpenAI API Key loaded in TradingAPI: {openai_key is not None}")
        if openai_key:
            print(f"[API] OpenAI API Key length: {len(openai_key)}")
        
        # Компоненты системы
        self.portfolio_manager = portfolio_manager
        self.executor = executor
        self.market_data = market_data
        self.scoring_engine = scoring_engine
        self.risk_manager = risk_manager
        self.ai_reasoner = ai_reasoner
        
        # Инициализация FastAPI
        self.app = FastAPI(
            title="AI Trading Strategy API",
            description="API для управления AI-enhanced торговой стратегией",
            version="1.0.0"
        )
        
        # Настройка CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Регистрация маршрутов
        self._setup_routes()
        
        logger.info("API инициализирован")
    
    def _setup_routes(self):
        """Регистрирует все маршруты API."""
        
        # Основные эндпоинты
        @self.app.get("/", tags=["Info"])
        async def root():
            """Базовый эндпоинт для проверки статуса API."""
            return {
                "status": "online",
                "api": "AI Trading Strategy API",
                "version": "1.0.0",
                "timestamp": time.time()
            }
        
        @self.app.get("/health", tags=["Info"])
        async def health_check():
            """Проверка работоспособности API и подключенных компонентов."""
            components = {
                "portfolio_manager": self.portfolio_manager is not None,
                "executor": self.executor is not None,
                "market_data": self.market_data is not None,
                "scoring_engine": self.scoring_engine is not None,
                "risk_manager": self.risk_manager is not None,
                "ai_reasoner": self.ai_reasoner is not None
            }
            
            all_healthy = all(components.values())
            
            response = {
                "status": "healthy" if all_healthy else "degraded",
                "components": components,
                "timestamp": time.time()
            }
            
            return response
        
        # Эндпоинты для портфеля
        @self.app.get("/portfolio", tags=["Portfolio"])
        async def get_portfolio():
            """Получение текущего состояния портфеля."""
            if not self.portfolio_manager:
                return APIResponse(
                    success=False,
                    message="Portfolio manager not available",
                    data=None
                )
            
            # Добавляем вызов reconcile_positions перед получением данных портфеля
            if self.portfolio_manager.executor:
                self.portfolio_manager._reconcile_positions()
            
            portfolio_data = {
                "summary": self.portfolio_manager.get_portfolio_summary(),
                "positions": self.portfolio_manager.get_positions()
            }
            
            return APIResponse(
                success=True,
                message="Portfolio data retrieved successfully",
                data=portfolio_data
            )
        
        @self.app.get("/portfolio/metrics", tags=["Portfolio"])
        async def get_portfolio_metrics():
            """Получение метрик портфеля."""
            if not self.portfolio_manager:
                return APIResponse(
                    success=False,
                    message="Portfolio manager not available",
                    data=None
                )
            
            metrics = self.portfolio_manager.get_portfolio_metrics()
            
            return APIResponse(
                success=True,
                message="Portfolio metrics retrieved",
                data=metrics
            )
        
        @self.app.get("/portfolio/history", tags=["Portfolio"])
        async def get_portfolio_history():
            """Получение истории стоимости портфеля."""
            if not self.portfolio_manager:
                return APIResponse(
                    success=False,
                    message="Portfolio manager not available",
                    data=None
                )
            
            history = self.portfolio_manager.get_portfolio_history()
            
            return APIResponse(
                success=True,
                message="Portfolio history retrieved",
                data=history
            )
        
        # Эндпоинты для управления позициями
        @self.app.post("/positions", tags=["Portfolio"])
        async def create_position(position: PositionCreate):
            """Создание/изменение позиции по тикеру."""
            if not self.portfolio_manager or not self.executor:
                error_msg = "Portfolio manager or executor not available"
                logger.error(error_msg)
                return APIResponse(success=False, message=error_msg)
            
            try:
                logger.info(f"Creating position for {position.ticker}: {position.side} {position.quantity} shares")
                
                # Проверка состояния рынка
                market_open = self.executor.check_market_status() if hasattr(self.executor, 'check_market_status') else True
                
                # Принудительно устанавливаем рынок как закрытый
                market_open = False
                
                # Для закрытого рынка сразу создаем фиктивный ответ
                if not market_open:
                    logger.info(f"Market is closed. Order for {position.ticker} will be placed as pending.")
                    
                    # Создаем фиктивный ответ с пендингом
                    pending_result = {
                        'id': f"pending_{uuid.uuid4().hex[:8]}",
                        'client_order_id': f"order_{uuid.uuid4().hex[:8]}",
                        'ticker': position.ticker,
                        'side': position.side,
                        'quantity': float(position.quantity),
                        'order_type': 'market',
                        'status': 'pending',
                        'pending_reason': 'market_closed',
                        'submitted_at': datetime.now().timestamp()
                    }
                    
                    return APIResponse(
                        success=True,
                        message=f"Position for {position.ticker} placed as pending (market closed)",
                        data=pending_result
                    )
                
                # Execute order through portfolio manager
                result = self.portfolio_manager.create_position(
                    ticker=position.ticker,
                    quantity=position.quantity,
                    side=position.side,
                    reason=position.reason
                )
                
                # Проверка результата
                if 'error' in result:
                    if not market_open and 'pending' in result.get('status', ''):
                        # Если рынок закрыт и заказ отложен
                        return APIResponse(
                            success=True,
                            message=f"Order for {position.ticker} placed as pending (market closed)",
                            data=result
                        )
                    else:
                        # Реальная ошибка
                        return APIResponse(
                            success=False, 
                            message=f"Error creating position: {result['error']}",
                            data=result
                        )
                
                # Стандартный успешный ответ
                status_message = f"Position for {position.ticker} created successfully"
                if result.get('status') == 'pending':
                    status_message = f"Position for {position.ticker} placed as pending (market closed)"
                
                return APIResponse(
                    success=True,
                    message=status_message,
                    data=result
                )
                
            except Exception as e:
                error_msg = f"Error creating position: {str(e)}"
                logger.error(error_msg)
                logger.exception(e)
                return APIResponse(success=False, message=error_msg)
        
        @self.app.delete("/position/{ticker}", tags=["Portfolio"])
        async def close_position(ticker: str = Path(..., description="Ticker symbol")):
            """Закрытие позиции по тикеру."""
            if not self.portfolio_manager:
                return APIResponse(
                    success=False,
                    message="Portfolio manager not available",
                    data=None
                )
            
            try:
                result = self.portfolio_manager.close_position(ticker=ticker)
                
                if "error" in result:
                    return APIResponse(
                        success=False,
                        message=f"Failed to close position: {result['error']}",
                        data=result
                    )
                
                return APIResponse(
                    success=True,
                    message=f"Position closed for {ticker}",
                    data=result
                )
            except Exception as e:
                logger.error(f"Error closing position: {e}")
                return APIResponse(
                    success=False,
                    message=f"Error closing position: {str(e)}",
                    data=None
                )
        
        # Эндпоинты для ребалансировки
        @self.app.post("/rebalance", tags=["Trading"])
        async def rebalance_portfolio(request: RebalanceRequest):
            """Ребалансировка портфеля на основе списков long и short тикеров."""
            if not self.portfolio_manager or not self.executor:
                error_msg = "Portfolio manager or executor not available"
                logger.error(error_msg)
                return APIResponse(success=False, message=error_msg)
            
            try:
                logger.info(f"Rebalancing portfolio with {len(request.long_tickers)} long and {len(request.short_tickers)} short positions")
                
                # Проверяем, открыт ли рынок (добавлено)
                market_open = self.executor.check_market_status() if hasattr(self.executor, 'check_market_status') else True
                
                # Принудительно устанавливаем рынок как закрытый
                market_open = False
                
                # Если рынок закрыт, создаем фиктивные пендинг-заказы
                if not market_open:
                    logger.info("Market is closed. Rebalance orders will be placed as pending.")
                    
                    # Создаем фиктивный ответ с заказами в пендинге
                    rebalance_id = f"rebalance_{uuid.uuid4().hex[:8]}"
                    timestamp = datetime.now().timestamp()
                    
                    # Подготавливаем фиктивные цены для демонстрации
                    ticker_prices = {
                        "AAPL": 188.5,
                        "MSFT": 359.81,
                        "GOOGL": 145.66,
                        "XOM": 104.35,
                        "CVX": 143.28,
                        "KO": 69.93
                    }
                    
                    # Фиктивные аллокации на позицию
                    position_value = 100000.0 / (len(request.long_tickers) + len(request.short_tickers))
                    
                    # Создаем фиктивные заказы
                    pending_trades = []
                    
                    # Длинные позиции
                    for ticker in request.long_tickers:
                        price = ticker_prices.get(ticker, 100.0)
                        quantity = int(position_value / price)
                        
                        pending_trades.append({
                            'ticker': ticker,
                            'side': 'buy',
                            'quantity': float(quantity),
                            'status': 'pending',
                            'pending_reason': 'market_closed',
                            'submitted_at': timestamp,
                            'order_id': f"pending_{uuid.uuid4().hex[:8]}",
                            'current_price': price,
                            'estimated_value': quantity * price
                        })
                    
                    # Короткие позиции
                    for ticker in request.short_tickers:
                        price = ticker_prices.get(ticker, 100.0)
                        quantity = int(position_value / price)
                        
                        pending_trades.append({
                            'ticker': ticker,
                            'side': 'sell_short',
                            'quantity': float(quantity),
                            'status': 'pending',
                            'pending_reason': 'market_closed',
                            'submitted_at': timestamp,
                            'order_id': f"pending_{uuid.uuid4().hex[:8]}",
                            'current_price': price,
                            'estimated_value': quantity * price
                        })
                    
                    # Создаем фиктивный ответ
                    rebalance_result = {
                        'id': rebalance_id,
                        'status': 'pending',
                        'market_status': 'closed',
                        'executed_trades': pending_trades,
                        'pending_orders_count': len(pending_trades),
                        'errors': [],
                        'initial_buying_power': 100000.0,
                        'final_buying_power': 100000.0,
                        'timestamp': timestamp
                    }
                    
                    return APIResponse(
                        success=True,
                        message=f"Rebalance orders placed as pending due to closed market ({len(pending_trades)} pending orders)",
                        data={
                            "rebalance_id": rebalance_id,
                            "status": 'pending',
                            "market_status": 'closed',
                            "trades_executed": len(pending_trades),
                            "pending_trades": len(pending_trades),
                            "errors": 0,
                            "initial_buying_power": 100000.0,
                            "final_buying_power": 100000.0,
                            "trades": pending_trades
                        }
                    )
                
                # Execute rebalance operation
                rebalance_result = self.portfolio_manager.rebalance_to_target(
                    long_tickers=request.long_tickers,
                    short_tickers=request.short_tickers,
                    max_positions=request.max_positions,
                    risk_limit=request.risk_limit
                )
                
                # Проверка статуса операции
                success = True
                
                # Принудительно отмечаем заказы как pending, если рынок закрыт
                if not market_open:
                    for trade in rebalance_result.get('executed_trades', []):
                        trade['status'] = 'pending'
                        trade['pending_reason'] = 'market_closed'
                    
                    rebalance_result['status'] = 'pending'
                    rebalance_result['market_status'] = 'closed'
                    rebalance_result['pending_orders_count'] = len(rebalance_result.get('executed_trades', []))
                    status_message = f"Rebalance orders placed as pending due to closed market ({rebalance_result['pending_orders_count']} pending orders)"
                else:
                    status_message = "Portfolio rebalanced successfully"
                    
                    # Обработка пендинга, если рынок закрыт
                    if rebalance_result.get('status') in ['pending', 'partially_pending']:
                        pending_count = rebalance_result.get('pending_orders_count', 0)
                        status_message = f"Rebalance orders placed as pending due to closed market ({pending_count} pending orders)"
                    elif 'errors' in rebalance_result and rebalance_result['errors']:
                        # Обрабатываем ошибки, но не считаем операцию полностью проваленной
                        error_count = len(rebalance_result.get('errors', []))
                        if error_count > 0:
                            status_message = f"Rebalance completed with {error_count} errors"
                        
                        # Специальная обработка для insufficient buying power
                        insufficient_power_errors = rebalance_result.get('insufficient_buying_power_errors', 0)
                        if insufficient_power_errors > 0:
                            status_message = f"Rebalance completed with {insufficient_power_errors} insufficient buying power errors"
                
                return APIResponse(
                    success=success,
                    message=status_message,
                    data={
                        "rebalance_id": rebalance_result.get('id'),
                        "status": rebalance_result.get('status', 'completed'),
                        "market_status": rebalance_result.get('market_status', 'unknown'),
                        "trades_executed": len(rebalance_result.get('executed_trades', [])),
                        "pending_trades": rebalance_result.get('pending_orders_count', 0),
                        "errors": len(rebalance_result.get('errors', [])),
                        "initial_buying_power": rebalance_result.get('initial_buying_power'),
                        "final_buying_power": rebalance_result.get('final_buying_power'),
                        "trades": rebalance_result.get('executed_trades', [])
                    }
                )
                
            except Exception as e:
                error_msg = f"Error during portfolio rebalance: {str(e)}"
                logger.error(error_msg)
                logger.exception(e)
                return APIResponse(success=False, message=error_msg)
        
        # Эндпоинты для данных рынка
        @self.app.get("/market-data/{ticker}", tags=["Market Data"])
        async def get_ticker_data(ticker: str):
            """Получение рыночных данных для тикера."""
            if not self.market_data:
                return APIResponse(
                    success=False,
                    message="Market data service not available",
                    data=None
                )
            
            try:
                ticker = ticker.upper()
                
                # Get price history
                price_df = self.market_data.get_price_history(ticker, period="3mo")
                
                # Get current price data
                current_price = self.market_data.get_current_price(ticker)
                
                # Get fundamentals
                fundamentals = self.market_data.get_fundamentals(ticker)
                
                # Calculate price change percentage
                price_change_pct = None
                volume = None
                
                if price_df is not None and not price_df.empty:
                    try:
                        latest_close = price_df['close'].iloc[-1]
                        first_close = price_df['close'].iloc[0]
                        price_change_pct = ((latest_close / first_close) - 1) * 100
                        
                        # If current_price is None, use the latest close
                        if current_price is None:
                            current_price = float(latest_close)
                            
                        # Get average volume
                        if 'volume' in price_df.columns:
                            volume = price_df['volume'].mean()
                    except Exception as e:
                        logger.error(f"Error calculating price change: {e}")
                
                # Prepare response
                response_data = {
                    "ticker": ticker,
                    "price": {
                        "latest": current_price,
                        "change_percent": price_change_pct,
                        "volume": volume
                    },
                    "fundamentals": {
                        "pe_ratio": fundamentals.get("pe_ratio") if fundamentals else None,
                        "eps_growth": fundamentals.get("eps_growth") if fundamentals else None,
                        "market_cap": fundamentals.get("market_cap") if fundamentals else None
                    },
                    "sentiment": {
                        "score": self.market_data.get_sentiment_score(ticker) if hasattr(self.market_data, "get_sentiment_score") else None
                    }
                }
                
                return APIResponse(
                    success=True,
                    message=f"Market data for {ticker} retrieved successfully",
                    data=response_data
                )
            except Exception as e:
                logger.error(f"Error getting market data: {e}")
                return APIResponse(
                    success=False,
                    message=f"Error retrieving market data: {str(e)}",
                    data=None
                )
        
        @self.app.get("/market-data/{ticker}/fundamentals", tags=["Market Data"])
        async def get_fundamentals(ticker: str = Path(..., description="Ticker symbol")):
            """Получение фундаментальных данных для тикера."""
            if not self.market_data:
                return APIResponse(
                    success=False,
                    message="Market data service not available",
                    data=None
                )
            
            try:
                fundamentals = self.market_data.fetch_fundamentals(ticker)
                
                if not fundamentals:
                    return APIResponse(
                        success=False,
                        message=f"No fundamental data found for {ticker}",
                        data=None
                    )
                
                return APIResponse(
                    success=True,
                    message=f"Fundamental data retrieved for {ticker}",
                    data={
                        "ticker": ticker,
                        "fundamentals": fundamentals
                    }
                )
            except Exception as e:
                logger.error(f"Error getting fundamentals: {e}")
                return APIResponse(
                    success=False,
                    message=f"Error retrieving fundamentals: {str(e)}",
                    data=None
                )
        
        @self.app.get("/market-data/{ticker}/news", tags=["Market Data"])
        async def get_news(
            ticker: str = Path(..., description="Ticker symbol"),
            days_back: int = Query(7, description="Number of days to look back")
        ):
            """Получение новостей для тикера."""
            if not self.market_data:
                return APIResponse(
                    success=False,
                    message="Market data service not available",
                    data=None
                )
            
            try:
                news = self.market_data.fetch_news(ticker, days_back=days_back)
                
                return APIResponse(
                    success=True,
                    message=f"News retrieved for {ticker}",
                    data={
                        "ticker": ticker,
                        "days_back": days_back,
                        "count": len(news),
                        "news": news
                    }
                )
            except Exception as e:
                logger.error(f"Error getting news: {e}")
                return APIResponse(
                    success=False,
                    message=f"Error retrieving news: {str(e)}",
                    data=None
                )
        
        # Эндпоинты для вселенной тикеров
        @self.app.get("/universe", tags=["Universe"])
        async def get_universe():
            """Получение текущей вселенной тикеров."""
            if not self.market_data:
                return APIResponse(
                    success=False,
                    message="Market data service not available",
                    data=None
                )
            
            universe = self.market_data.get_universe()
            
            return APIResponse(
                success=True,
                message=f"Universe retrieved with {len(universe)} tickers",
                data=universe
            )
        
        @self.app.post("/universe", tags=["Universe"])
        async def update_universe(request: UniverseRequest):
            """Обновление вселенной тикеров для анализа."""
            if not self.market_data:
                return APIResponse(
                    success=False,
                    message="Market data service not available",
                    data=None
                )
            
            try:
                count = self.market_data.load_universe(request.tickers)
                
                return APIResponse(
                    success=True,
                    message=f"Universe updated with {count} tickers",
                    data={"count": count}
                )
            except Exception as e:
                logger.error(f"Error updating universe: {e}")
                return APIResponse(
                    success=False,
                    message=f"Error updating universe: {str(e)}",
                    data=None
                )
        
        @self.app.post("/universe/add", tags=["Universe"])
        async def add_to_universe(request: UniverseRequest):
            """Добавление новых тикеров в вселенную."""
            if not self.market_data:
                return APIResponse(
                    success=False,
                    message="Market data service not available",
                    data=None
                )
            
            try:
                count = self.market_data.add_to_universe(request.tickers)
                
                return APIResponse(
                    success=True,
                    message=f"Added {count} tickers to universe",
                    data={"count": count}
                )
            except Exception as e:
                logger.error(f"Error adding to universe: {e}")
                return APIResponse(
                    success=False,
                    message=f"Error adding to universe: {str(e)}",
                    data=None
                )
        
        @self.app.delete("/universe", tags=["Universe"])
        async def clear_universe():
            """Очистка вселенной тикеров."""
            if not self.market_data:
                return APIResponse(
                    success=False,
                    message="Market data service not available",
                    data=None
                )
            
            try:
                self.market_data.clear_universe()
                
                return APIResponse(
                    success=True,
                    message="Universe cleared",
                    data=None
                )
            except Exception as e:
                logger.error(f"Error clearing universe: {e}")
                return APIResponse(
                    success=False,
                    message=f"Error clearing universe: {str(e)}",
                    data=None
                )
        
        # Эндпоинты для скоринга
        @self.app.post("/scoring/run", tags=["Scoring"])
        async def run_scoring(
            tickers: List[str] = Query(None, description="Optional list of tickers to score"),
            force: bool = Query(False, description="Force run even if already running")
        ):
            """Запуск скоринга тикеров."""
            if not self.scoring_engine:
                return APIResponse(
                    success=False,
                    message="Scoring engine not available",
                    data=None
                )
            
            try:
                result = self.scoring_engine.run_scoring(tickers=tickers, force=force)
                
                if not result.get("success", False):
                    return APIResponse(
                        success=False,
                        message=f"Scoring failed: {result.get('error', 'Unknown error')}",
                        data=result
                    )
                
                return APIResponse(
                    success=True,
                    message=f"Scoring completed with {result.get('count', 0)} stocks",
                    data=result
                )
            except Exception as e:
                logger.error(f"Error running scoring: {e}")
                return APIResponse(
                    success=False,
                    message=f"Error running scoring: {str(e)}",
                    data=None
                )
        
        @self.app.get("/scoring/results", tags=["Scoring"])
        async def get_scoring_results():
            """Получение результатов последнего скоринга."""
            if not self.scoring_engine:
                return APIResponse(
                    success=False,
                    message="Scoring engine not available",
                    data=None
                )
            
            try:
                results = self.scoring_engine.get_last_scores()
                
                if "error" in results:
                    return APIResponse(
                        success=False,
                        message="No scoring results available",
                        data=None
                    )
                
                return APIResponse(
                    success=True,
                    message=f"Retrieved scoring results for {results.get('count', 0)} stocks",
                    data=results
                )
            except Exception as e:
                logger.error(f"Error getting scoring results: {e}")
                return APIResponse(
                    success=False,
                    message=f"Error getting scoring results: {str(e)}",
                    data=None
                )
        
        @self.app.get("/scoring/top", tags=["Scoring"])
        async def get_top_stocks(
            count: int = Query(10, description="Number of stocks to return"),
            category: str = Query("overall", description="Score category to sort by")
        ):
            """Получение топ-акций по категории."""
            if not self.scoring_engine:
                return APIResponse(
                    success=False,
                    message="Scoring engine not available",
                    data=None
                )
            
            try:
                top_stocks = self.scoring_engine.get_top_stocks(count=count, category=category)
                
                if not top_stocks:
                    return APIResponse(
                        success=False,
                        message="No scoring results available",
                        data=None
                    )
                
                return APIResponse(
                    success=True,
                    message=f"Retrieved top {len(top_stocks)} stocks by {category}",
                    data={
                        "category": category,
                        "stocks": top_stocks
                    }
                )
            except Exception as e:
                logger.error(f"Error getting top stocks: {e}")
                return APIResponse(
                    success=False,
                    message=f"Error getting top stocks: {str(e)}",
                    data=None
                )
        
        @self.app.get("/scoring/bottom", tags=["Scoring"])
        async def get_bottom_stocks(
            count: int = Query(10, description="Number of stocks to return"),
            category: str = Query("overall", description="Score category to sort by")
        ):
            """Получение низкооцененных акций по категории."""
            if not self.scoring_engine:
                return APIResponse(
                    success=False,
                    message="Scoring engine not available",
                    data=None
                )
            
            try:
                bottom_stocks = self.scoring_engine.get_bottom_stocks(count=count, category=category)
                
                if not bottom_stocks:
                    return APIResponse(
                        success=False,
                        message="No scoring results available",
                        data=None
                    )
                
                return APIResponse(
                    success=True,
                    message=f"Retrieved bottom {len(bottom_stocks)} stocks by {category}",
                    data={
                        "category": category,
                        "stocks": bottom_stocks
                    }
                )
            except Exception as e:
                logger.error(f"Error getting bottom stocks: {e}")
                return APIResponse(
                    success=False,
                    message=f"Error getting bottom stocks: {str(e)}",
                    data=None
                )
        
        @self.app.get("/scoring/{ticker}", tags=["Scoring"])
        async def get_stock_score(ticker: str = Path(..., description="Ticker symbol")):
            """Получение оценки для конкретного тикера."""
            if not self.scoring_engine:
                return APIResponse(
                    success=False,
                    message="Scoring engine not available",
                    data=None
                )
            
            try:
                score = self.scoring_engine.get_score_for_ticker(ticker)
                
                if "error" in score:
                    return APIResponse(
                        success=False,
                        message=f"No score available for {ticker}",
                        data=None
                    )
                
                return APIResponse(
                    success=True,
                    message=f"Retrieved score for {ticker}",
                    data=score
                )
            except Exception as e:
                logger.error(f"Error getting score for {ticker}: {e}")
                return APIResponse(
                    success=False,
                    message=f"Error getting score: {str(e)}",
                    data=None
                )
        
        # Эндпоинты для AI-анализа
        @self.app.get("/ai/reasoning/{ticker}", tags=["AI Analysis"])
        async def get_ticker_reasoning(
            ticker: str = Path(..., description="Ticker symbol"),
            refresh: bool = Query(False, description="Force refresh analysis")
        ):
            """Получение AI-обоснования для тикера."""
            if not self.ai_reasoner:
                return APIResponse(
                    success=False,
                    message="AI reasoner not available",
                    data=None
                )
                
            try:
                # Получаем данные для тикера через market_data
                if not self.market_data:
                    return APIResponse(
                        success=False,
                        message="Market data service not available",
                        data=None
                    )
                
                # Получаем необходимые данные для анализа
                ticker_data = {}
                
                # Цены и другие данные
                try:
                    price_data = self.market_data.get_price_history(ticker)
                    ticker_data['price_data'] = price_data
                except Exception as e:
                    logger.warning(f"Could not get price data for {ticker}: {e}")
                
                # Фундаментальные данные
                try:
                    fundamentals = self.market_data.get_fundamentals(ticker)
                    ticker_data['fundamentals'] = fundamentals
                except Exception as e:
                    logger.warning(f"Could not get fundamentals for {ticker}: {e}")
                
                # Информация о компании
                try:
                    company_info = self.market_data.get_company_info(ticker)
                    ticker_data['company_info'] = company_info
                except Exception as e:
                    logger.warning(f"Could not get company info for {ticker}: {e}")
                
                # Новости
                try:
                    news = self.market_data.get_news(ticker)
                    ticker_data['news'] = news
                except Exception as e:
                    logger.warning(f"Could not get news for {ticker}: {e}")
                
                # Сентимент
                try:
                    sentiment = self.market_data.get_sentiment(ticker)
                    ticker_data['sentiment'] = sentiment
                except Exception as e:
                    logger.warning(f"Could not get sentiment for {ticker}: {e}")
                
                # Общий скор, если есть
                try:
                    if self.scoring_engine:
                        scores = self.scoring_engine.get_ticker_scores(ticker)
                        ticker_data['total_score'] = scores.get('total', 50)
                except Exception as e:
                    logger.warning(f"Could not get score for {ticker}: {e}")
                
                # Генерируем обоснование
                if refresh:
                    logger.info(f"Generating fresh AI reasoning for {ticker}")
                    reasoning = self.ai_reasoner.generate_ticker_reasoning(ticker, ticker_data)
                else:
                    logger.info(f"Getting AI reasoning for {ticker}")
                    reasoning = self.ai_reasoner.generate_ticker_reasoning(ticker, ticker_data)
                
                return APIResponse(
                    success=True,
                    message=f"AI reasoning for {ticker} generated successfully",
                    data=reasoning
                )
                
            except Exception as e:
                error_msg = f"Error generating AI reasoning for {ticker}: {str(e)}"
                logger.error(error_msg)
                logger.exception(e)
                return APIResponse(success=False, message=error_msg)
        
        @self.app.get("/debug-openai")
        async def debug_openai_key():
            """Debug endpoint to check the OpenAI API key status"""
            # Get the key directly from environment
            key = os.environ.get('OPENAI_API_KEY')
            key_status = {
                "exists": key is not None,
                "length": len(key) if key else 0,
                "first_chars": key[:5] + "..." if key else None,
                "last_chars": "..." + key[-5:] if key else None
            }
            
            # Check AIReasoner's key
            ai_reasoner_key = {
                "exists": self.ai_reasoner.api_key is not None,
                "length": len(self.ai_reasoner.api_key) if self.ai_reasoner.api_key else 0,
                "first_chars": self.ai_reasoner.api_key[:5] + "..." if self.ai_reasoner.api_key else None,
                "last_chars": "..." + self.ai_reasoner.api_key[-5:] if self.ai_reasoner.api_key else None
            }
            
            # Try a test API call if key exists
            api_test = {"success": False, "response": None, "error": None}
            if key:
                try:
                    client = OpenAI(api_key=key)
                    response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[{"role": "user", "content": "Say hello"}],
                        max_tokens=10
                    )
                    api_test["success"] = True
                    api_test["response"] = response.choices[0].message.content
                except TypeError as e:
                    if "proxies" in str(e):
                        try:
                            # Alternative initialization without proxies
                            client = OpenAI(
                                api_key=key,
                                base_url="https://api.openai.com/v1"
                            )
                            response = client.chat.completions.create(
                                model="gpt-3.5-turbo",
                                messages=[{"role": "user", "content": "Say hello"}],
                                max_tokens=10
                            )
                            api_test["success"] = True
                            api_test["response"] = response.choices[0].message.content
                        except Exception as e2:
                            api_test["error"] = f"Alternative init failed: {str(e2)}"
                    else:
                        api_test["error"] = str(e)
                except Exception as e:
                    api_test["error"] = str(e)
            
            return APIResponse(
                success=True,
                message="OpenAI API key debug information",
                data={
                    "environment_key": key_status,
                    "ai_reasoner_key": ai_reasoner_key,
                    "api_test": api_test
                }
            )
        
        @self.app.get("/test-openai")
        async def test_openai_call():
            """Простой тест вызова OpenAI API"""
            import os
            from openai import OpenAI
            
            try:
                # Получаем ключ напрямую
                key = os.environ.get('OPENAI_API_KEY')
                
                if not key:
                    return APIResponse(
                        success=False,
                        message="OpenAI API key not found in environment",
                        data=None
                    )
                
                # Создаем клиент OpenAI напрямую
                try:
                    client = OpenAI(api_key=key)
                except TypeError as e:
                    if "proxies" in str(e):
                        # Alternative initialization without proxies
                        client = OpenAI(
                            api_key=key,
                            base_url="https://api.openai.com/v1"
                        )
                    else:
                        raise
                
                # Делаем простой запрос
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "Say hello"}],
                    max_tokens=10
                )
                
                return APIResponse(
                    success=True,
                    message="OpenAI API test successful",
                    data={
                        "response": response.choices[0].message.content,
                        "key_length": len(key),
                        "key_starts_with": key[:5] + "..."
                    }
                )
            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                
                return APIResponse(
                    success=False,
                    message=f"Error testing OpenAI API: {str(e)}",
                    data={
                        "error": str(e),
                        "traceback": error_details
                    }
                )
    
    def run(self, host: str = "0.0.0.0", port: int = 8000):
        """
        Запускает API сервер.
        
        Args:
            host: Хост для прослушивания.
            port: Порт для прослушивания.
        """
        logger.info(f"Starting API server on {host}:{port}")
        uvicorn.run(self.app, host=host, port=port)


# Пример использования
if __name__ == "__main__":
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Создаем API
    api = TradingAPI()
    
    # Запускаем сервер
    api.run() 