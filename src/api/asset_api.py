#!/usr/bin/env python3
"""
API для доступа к данным, портфелю и аналитике HedgeFundAI.
"""
import os
import sys
import time
import json
import logging
import random
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from fastapi import FastAPI, Query, Path as PathParam, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd

# Fix import paths
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
root_dir = os.path.dirname(parent_dir)
if root_dir not in sys.path:
    sys.path.append(root_dir)

# Try different import paths
try:
    from analysis.ai_reasoner import AIReasoner
    from analysis.scoring_engine import ScoringEngine
    from analysis.run_scoring import main as run_scoring_main
    from data.market_data_service import MarketDataService
    try:
        from trading.portfolio_manager import PortfolioManager
    except ImportError:
        logger.warning("Could not import PortfolioManager. Trading functionality will be limited.")
        PortfolioManager = None
except ImportError:
    try:
        from src.analysis.ai_reasoner import AIReasoner
        from src.analysis.scoring_engine import ScoringEngine
        from src.analysis.run_scoring import main as run_scoring_main
        from src.data.market_data_service import MarketDataService
        try:
            from src.trading.portfolio_manager import PortfolioManager
        except ImportError:
            logger.warning("Could not import PortfolioManager. Trading functionality will be limited.")
            PortfolioManager = None
    except ImportError:
        logging.error("Cannot import required modules. Check your PYTHONPATH.")
        sys.exit(1)

# Загрузка переменных окружения, если есть .env файл
from dotenv import load_dotenv
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Пути к директориям и файлам
ROOT_DIR = Path(__file__).parent.parent  # src/
DATA_DIR = ROOT_DIR / "data"
REASONING_DIR = DATA_DIR / "reasoning"
OUTPUT_DIR = DATA_DIR / "output"

# Создаем директории, если они не существуют
REASONING_DIR.mkdir(exist_ok=True, parents=True)
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

class AssetAPI:
    """API для работы с активами и рекомендациями ИИ."""
    
    def __init__(self):
        """Инициализация API."""
        # Создаем экземпляры необходимых компонентов
        self._initialize_data_services()
        
        # Инициализация FastAPI
        self.app = FastAPI(
            title="HedgeFundAI Asset API",
            description="API для работы с активами и рекомендациями ИИ",
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
        
        logger.info("AssetAPI инициализирован")
    
    def _initialize_data_services(self):
        """Инициализирует сервисы данных и анализа"""
        # Инициализация сервиса рыночных данных с API ключом из переменной окружения
        finnhub_api_key = os.environ.get('FINNHUB_API_KEY')
        if not finnhub_api_key:
            logger.warning("FINNHUB_API_KEY not found in environment variables. Using cached data only.")
        
        self.market_data = MarketDataService(cache_dir='.cache', api_keys={'finnhub': finnhub_api_key})
        
        # Получение SP500 тикеров (исключая топ-50)
        self.tickers = self.market_data.get_sp500_tickers(start_rank=51, end_rank=500)
        
        # Инициализация AI Reasoner с API ключом из переменной окружения
        openai_api_key = os.environ.get('OPENAI_API_KEY')
        if not openai_api_key:
            logger.warning("OPENAI_API_KEY not found in environment variables. AI reasoning will be limited.")
        
        self.ai_reasoner = AIReasoner(reasoning_dir='src/data/reasoning', api_key=openai_api_key)
        
        # Инициализация Scoring Engine
        self.scoring_engine = ScoringEngine()
        
    def _setup_routes(self):
        """Регистрирует все маршруты API."""
        
        # Основные эндпоинты
        @self.app.get("/", tags=["Info"])
        async def root():
            """Базовый эндпоинт для проверки статуса API."""
            return {
                "status": "online",
                "api": "HedgeFundAI Asset API",
                "version": "1.0.0",
                "timestamp": time.time()
            }
        
        @self.app.get("/health", tags=["Info"])
        async def health_check():
            """Проверка работоспособности API и подключенных компонентов."""
            components = {
                "ai_reasoner": self.ai_reasoner is not None,
                "scoring_engine": self.scoring_engine is not None,
                "data_directory": DATA_DIR.exists(),
                "reasoning_directory": REASONING_DIR.exists(),
                "output_directory": OUTPUT_DIR.exists()
            }
            
            all_healthy = all(components.values())
            
            return {
                "status": "healthy" if all_healthy else "degraded",
                "components": components,
                "timestamp": time.time()
            }
        
        @self.app.get("/universe/stocks", tags=["Assets"])
        async def get_asset_universe():
            """Получение списка активов с метриками и рекомендациями."""
            try:
                # Список тикеров для анализа
                tickers = self.tickers[:100]  # Берем первые 100 тикеров для производительности
                logger.info(f"Getting data for {len(tickers)} tickers")
                
                # Приоритет отдаем данным из Finnhub API
                assets = []
                
                # Подготовка для кэшированных рекомендаций ИИ
                ai_recommendations = self.ai_reasoner.get_all_cached_reasoning()
                
                # Проверяем наличие CSV файла с метриками как резервный источник данных
                metrics_file = DATA_DIR / "sample_metrics.csv"
                df = None
                if metrics_file.exists():
                    df = pd.read_csv(metrics_file)
                
                # Получаем данные для каждого тикера
                for i, ticker in enumerate(tickers[:20]):  # Limit to 20 tickers for faster response
                    if i % 5 == 0:
                        logger.info(f"Processing ticker {i+1}/{min(len(tickers), 20)}: {ticker}")
                    
                    # Получаем рекомендацию ИИ для тикера (если есть)
                    recommendation = None
                    sentiment = None
                    if ticker in ai_recommendations:
                        ai_data = ai_recommendations[ticker]
                        recommendation = ai_data.get('recommendation', 'Hold')
                        
                        # Определяем сентимент на основе рекомендации
                        if recommendation == 'BUY':
                            sentiment = 'bullish'
                        elif recommendation == 'SELL':
                            sentiment = 'bearish'
                        else:
                            sentiment = 'neutral'
                    
                    # Инициализируем объект актива
                    asset = {
                        'ticker': ticker,
                        'name': f"{ticker}",  # Будет заменено на реальное название, если доступно
                        'sentiment': sentiment or 'neutral',
                        'recommendation': recommendation or 'Hold',
                        'aiRecommendation': recommendation,
                        'inPortfolio': False,
                        'inTarget': False,
                    }
                    
                    # Получение данных из API Finnhub
                    try:
                        if self.market_data and self.market_data.finnhub_client:
                            # Получаем данные тикера из API
                            ticker_data = self.market_data.get_ticker_data(ticker)
                            
                            if ticker_data and not ticker_data.get('no_data', False):
                                # Дополняем основной объект фундаментальными метриками
                                fundamental = ticker_data.get('fundamental', {})
                                for key, value in fundamental.items():
                                    if key == 'name' and value:
                                        asset['name'] = value
                                        asset['companyName'] = value
                                
                                # Технические метрики
                                technical = ticker_data.get('technical', {})
                                if technical:
                                    asset['price'] = technical.get('latest_price')
                                    asset['change'] = technical.get('day_change')
                                    asset['changePercent'] = technical.get('day_change_percent')
                                    asset['momentum3m'] = technical.get('momentum_3m')
                                    asset['volatility3m'] = technical.get('volatility_3m')
                                    asset['priceChangeYtd'] = technical.get('price_change_ytd')
                                    asset['avgVolume10d'] = technical.get('avg_volume_10d')
                                    asset['sector'] = fundamental.get('sector', 'Unknown')
                    except Exception as e:
                        logger.warning(f"Error getting data for {ticker}: {str(e)}")
                    
                    # Если данные из API недоступны, используем CSV как резервный источник
                    if df is not None and ticker in df['ticker'].values:
                        row = df[df['ticker'] == ticker].iloc[0]
                        
                        # Заполняем отсутствующие поля из CSV
                        for col in df.columns:
                            if col in ['ticker']:
                                continue
                                
                            # Преобразовываем имена столбцов в camelCase для фронтенда
                            api_field = self._to_camel_case(col) if not col.startswith('price_vs_') else f"priceVs{col[9:].upper()}"
                            if api_field not in asset or asset[api_field] is None:
                                asset[api_field] = row[col]
                    
                    # Рассчитываем скоры
                    scores = self._calculate_basic_scores(asset)
                    for score_key, score_value in scores.items():
                        asset[score_key] = score_value
                    
                    # Удаляем None значения из объекта, чтобы не перегружать ответ
                    asset = {k: v for k, v in asset.items() if v is not None}
                    
                    assets.append(asset)
                
                return self._create_response(
                    success=True,
                    message="Asset universe retrieved successfully",
                    data=assets
                )
            except Exception as e:
                logger.error(f"Error retrieving asset universe: {str(e)}")
                return self._create_response(
                    success=False,
                    message=f"Error retrieving asset universe: {str(e)}",
                    data=[]
                )
        
        @self.app.get("/ai/reasoning/{ticker}", tags=["AI Analysis"])
        async def get_ticker_reasoning(
            ticker: str,
            refresh: bool = Query(False, description="Force refresh analysis")
        ):
            """Получение обоснования ИИ для тикера."""
            try:
                ticker = ticker.upper()
                
                # Получаем метрики тикера из CSV
                metrics_file = DATA_DIR / "sample_metrics.csv"
                if not metrics_file.exists():
                    return self._create_response(
                        success=False,
                        message="Metrics file not found",
                        data=None
                    )
                
                df = pd.read_csv(metrics_file)
                ticker_row = df[df['ticker'] == ticker]
                
                if ticker_row.empty:
                    return self._create_response(
                        success=False,
                        message=f"Ticker {ticker} not found in metrics data",
                        data=None
                    )
                
                metrics = ticker_row.iloc[0].to_dict()
                
                # Получаем дополнительные метрики, если доступен Finnhub API
                if self.market_data and self.market_data.finnhub_client:
                    try:
                        # Получаем технические метрики
                        technical_metrics = self.market_data.get_technical_metrics(ticker)
                        # Дополняем метрики данными
                        for key, value in technical_metrics.items():
                            metrics[key] = value
                    except Exception as e:
                        logger.warning(f"Error getting technical metrics for {ticker}: {str(e)}")
                    
                    try:
                        # Получаем аналитические метрики
                        analyst_metrics = self.market_data.get_analyst_metrics(ticker)
                        # Дополняем метрики данными
                        for key, value in analyst_metrics.items():
                            metrics[key] = value
                    except Exception as e:
                        logger.warning(f"Error getting analyst metrics for {ticker}: {str(e)}")
                    
                    try:
                        # Получаем фундаментальные метрики
                        fundamental_metrics = self.market_data.get_fundamental_metrics(ticker)
                        # Дополняем метрики данными
                        for key, value in fundamental_metrics.items():
                            metrics[key] = value
                    except Exception as e:
                        logger.warning(f"Error getting fundamental metrics for {ticker}: {str(e)}")
                        
                # Определяем сторону позиции на основе composite_score
                # Если composite_score нет, используем другие метрики
                if 'composite_score' in metrics:
                    side = 'long' if metrics['composite_score'] > 0 else 'short'
                else:
                    # Используем доступные метрики для определения стороны
                    growth_metrics = [
                        metrics.get('eps_growth_12m', 0),
                        metrics.get('revenue_growth_yoy', 0),
                        metrics.get('momentum_3m', 0)
                    ]
                    avg_growth = sum(growth_metrics) / len(growth_metrics) if growth_metrics else 0
                    side = 'long' if avg_growth > 0 else 'short'
                
                # Получаем рекомендацию (с обновлением, если запрошено)
                if refresh:
                    reasoning = self.ai_reasoner.generate_reasoning_for_ticker(
                        ticker=ticker,
                        metrics=metrics,
                        side=side,
                        force_refresh=True
                    )
                else:
                    # Сначала проверяем кэш
                    reasoning = self.ai_reasoner.get_cached_reasoning(ticker)
                    
                    # Если нет в кэше, генерируем
                    if not reasoning:
                        reasoning = self.ai_reasoner.generate_reasoning_for_ticker(
                            ticker=ticker,
                            metrics=metrics,
                            side=side
                        )
                
                if not reasoning:
                    return self._create_response(
                        success=False,
                        message=f"Failed to get AI reasoning for {ticker}",
                        data=None
                    )
                
                return self._create_response(
                    success=True,
                    message=f"AI reasoning for {ticker} retrieved successfully",
                    data=reasoning
                )
            except Exception as e:
                logger.error(f"Error getting AI reasoning for {ticker}: {str(e)}")
                return self._create_response(
                    success=False,
                    message=f"Error getting AI reasoning: {str(e)}",
                    data=None
                )
        
        @self.app.post("/scoring/run", tags=["Scoring"])
        async def run_scoring(
            force: bool = Query(False, description="Force run even if already running")
        ):
            """Запуск процесса скоринга."""
            try:
                # В асинхронной среде запуск длительных процессов должен быть в отдельном потоке
                # Для простоты демонстрации запускаем напрямую
                run_scoring_main()
                
                return self._create_response(
                    success=True,
                    message="Scoring process started",
                    data={"status": "running"}
                )
            except Exception as e:
                logger.error(f"Error starting scoring process: {str(e)}")
                return self._create_response(
                    success=False,
                    message=f"Error starting scoring process: {str(e)}",
                    data=None
                )
        
        @self.app.get("/scoring/results", tags=["Scoring"])
        async def get_scoring_results():
            """Получение результатов скоринга."""
            try:
                # Читаем результаты из JSON файла
                results_file = OUTPUT_DIR / "long_short_selection.json"
                if not results_file.exists():
                    return self._create_response(
                        success=False,
                        message="Scoring results not found",
                        data=None
                    )
                
                with open(results_file, 'r') as f:
                    results = json.load(f)
                
                return self._create_response(
                    success=True,
                    message="Scoring results retrieved successfully",
                    data=results
                )
            except Exception as e:
                logger.error(f"Error getting scoring results: {str(e)}")
                return self._create_response(
                    success=False,
                    message=f"Error getting scoring results: {str(e)}",
                    data=None
                )
        
        @self.app.get("/analysis/scores", tags=["Analysis"])
        async def get_analysis_scores(
            force: bool = Query(False, description="Запустить обновление скоринга для всех тикеров")
        ):
            """Получение результатов анализа и скоринга с синхронизацией обоих систем (AI и скоринг)."""
            try:
                # Если запрошено принудительное обновление, запускаем скоринг
                if force:
                    logger.info("Запуск принудительного обновления скоринга")
                    run_scoring_main()
                
                # Получаем кэшированные рекомендации ИИ
                ai_recommendations = self.ai_reasoner.get_all_cached_reasoning()
                
                # Загружаем результаты скоринга
                scores_file = DATA_DIR / "output" / "scoring_results.csv"
                if not scores_file.exists():
                    return self._create_response(
                        success=False,
                        message="Scoring results not found",
                        data=None
                    )
                
                # Читаем данные скоринга
                scores_df = pd.read_csv(scores_file)
                
                # Читаем selection файл
                selection_file = DATA_DIR / "output" / "long_short_selection.json"
                if selection_file.exists():
                    with open(selection_file, 'r') as f:
                        selection = json.load(f)
                else:
                    selection = {"long": [], "short": []}
                
                # Добавляем рекомендации ИИ к данным скоринга
                scores_df['ai_recommendation'] = None
                for ticker in scores_df['ticker']:
                    if ticker in ai_recommendations:
                        scores_df.loc[scores_df['ticker'] == ticker, 'ai_recommendation'] = ai_recommendations[ticker].get('recommendation', 'HOLD')
                
                # Фильтрация согласованных рекомендаций
                # Long позиции: composite_score > 0 и ai_recommendation = BUY
                # Short позиции: composite_score < 0 и ai_recommendation = SELL
                consistent_long = scores_df[(scores_df['composite_score'] > 0) & 
                                           (scores_df['ai_recommendation'] == 'BUY')]
                
                consistent_short = scores_df[(scores_df['composite_score'] < 0) & 
                                            (scores_df['ai_recommendation'] == 'SELL')]
                
                # Сортируем согласованные рекомендации
                if not consistent_long.empty:
                    consistent_long = consistent_long.sort_values('composite_score', ascending=False)
                
                if not consistent_short.empty:
                    consistent_short = consistent_short.sort_values('composite_score', ascending=True)
                
                # Создаем согласованные списки
                consistent_selection = {
                    "long": consistent_long['ticker'].tolist()[:10] if not consistent_long.empty else [],
                    "short": consistent_short['ticker'].tolist()[:10] if not consistent_short.empty else []
                }
                
                # Преобразуем данные для ответа
                data = {
                    "all_scores": scores_df.to_dict(orient='records'),
                    "original_selection": selection,
                    "consistent_selection": consistent_selection
                }
                
                return self._create_response(
                    success=True,
                    message="Analysis scores retrieved successfully",
                    data=data
                )
            except Exception as e:
                logger.error(f"Error getting analysis scores: {str(e)}")
                return self._create_response(
                    success=False,
                    message=f"Error getting analysis scores: {str(e)}",
                    data=None
                )
    
    def _create_response(self, success: bool, message: str, data: Any = None) -> Dict:
        """Создает стандартный ответ API."""
        return {
            "success": success,
            "message": message,
            "data": data,
            "timestamp": time.time()
        }
    
    def _calculate_basic_scores(self, asset: Dict) -> Dict:
        """Рассчитывает базовые скоры для актива."""
        try:
            scores = {}
            
            # Технические скоры
            if 'momentum3m' in asset and asset['momentum3m'] is not None:
                scores['momentum_score'] = min(max(asset['momentum3m'] / 0.3, -1.0), 1.0)
            else:
                scores['momentum_score'] = 0.0
                
            if 'volatility3m' in asset and asset['volatility3m'] is not None:
                # Низкая волатильность - хорошо, высокая - плохо
                vol_normalized = min(asset['volatility3m'] / 0.5, 1.0)
                scores['volatility_score'] = 1.0 - vol_normalized
            else:
                scores['volatility_score'] = 0.0
            
            # Суммарный скор
            total_score = 0.0
            weights = {
                'momentum_score': 0.7,
                'volatility_score': 0.3
            }
            
            for key, weight in weights.items():
                if key in scores:
                    total_score += scores[key] * weight
            
            scores['total_score'] = total_score
            return scores
        except Exception as e:
            logger.error(f"Error calculating scores: {str(e)}")
            return {
                'momentum_score': 0.0,
                'volatility_score': 0.0,
                'total_score': 0.0
            }
    
    def _to_camel_case(self, snake_str: str) -> str:
        """Преобразует snake_case в camelCase."""
        components = snake_str.split('_')
        return components[0] + ''.join(x.title() for x in components[1:])
    
    def run(self, host: str = "0.0.0.0", port: int = 8000):
        """Запуск API сервера."""
        import uvicorn
        logger.info(f"Starting AssetAPI on {host}:{port}")
        uvicorn.run(self.app, host=host, port=port)


def main():
    """Точка входа для запуска API."""
    api = AssetAPI()
    api.run()


if __name__ == "__main__":
    main() 