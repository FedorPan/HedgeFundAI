"use client"

import React from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { formatCurrency, formatNumber, formatPercentage } from "@/lib/utils"
import { CalendarIcon, CheckCircle, XCircle, AlertCircle } from "lucide-react"

// Define the Rebalance interface
interface RebalanceRecord {
  id: number
  date: string
  timestamp: number
  status: "completed" | "partial" | "failed"
  ordersPlaced: number
  ordersFilled: number
  portfolioValue: number
  portfolioChange: number
  portfolioChangePercent: number
  notes: string | null
}

// Mock data for rebalance history
const mockHistory: RebalanceRecord[] = [
  {
    id: 1,
    date: "14 Apr 2025",
    timestamp: 1744276800000,
    status: "completed",
    ordersPlaced: 18,
    ordersFilled: 18,
    portfolioValue: 1125000,
    portfolioChange: 15000,
    portfolioChangePercent: 1.35,
    notes: null
  },
  {
    id: 2,
    date: "31 Mar 2025",
    timestamp: 1743672000000,
    status: "completed",
    ordersPlaced: 22,
    ordersFilled: 22,
    portfolioValue: 1110000,
    portfolioChange: 45000,
    portfolioChangePercent: 4.22,
    notes: null
  },
  {
    id: 3,
    date: "15 Mar 2025",
    timestamp: 1742203200000,
    status: "partial",
    ordersPlaced: 16,
    ordersFilled: 12,
    portfolioValue: 1065000,
    portfolioChange: -8000,
    portfolioChangePercent: -0.74,
    notes: "Market volatility prevented execution of 4 orders"
  },
  {
    id: 4,
    date: "28 Feb 2025",
    timestamp: 1740388800000,
    status: "completed",
    ordersPlaced: 14,
    ordersFilled: 14,
    portfolioValue: 1073000,
    portfolioChange: 22500,
    portfolioChangePercent: 2.14,
    notes: null
  },
  {
    id: 5,
    date: "15 Feb 2025",
    timestamp: 1739030400000,
    status: "failed",
    ordersPlaced: 20,
    ordersFilled: 0,
    portfolioValue: 1050500,
    portfolioChange: 0,
    portfolioChangePercent: 0,
    notes: "System failure during rebalance attempt, no orders executed"
  },
  {
    id: 6,
    date: "31 Jan 2025",
    timestamp: 1737561600000,
    status: "completed",
    ordersPlaced: 24,
    ordersFilled: 24,
    portfolioValue: 1050500,
    portfolioChange: 38200,
    portfolioChangePercent: 3.77,
    notes: null
  },
  {
    id: 7,
    date: "15 Jan 2025",
    timestamp: 1736102400000,
    status: "completed",
    ordersPlaced: 18,
    ordersFilled: 18,
    portfolioValue: 1012300,
    portfolioChange: 12300,
    portfolioChangePercent: 1.23,
    notes: null
  }
];

// Status icon mapper
const StatusIcon = ({ status }: { status: RebalanceRecord["status"] }) => {
  switch (status) {
    case "completed":
      return <CheckCircle className="h-5 w-5 text-green-500" />;
    case "partial":
      return <AlertCircle className="h-5 w-5 text-yellow-500" />;
    case "failed":
      return <XCircle className="h-5 w-5 text-red-500" />;
    default:
      return null;
  }
};

export default function RebalanceHistoryTable() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Rebalance History</CardTitle>
        <CardDescription>Previous portfolio rebalancing operations</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="overflow-auto max-h-[30rem]">
          <table className="w-full border-collapse">
            <thead className="sticky top-0 bg-white">
              <tr className="border-b">
                <th className="px-4 py-2 text-left font-medium text-muted-foreground">Date</th>
                <th className="px-4 py-2 text-center font-medium text-muted-foreground">Status</th>
                <th className="px-4 py-2 text-center font-medium text-muted-foreground">Orders</th>
                <th className="px-4 py-2 text-right font-medium text-muted-foreground">Portfolio Value</th>
                <th className="px-4 py-2 text-right font-medium text-muted-foreground">Change</th>
                <th className="px-4 py-2 text-left font-medium text-muted-foreground">Notes</th>
              </tr>
            </thead>
            <tbody>
              {mockHistory.map((record) => (
                <tr key={record.id} className="border-b hover:bg-muted/50">
                  <td className="px-4 py-3">
                    <div className="flex items-center">
                      <CalendarIcon className="h-4 w-4 mr-2 text-muted-foreground" />
                      <span className="font-medium">{record.date}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <div className="flex items-center justify-center">
                      <StatusIcon status={record.status} />
                      <span className="ml-1.5 capitalize">{record.status}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-center">
                    {record.ordersFilled} / {record.ordersPlaced}
                  </td>
                  <td className="px-4 py-3 text-right font-medium">
                    {formatCurrency(record.portfolioValue)}
                  </td>
                  <td className={`px-4 py-3 text-right ${record.portfolioChange >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {record.portfolioChange === 0 ? '-' : (
                      <>
                        {record.portfolioChange >= 0 ? '+' : ''}
                        {formatCurrency(record.portfolioChange)} 
                        ({record.portfolioChange >= 0 ? '+' : ''}
                        {formatNumber(record.portfolioChangePercent, 2)}%)
                      </>
                    )}
                  </td>
                  <td className="px-4 py-3 text-sm text-muted-foreground">
                    {record.notes || "-"}
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