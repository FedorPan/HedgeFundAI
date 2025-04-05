#!/usr/bin/env python3
"""
Скрипт для запуска API-сервера HedgeFundAI.
"""
import os
import logging
from pathlib import Path
import argparse
import time
import multiprocessing

# Fix the import to use relative or absolute path
try:
    from asset_api import AssetAPI  # Try local import first
except ImportError:
    try:
        from src.api.asset_api import AssetAPI  # Try absolute import
    except ImportError:
        import sys
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        from src.api.asset_api import AssetAPI

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_args():
    """Обработка аргументов командной строки."""
    parser = argparse.ArgumentParser(description='Запуск API-сервера HedgeFundAI')
    
    parser.add_argument('--host', default='0.0.0.0', help='Хост для запуска сервера (по умолчанию 0.0.0.0)')
    parser.add_argument('--port', type=int, default=8000, help='Порт для запуска сервера (по умолчанию 8000)')
    
    return parser.parse_args()

def run_asset_api(host, port):
    """Запуск AssetAPI."""
    try:
        api = AssetAPI()
        api.run(host=host, port=port)
    except Exception as e:
        logger.error(f"Error running AssetAPI: {e}")
        raise

def main():
    """Основная функция для запуска API-сервера."""
    # Обработка аргументов командной строки
    args = parse_args()
    
    # Вывод информации о настройках среды
    logger.info(f"Starting HedgeFundAI API server")
    logger.info(f"Host: {args.host}, Port: {args.port}")
    
    # Запуск API в отдельном процессе
    api_process = multiprocessing.Process(target=run_asset_api, args=(args.host, args.port))
    api_process.start()
    
    logger.info(f"API server started on http://{args.host}:{args.port}")
    
    try:
        # Ожидаем завершения процесса
        api_process.join()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
        api_process.terminate()
        api_process.join()

if __name__ == "__main__":
    main() 