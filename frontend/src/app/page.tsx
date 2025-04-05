"use client"

import React from 'react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import MetricsOverview from '@/components/metrics-overview'
import AssetUniverseTable from '@/components/asset-universe-table'
import PortfolioView from '@/components/portfolio-view'
import RebalanceHistoryTable from '@/components/rebalance-history-table'

export default function DashboardPage() {
  return (
    <div className="container max-w-7xl py-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">HedgeFundAI Dashboard</h1>
          <p className="text-muted-foreground">
            Advanced trading strategies powered by AI
          </p>
        </div>
      </div>

      <MetricsOverview />

      <Tabs defaultValue="assets" className="space-y-4">
        <TabsList>
          <TabsTrigger value="assets">Asset Universe</TabsTrigger>
          <TabsTrigger value="portfolio">Portfolio</TabsTrigger>
          <TabsTrigger value="history">Rebalance History</TabsTrigger>
        </TabsList>
        
        <TabsContent value="assets" className="space-y-4">
          <AssetUniverseTable />
        </TabsContent>
        
        <TabsContent value="portfolio" className="space-y-4">
          <PortfolioView />
        </TabsContent>
        
        <TabsContent value="history" className="space-y-4">
          <RebalanceHistoryTable />
        </TabsContent>
      </Tabs>
    </div>
  )
}