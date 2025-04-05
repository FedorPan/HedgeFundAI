"use client"

import React from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { formatNumber, formatPercentage } from "@/lib/utils"

interface PortfolioPosition {
  ticker: string;
  currentWeight: number;
  targetWeight: number;
  delta: number;
  side: "long" | "short";
}

// Mock data for portfolio comparison
const mockComparisonData: PortfolioPosition[] = [
  { ticker: "TICK5", currentWeight: 15.0, targetWeight: 12.0, delta: -3.0, side: "long" },
  { ticker: "TICK28", currentWeight: 14.0, targetWeight: 15.0, delta: 1.0, side: "long" },
  { ticker: "TICK42", currentWeight: 13.0, targetWeight: 10.0, delta: -3.0, side: "long" },
  { ticker: "TICK87", currentWeight: 8.0, targetWeight: 8.0, delta: 0.0, side: "long" },
  { ticker: "TICK15", currentWeight: 12.0, targetWeight: 15.0, delta: 3.0, side: "short" },
  { ticker: "TICK76", currentWeight: 9.0, targetWeight: 10.0, delta: 1.0, side: "short" },
  { ticker: "TICK31", currentWeight: 0.0, targetWeight: 15.0, delta: 15.0, side: "long" },
  { ticker: "TICK63", currentWeight: 0.0, targetWeight: 15.0, delta: 15.0, side: "short" },
  { ticker: "TICK99", currentWeight: 29.0, targetWeight: 0.0, delta: -29.0, side: "long" },
];

export default function TargetPortfolioComparison() {
  // Sort by absolute delta value (descending)
  const sortedData = [...mockComparisonData].sort((a, b) => 
    Math.abs(b.delta) - Math.abs(a.delta)
  );
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>Target Portfolio</CardTitle>
        <CardDescription>Compare current with target allocation</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="overflow-auto max-h-[18rem]">
          <table className="w-full border-collapse">
            <thead className="sticky top-0 bg-white">
              <tr className="border-b">
                <th className="px-4 py-2 text-left font-medium text-muted-foreground">Ticker</th>
                <th className="px-4 py-2 text-left font-medium text-muted-foreground">Side</th>
                <th className="px-4 py-2 text-left font-medium text-muted-foreground">Current</th>
                <th className="px-4 py-2 text-left font-medium text-muted-foreground">Target</th>
                <th className="px-4 py-2 text-left font-medium text-muted-foreground">Delta</th>
              </tr>
            </thead>
            <tbody>
              {sortedData.map((position) => (
                <tr key={position.ticker} className="border-b hover:bg-muted/50">
                  <td className="px-4 py-2 font-medium">{position.ticker}</td>
                  <td className={`px-4 py-2 ${position.side === 'long' ? 'text-green-600' : 'text-red-600'}`}>
                    {position.side.toUpperCase()}
                  </td>
                  <td className="px-4 py-2">{formatNumber(position.currentWeight, 1)}%</td>
                  <td className="px-4 py-2">{formatNumber(position.targetWeight, 1)}%</td>
                  <td className={`px-4 py-2 ${position.delta > 0 ? 'text-green-600' : position.delta < 0 ? 'text-red-600' : ''}`}>
                    {position.delta > 0 ? '+' : ''}{formatNumber(position.delta, 1)}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="text-xs text-muted-foreground mt-4">
          * Positive delta means increase position, negative means decrease
        </div>
      </CardContent>
    </Card>
  )
} 