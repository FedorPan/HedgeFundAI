import os
import json
from pathlib import Path
from dotenv import load_dotenv
from src.analysis.ai_reasoner import AIReasoner

# Загружаем переменные окружения
load_dotenv()

def test_ai_reasoner_single():
    """Тестирование генерации reasoning для одного тикера"""
    # Тестовые данные для одного тикера
    ticker = "AAPL"
    metrics = {
        "ticker": ticker,
        "pe_ratio": 28.5,
        "eps_growth_12m": 15.2,
        "revenue_growth_yoy": 8.1,
        "peg_ratio": 1.5,
        "roe": 28.5,
        "momentum_3m": 12.3,
        "volatility_3m": 18.4,
        "avg_volume_10d": 85000000,
        "debt_equity": 1.2,
        "sentiment_score": 0.75,
        "market_cap": 2800000000000,
        "rank": 1,
        "composite_score": 0.85
    }
    
    # Проверка наличия API ключа
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        print("API ключ OpenAI не найден в переменных окружения. Тест не может быть выполнен.")
        return False
    
    # Инициализируем AIReasoner
    reasoner = AIReasoner(reasoning_dir='test_output/reasoning', api_key=api_key)
    
    print(f"Генерация обоснования для тикера {ticker}...")
    
    # Создаем директорию для выходных данных, если она не существует
    Path('test_output/reasoning').mkdir(exist_ok=True, parents=True)
    
    # Генерируем обоснование
    reasoning = reasoner.generate_reasoning_for_ticker(ticker, metrics, side="long", force_refresh=True)
    
    if reasoning:
        print(f"Обоснование успешно сгенерировано ({len(reasoning)} символов)")
        print("\nНачало обоснования:")
        print("---")
        print(reasoning[:300] + "..." if len(reasoning) > 300 else reasoning)
        print("---")
        
        # Проверяем наличие файла
        reasoning_file = Path(f"test_output/reasoning/{ticker}.md")
        if reasoning_file.exists():
            print(f"Файл успешно сохранен: {reasoning_file}")
            return True
        else:
            print(f"Ошибка: файл {reasoning_file} не был создан")
    else:
        print("Ошибка: обоснование не было сгенерировано")
    
    return False

def main():
    """Основная функция для тестирования"""
    print("=== Тестирование AIReasoner ===")
    
    # Тест генерации обоснования для одного тикера
    success = test_ai_reasoner_single()
    
    # Итог тестирования
    if success:
        print("\nТест успешно пройден!")
    else:
        print("\nТест не пройден.")

if __name__ == "__main__":
    main() 