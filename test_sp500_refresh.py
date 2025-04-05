#!/usr/bin/env python
import os
import json
import time
from pathlib import Path
from dotenv import load_dotenv
from src.data.market_data_service import MarketDataService

# Загрузка переменных окружения из .env файла
load_dotenv()

# Удаляем кэш S&P500
cache_dir = Path(".cache")
sp500_cache_file = cache_dir / "sp500_201_300.json"
if sp500_cache_file.exists():
    print(f"Удаление кэша списка S&P500 ({sp500_cache_file})...")
    sp500_cache_file.unlink()
    print("Кэш успешно удален.\n")

# Создание сервиса
service = MarketDataService(cache_dir=cache_dir)

# Получение списка тикеров S&P500 (позиции 201-300)
print("Получение списка тикеров S&P500 (позиции 201-300)...")
start_time = time.time()
tickers = service.get_sp500_tickers(start_rank=201, end_rank=300)
elapsed = time.time() - start_time
print(f"Список получен за {elapsed:.2f} секунд.")
print(f"Получено {len(tickers)} тикеров.")
print(f"Первые 10 тикеров: {', '.join(tickers[:10])}")
print(f"Последние 10 тикеров: {', '.join(tickers[-10:])}")

# Проверяем, что кэш создан
if sp500_cache_file.exists():
    cache_size = sp500_cache_file.stat().st_size / 1024
    print(f"\nКэш создан: {sp500_cache_file} ({cache_size:.2f} КБ)")
    
    # Чтение из кэша
    print("\nПовторное получение списка тикеров (должно быть из кэша)...")
    start_time = time.time()
    cached_tickers = service.get_sp500_tickers(start_rank=201, end_rank=300)
    elapsed = time.time() - start_time
    print(f"Список получен из кэша за {elapsed:.4f} секунд.")
    
    # Проверка идентичности списков
    print(f"Списки идентичны: {tickers == cached_tickers}")
else:
    print("\nОшибка: кэш не был создан.")