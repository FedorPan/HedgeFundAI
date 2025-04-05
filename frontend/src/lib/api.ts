import { Asset } from "@/components/asset-universe-table";

// API URLs for direct backend access (used only if proxy fails)
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002';
// API proxy URL - use the backend API route
const API_PROXY_URL = '/api/backend';

// Типы для API ответов
interface APIResponse<T> {
  success: boolean;
  message: string;
  data: T;
  timestamp: number;
}

// Интерфейсы для данных
export interface PortfolioSummary {
  total_value: number;
  cash_balance: number;
  long_value: number;
  short_value: number;
  daily_pnl: number;
  daily_pnl_percent: number;
  total_pnl: number;
  total_pnl_percent: number;
}

export interface PortfolioPosition {
  ticker: string;
  quantity: number;
  entry_price: number;
  current_price: number;
  market_value: number;
  unrealized_pnl: number;
  unrealized_pnl_percent: number;
  weight: number;
  side: 'long' | 'short';
  status?: 'current' | 'target' | 'exit';
}

export interface PortfolioData {
  summary: PortfolioSummary;
  positions: PortfolioPosition[];
}

export interface Metrics {
  sharpe_ratio: number;
  sortino_ratio: number;
  max_drawdown: number;
  volatility: number;
  beta: number;
  alpha: number;
  win_rate: number;
  long_short_ratio: number;
}

export interface RebalanceHistoryItem {
  id: string;
  timestamp: string;
  type: string;
  added_tickers: string[];
  removed_tickers: string[];
  rebalanced_tickers: string[];
  metrics_before: Metrics;
  metrics_after: Metrics;
}

export interface StockReasoning {
  ticker: string;
  text: string;
  recommendation: 'BUY' | 'SELL' | 'HOLD';
  generated_at: string;
}

/**
 * Получение портфеля
 * @returns Данные портфеля
 */
export async function getPortfolio(): Promise<PortfolioData> {
  try {
    // Try using the direct backend route
    const response = await fetch(`${API_PROXY_URL}/portfolio`);
    const json = await response.json() as APIResponse<PortfolioData>;
    
    if (!json.success) {
      throw new Error(json.message);
    }
    
    return json.data;
  } catch (error) {
    console.error('Error fetching portfolio data:', error);
    // Возвращаем пустые данные при ошибке
    return {
      summary: {
        total_value: 0,
        cash_balance: 0,
        long_value: 0,
        short_value: 0,
        daily_pnl: 0,
        daily_pnl_percent: 0,
        total_pnl: 0,
        total_pnl_percent: 0
      },
      positions: []
    };
  }
}

/**
 * Получение метрик портфеля
 * @returns Метрики портфеля
 */
export async function getPortfolioMetrics(): Promise<Metrics> {
  try {
    const response = await fetch(`${API_PROXY_URL}/portfolio/metrics`);
    const json = await response.json() as APIResponse<Metrics>;
    
    if (!json.success) {
      throw new Error(json.message);
    }
    
    return json.data;
  } catch (error) {
    console.error('Error fetching portfolio metrics:', error);
    // Возвращаем пустые метрики при ошибке
    return {
      sharpe_ratio: 0,
      sortino_ratio: 0,
      max_drawdown: 0,
      volatility: 0,
      beta: 0,
      alpha: 0,
      win_rate: 0,
      long_short_ratio: 0
    };
  }
}

/**
 * Получение истории ребалансировок
 * @returns История ребалансировок
 */
export async function getRebalanceHistory(): Promise<RebalanceHistoryItem[]> {
  try {
    const response = await fetch(`${API_PROXY_URL}/portfolio/rebalances`);
    const json = await response.json() as APIResponse<RebalanceHistoryItem[]>;
    
    if (!json.success) {
      throw new Error(json.message);
    }
    
    return json.data;
  } catch (error) {
    console.error('Error fetching rebalance history:', error);
    return [];
  }
}

/**
 * Получение вселенной активов
 * @returns Список активов
 */
export async function getAssetUniverse(): Promise<Asset[]> {
  try {
    const response = await fetch(`${API_PROXY_URL}/universe/stocks`);
    const json = await response.json() as APIResponse<Asset[]>;
    
    if (!json.success) {
      throw new Error(json.message);
    }
    
    return json.data;
  } catch (error) {
    console.error('Error fetching asset universe:', error);
    return [];
  }
}

/**
 * Получение обоснования ИИ для тикера
 * @param ticker Тикер
 * @param refresh Обновить данные принудительно
 * @returns Обоснование ИИ
 */
export async function getAIReasoning(ticker: string, refresh: boolean = false): Promise<StockReasoning | null> {
  try {
    const response = await fetch(`${API_PROXY_URL}/ai/reasoning/${ticker}?refresh=${refresh}`);
    const json = await response.json() as APIResponse<StockReasoning>;
    
    if (!json.success) {
      throw new Error(json.message);
    }
    
    return json.data;
  } catch (error) {
    console.error(`Error fetching AI reasoning for ${ticker}:`, error);
    return null;
  }
}

/**
 * Запуск ребалансировки портфеля
 * @param longTickers Тикеры для long позиций
 * @param shortTickers Тикеры для short позиций
 * @returns Результат операции
 */
export async function runRebalance(longTickers: string[], shortTickers: string[]): Promise<any> {
  try {
    const response = await fetch(`${API_PROXY_URL}/rebalance`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        long_tickers: longTickers,
        short_tickers: shortTickers
      }),
    });
    
    const json = await response.json() as APIResponse<any>;
    
    if (!json.success) {
      throw new Error(json.message);
    }
    
    return json.data;
  } catch (error) {
    console.error('Error running rebalance:', error);
    return null;
  }
}

/**
 * Запуск скоринга
 * @param force Запустить скоринг принудительно
 * @returns Результат операции
 */
export async function runScoring(force: boolean = false): Promise<any> {
  try {
    const response = await fetch(`${API_PROXY_URL}/scoring/run?force=${force}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    const json = await response.json() as APIResponse<any>;
    
    if (!json.success) {
      throw new Error(json.message);
    }
    
    return json.data;
  } catch (error) {
    console.error('Error running scoring:', error);
    return null;
  }
}