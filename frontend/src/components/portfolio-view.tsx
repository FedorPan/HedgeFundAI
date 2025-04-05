"use client"

import React, { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { formatCurrency, formatNumber, formatPercentage } from "@/lib/utils"
import { ChevronDown, ChevronUp, ArrowRight, RefreshCw } from "lucide-react"

// Используем одинаковые тикеры для текущего и целевого портфеля для лучшего сравнения
const commonTickers = [
  "TICK5", "TICK28", "TICK42", "TICK87", "TICK15", "TICK76", "TICK31", "TICK63"
];

// Общий интерфейс для позиций
interface Position {
  ticker: string;
  side: "long" | "short";
}

// Интерфейс для текущей позиции
interface CurrentPosition extends Position {
  id: number;
  quantity: number;
  entryPrice: number;
  currentPrice: number;
  pnl: number;
  pnlPercent: number;
  value: number;
  weight: number;
  takeProfit: number;
  stopLoss: number;
}

// Интерфейс для целевой позиции
interface TargetPosition extends Position {
  targetWeight: number;
}

// Mock data для текущего портфеля
const mockCurrentPositions: CurrentPosition[] = [
  {
    id: 1,
    ticker: "TICK5",
    quantity: 150,
    entryPrice: 96.50,
    currentPrice: 102.75,
    pnl: 937.5,
    pnlPercent: 6.48,
    value: 15412.5,
    weight: 15.4,
    side: "long",
    takeProfit: 10,
    stopLoss: 5
  },
  {
    id: 2,
    ticker: "TICK28",
    quantity: 300,
    entryPrice: 43.20,
    currentPrice: 47.50,
    pnl: 1290,
    pnlPercent: 9.95,
    value: 14250,
    weight: 14.3,
    side: "long",
    takeProfit: 15,
    stopLoss: 7
  },
  {
    id: 3,
    ticker: "TICK42",
    quantity: 75,
    entryPrice: 187.30,
    currentPrice: 175.20,
    pnl: -907.5,
    pnlPercent: -6.46,
    value: 13140,
    weight: 13.1,
    side: "long",
    takeProfit: 12,
    stopLoss: 10
  },
  {
    id: 4,
    ticker: "TICK87",
    quantity: 120,
    entryPrice: 63.40,
    currentPrice: 68.90,
    pnl: 660,
    pnlPercent: 8.67,
    value: 8268,
    weight: 8.3,
    side: "long",
    takeProfit: 12,
    stopLoss: 8
  },
  {
    id: 5,
    ticker: "TICK15",
    quantity: -100,
    entryPrice: 129.80,
    currentPrice: 118.50,
    pnl: 1130,
    pnlPercent: 8.70,
    value: 11850,
    weight: 11.9,
    side: "short",
    takeProfit: 15,
    stopLoss: 8
  },
  {
    id: 6,
    ticker: "TICK76",
    quantity: -200,
    entryPrice: 42.30,
    currentPrice: 45.80,
    pnl: -700,
    pnlPercent: -8.27,
    value: 9160,
    weight: 9.2,
    side: "short",
    takeProfit: 10,
    stopLoss: 5
  }
];

// Mock data для целевого портфеля (используем те же тикеры для корректного сравнения)
const mockTargetPositions: TargetPosition[] = [
  { ticker: "TICK5", targetWeight: 12.0, side: "long" },
  { ticker: "TICK28", targetWeight: 15.0, side: "long" },
  { ticker: "TICK42", targetWeight: 10.0, side: "long" },
  { ticker: "TICK87", targetWeight: 8.0, side: "long" },
  { ticker: "TICK15", targetWeight: 15.0, side: "short" },
  { ticker: "TICK76", targetWeight: 10.0, side: "short" },
  { ticker: "TICK31", targetWeight: 15.0, side: "long" },
  { ticker: "TICK63", targetWeight: 15.0, side: "short" }
];

// Создаем объединенные данные для сравнения
const createCombinedData = () => {
  const result = [];
  
  // Добавляем все текущие позиции
  for (const current of mockCurrentPositions) {
    const target = mockTargetPositions.find(t => t.ticker === current.ticker);
    
    result.push({
      ticker: current.ticker,
      currentSide: current.side,
      targetSide: target?.side || current.side,
      currentWeight: current.weight,
      targetWeight: target?.targetWeight || 0,
      delta: (target?.targetWeight || 0) - current.weight,
      current: current,
      target: target
    });
  }
  
  // Добавляем целевые позиции, которых нет в текущем портфеле
  for (const target of mockTargetPositions) {
    if (!mockCurrentPositions.find(c => c.ticker === target.ticker)) {
      result.push({
        ticker: target.ticker,
        currentSide: null,
        targetSide: target.side,
        currentWeight: 0,
        targetWeight: target.targetWeight,
        delta: target.targetWeight,
        current: null,
        target: target
      });
    }
  }
  
  return result;
};

export default function PortfolioView() {
  const [sortField, setSortField] = useState<string>("ticker");
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("asc");
  const [isRebalancing, setIsRebalancing] = useState(false);
  
  const combinedData = createCombinedData();
  
  // Calculate total portfolio value and PnL
  const totalValue = mockCurrentPositions.reduce((sum, pos) => sum + pos.value, 0);
  const totalPnl = mockCurrentPositions.reduce((sum, pos) => sum + pos.pnl, 0);
  const totalPnlPercent = (totalPnl / (totalValue - totalPnl)) * 100;
  
  // Handle sort
  const handleSort = (field: string) => {
    if (sortField === field) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortDirection("asc");
    }
  };
  
  // Sort data based on sort field and direction
  const sortedData = [...combinedData].sort((a, b) => {
    let aValue = a[sortField];
    let bValue = b[sortField];
    
    // Special case for ticker - always string
    if (sortField === "ticker") {
      aValue = a.ticker;
      bValue = b.ticker;
    }
    
    // Compare values
    if (aValue < bValue) return sortDirection === "asc" ? -1 : 1;
    if (aValue > bValue) return sortDirection === "asc" ? 1 : -1;
    return 0;
  });
  
  // Handle close position
  const handleClosePosition = (id: number) => {
    console.log(`Closing position: ${id}`);
    // In a real app, would call API to close position
  };
  
  // Handle rebalance
  const handleRebalance = () => {
    setIsRebalancing(true);
    // Имитация процесса ребалансировки
    setTimeout(() => {
      setIsRebalancing(false);
      // В реальном приложении здесь был бы вызов API
      console.log("Portfolio rebalanced");
    }, 2000);
  };
  
  // Render sort indicator
  const renderSortIndicator = (field: string) => {
    if (sortField !== field) return null;
    return sortDirection === "asc" ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />;
  };
  
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold">Portfolio Comparison</h2>
        <Button 
          onClick={handleRebalance} 
          disabled={isRebalancing}
          className="flex items-center gap-1"
        >
          <RefreshCw className={`h-4 w-4 ${isRebalancing ? 'animate-spin' : ''}`} />
          <span>Rebalance Portfolio</span>
        </Button>
      </div>
      
      <Card>
        <CardHeader>
          <CardDescription className="flex justify-between">
            <span>Active positions: {mockCurrentPositions.length}</span>
            <span className={totalPnl >= 0 ? "text-green-600 font-medium" : "text-red-600 font-medium"}>
              Total P&L: {formatCurrency(totalPnl)} ({formatNumber(totalPnlPercent, 2)}%)
            </span>
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-auto max-h-[30rem]">
            <table className="w-full border-collapse">
              <thead className="sticky top-0 bg-white">
                <tr className="border-b">
                  <th 
                    className="px-4 py-2 text-left font-medium text-muted-foreground cursor-pointer"
                    onClick={() => handleSort("ticker")}
                  >
                    <div className="flex items-center">
                      Ticker
                      {renderSortIndicator("ticker")}
                    </div>
                  </th>
                  <th 
                    className="px-4 py-2 text-left font-medium text-muted-foreground"
                    colSpan={2}
                  >
                    Side
                  </th>
                  <th 
                    className="px-4 py-2 text-left font-medium text-muted-foreground cursor-pointer"
                    onClick={() => handleSort("currentWeight")}
                  >
                    <div className="flex items-center">
                      Current %
                      {renderSortIndicator("currentWeight")}
                    </div>
                  </th>
                  <th 
                    className="px-4 py-2 text-left font-medium text-muted-foreground cursor-pointer"
                    onClick={() => handleSort("targetWeight")}
                  >
                    <div className="flex items-center">
                      Target %
                      {renderSortIndicator("targetWeight")}
                    </div>
                  </th>
                  <th 
                    className="px-4 py-2 text-left font-medium text-muted-foreground cursor-pointer"
                    onClick={() => handleSort("delta")}
                  >
                    <div className="flex items-center">
                      Delta
                      {renderSortIndicator("delta")}
                    </div>
                  </th>
                  <th 
                    className="px-4 py-2 text-left font-medium text-muted-foreground"
                  >
                    Value
                  </th>
                  <th 
                    className="px-4 py-2 text-left font-medium text-muted-foreground"
                  >
                    P&L
                  </th>
                  <th 
                    className="px-4 py-2 text-left font-medium text-muted-foreground"
                  >
                    Action
                  </th>
                </tr>
              </thead>
              <tbody>
                {sortedData.map((item) => (
                  <tr key={item.ticker} className="border-b hover:bg-muted/50">
                    <td className="px-4 py-2 font-medium">{item.ticker}</td>
                    <td className={`px-2 py-2 ${item.currentSide === 'long' ? 'text-green-600' : item.currentSide === 'short' ? 'text-red-600' : 'text-gray-400'}`}>
                      {item.currentSide ? item.currentSide.toUpperCase() : "-"}
                    </td>
                    <td className="px-0 py-2">
                      {item.currentSide !== item.targetSide && (
                        <div className="flex items-center text-gray-400">
                          <ArrowRight className="h-4 w-4 mx-1" />
                          <span className={item.targetSide === 'long' ? 'text-green-600' : 'text-red-600'}>
                            {item.targetSide.toUpperCase()}
                          </span>
                        </div>
                      )}
                    </td>
                    <td className="px-4 py-2">{formatNumber(item.currentWeight, 1)}%</td>
                    <td className="px-4 py-2">{formatNumber(item.targetWeight, 1)}%</td>
                    <td className={`px-4 py-2 ${item.delta > 0 ? 'text-green-600' : item.delta < 0 ? 'text-red-600' : ''}`}>
                      {item.delta > 0 ? '+' : ''}{formatNumber(item.delta, 1)}%
                    </td>
                    <td className="px-4 py-2">{item.current ? formatCurrency(item.current.value) : "-"}</td>
                    <td className={`px-4 py-2 ${item.current?.pnl >= 0 ? 'text-green-600' : item.current?.pnl < 0 ? 'text-red-600' : ''}`}>
                      {item.current ? formatCurrency(item.current.pnl) : "-"}
                    </td>
                    <td className="px-4 py-2">
                      {item.current && (
                        <Button 
                          variant="outline" 
                          size="sm"
                          className="h-7 px-2 text-xs"
                          onClick={() => handleClosePosition(item.current.id)}
                        >
                          Close
                        </Button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="text-xs text-muted-foreground mt-4 flex justify-between">
            <div>* Positive delta means increase position, negative means decrease</div>
            <div>Total portfolio value: {formatCurrency(totalValue)}</div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
} 