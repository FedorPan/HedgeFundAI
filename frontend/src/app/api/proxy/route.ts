import { NextRequest, NextResponse } from 'next/server';

const API_URL = "https://hedgefund-ai-lwmjr.ondigitalocean.app";

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const endpoint = searchParams.get("endpoint");
  
  if (!endpoint) {
    return NextResponse.json({ error: "Missing endpoint parameter" }, { status: 400 });
  }
  
  try {
    console.log(`Proxying GET request to ${API_URL}/${endpoint}`);
    const response = await fetch(`${API_URL}/${endpoint}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });
    
    if (!response.ok) {
      console.error(`API error: ${response.status} ${response.statusText}`);
      
      // Get error details
      let errorMessage;
      try {
        const errorData = await response.json();
        errorMessage = errorData.message || `API error: ${response.status}`;
      } catch (e) {
        errorMessage = `API error: ${response.status}`;
      }
      
      // Return a more descriptive error for debugging
      return NextResponse.json(
        {
          success: false, 
          message: errorMessage,
          status: response.status,
          statusText: response.statusText,
          data: []
        }, 
        { status: 500 }
      );
    }
    
    const data = await response.json();
    console.log("API response received successfully");
    
    return NextResponse.json(data);
  } catch (error) {
    console.error("Proxy error:", error);
    
    // Generate mock data as fallback
    const mockData = generateMockData(endpoint);
    
    return NextResponse.json({
      success: true,
      message: "Using mock data (API unavailable)",
      data: mockData
    });
  }
}

export async function POST(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const endpoint = searchParams.get("endpoint");
  
  if (!endpoint) {
    return NextResponse.json({ error: "Missing endpoint parameter" }, { status: 400 });
  }
  
  try {
    const bodyData = await request.json();
    console.log(`Proxying POST request to ${API_URL}/${endpoint}`);
    
    const response = await fetch(`${API_URL}/${endpoint}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(bodyData),
    });
    
    if (!response.ok) {
      console.error(`API error: ${response.status} ${response.statusText}`);
      return NextResponse.json(
        { 
          success: false, 
          message: `API error: ${response.status}`,
          status: response.status,
          statusText: response.statusText
        }, 
        { status: 500 }
      );
    }
    
    const data = await response.json();
    console.log("API response received successfully");
    
    return NextResponse.json(data);
  } catch (error) {
    console.error("Proxy error:", error);
    return NextResponse.json(
      { 
        success: false, 
        message: "Error connecting to API",
        error: String(error)
      }, 
      { status: 500 }
    );
  }
}

// Helper function to generate mock data for fallback
function generateMockData(endpoint: string) {
  if (endpoint === "universe/stocks") {
    // Generate stock data
    return Array.from({ length: 50 }, (_, i) => ({
      ticker: `MOCK${i+1}`,
      name: `Mock Corp ${i+1}`,
      score: Math.floor(Math.random() * 100) - 50,
      value_score: Math.floor(Math.random() * 100) - 50,
      growth_score: Math.floor(Math.random() * 100) - 50,
      risk_score: Math.floor(Math.random() * 100) - 50,
      analyst_score: Math.floor(Math.random() * 100) - 50,
      momentum_score: Math.floor(Math.random() * 100) - 50,
      sentiment: ["bullish", "bearish", "neutral"][Math.floor(Math.random() * 3)],
      sector: ["Technology", "Healthcare", "Financial"][Math.floor(Math.random() * 3)],
      price: Math.random() * 500 + 10,
      change: Math.random() * 10 - 5,
      changePercent: Math.random() * 10 - 5,
      change1w: Math.random() * 20 - 10,
      changePercent1w: Math.random() * 20 - 10,
      change1m: Math.random() * 30 - 15,
      changePercent1m: Math.random() * 30 - 15,
      marketCap: Math.random() * 1000000000000,
      recommendation: ["BUY", "SELL", "HOLD"][Math.floor(Math.random() * 3)],
      peRatio: Math.random() * 30 + 10,
      epsGrowth: Math.random() * 30 - 10,
      revenueGrowth: Math.random() * 20 - 5,
      volatility3m: Math.random() * 2 + 0.5,
      debtEquity: Math.random() * 2,
      inPortfolio: Math.random() > 0.8,
      inTarget: Math.random() > 0.8,
    }));
  }
  
  return [];
} 