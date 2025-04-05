"use client"

import React from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { formatCurrency, formatPercentage, formatNumber } from "@/lib/utils"

interface MetricsOverviewProps {
  metrics?: {
    portfolioBalance: number
    ytdReturn: number
    sharpeRatio: number
    lastRebalance: string
  }
}

// Значения по умолчанию для демонстрации
const defaultMetrics = {
  portfolioBalance: 1000000,
  ytdReturn: 12.5,
  sharpeRatio: 1.8,
  lastRebalance: "14 Apr 2025"
}

export default function MetricsOverview({ metrics = defaultMetrics }: MetricsOverviewProps) {
  return (
    <div className="grid gap-4 md:grid-cols-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Portfolio Balance</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{formatCurrency(metrics.portfolioBalance)}</div>
          <p className="text-xs text-muted-foreground">Current total value</p>
        </CardContent>
      </Card>
      
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">YTD Return</CardTitle>
        </CardHeader>
        <CardContent>
          <div className={`text-2xl font-bold ${metrics.ytdReturn >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {metrics.ytdReturn >= 0 ? '+' : ''}{formatNumber(metrics.ytdReturn, 1)}%
          </div>
          <p className="text-xs text-muted-foreground">Year to date performance</p>
        </CardContent>
      </Card>
      
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Sharpe Ratio</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{formatNumber(metrics.sharpeRatio, 2)}</div>
          <p className="text-xs text-muted-foreground">Risk-adjusted return</p>
        </CardContent>
      </Card>
      
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Last Rebalance</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{metrics.lastRebalance}</div>
          <p className="text-xs text-muted-foreground">Date of previous rebalance</p>
        </CardContent>
      </Card>
    </div>
  )
} 