"use client"

import React from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { formatDate, formatNumber } from "@/lib/utils"

interface RebalanceRecord {
  id: number;
  date: string;
  positions: number;
  tickers: string[];
  pnl: number;
  pnlPercent: number;
}

// Mock data for rebalance history
const mockHistory: RebalanceRecord[] = [
  {
    id: 1,
    date: "2025-04-14T10:30:00Z",
    positions: 10,
    tickers: ["TICK5", "TICK28", "TICK42", "TICK87", "TICK15", "TICK76", "TICK31", "TICK63", "TICK99", "TICK12"],
    pnl: 4320,
    pnlPercent: 4.32
  },
  {
    id: 2,
    date: "2025-04-07T11:15:00Z",
    positions: 8,
    tickers: ["TICK5", "TICK28", "TICK42", "TICK87", "TICK15", "TICK76", "TICK31", "TICK63"],
    pnl: 2150,
    pnlPercent: 2.15
  },
  {
    id: 3,
    date: "2025-03-31T09:45:00Z",
    positions: 12,
    tickers: ["TICK5", "TICK28", "TICK42", "TICK87", "TICK15", "TICK76", "TICK31", "TICK63", "TICK99", "TICK12", "TICK38", "TICK54"],
    pnl: -1280,
    pnlPercent: -1.28
  },
  {
    id: 4,
    date: "2025-03-24T14:20:00Z",
    positions: 10,
    tickers: ["TICK5", "TICK28", "TICK42", "TICK87", "TICK15", "TICK76", "TICK31", "TICK63", "TICK99", "TICK12"],
    pnl: 3750,
    pnlPercent: 3.75
  },
  {
    id: 5,
    date: "2025-03-17T10:00:00Z",
    positions: 9,
    tickers: ["TICK5", "TICK28", "TICK42", "TICK87", "TICK15", "TICK76", "TICK31", "TICK63", "TICK99"],
    pnl: 1830,
    pnlPercent: 1.83
  }
];

export default function RebalanceHistory() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Rebalance History</CardTitle>
        <CardDescription>Previous portfolio rebalances</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="overflow-auto">
          <table className="w-full border-collapse">
            <thead className="bg-white">
              <tr className="border-b">
                <th className="px-4 py-2 text-left font-medium text-muted-foreground">Date</th>
                <th className="px-4 py-2 text-left font-medium text-muted-foreground">Positions</th>
                <th className="px-4 py-2 text-left font-medium text-muted-foreground">Tickers</th>
                <th className="px-4 py-2 text-left font-medium text-muted-foreground">P&L</th>
              </tr>
            </thead>
            <tbody>
              {mockHistory.map((record) => (
                <tr key={record.id} className="border-b hover:bg-muted/50">
                  <td className="px-4 py-2 font-medium">{formatDate(new Date(record.date))}</td>
                  <td className="px-4 py-2">{record.positions}</td>
                  <td className="px-4 py-2 max-w-xs truncate">
                    {record.tickers.join(", ")}
                  </td>
                  <td className={`px-4 py-2 ${record.pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {record.pnl >= 0 ? '+' : ''}{formatNumber(record.pnlPercent, 2)}%
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