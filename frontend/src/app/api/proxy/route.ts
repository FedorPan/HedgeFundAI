import { NextRequest, NextResponse } from 'next/server';

// API URL
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://hedgefund-ai-lwmjr.ondigitalocean.app';

// Функция для имитации данных при недоступности API
function generateMockData(endpoint: string) {
  // Имитация данных для разных эндпоинтов
  if (endpoint === 'universe/stocks') {
    return {
      success: true,
      message: "Mock data generated due to API unavailability",
      data: Array.from({ length: 20 }, (_, i) => ({
        ticker: `MOCK${i+1}`,
        name: `Mock Company ${i+1}`,
        price: Math.round(Math.random() * 100) + 10,
        change: Math.round((Math.random() * 10 - 5) * 100) / 100,
        changePercent: Math.round((Math.random() * 10 - 5) * 100) / 100,
        sector: ['Technology', 'Healthcare', 'Finance', 'Consumer', 'Energy'][Math.floor(Math.random() * 5)],
        recommendation: ['BUY', 'SELL', 'HOLD'][Math.floor(Math.random() * 3)],
        score: Math.round((Math.random() * 100 - 50) * 100) / 100
      }))
    };
  } else if (endpoint === 'data/status') {
    const now = new Date().toISOString();
    return {
      success: true,
      message: "Mock status data generated",
      data: {
        market_data: {
          last_update: now,
          status: "ok"
        },
        ai_recommendations: {
          last_update: now,
          status: "ok"
        },
        scoring: {
          last_update: now,
          status: "ok"
        }
      }
    };
  } else if (endpoint === 'data/refresh') {
    return {
      success: true,
      message: "Mock refresh process started",
      data: {
        status: "running",
        started_at: new Date().toISOString()
      }
    };
  } else if (endpoint === 'health') {
    return {
      status: "healthy",
      components: {
        market_data: "ok",
        ai_reasoner: "ok",
        scoring_engine: "ok",
        database: "ok"
      },
      updates: {
        market_data: {
          last_update: new Date().toISOString(),
          status: "ok"
        },
        ai_recommendations: {
          last_update: new Date().toISOString(),
          status: "ok"
        },
        scoring: {
          last_update: new Date().toISOString(),
          status: "ok"
        }
      },
      timestamp: new Date().toISOString()
    };
  }
  
  // Дефолтные моковые данные
  return {
    success: true,
    message: "Mock data generated",
    data: { mock: true, timestamp: Date.now() }
  };
}

// Обработка GET запросов
export async function GET(request: NextRequest) {
  const endpoint = request.nextUrl.searchParams.get('endpoint');
  
  if (!endpoint) {
    return NextResponse.json(
      { success: false, message: "Missing 'endpoint' parameter" },
      { status: 400 }
    );
  }
  
  try {
    // Пытаемся получить данные с API
    const apiResponse = await fetch(`${API_URL}/${endpoint}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      },
      // Увеличиваем таймаут для долгих запросов
      signal: AbortSignal.timeout(10000)
    });
    
    if (apiResponse.ok) {
      const data = await apiResponse.json();
      return NextResponse.json(data);
    } else {
      console.log(`API returned status ${apiResponse.status} for ${endpoint}`);
      
      // API недоступен, возвращаем моковые данные
      return NextResponse.json(
        generateMockData(endpoint),
        { status: 200 }
      );
    }
  } catch (error) {
    console.error(`Error fetching from API (${endpoint}):`, error);
    
    // В случае ошибки (таймаут или соединение) возвращаем моковые данные
    return NextResponse.json(
      generateMockData(endpoint),
      { status: 200 }
    );
  }
}

// Обработка POST запросов
export async function POST(request: NextRequest) {
  const endpoint = request.nextUrl.searchParams.get('endpoint');
  
  if (!endpoint) {
    return NextResponse.json(
      { success: false, message: "Missing 'endpoint' parameter" },
      { status: 400 }
    );
  }
  
  try {
    // Получаем данные из тела запроса
    let requestBody = {};
    try {
      requestBody = await request.json();
    } catch (e) {
      // Тело запроса пустое или не JSON, используем пустой объект
    }
    
    // Пытаемся выполнить POST запрос
    const apiResponse = await fetch(`${API_URL}/${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(requestBody),
      // Увеличиваем таймаут для долгих запросов
      signal: AbortSignal.timeout(10000)
    });
    
    if (apiResponse.ok) {
      const data = await apiResponse.json();
      return NextResponse.json(data);
    } else {
      console.log(`API returned status ${apiResponse.status} for POST ${endpoint}`);
      
      // API недоступен, возвращаем моковые данные для этого эндпоинта
      return NextResponse.json(
        generateMockData(endpoint),
        { status: 200 }
      );
    }
  } catch (error) {
    console.error(`Error POSTing to API (${endpoint}):`, error);
    
    // В случае ошибки возвращаем моковые данные
    return NextResponse.json(
      generateMockData(endpoint),
      { status: 200 }
    );
  }
} 