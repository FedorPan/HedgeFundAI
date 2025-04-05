import React from 'react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogClose,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { X } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

interface Asset {
  id: string
  symbol: string
  companyName: string
  sector: string
  industry: string
  marketCap: number
  price: number
  change: number
  changePercent: number
  change1w: number
  changePercent1w: number 
  change1m: number
  changePercent1m: number
  volume: number
  peRatio?: number
  pegRatio?: number
  roe?: number
  epsGrowth?: number
  revenueGrowth?: number
  momentum3m?: number
  volatility3m?: number
  debtEquity?: number
  recommendation: string
  sentiment: string
  consensusScore: number
  analystRatingTrend?: string // Changed from number to string
  
  // Additional metrics
  priceToBook?: number
  priceToSales?: number
  forwardPE?: number
  dividendYield?: number
  evToEbitda?: number
  
  // Technical indicators
  sma50?: number
  sma200?: number
  priceVsSma50?: number
  priceVsSma200?: number
  rsi?: number
  avgVolume10d?: number
  priceChangeYtd?: number
  
  // Price targets
  targetHigh?: number
  targetLow?: number
  targetMean?: number
  targetMedian?: number
  priceToTarget?: number
  targetLastUpdated?: string
  
  // Analyst recommendation details
  analystCount?: number
  strongBuy?: number
  buy?: number
  hold?: number
  sell?: number
  strongSell?: number
  
  // EPS metrics
  epsActual?: number
  epsEstimate?: number
  epsSurprisePercent?: number
  earningsBeatRate?: number
}

interface AssetDetailDialogProps {
  asset: Asset | null
  open: boolean
  onOpenChange: (open: boolean) => void
}

const formatCurrency = (value: number | undefined): string => {
  if (value === undefined) return 'N/A'
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value)
}

const formatNumber = (value: number | undefined, decimals: number = 2): string => {
  if (value === undefined) return 'N/A'
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value)
}

const formatPercentage = (value: number | undefined, decimals: number = 2): string => {
  if (value === undefined) return 'N/A'
  return `${value >= 0 ? '+' : ''}${formatNumber(value, decimals)}%`
}

const formatMarketCap = (value: number): string => {
  if (value >= 1000000000000) {
    return `$${(value / 1000000000000).toFixed(2)}T`
  } else if (value >= 1000000000) {
    return `$${(value / 1000000000).toFixed(2)}B`
  } else if (value >= 1000000) {
    return `$${(value / 1000000).toFixed(2)}M`
  }
  return formatCurrency(value)
}

export function AssetDetailDialog({ asset, open, onOpenChange }: AssetDetailDialogProps) {
  if (!asset) return null

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-xl flex items-center gap-2">
            <span className="font-semibold">{asset.symbol}</span>
            <span className="text-muted-foreground">{asset.companyName}</span>
          </DialogTitle>
          <DialogDescription className="text-sm text-muted-foreground">
            {asset.sector} · {asset.industry}
          </DialogDescription>
          <button
            onClick={() => onOpenChange(false)}
            className="absolute right-4 top-4 rounded-sm opacity-70 ring-offset-background transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
          >
            <X className="h-4 w-4" />
            <span className="sr-only">Close</span>
          </button>
        </DialogHeader>
        
        <Tabs defaultValue="overview" className="mt-4">
          <TabsList className="mb-4">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="fundamentals">Fundamentals</TabsTrigger>
            <TabsTrigger value="technicals">Technicals</TabsTrigger>
            <TabsTrigger value="valuation">Valuation</TabsTrigger>
            <TabsTrigger value="analyst">Analyst</TabsTrigger>
            <TabsTrigger value="earnings">Earnings</TabsTrigger>
          </TabsList>
          
          <TabsContent value="overview" className="p-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Card>
                  <CardContent className="p-4">
                    <div className="flex flex-col">
                      <div className="flex items-baseline justify-between">
                        <h2 className="text-3xl font-bold">{formatCurrency(asset.price)}</h2>
                        <span className={`text-sm font-medium ${asset.change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {asset.change >= 0 ? '+' : ''}{formatCurrency(asset.change)} ({formatPercentage(asset.changePercent)})
                        </span>
                      </div>
                      <div className="mt-4 grid grid-cols-2 gap-y-2">
                        <div className="text-sm text-muted-foreground">Market Cap</div>
                        <div className="text-sm font-medium text-right">{formatMarketCap(asset.marketCap)}</div>
                        
                        <div className="text-sm text-muted-foreground">Volume</div>
                        <div className="text-sm font-medium text-right">{formatNumber(asset.volume, 0)}</div>
                        
                        <div className="text-sm text-muted-foreground">Recommendation</div>
                        <div className="text-sm font-medium text-right">
                          <span className={`px-2 py-0.5 text-xs rounded-full ${
                            asset.recommendation === 'Buy' || asset.recommendation === 'Strong Buy' ? 'bg-green-100 text-green-800' : 
                            asset.recommendation === 'Sell' || asset.recommendation === 'Strong Sell' ? 'bg-red-100 text-red-800' : 
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {asset.recommendation}
                          </span>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
              
              <div>
                <Card>
                  <CardContent className="p-4">
                    <div className="grid grid-cols-2 gap-y-2">
                      <div className="text-sm text-muted-foreground">Daily Change</div>
                      <div className={`text-sm font-medium text-right ${asset.change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {formatPercentage(asset.changePercent)}
                      </div>
                      
                      <div className="text-sm text-muted-foreground">Weekly Change</div>
                      <div className={`text-sm font-medium text-right ${asset.change1w >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {formatPercentage(asset.changePercent1w)}
                      </div>
                      
                      <div className="text-sm text-muted-foreground">Monthly Change</div>
                      <div className={`text-sm font-medium text-right ${asset.change1m >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {formatPercentage(asset.changePercent1m)}
                      </div>
                      
                      <div className="text-sm text-muted-foreground">3M Momentum</div>
                      <div className={`text-sm font-medium text-right ${asset.momentum3m && asset.momentum3m >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {formatPercentage(asset.momentum3m)}
                      </div>
                      
                      <div className="text-sm text-muted-foreground">P/E Ratio</div>
                      <div className="text-sm font-medium text-right">{formatNumber(asset.peRatio)}</div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          </TabsContent>
          
          <TabsContent value="fundamentals" className="p-4">
            <Card>
              <CardContent className="p-4">
                <div className="grid grid-cols-2 gap-y-2">
                  <div className="text-sm text-muted-foreground">P/E Ratio</div>
                  <div className="text-sm font-medium text-right">{formatNumber(asset.peRatio)}</div>
                  
                  <div className="text-sm text-muted-foreground">PEG Ratio</div>
                  <div className="text-sm font-medium text-right">{formatNumber(asset.pegRatio)}</div>
                  
                  <div className="text-sm text-muted-foreground">ROE</div>
                  <div className="text-sm font-medium text-right">{formatPercentage(asset.roe)}</div>
                  
                  <div className="text-sm text-muted-foreground">EPS Growth</div>
                  <div className={`text-sm font-medium text-right ${asset.epsGrowth && asset.epsGrowth >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {formatPercentage(asset.epsGrowth)}
                  </div>
                  
                  <div className="text-sm text-muted-foreground">Revenue Growth</div>
                  <div className={`text-sm font-medium text-right ${asset.revenueGrowth && asset.revenueGrowth >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {formatPercentage(asset.revenueGrowth)}
                  </div>
                  
                  <div className="text-sm text-muted-foreground">Debt/Equity</div>
                  <div className="text-sm font-medium text-right">{formatNumber(asset.debtEquity)}</div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
          
          <TabsContent value="technicals" className="p-4">
            <Card>
              <CardContent className="p-4">
                <div className="grid grid-cols-2 gap-y-2">
                  <div className="text-sm text-muted-foreground">50-Day MA</div>
                  <div className="text-sm font-medium text-right">{formatCurrency(asset.sma50)}</div>
                  
                  <div className="text-sm text-muted-foreground">200-Day MA</div>
                  <div className="text-sm font-medium text-right">{formatCurrency(asset.sma200)}</div>
                  
                  <div className="text-sm text-muted-foreground">Price vs 50-Day MA</div>
                  <div className={`text-sm font-medium text-right ${asset.priceVsSma50 && asset.priceVsSma50 >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {formatPercentage(asset.priceVsSma50)}
                  </div>
                  
                  <div className="text-sm text-muted-foreground">Price vs 200-Day MA</div>
                  <div className={`text-sm font-medium text-right ${asset.priceVsSma200 && asset.priceVsSma200 >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {formatPercentage(asset.priceVsSma200)}
                  </div>
                  
                  <div className="text-sm text-muted-foreground">RSI (14)</div>
                  <div className={`text-sm font-medium text-right ${
                    asset.rsi && asset.rsi > 70 ? 'text-red-600' : 
                    asset.rsi && asset.rsi < 30 ? 'text-green-600' : 'text-gray-600'
                  }`}>
                    {asset.rsi ? formatNumber(asset.rsi) : 'N/A'}
                  </div>
                  
                  <div className="text-sm text-muted-foreground">YTD Change</div>
                  <div className={`text-sm font-medium text-right ${asset.priceChangeYtd && asset.priceChangeYtd >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {formatPercentage(asset.priceChangeYtd)}
                  </div>
                  
                  <div className="text-sm text-muted-foreground">3M Volatility</div>
                  <div className="text-sm font-medium text-right">{formatPercentage(asset.volatility3m)}</div>
                  
                  <div className="text-sm text-muted-foreground">Average Volume (10d)</div>
                  <div className="text-sm font-medium text-right">{asset.avgVolume10d ? formatNumber(asset.avgVolume10d, 0) : 'N/A'}</div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
          
          <TabsContent value="valuation" className="p-4">
            <Card>
              <CardContent className="p-4">
                <div className="grid grid-cols-2 gap-y-2">
                  <div className="text-sm text-muted-foreground">Price/Book</div>
                  <div className="text-sm font-medium text-right">{formatNumber(asset.priceToBook)}</div>
                  
                  <div className="text-sm text-muted-foreground">Price/Sales</div>
                  <div className="text-sm font-medium text-right">{formatNumber(asset.priceToSales)}</div>
                  
                  <div className="text-sm text-muted-foreground">Forward P/E</div>
                  <div className="text-sm font-medium text-right">{formatNumber(asset.forwardPE)}</div>
                  
                  <div className="text-sm text-muted-foreground">EV/EBITDA</div>
                  <div className="text-sm font-medium text-right">{formatNumber(asset.evToEbitda)}</div>
                  
                  <div className="text-sm text-muted-foreground">Debt/Equity</div>
                  <div className="text-sm font-medium text-right">{formatNumber(asset.debtEquity)}</div>
                  
                  <div className="text-sm text-muted-foreground">Dividend Yield</div>
                  <div className="text-sm font-medium text-right">{formatPercentage(asset.dividendYield)}</div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
          
          <TabsContent value="analyst" className="p-4">
            <Card>
              <CardContent className="p-4">
                <div className="grid grid-cols-2 gap-y-2">
                  <div className="text-sm text-muted-foreground">Target High</div>
                  <div className="text-sm font-medium text-right">{formatCurrency(asset.targetHigh)}</div>
                  
                  <div className="text-sm text-muted-foreground">Target Low</div>
                  <div className="text-sm font-medium text-right">{formatCurrency(asset.targetLow)}</div>
                  
                  <div className="text-sm text-muted-foreground">Target Mean</div>
                  <div className="text-sm font-medium text-right">{formatCurrency(asset.targetMean)}</div>
                  
                  <div className="text-sm text-muted-foreground">Target Median</div>
                  <div className="text-sm font-medium text-right">{formatCurrency(asset.targetMedian)}</div>
                  
                  <div className="text-sm text-muted-foreground">Price to Target</div>
                  <div className={`text-sm font-medium text-right ${asset.priceToTarget && asset.priceToTarget >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {formatPercentage(asset.priceToTarget)}
                  </div>
                  
                  <div className="text-sm text-muted-foreground">Last Updated</div>
                  <div className="text-sm font-medium text-right">{asset.targetLastUpdated || 'N/A'}</div>
                  
                  <div className="text-sm text-muted-foreground">Analyst Count</div>
                  <div className="text-sm font-medium text-right">{asset.analystCount || 'N/A'}</div>
                  
                  <div className="text-sm text-muted-foreground">Strong Buy / Buy / Hold</div>
                  <div className="text-sm font-medium text-right">
                    {asset.strongBuy || 0} / {asset.buy || 0} / {asset.hold || 0}
                  </div>
                  
                  <div className="text-sm text-muted-foreground">Sell / Strong Sell</div>
                  <div className="text-sm font-medium text-right">
                    {asset.sell || 0} / {asset.strongSell || 0}
                  </div>
                  
                  <div className="text-sm text-muted-foreground">Consensus Score</div>
                  <div className="text-sm font-medium text-right">{formatNumber(asset.consensusScore, 1)}/5.0</div>
                  
                  <div className="text-sm text-muted-foreground">Rating Trend</div>
                  <div className={`text-sm font-medium text-right ${
                    asset.analystRatingTrend === 'Improving' ? 'text-green-600' : 
                    asset.analystRatingTrend === 'Deteriorating' ? 'text-red-600' : 'text-gray-600'
                  }`}>
                    {asset.analystRatingTrend || 'N/A'}
                  </div>
                  
                  <div className="text-sm text-muted-foreground">Sentiment</div>
                  <div className="text-sm font-medium text-right">
                    <span className={`px-2 py-0.5 text-xs rounded-full ${
                      asset.sentiment === 'bullish' ? 'bg-green-100 text-green-800' : 
                      asset.sentiment === 'bearish' ? 'bg-red-100 text-red-800' : 
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {asset.sentiment.toUpperCase()}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
          
          <TabsContent value="earnings" className="p-4">
            <Card>
              <CardContent className="p-4">
                <div className="grid grid-cols-2 gap-y-2">
                  <div className="text-sm text-muted-foreground">Last EPS (Actual)</div>
                  <div className="text-sm font-medium text-right">{formatCurrency(asset.epsActual)}</div>
                  
                  <div className="text-sm text-muted-foreground">Last EPS (Estimate)</div>
                  <div className="text-sm font-medium text-right">{formatCurrency(asset.epsEstimate)}</div>
                  
                  <div className="text-sm text-muted-foreground">EPS Surprise %</div>
                  <div className={`text-sm font-medium text-right ${asset.epsSurprisePercent && asset.epsSurprisePercent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {formatPercentage(asset.epsSurprisePercent)}
                  </div>
                  
                  <div className="text-sm text-muted-foreground">Earnings Beat Rate</div>
                  <div className="text-sm font-medium text-right">{formatPercentage(asset.earningsBeatRate)}</div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  )
} 