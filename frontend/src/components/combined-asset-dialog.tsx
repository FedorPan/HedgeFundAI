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
  id: number
  ticker: string
  score: number
  value_score: number
  growth_score: number
  risk_score: number
  analyst_score: number
  momentum_score: number
  sentiment: "bullish" | "bearish" | "neutral"
  sector: string
  price: number
  peRatio: number
  pegRatio: number
  roe: number
  epsGrowth: number
  revenueGrowth: number
  volatility3m: number
  debtEquity: number
  consensusScore: number
  analystRatingTrend: number
  momentum3m: number
  change: number
  changePercent: number
  change1w: number
  changePercent1w: number
  change1m: number
  changePercent1m: number
  marketCap: number
  volume: number
  inPortfolio: boolean
  inTarget: boolean
}

interface CombinedAssetDialogProps {
  asset: Asset | null
  open: boolean
  onOpenChange: (open: boolean) => void
}

const formatCurrency = (value: number): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value)
}

const formatNumber = (value: number, decimals: number = 2): string => {
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value)
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

// Mock AI reasoning data
const mockReasoningData = {
  'TICK5': {
    summary: "Strong buy recommendation based on solid growth metrics and positive analyst sentiment",
    positives: [
      "Revenue growth exceeded expectations for the last 3 quarters",
      "Strong market position in a rapidly expanding sector",
      "Recent product launches have been well-received by the market",
      "Technical indicators show positive momentum",
      "Analyst consensus has improved significantly in the last month"
    ],
    negatives: [
      "Slightly higher P/E ratio compared to industry average",
      "Potential regulatory challenges in European markets",
      "Competition is increasing in the core product segment"
    ],
    recommendation: "BUY",
    targetPrice: 115.50,
    confidenceScore: 85
  },
  'TICK42': {
    summary: "Sell recommendation due to deteriorating financials and negative growth outlook",
    positives: [
      "Strong cash position provides some downside protection",
      "Brand recognition remains high despite recent challenges",
      "Dividend yield is attractive compared to peers"
    ],
    negatives: [
      "Revenue decline for 4 consecutive quarters",
      "Profit margins are contracting due to increased costs",
      "Recent management changes have created uncertainty",
      "Technical indicators show a strong downtrend",
      "Product pipeline appears weak compared to competitors",
      "Market share is declining in key segments"
    ],
    recommendation: "SELL",
    targetPrice: 155.75,
    confidenceScore: 82
  },
  'TICK28': {
    summary: "Moderate buy based on promising pipeline and attractive valuation",
    positives: [
      "New product approvals expected within the next 6 months",
      "Valuation metrics are attractive compared to historical averages",
      "Cost-cutting initiatives are starting to show results",
      "Recent acquisitions strengthen the company's market position"
    ],
    negatives: [
      "Revenue growth has been inconsistent",
      "Regulatory risks in key markets",
      "Integration challenges with recent acquisitions"
    ],
    recommendation: "BUY",
    targetPrice: 52.25,
    confidenceScore: 70
  }
};

// Default reasoning for tickers without specific data
const defaultReasoning = {
  summary: "Neutral outlook based on balanced risk-reward profile",
  positives: [
    "Reasonable valuation compared to sector peers",
    "Stable market position in core segments",
    "Management team has a proven track record"
  ],
  negatives: [
    "Growth metrics are average compared to peers",
    "Competitive pressures may impact margins",
    "Limited catalysts for significant price movement in the near term"
  ],
  recommendation: "HOLD",
  targetPrice: 0, // Will be replaced
  confidenceScore: 50
};

export function CombinedAssetDialog({ asset, open, onOpenChange }: CombinedAssetDialogProps) {
  if (!asset) return null

  // Get reasoning data for the ticker, or use default with adjusted price
  const reasoning = mockReasoningData[asset.ticker as keyof typeof mockReasoningData] || {
    ...defaultReasoning,
    targetPrice: asset.price * 1.05 // Set a default target 5% above current price
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[700px] max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center justify-between">
            <div>
              <DialogTitle className="text-xl flex items-center gap-2">
                {asset.ticker}
                <span className={`px-2 py-0.5 text-xs rounded-full ${
                  asset.sentiment === 'bullish' ? 'bg-green-100 text-green-800' : 
                  asset.sentiment === 'bearish' ? 'bg-red-100 text-red-800' : 
                  'bg-gray-100 text-gray-800'
                }`}>
                  {asset.sentiment.toUpperCase()}
                </span>
                <span className={`px-2 py-0.5 text-xs rounded-full ${
                  reasoning.recommendation === 'BUY' ? 'bg-green-100 text-green-800' : 
                  reasoning.recommendation === 'SELL' ? 'bg-red-100 text-red-800' : 
                  'bg-yellow-100 text-yellow-800'
                }`}>
                  {reasoning.recommendation}
                </span>
              </DialogTitle>
              <DialogDescription className="text-sm text-muted-foreground">
                {asset.sector} | {formatMarketCap(asset.marketCap)} | Score: {asset.score >= 0 ? "+" : ""}{formatNumber(asset.score, 1)}
              </DialogDescription>
            </div>
            <DialogClose asChild>
              <Button variant="ghost" className="h-8 w-8 p-0" aria-label="Close">
                <X className="h-4 w-4" />
              </Button>
            </DialogClose>
          </div>
        </DialogHeader>
        
        <Tabs defaultValue="details" className="mt-2">
          <TabsList className="w-full">
            <TabsTrigger value="details" className="flex-1">Metrics & Details</TabsTrigger>
            <TabsTrigger value="ai-reasoning" className="flex-1">AI Analysis</TabsTrigger>
          </TabsList>
          
          <TabsContent value="details" className="mt-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <h3 className="font-medium mb-2">Price & Performance</h3>
                <Card>
                  <CardContent className="p-4">
                    <div className="grid grid-cols-2 gap-y-2">
                      <div className="text-sm text-muted-foreground">Current Price</div>
                      <div className="text-sm font-medium text-right">{formatCurrency(asset.price)}</div>
                      
                      <div className="text-sm text-muted-foreground">Daily Change</div>
                      <div className={`text-sm font-medium text-right ${asset.change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {asset.change >= 0 ? '+' : ''}{formatNumber(asset.changePercent, 2)}%
                      </div>
                      
                      <div className="text-sm text-muted-foreground">Weekly Change</div>
                      <div className={`text-sm font-medium text-right ${asset.change1w >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {asset.change1w >= 0 ? '+' : ''}{formatNumber(asset.changePercent1w, 2)}%
                      </div>
                      
                      <div className="text-sm text-muted-foreground">Monthly Change</div>
                      <div className={`text-sm font-medium text-right ${asset.change1m >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {asset.change1m >= 0 ? '+' : ''}{formatNumber(asset.changePercent1m, 2)}%
                      </div>
                      
                      <div className="text-sm text-muted-foreground">3M Momentum</div>
                      <div className={`text-sm font-medium text-right ${asset.momentum3m >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {asset.momentum3m >= 0 ? '+' : ''}{formatNumber(asset.momentum3m, 2)}%
                      </div>
                      
                      <div className="text-sm text-muted-foreground">3M Volatility</div>
                      <div className="text-sm font-medium text-right">{formatNumber(asset.volatility3m, 2)}</div>
                      
                      <div className="text-sm text-muted-foreground">Volume</div>
                      <div className="text-sm font-medium text-right">{formatNumber(asset.volume, 0)}</div>
                    </div>
                  </CardContent>
                </Card>
              </div>
              
              <div>
                <h3 className="font-medium mb-2">Fundamental Metrics</h3>
                <Card>
                  <CardContent className="p-4">
                    <div className="grid grid-cols-2 gap-y-2">
                      <div className="text-sm text-muted-foreground">P/E Ratio</div>
                      <div className="text-sm font-medium text-right">{formatNumber(asset.peRatio, 2)}</div>
                      
                      <div className="text-sm text-muted-foreground">PEG Ratio</div>
                      <div className="text-sm font-medium text-right">{formatNumber(asset.pegRatio, 2)}</div>
                      
                      <div className="text-sm text-muted-foreground">ROE</div>
                      <div className="text-sm font-medium text-right">{formatNumber(asset.roe, 2)}%</div>
                      
                      <div className="text-sm text-muted-foreground">EPS Growth</div>
                      <div className={`text-sm font-medium text-right ${asset.epsGrowth >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {asset.epsGrowth >= 0 ? '+' : ''}{formatNumber(asset.epsGrowth, 2)}%
                      </div>
                      
                      <div className="text-sm text-muted-foreground">Revenue Growth</div>
                      <div className={`text-sm font-medium text-right ${asset.revenueGrowth >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {asset.revenueGrowth >= 0 ? '+' : ''}{formatNumber(asset.revenueGrowth, 2)}%
                      </div>
                      
                      <div className="text-sm text-muted-foreground">Debt/Equity</div>
                      <div className="text-sm font-medium text-right">{formatNumber(asset.debtEquity, 2)}</div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
            
            <div className="mt-4">
              <h3 className="font-medium mb-2">Analyst Metrics</h3>
              <Card>
                <CardContent className="p-4">
                  <div className="grid grid-cols-2 gap-y-2">
                    <div className="text-sm text-muted-foreground">Consensus Score</div>
                    <div className="text-sm font-medium text-right">{formatNumber(asset.consensusScore, 1)}/5.0</div>
                    
                    <div className="text-sm text-muted-foreground">Rating Trend</div>
                    <div className={`text-sm font-medium text-right ${asset.analystRatingTrend >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {asset.analystRatingTrend >= 0 ? '+' : ''}{formatNumber(asset.analystRatingTrend, 1)}
                    </div>
                    
                    <div className="text-sm text-muted-foreground">Value Score</div>
                    <div className={`text-sm font-medium text-right ${asset.value_score >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {asset.value_score >= 0 ? '+' : ''}{formatNumber(asset.value_score, 1)}
                    </div>
                    
                    <div className="text-sm text-muted-foreground">Growth Score</div>
                    <div className={`text-sm font-medium text-right ${asset.growth_score >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {asset.growth_score >= 0 ? '+' : ''}{formatNumber(asset.growth_score, 1)}
                    </div>
                    
                    <div className="text-sm text-muted-foreground">Risk Score</div>
                    <div className={`text-sm font-medium text-right ${asset.risk_score >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {asset.risk_score >= 0 ? '+' : ''}{formatNumber(asset.risk_score, 1)}
                    </div>
                    
                    <div className="text-sm text-muted-foreground">Momentum Score</div>
                    <div className={`text-sm font-medium text-right ${asset.momentum_score >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {asset.momentum_score >= 0 ? '+' : ''}{formatNumber(asset.momentum_score, 1)}
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
          
          <TabsContent value="ai-reasoning" className="mt-4">
            <div className="mb-4">
              <div className="mb-2">
                <div className="font-medium text-lg">{reasoning.summary}</div>
                <div className="text-sm text-muted-foreground mt-1">Confidence Score: {reasoning.confidenceScore}%</div>
              </div>
              
              {reasoning.targetPrice > 0 && (
                <div className="p-3 bg-blue-50 rounded-md mb-4">
                  <div className="text-sm font-medium">Target Price: ${reasoning.targetPrice.toFixed(2)} ({formatNumber(reasoning.targetPrice / asset.price * 100 - 100, 2)}% from current)</div>
                </div>
              )}
            </div>
            
            <div className="grid grid-cols-1 gap-4">
              <Card>
                <CardContent className="p-4">
                  <h3 className="font-medium text-green-600 mb-2">Positive Factors</h3>
                  <ul className="list-disc pl-5 space-y-1">
                    {reasoning.positives.map((point, index) => (
                      <li key={index} className="text-sm">{point}</li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
              
              <Card>
                <CardContent className="p-4">
                  <h3 className="font-medium text-red-600 mb-2">Risk Factors</h3>
                  <ul className="list-disc pl-5 space-y-1">
                    {reasoning.negatives.map((point, index) => (
                      <li key={index} className="text-sm">{point}</li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  )
} 