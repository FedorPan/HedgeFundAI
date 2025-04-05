"use client"

import React from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { formatCurrency, formatNumber, formatPercentage } from "@/lib/utils"

interface Position {
  id: number;
  ticker: string;
  quantity: number;
  entryPrice: number;
  currentPrice: number;
  pnl: number;
  pnlPercent: number;
  value: number;
  side: "long" | "short";
  takeProfit: number;
  stopLoss: number;
}

// Mock data for current portfolio
const mockPositions: Position[] = [
  {
    id: 1,
    ticker: "TICK5",
    quantity: 150,
    entryPrice: 96.50,
    currentPrice: 102.75,
    pnl: 937.5,
    pnlPercent: 6.48,
    value: 15412.5,
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
    side: "short",
    takeProfit: 10,
    stopLoss: 5
  }
];

export default function CurrentPortfolio() {
  const handleClosePosition = (id: number) => {
    console.log(`Closing position: ${id}`);
    // In a real app, would call API to close position
  };
  
  // Calculate total portfolio value and PnL
  const totalValue = mockPositions.reduce((sum, pos) => sum + pos.value, 0);
  const totalPnl = mockPositions.reduce((sum, pos) => sum + pos.pnl, 0);
  const totalPnlPercent = (totalPnl / (totalValue - totalPnl)) * 100;
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>Current Portfolio</CardTitle>
        <CardDescription className="flex justify-between">
          <span>Active positions: {mockPositions.length}</span>
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
                <th className="px-4 py-2 text-left font-medium text-muted-foreground">Ticker</th>
                <th className="px-4 py-2 text-left font-medium text-muted-foreground">Side</th>
                <th className="px-4 py-2 text-left font-medium text-muted-foreground">Qty</th>
                <th className="px-4 py-2 text-left font-medium text-muted-foreground">Entry</th>
                <th className="px-4 py-2 text-left font-medium text-muted-foreground">Current</th>
                <th className="px-4 py-2 text-left font-medium text-muted-foreground">P&L</th>
                <th className="px-4 py-2 text-left font-medium text-muted-foreground">Value</th>
                <th className="px-4 py-2 text-left font-medium text-muted-foreground">TP%</th>
                <th className="px-4 py-2 text-left font-medium text-muted-foreground">SL%</th>
                <th className="px-4 py-2 text-left font-medium text-muted-foreground">Action</th>
              </tr>
            </thead>
            <tbody>
              {mockPositions.map((position) => (
                <tr key={position.id} className="border-b hover:bg-muted/50">
                  <td className="px-4 py-2 font-medium">{position.ticker}</td>
                  <td className={`px-4 py-2 ${position.side === 'long' ? 'text-green-600' : 'text-red-600'}`}>
                    {position.side.toUpperCase()}
                  </td>
                  <td className="px-4 py-2">{position.quantity}</td>
                  <td className="px-4 py-2">${formatNumber(position.entryPrice, 2)}</td>
                  <td className="px-4 py-2">${formatNumber(position.currentPrice, 2)}</td>
                  <td className={`px-4 py-2 ${position.pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    ${formatNumber(position.pnl, 2)} ({formatNumber(position.pnlPercent, 2)}%)
                  </td>
                  <td className="px-4 py-2">${formatNumber(position.value, 2)}</td>
                  <td className="px-4 py-2 text-green-600">+{position.takeProfit}%</td>
                  <td className="px-4 py-2 text-red-600">-{position.stopLoss}%</td>
                  <td className="px-4 py-2">
                    <Button 
                      variant="outline" 
                      size="sm"
                      className="h-7 px-2 text-xs"
                      onClick={() => handleClosePosition(position.id)}
                    >
                      Close
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  )
} 