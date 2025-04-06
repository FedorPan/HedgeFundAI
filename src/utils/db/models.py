import os
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Путь к базе данных
DB_PATH = Path(__file__).parent.parent.parent.parent / "data" / "hedgefund.db"

def ensure_db_path():
    """Убедиться, что директория для БД существует"""
    db_dir = DB_PATH.parent
    if not db_dir.exists():
        db_dir.mkdir(parents=True, exist_ok=True)

class Database:
    """Класс для работы с SQLite базой данных"""
    
    def __init__(self):
        ensure_db_path()
        self.conn = sqlite3.connect(str(DB_PATH))
        # Включаем поддержку словарей в результатах запросов
        self.conn.row_factory = sqlite3.Row
        # Включаем поддержку внешних ключей
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.init_db()
    
    def init_db(self):
        """Инициализирует структуру базы данных"""
        cursor = self.conn.cursor()
        
        # Таблица с активами
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS assets (
            ticker TEXT PRIMARY KEY,
            name TEXT,
            sector TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Таблица с метриками активов
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS asset_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT,
            price REAL,
            change REAL,
            change_percent REAL,
            market_cap REAL,
            pe_ratio REAL,
            eps_growth REAL,
            revenue_growth REAL,
            volatility_3m REAL,
            debt_equity REAL,
            momentum_3m REAL,
            analyst_consensus REAL,
            data_date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ticker) REFERENCES assets(ticker)
        )
        ''')
        
        # Таблица с рекомендациями AI
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT,
            recommendation TEXT, 
            reasoning TEXT,
            score REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ticker) REFERENCES assets(ticker)
        )
        ''')
        
        # Таблица для кэширования результатов скоринга
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS scoring_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            result_type TEXT,
            data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Таблица для отслеживания обновлений данных
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS data_updates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            update_type TEXT,
            status TEXT,
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            details TEXT
        )
        ''')
        
        self.conn.commit()
    
    def close(self):
        """Закрывает соединение с базой данных"""
        if self.conn:
            self.conn.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

class AssetRepository:
    """Репозиторий для работы с активами"""
    
    def __init__(self, db_connection=None):
        self.db = db_connection if db_connection else Database()
        self.own_connection = db_connection is None
    
    def close(self):
        """Закрывает соединение с базой данных, если оно было создано в этом репозитории"""
        if self.own_connection and self.db:
            self.db.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def save_asset(self, ticker: str, name: str = None, sector: str = None):
        """Сохраняет информацию об активе"""
        cursor = self.db.conn.cursor()
        
        # Проверяем, существует ли уже актив с таким тикером
        cursor.execute("SELECT ticker FROM assets WHERE ticker = ?", (ticker,))
        exists = cursor.fetchone()
        
        if exists:
            # Обновляем информацию
            cursor.execute(
                "UPDATE assets SET name = ?, sector = ?, updated_at = CURRENT_TIMESTAMP WHERE ticker = ?",
                (name, sector, ticker)
            )
        else:
            # Создаем новую запись
            cursor.execute(
                "INSERT INTO assets (ticker, name, sector) VALUES (?, ?, ?)",
                (ticker, name, sector)
            )
        
        self.db.conn.commit()
        return ticker
    
    def save_metrics(self, ticker: str, metrics: Dict):
        """Сохраняет метрики актива"""
        cursor = self.db.conn.cursor()
        
        # Убеждаемся, что актив существует
        self.save_asset(ticker)
        
        # Подготавливаем данные
        data_date = datetime.now().date().isoformat()
        
        # Вставляем метрики
        cursor.execute(
            """
            INSERT INTO asset_metrics (
                ticker, price, change, change_percent, market_cap, pe_ratio,
                eps_growth, revenue_growth, volatility_3m, debt_equity,
                momentum_3m, analyst_consensus, data_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ticker, metrics.get('price'), metrics.get('change'),
                metrics.get('change_percent'), metrics.get('market_cap'),
                metrics.get('pe_ratio'), metrics.get('eps_growth'),
                metrics.get('revenue_growth'), metrics.get('volatility_3m'),
                metrics.get('debt_equity'), metrics.get('momentum_3m'),
                metrics.get('analyst_consensus'), data_date
            )
        )
        
        self.db.conn.commit()
    
    def save_ai_recommendation(self, ticker: str, recommendation: str, reasoning: str, score: float = None):
        """Сохраняет рекомендацию AI"""
        cursor = self.db.conn.cursor()
        
        # Убеждаемся, что актив существует
        self.save_asset(ticker)
        
        # Вставляем рекомендацию
        cursor.execute(
            "INSERT INTO ai_recommendations (ticker, recommendation, reasoning, score) VALUES (?, ?, ?, ?)",
            (ticker, recommendation, reasoning, score)
        )
        
        self.db.conn.commit()
    
    def get_latest_metrics(self, ticker: str) -> Optional[Dict]:
        """Получает последние метрики для актива"""
        cursor = self.db.conn.cursor()
        
        cursor.execute(
            """
            SELECT * FROM asset_metrics 
            WHERE ticker = ? 
            ORDER BY created_at DESC 
            LIMIT 1
            """,
            (ticker,)
        )
        
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    
    def get_latest_recommendation(self, ticker: str) -> Optional[Dict]:
        """Получает последнюю рекомендацию AI для актива"""
        cursor = self.db.conn.cursor()
        
        cursor.execute(
            """
            SELECT * FROM ai_recommendations 
            WHERE ticker = ? 
            ORDER BY created_at DESC 
            LIMIT 1
            """,
            (ticker,)
        )
        
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    
    def get_all_assets(self) -> List[Dict]:
        """Получает список всех активов"""
        cursor = self.db.conn.cursor()
        
        cursor.execute("SELECT * FROM assets")
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_asset_universe(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        """
        Получает список активов с последними метриками и рекомендациями
        с поддержкой пагинации
        """
        cursor = self.db.conn.cursor()
        
        cursor.execute(
            """
            SELECT a.ticker, a.name, a.sector, m.price, m.change, m.change_percent,
                   m.market_cap, m.pe_ratio, m.eps_growth, m.revenue_growth,
                   m.volatility_3m, m.debt_equity, m.momentum_3m,
                   r.recommendation, r.score
            FROM assets a
            LEFT JOIN (
                SELECT ticker, MAX(created_at) as max_date
                FROM asset_metrics
                GROUP BY ticker
            ) latest_m ON a.ticker = latest_m.ticker
            LEFT JOIN asset_metrics m ON latest_m.ticker = m.ticker AND latest_m.max_date = m.created_at
            LEFT JOIN (
                SELECT ticker, MAX(created_at) as max_date
                FROM ai_recommendations
                GROUP BY ticker
            ) latest_r ON a.ticker = latest_r.ticker
            LEFT JOIN ai_recommendations r ON latest_r.ticker = r.ticker AND latest_r.max_date = r.created_at
            LIMIT ? OFFSET ?
            """,
            (limit, offset)
        )
        
        return [dict(row) for row in cursor.fetchall()]
    
    def save_scoring_result(self, result_type: str, data: Any):
        """Сохраняет результат скоринга"""
        cursor = self.db.conn.cursor()
        
        # Преобразуем данные в JSON
        json_data = json.dumps(data)
        
        cursor.execute(
            "INSERT INTO scoring_results (result_type, data) VALUES (?, ?)",
            (result_type, json_data)
        )
        
        self.db.conn.commit()
    
    def get_latest_scoring_result(self, result_type: str) -> Optional[Dict]:
        """Получает последний результат скоринга заданного типа"""
        cursor = self.db.conn.cursor()
        
        cursor.execute(
            """
            SELECT * FROM scoring_results 
            WHERE result_type = ? 
            ORDER BY created_at DESC 
            LIMIT 1
            """,
            (result_type,)
        )
        
        row = cursor.fetchone()
        if row:
            result = dict(row)
            # Преобразуем JSON обратно в объект Python
            if 'data' in result and result['data']:
                result['data'] = json.loads(result['data'])
            return result
        return None
    
    def log_data_update(self, update_type: str, status: str = 'started', details: str = None):
        """Логирует начало или завершение обновления данных"""
        cursor = self.db.conn.cursor()
        
        if status == 'started':
            cursor.execute(
                "INSERT INTO data_updates (update_type, status, start_time, details) VALUES (?, ?, CURRENT_TIMESTAMP, ?)",
                (update_type, status, details)
            )
            self.db.conn.commit()
            return cursor.lastrowid
        else:
            # Находим последнюю запись для данного типа обновления со статусом 'started'
            cursor.execute(
                """
                SELECT id FROM data_updates 
                WHERE update_type = ? AND status = 'started' 
                ORDER BY start_time DESC 
                LIMIT 1
                """,
                (update_type,)
            )
            
            row = cursor.fetchone()
            if row:
                update_id = row[0]
                
                cursor.execute(
                    "UPDATE data_updates SET status = ?, end_time = CURRENT_TIMESTAMP, details = ? WHERE id = ?",
                    (status, details, update_id)
                )
                self.db.conn.commit()
                return update_id
            
            return None
    
    def get_last_update_time(self, update_type: str) -> Optional[datetime]:
        """Получает время последнего успешного обновления данных заданного типа"""
        cursor = self.db.conn.cursor()
        
        cursor.execute(
            """
            SELECT end_time FROM data_updates 
            WHERE update_type = ? AND status = 'completed' 
            ORDER BY end_time DESC 
            LIMIT 1
            """,
            (update_type,)
        )
        
        row = cursor.fetchone()
        if row and row[0]:
            # Преобразуем строку в datetime
            return datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S')
        return None

# Создаем экземпляр для проверки и инициализации базы данных
if __name__ == "__main__":
    with Database() as db:
        print(f"База данных инициализирована по пути: {DB_PATH}") 